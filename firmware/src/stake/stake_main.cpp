/*
 * stake_main.cpp - Gaiapus field stake firmware (ESP32-S3-MINI-1 head board + probe board).
 *
 * The MCU lives in deep sleep. Each wake runs setup() from the top and sleeps again;
 * everything that must survive lives in RTC RAM (stake_state_t).
 *
 *   wake by timer  -> measure, queue, send (newest first + backlog), sleep
 *   wake by rain   -> count one bucket tip, sleep until the planned measurement
 *   wake by button -> show the status LED, measure and send now (flag bit0);
 *                     held 3 s -> diagnostic mode on USB (live readings, calibration)
 *   power-on       -> LED sweep, measure and send at once (installation feedback)
 *
 * Contract: docs/protocolo-dados.md. Pins: include/pinos.h (= schematic).
 */
#include <Arduino.h>
#include <math.h>
#include <sys/time.h>
#include "esp_sleep.h"
#include "esp_idf_version.h"
#include "esp_mac.h"
#include "esp_random.h"
#include "driver/gpio.h"
#include "driver/rtc_io.h"
#include "gaiapus_protocol.h"
#include "pinos.h"
#include "config.h"
#include "stake_core.h"
#include "sensors.h"
#include "link.h"

RTC_DATA_ATTR static stake_state_t st;

static uint32_t node_id;
static volatile uint16_t rain_awake;                    /* tips counted while awake */
static volatile uint32_t rain_last_ms;
static uint32_t led_until_ms;                           /* keep status LED on until */

static const int HELD_PINS[] = { PIN_LORA_NSS, PIN_LORA_NRST, PIN_LORA_TXEN, PIN_LORA_RXEN,
                                 PIN_PWR_NTC, PIN_PWR_OSC15, PIN_PWR_OSC40,
                                 PIN_LED_G, PIN_LED_Y, PIN_LED_R };
static const int LED_PINS[3] = { PIN_LED_G, PIN_LED_Y, PIN_LED_R };   /* index = GP_LED_x - 1 */

#define LOG(...) Serial.printf(__VA_ARGS__)
#if ESP_IDF_VERSION_MAJOR >= 5
#define EXT1_LOW ESP_EXT1_WAKEUP_ANY_LOW
#else
#define EXT1_LOW ESP_EXT1_WAKEUP_ALL_LOW                /* single pin: same as "any low" */
#endif

static int64_t now_s(void) { return (int64_t)time(nullptr); }

/* ------------------------------------------------------------------ pins */
static void pins_wake(void)
{
    /* drive the same levels the pads were held at, then release the hold */
    pinMode(PIN_LORA_NSS, OUTPUT);  digitalWrite(PIN_LORA_NSS, HIGH);
    pinMode(PIN_LORA_NRST, OUTPUT); digitalWrite(PIN_LORA_NRST, HIGH);
    for (int p : { PIN_LORA_TXEN, PIN_LORA_RXEN, PIN_PWR_NTC, PIN_PWR_OSC15, PIN_PWR_OSC40,
                   PIN_LED_G, PIN_LED_Y, PIN_LED_R }) {
        pinMode(p, OUTPUT);
        digitalWrite(p, LOW);
    }
    gpio_deep_sleep_hold_dis();
    for (int p : HELD_PINS) gpio_hold_dis((gpio_num_t)p);
    rtc_gpio_deinit((gpio_num_t)PIN_RAIN);
    rtc_gpio_deinit((gpio_num_t)PIN_BTN);
    pinMode(PIN_RAIN, INPUT);                           /* 470k external pull-up */
    pinMode(PIN_BTN, INPUT);                            /* 10k external pull-up  */
    pinMode(PIN_LORA_BUSY, INPUT);
    pinMode(PIN_LORA_DIO1, INPUT);
}

static void pins_sleep(void)
{
    /* NSS/NRST high keep the SX1262 asleep, TXEN/RXEN low keep the RF switch off,
     * probe and LEDs unpowered. Held through deep sleep (digital pads included). */
    digitalWrite(PIN_LORA_NSS, HIGH);
    digitalWrite(PIN_LORA_NRST, HIGH);
    for (int p : { PIN_LORA_TXEN, PIN_LORA_RXEN, PIN_PWR_NTC, PIN_PWR_OSC15, PIN_PWR_OSC40,
                   PIN_LED_G, PIN_LED_Y, PIN_LED_R })
        digitalWrite(p, LOW);
    for (int p : HELD_PINS) gpio_hold_en((gpio_num_t)p);
    gpio_deep_sleep_hold_en();
}

/* ------------------------------------------------------------------ rain */
static void IRAM_ATTR on_rain(void)
{
    uint32_t t = millis();
    if (t - rain_last_ms > RAIN_DEBOUNCE_MS) { rain_awake++; rain_last_ms = t; }
}

static uint16_t take_rain(void)
{
    noInterrupts();
    uint32_t total = (uint32_t)st.rain_pulses + rain_awake;
    rain_awake = 0;
    st.rain_pulses = 0;
    interrupts();
    return (uint16_t)(total > 65535 ? 65535 : total);
}

static bool wait_level(int pin, int level, uint32_t max_ms)
{
    uint32_t t0 = millis();
    while (digitalRead(pin) != level) {
        if (millis() - t0 >= max_ms) return false;
        delay(5);
    }
    return true;
}

/* ------------------------------------------------------------------ LEDs */
static void led_show(uint8_t state)
{
    for (int i = 0; i < 3; i++) digitalWrite(LED_PINS[i], state == i + 1 ? HIGH : LOW);
}

static void led_sweep(void)                             /* "I'm alive, no status yet" */
{
    for (int i = 0; i < 3; i++) { led_show((uint8_t)(i + 1)); delay(150); }
    led_show(GP_LED_OFF);
}

static void led_finish(void)
{
    if (led_until_ms) {                                 /* button: hold the status until the deadline */
        int32_t left = (int32_t)(led_until_ms - millis());
        if (st.led == GP_LED_OFF) led_sweep();
        else { led_show(st.led); if (left > 0) delay((uint32_t)left); }
    } else if (st.led != GP_LED_OFF) {                  /* routine cycle: short flash only */
        led_show(st.led);
        delay(LED_FLASH_MS);
    }
    led_show(GP_LED_OFF);
}

/* ------------------------------------------------------------------ measurement */
static void build_uplink(const readings_t *r, uint16_t rain, uint8_t extra_flags, uint8_t out[GP_UPLINK_LEN])
{
    gp_uplink_t m;
    memset(&m, 0, sizeof m);
    m.version = GP_PROTOCOL_VERSION;
    m.node_id = node_id;
    m.seq = ++st.seq;
    m.raw_15 = r->raw_15;
    m.raw_40 = r->raw_40;
    m.t_soil_15 = gp_centi(r->t_soil_15);
    m.t_soil_40 = gp_centi(r->t_soil_40);
    m.t_air = gp_centi(r->t_air);
    m.rh_air = isnan(r->rh_air) ? 0 : (uint8_t)lroundf(r->rh_air);
    m.rain_pulses = rain;
    m.vbat_mv = r->vbat_mv;
    m.age_min = 0;
    m.flags = extra_flags;
    if (r->vbat_mv < VBAT_LOW_MV) m.flags |= GP_FLAG_LOW_BATTERY;
    if (!sensors_ok(r)) m.flags |= GP_FLAG_SENSOR_ERROR;
    if (r->charging) m.flags |= GP_FLAG_CHARGING;
    gp_encode_uplink(&m, out);
}

static void log_readings(const readings_t *r)
{
    LOG("raw15=%u raw40=%u  t15=%.2f t40=%.2f  air=%.2fC %.0f%%  vbat=%umV  chg=%d done=%d\n",
        r->raw_15, r->raw_40, r->t_soil_15, r->t_soil_40, r->t_air, r->rh_air, r->vbat_mv,
        r->charging, r->charged);
}

/* ------------------------------------------------------------------ cycle */
static void send_queue(bool cold_boot)
{
    uint16_t vbat = sensors_vbat_mv();
    if (vbat < link_min_mv()) {
        LOG("[cycle] battery %u mV < %u mV: queued only (%u waiting)\n", vbat, link_min_mv(), st.q_count);
        return;
    }
    if (!link_begin(&st, cold_boot)) {
        st.fail_streak++;
        link_end(&st);
        LOG("[cycle] %s down, %u waiting\n", link_name(), st.q_count);
        return;
    }
    for (int i = 0; i < MAX_SENDS_PER_CYCLE; i++) {
        uint8_t pkt[GP_UPLINK_LEN];
        if (!core_queue_peek_newest(&st, now_s(), pkt)) break;
        gp_downlink_t dl;
        bool got_dl = false;
        bool ok = link_send(&st, pkt, &dl, &got_dl);
        if (got_dl) {
            if (dl.led != st.led || dl.interval_min != st.interval_min)
                LOG("[down] led %u -> %u, interval %u -> %u min\n", st.led, dl.led, st.interval_min, dl.interval_min);
            core_apply_downlink(&st, &dl);
            if (led_until_ms) led_show(st.led);          /* user is looking: show the fresh status */
        }
        if (!ok) { st.fail_streak++; break; }
        core_queue_pop_newest(&st);
        st.delivered++;
        st.fail_streak = 0;
    }
    link_end(&st);
    LOG("[cycle] %u still queued, delivered %lu, dropped %lu\n", st.q_count,
        (unsigned long)st.delivered, (unsigned long)st.dropped);
}

static void measure_and_send(bool cold_boot)
{
    readings_t r;
    sensors_read(&r);
    log_readings(&r);
    uint8_t pkt[GP_UPLINK_LEN];
    build_uplink(&r, take_rain(), st.pending_flags, pkt);
    st.pending_flags = 0;
    core_queue_push(&st, pkt, now_s());
    LOG("[cycle] seq %u queued\n", st.seq);
    send_queue(cold_boot);
}

/* Button held DIAG_HOLD_MS at wake: live readings on USB for factory calibration
 * (probe in air / in water) and bench checks. Press again to leave. */
static void diagnostics(void)
{
    LOG("\n=== DIAGNOSTICS node %08lx (%s link) - press the button to exit ===\n",
        (unsigned long)node_id, link_name());
    LOG("state: seq %u, interval %u min, led %u, queued %u, delivered %lu, dropped %lu, boots %lu\n",
        st.seq, st.interval_min, st.led, st.q_count, (unsigned long)st.delivered,
        (unsigned long)st.dropped, (unsigned long)st.boots);
    wait_level(PIN_BTN, HIGH, 10000);
    uint32_t t0 = millis();
    uint8_t led = GP_LED_GREEN;
    while (millis() - t0 < (uint32_t)DIAG_DURATION_S * 1000) {
        readings_t r;
        sensors_read(&r);
        log_readings(&r);
        led_show(led);
        led = led == GP_LED_RED ? (uint8_t)GP_LED_GREEN : (uint8_t)(led + 1);
        for (int i = 0; i < 100; i++) {
            if (digitalRead(PIN_BTN) == LOW) { led_show(GP_LED_OFF); wait_level(PIN_BTN, HIGH, 5000); return; }
            delay(10);
        }
    }
    led_show(GP_LED_OFF);
}

/* ------------------------------------------------------------------ sleep */
static void go_to_sleep(int64_t seconds)
{
    if (seconds < 1) seconds = 1;
    noInterrupts();
    uint32_t extra = rain_awake;
    rain_awake = 0;
    interrupts();
    st.rain_pulses = (uint16_t)((uint32_t)st.rain_pulses + extra > 65535 ? 65535 : st.rain_pulses + extra);

    esp_sleep_disable_wakeup_source(ESP_SLEEP_WAKEUP_ALL);
    esp_sleep_enable_timer_wakeup((uint64_t)seconds * 1000000ULL);
    if (digitalRead(PIN_RAIN) == LOW) st.rain_stuck = 1;     /* reed resting closed: would wake forever */
    if (!st.rain_stuck) esp_sleep_enable_ext0_wakeup((gpio_num_t)PIN_RAIN, 0);
    if (wait_level(PIN_BTN, HIGH, 2000))
        esp_sleep_enable_ext1_wakeup(1ULL << PIN_BTN, EXT1_LOW);

    LOG("[sleep] %lld s (next measurement in %lld s)%s\n", (long long)seconds,
        (long long)core_seconds_to_due(&st, now_s()), st.rain_stuck ? " rain input stuck low" : "");
    Serial.flush();
    pins_sleep();
    esp_deep_sleep_start();
}

/* ------------------------------------------------------------------ entry */
void setup(void)
{
    pins_wake();
    Serial.begin(115200);
#if ARDUINO_USB_CDC_ON_BOOT
    Serial.setTxTimeoutMs(0);                            /* never block when no USB host is attached */
#endif
    esp_sleep_wakeup_cause_t cause = esp_sleep_get_wakeup_cause();
    bool cold = cause == ESP_SLEEP_WAKEUP_UNDEFINED;
    if (core_init(&st, esp_random())) LOG("[boot] RTC state reset\n");
    st.boots++;

    uint8_t mac[6];
    esp_read_mac(mac, ESP_MAC_WIFI_STA);
    node_id = ((uint32_t)mac[2] << 24) | ((uint32_t)mac[3] << 16) | ((uint32_t)mac[4] << 8) | mac[5];
    LOG("\n[boot] gaiapus stake %08lx  link=%s  wake=%d  t=%lld\n", (unsigned long)node_id, link_name(),
        (int)cause, (long long)now_s());

    sensors_init();
    attachInterrupt(digitalPinToInterrupt(PIN_RAIN), on_rain, FALLING);

    bool run = false;
    switch (cause) {
    case ESP_SLEEP_WAKEUP_EXT0:                          /* rain gauge tip */
        rain_awake++;
        rain_last_ms = millis();
        if (!wait_level(PIN_RAIN, HIGH, RAIN_RELEASE_WAIT_MS)) st.rain_stuck = 1;
        LOG("[rain] tip, %u since last measurement\n", st.rain_pulses + rain_awake);
        run = core_seconds_to_due(&st, now_s()) <= 0;
        break;
    case ESP_SLEEP_WAKEUP_EXT1: {                        /* user button */
        if (st.led != GP_LED_OFF) led_show(st.led);
        led_until_ms = millis() + LED_SHOW_MS;
        if (!wait_level(PIN_BTN, HIGH, DIAG_HOLD_MS)) { led_show(GP_LED_OFF); diagnostics(); led_until_ms = 0; }
        st.pending_flags |= GP_FLAG_BUTTON;
        run = true;
        break;
    }
    case ESP_SLEEP_WAKEUP_TIMER:
        st.rain_stuck = 0;                               /* give the reed another chance every cycle */
        run = core_seconds_to_due(&st, now_s()) <= 1;
        break;
    default:                                             /* power-on, reset, brown-out, USB flash */
        led_sweep();
        run = true;
        break;
    }

    if (run) {
        measure_and_send(cold);
        led_finish();
        go_to_sleep(core_schedule_next(&st, now_s()));
    }
    go_to_sleep(core_seconds_to_due(&st, now_s()));
}

void loop(void) { /* never reached: setup() always ends in deep sleep */ }

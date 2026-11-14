/*
 * Gaiapus bench / Wokwi firmware (ESP32-S3, Arduino core).
 *
 * Same measurement cycle and the same 25-byte packet as the field stake; the only
 * difference is the link: the stake sends the packet over LoRa to a gateway, the
 * bench publishes the gateway's JSON itself over Wi-Fi/MQTT (Wokwi has no LoRa).
 *
 * Simulated sensors on the bench (honest labels for the jury):
 *   - soil moisture 15/40 cm : potentiometers on the oscillator pins, mapped to the
 *                              raw count range of the real probe (wetter = lower count)
 *   - soil temperature       : NTC 10k modules (same divider as the PCB)
 *   - air T/RH               : DHT22 as a stand-in for the SHT40
 *   - battery                : potentiometer mapped to 2.5-3.65 V
 *   - rain gauge             : push button = one bucket tip
 * Contract: docs/protocolo-dados.md
 */
#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <DHTesp.h>
#include <time.h>
#include <math.h>
#include "gaiapus_protocol.h"
#include "pinos.h"

/* ---------------- configuration ---------------- */
#ifndef WIFI_SSID
#define WIFI_SSID      "Wokwi-GUEST"
#define WIFI_PASS      ""
#define WIFI_CHANNEL   6
#endif
#ifndef MQTT_HOST
#define MQTT_HOST      "broker.hivemq.com"
#define MQTT_PORT      1883
#endif
#define DEMO_MS_PER_MIN   500     /* demo time: 1 protocol minute = 0.5 s (30 min -> 15 s) */
#define MM_PER_PULSE      0.2f    /* placeholder until mechanics defines the rain gauge   */
#define RAW_DRY           26000   /* oscillator counts in air  (to be measured on the probe) */
#define RAW_WET           12000   /* oscillator counts in water                               */
#define NTC_BETA          3950.0f /* Wokwi module; Murata NCP18XH103 on the PCB is 3380      */
#define VBAT_LOW_MV       3000
#define LED_STEADY        1       /* demo: steady LED; field stake: short blink every 4 s    */
#define BUF_LEN           8       /* offline buffer (measurements not yet delivered)         */

/* ---------------- state ---------------- */
static WiFiClient net;
static PubSubClient mqtt(net);
static DHTesp dht;
static uint32_t node_id;
static char dev_id[9];
static char topic_up[48], topic_down[48];
static uint16_t seq;
static uint8_t interval_min = 30;
static uint8_t led_state = GP_LED_OFF;
static volatile uint16_t rain_pulses;
static volatile uint32_t rain_last_ms;
static volatile bool button_pressed;
static uint32_t next_measure_ms;

typedef struct { gp_uplink_t m; time_t taken_utc; } pending_t;
static pending_t buf[BUF_LEN];
static uint8_t buf_head, buf_count;

/* ---------------- interrupts ---------------- */
static void IRAM_ATTR on_rain(void)
{
    uint32_t now = millis();
    if (now - rain_last_ms > 50) { rain_pulses++; rain_last_ms = now; }   /* 50 ms debounce */
}
static void IRAM_ATTR on_button(void) { button_pressed = true; }

/* ---------------- sensors ---------------- */
static uint16_t read_moisture_raw(int pin)
{
    /* PCB: count oscillator edges with PCNT in a fixed gate. Bench: analog stand-in. */
    long adc = analogRead(pin);
    return (uint16_t)map(adc, 0, 4095, RAW_DRY, RAW_WET);
}

static float read_ntc_c(int pin)
{
    int a = analogRead(pin);
    if (a <= 0 || a >= 4095) return NAN;                 /* open or shorted thermistor */
    float r_ratio = (float)a / (4095.0f - (float)a);     /* R_ntc / R_fixed, NTC to GND */
    return 1.0f / (logf(r_ratio) / NTC_BETA + 1.0f / 298.15f) - 273.15f;
}

static uint16_t read_vbat_mv(void)
{
    /* PCB: (analogReadMilliVolts * 2). Bench: potentiometer mapped to a LiFePO4 range. */
    return (uint16_t)map(analogRead(PIN_VBAT_ADC), 0, 4095, 2500, 3650);
}

static gp_uplink_t measure(void)
{
    gp_uplink_t m = {};
    m.version = GP_PROTOCOL_VERSION;
    m.node_id = node_id;
    m.seq = ++seq;

    digitalWrite(PIN_PWR_NTC, HIGH);
    digitalWrite(PIN_PWR_OSC15, HIGH);
    digitalWrite(PIN_PWR_OSC40, HIGH);
    delay(5);                                            /* settle */
    m.raw_15 = read_moisture_raw(PIN_OSC15_FREQ);
    m.raw_40 = read_moisture_raw(PIN_OSC40_FREQ);
    float t15 = read_ntc_c(PIN_NTC15_ADC), t40 = read_ntc_c(PIN_NTC40_ADC);
    digitalWrite(PIN_PWR_NTC, LOW);
    digitalWrite(PIN_PWR_OSC15, LOW);
    digitalWrite(PIN_PWR_OSC40, LOW);

    TempAndHumidity th = dht.getTempAndHumidity();
    bool air_ok = !isnan(th.temperature) && !isnan(th.humidity);

    m.t_soil_15 = gp_centi(t15);
    m.t_soil_40 = gp_centi(t40);
    m.t_air     = air_ok ? gp_centi(th.temperature) : GP_TEMP_INVALID;
    m.rh_air    = air_ok ? (uint8_t)constrain(lroundf(th.humidity), 0, 100) : 0;

    noInterrupts();
    m.rain_pulses = rain_pulses; rain_pulses = 0;
    interrupts();

    m.vbat_mv = read_vbat_mv();
    m.age_min = 0;
    if (button_pressed) { m.flags |= GP_FLAG_BUTTON; button_pressed = false; }
    if (m.vbat_mv < VBAT_LOW_MV) m.flags |= GP_FLAG_LOW_BATTERY;
    if (isnan(t15) || isnan(t40) || !air_ok) m.flags |= GP_FLAG_SENSOR_ERROR;
    return m;
}

/* ---------------- output ---------------- */
static void apply_led(void)
{
    static const int pins[3] = { PIN_LED_G, PIN_LED_Y, PIN_LED_R };
    for (int i = 0; i < 3; i++) {
        bool on = (led_state == i + 1);
#if !LED_STEADY
        on = on && (millis() % 4000) < 60;               /* 60 ms flash every 4 s */
#endif
        digitalWrite(pins[i], on ? HIGH : LOW);
    }
}

static void iso_utc(time_t t, char *out, size_t n)
{
    struct tm tm;
    gmtime_r(&t, &tm);
    strftime(out, n, "%Y-%m-%dT%H:%M:%SZ", &tm);
}

static void fmt_temp(int16_t v, char *out, size_t n)
{
    if (v == GP_TEMP_INVALID) snprintf(out, n, "null");
    else snprintf(out, n, "%.2f", v / 100.0);
}

/* Builds exactly the JSON the LoRa gateway publishes (docs/protocolo-dados.md). */
static bool publish(const gp_uplink_t *m, time_t observed, time_t received)
{
    uint8_t pkt[GP_UPLINK_LEN];
    gp_encode_uplink(m, pkt);
    char hex[2 * GP_UPLINK_LEN + 1];
    for (unsigned i = 0; i < GP_UPLINK_LEN; i++) snprintf(hex + 2 * i, 3, "%02X", pkt[i]);

    char obs[24], rec[24], t15[12], t40[12], ta[12];
    iso_utc(observed, obs, sizeof obs);
    iso_utc(received, rec, sizeof rec);
    fmt_temp(m->t_soil_15, t15, sizeof t15);
    fmt_temp(m->t_soil_40, t40, sizeof t40);
    fmt_temp(m->t_air, ta, sizeof ta);

    char json[640];
    int len = snprintf(json, sizeof json,
        "{\"device_id\":\"%s\",\"seq\":%u,\"observed_at\":\"%s\",\"received_at\":\"%s\","
        "\"readings\":[{\"depth_cm\":15,\"raw_moisture\":%u,\"soil_temp_c\":%s},"
        "{\"depth_cm\":40,\"raw_moisture\":%u,\"soil_temp_c\":%s}],"
        "\"air_temp_c\":%s,\"air_rh_pct\":%u,\"rain_mm\":%.2f,\"battery_mv\":%u,"
        "\"rssi\":%d,\"snr\":null,\"flags\":%u,\"lora_payload_hex\":\"%s\"}",
        dev_id, m->seq, obs, rec, m->raw_15, t15, m->raw_40, t40, ta, m->rh_air,
        m->rain_pulses * MM_PER_PULSE, m->vbat_mv, (int)WiFi.RSSI(), m->flags, hex);
    if (len <= 0 || len >= (int)sizeof json) return false;

    Serial.printf("[up] LoRa payload (%u B): %s\n", GP_UPLINK_LEN, hex);
    bool ok = mqtt.connected() && mqtt.publish(topic_up, json);
    Serial.printf("[up] %s %s\n", ok ? "published" : "NOT SENT, buffered:", json);
    return ok;
}

static void buffer_push(const gp_uplink_t *m, time_t utc)
{
    uint8_t idx = (buf_head + buf_count) % BUF_LEN;
    if (buf_count == BUF_LEN) { buf_head = (buf_head + 1) % BUF_LEN; buf_count--; }   /* drop oldest */
    buf[idx].m = *m; buf[idx].taken_utc = utc;
    buf_count++;
}

static void buffer_flush(void)
{
    while (buf_count && mqtt.connected()) {
        pending_t *p = &buf[buf_head];
        time_t now = time(nullptr);
        long age = (long)(now - p->taken_utc) / 60;       /* real minutes: backend does received_at - idade_min */
        p->m.age_min = (uint16_t)(age < 0 ? 0 : (age > 65535 ? 65535 : age));
        if (!publish(&p->m, p->taken_utc, now)) return;
        buf_head = (buf_head + 1) % BUF_LEN;
        buf_count--;
    }
}

/* ---------------- downlink ---------------- */
static bool json_int(const char *s, const char *key, long *out)
{
    const char *p = strstr(s, key);
    if (!p) return false;
    p = strchr(p + strlen(key), ':');
    if (!p) return false;
    char *end;
    long v = strtol(p + 1, &end, 10);
    if (end == p + 1) return false;
    *out = v;
    return true;
}

static void on_mqtt(char *topic, byte *payload, unsigned int len)
{
    (void)topic;
    char s[128];
    len = len < sizeof s - 1 ? len : sizeof s - 1;
    memcpy(s, payload, len); s[len] = 0;
    long led, iv;
    uint8_t raw[GP_DOWNLINK_LEN] = { led_state, interval_min };
    if (json_int(s, "\"led\"", &led)) raw[0] = (uint8_t)led;
    if (json_int(s, "\"intervalo_min\"", &iv)) raw[1] = (uint8_t)constrain(iv, 1, 255);
    gp_downlink_t d;
    gp_decode_downlink(raw, sizeof raw, &d);              /* same validation as the stake */
    led_state = d.led;
    interval_min = d.interval_min;
    Serial.printf("[down] led=%u intervalo_min=%u (LoRa downlink bytes %02X %02X)\n",
                  led_state, interval_min, raw[0], raw[1]);
    apply_led();
}

/* ---------------- connectivity ---------------- */
static void ensure_connected(void)
{
    if (WiFi.status() != WL_CONNECTED) return;
    if (mqtt.connected()) return;
    static uint32_t last_try;
    if (millis() - last_try < 3000) return;
    last_try = millis();
    char cid[24];
    snprintf(cid, sizeof cid, "gaiapus-%s", dev_id);
    if (mqtt.connect(cid)) {
        mqtt.subscribe(topic_down);
        Serial.printf("[mqtt] connected, up: %s  down: %s\n", topic_up, topic_down);
    }
}

void setup(void)
{
    Serial.begin(115200);
    pinMode(PIN_BTN, INPUT_PULLUP);
    pinMode(PIN_RAIN, INPUT_PULLUP);
    for (int p : { PIN_LED_G, PIN_LED_Y, PIN_LED_R, PIN_PWR_NTC, PIN_PWR_OSC15, PIN_PWR_OSC40 }) {
        pinMode(p, OUTPUT);
        digitalWrite(p, LOW);
    }
    analogReadResolution(12);
    attachInterrupt(digitalPinToInterrupt(PIN_RAIN), on_rain, FALLING);
    attachInterrupt(digitalPinToInterrupt(PIN_BTN), on_button, FALLING);
    dht.setup(PIN_I2C_SDA, DHTesp::DHT22);

    WiFi.mode(WIFI_STA);
    uint8_t mac[6];
    WiFi.macAddress(mac);
    node_id = ((uint32_t)mac[2] << 24) | ((uint32_t)mac[3] << 16) | ((uint32_t)mac[4] << 8) | mac[5];
    snprintf(dev_id, sizeof dev_id, "%08lx", (unsigned long)node_id);
    snprintf(topic_up, sizeof topic_up, "gaiapus/devices/%s/up", dev_id);
    snprintf(topic_down, sizeof topic_down, "gaiapus/devices/%s/down", dev_id);
    Serial.printf("Gaiapus bench node %s\n", dev_id);

    WiFi.begin(WIFI_SSID, WIFI_PASS, WIFI_CHANNEL);
    uint32_t t0 = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - t0 < 15000) delay(100);
    configTime(0, 0, "pool.ntp.org", "time.google.com");
    struct tm tm;
    getLocalTime(&tm, 5000);                              /* UTC for observed_at */

    mqtt.setServer(MQTT_HOST, MQTT_PORT);
    mqtt.setCallback(on_mqtt);
    mqtt.setBufferSize(768);
    next_measure_ms = millis() + 2000;
}

void loop(void)
{
    ensure_connected();
    mqtt.loop();
    apply_led();

    bool due = (int32_t)(millis() - next_measure_ms) >= 0;
    if (due || button_pressed) {                          /* button = measure now (demo) */
        next_measure_ms = millis() + (uint32_t)interval_min * DEMO_MS_PER_MIN;
        gp_uplink_t m = measure();
        time_t now = time(nullptr);
        buffer_flush();                                   /* older first */
        if (buf_count || !publish(&m, now, now)) buffer_push(&m, now);
    }
    delay(10);
}

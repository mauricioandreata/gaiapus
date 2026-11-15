/*
 * sensors.cpp - measurement chain of the stake.
 *
 * Soil moisture : 74LVC1G14 RC oscillator next to each electrode (probe board),
 *                 0.5-2 MHz, counted by the PCNT for a 10 ms gate. One oscillator
 *                 powered at a time (no cross-coupling between the two electrodes).
 * Soil temp     : NTC 10k/B3380 to GND, 10k from PWR_NTC (powered only while reading).
 * Air T/RH      : SHT40 at 0x44, high-repeatability single shot, CRC checked.
 * Battery       : VBAT / 2 (2.2M + 2.2M, 100 nF) on ADC1.
 * Charger       : CN3058E CHRG / DONE, open drain, internal pull-ups while awake.
 */
#include <Arduino.h>
#include <Wire.h>
#include <math.h>
#include "esp_timer.h"
#include "esp_idf_version.h"
#include "pinos.h"
#include "config.h"
#include "sensors.h"

#if ESP_IDF_VERSION_MAJOR >= 5
#include "driver/pulse_cnt.h"
#else
#include "driver/pcnt.h"
#endif

#define OSC_HIGH_LIMIT 30000   /* PCNT is 16-bit signed: wrap at 30000 and accumulate */
#define SHT40_ADDR     0x44
#define SHT40_MEAS_HI  0xFD

/* ------------------------------------------------------------------ PCNT */
#if ESP_IDF_VERSION_MAJOR >= 5

static int64_t count_edges(int pin, int64_t *gate_us)
{
    pcnt_unit_config_t ucfg;
    memset(&ucfg, 0, sizeof ucfg);
    ucfg.low_limit = -1;
    ucfg.high_limit = OSC_HIGH_LIMIT;
    ucfg.flags.accum_count = 1;                       /* driver adds the wraps for us */
    pcnt_unit_handle_t unit = NULL;
    pcnt_channel_handle_t chan = NULL;
    int64_t total = -1;
    *gate_us = 0;

    if (pcnt_new_unit(&ucfg, &unit) != ESP_OK) return -1;
    pcnt_chan_config_t ccfg;
    memset(&ccfg, 0, sizeof ccfg);
    ccfg.edge_gpio_num = pin;
    ccfg.level_gpio_num = -1;
    if (pcnt_new_channel(unit, &ccfg, &chan) == ESP_OK &&
        pcnt_channel_set_edge_action(chan, PCNT_CHANNEL_EDGE_ACTION_INCREASE,
                                     PCNT_CHANNEL_EDGE_ACTION_HOLD) == ESP_OK &&
        pcnt_unit_add_watch_point(unit, OSC_HIGH_LIMIT) == ESP_OK &&
        pcnt_unit_enable(unit) == ESP_OK) {
        pcnt_unit_clear_count(unit);
        int64_t t0 = esp_timer_get_time();
        pcnt_unit_start(unit);
        while (esp_timer_get_time() - t0 < OSC_GATE_US) { }
        pcnt_unit_stop(unit);
        *gate_us = esp_timer_get_time() - t0;
        int c = 0;
        if (pcnt_unit_get_count(unit, &c) == ESP_OK) total = c;
        pcnt_unit_disable(unit);
        pcnt_unit_remove_watch_point(unit, OSC_HIGH_LIMIT);
    }
    if (chan) pcnt_del_channel(chan);
    pcnt_del_unit(unit);
    return total;
}

#else  /* ESP-IDF 4.4 (Arduino core 2.x): legacy driver */

static volatile int32_t s_wraps;
static void IRAM_ATTR pcnt_wrap_isr(void *arg) { (void)arg; s_wraps++; }

static int64_t count_edges(int pin, int64_t *gate_us)
{
    static bool isr_installed;
    pcnt_config_t c;
    memset(&c, 0, sizeof c);
    c.pulse_gpio_num = pin;
    c.ctrl_gpio_num = PCNT_PIN_NOT_USED;
    c.channel = PCNT_CHANNEL_0;
    c.unit = PCNT_UNIT_0;
    c.pos_mode = PCNT_COUNT_INC;
    c.neg_mode = PCNT_COUNT_DIS;
    c.lctrl_mode = PCNT_MODE_KEEP;
    c.hctrl_mode = PCNT_MODE_KEEP;
    c.counter_h_lim = OSC_HIGH_LIMIT;
    c.counter_l_lim = 0;
    *gate_us = 0;
    if (pcnt_unit_config(&c) != ESP_OK) return -1;
    pcnt_filter_disable(PCNT_UNIT_0);
    pcnt_event_enable(PCNT_UNIT_0, PCNT_EVT_H_LIM);
    if (!isr_installed) { pcnt_isr_service_install(0); isr_installed = true; }
    pcnt_isr_handler_remove(PCNT_UNIT_0);
    pcnt_isr_handler_add(PCNT_UNIT_0, pcnt_wrap_isr, NULL);
    pcnt_counter_pause(PCNT_UNIT_0);
    pcnt_counter_clear(PCNT_UNIT_0);
    s_wraps = 0;
    int64_t t0 = esp_timer_get_time();
    pcnt_counter_resume(PCNT_UNIT_0);
    while (esp_timer_get_time() - t0 < OSC_GATE_US) { }
    pcnt_counter_pause(PCNT_UNIT_0);
    *gate_us = esp_timer_get_time() - t0;
    int16_t v = 0;
    pcnt_get_counter_value(PCNT_UNIT_0, &v);
    pcnt_isr_handler_remove(PCNT_UNIT_0);
    return (int64_t)s_wraps * OSC_HIGH_LIMIT + v;
}
#endif

/* Powers one oscillator, counts its edges in the gate, normalises to exactly 10 ms. */
static uint16_t read_osc(int pwr_pin, int freq_pin)
{
    digitalWrite(pwr_pin, HIGH);
    delay(OSC_SETTLE_MS);
    int64_t gate_us = 0;
    int64_t edges = count_edges(freq_pin, &gate_us);
    digitalWrite(pwr_pin, LOW);
    if (edges < 0 || gate_us <= 0) return 0;
    int64_t raw = (edges * OSC_GATE_US + gate_us / 2) / gate_us;
    if (raw < OSC_MIN_RAW) return 0;                   /* no oscillation: probe unplugged/broken */
    return (uint16_t)(raw > 65534 ? 65534 : raw);      /* 65535 is "out of range" for the backend */
}

/* ------------------------------------------------------------------ ADC */
static uint32_t adc_mv(int pin)
{
    uint32_t sum = 0;
    for (int i = 0; i < ADC_SAMPLES; i++) sum += analogReadMilliVolts(pin);
    return (sum + ADC_SAMPLES / 2) / ADC_SAMPLES;
}

static float ntc_c(uint32_t mv)
{
    const float vdd = 3300.0f;                         /* PWR_NTC = GPIO high = +3V3 (TPS63802) */
    if (mv < 30 || mv > (uint32_t)vdd - 30) return NAN;   /* open or shorted thermistor / cable */
    float r = NTC_R_FIXED * (float)mv / (vdd - (float)mv);
    return 1.0f / (logf(r / NTC_R0) / NTC_BETA + 1.0f / 298.15f) - 273.15f;
}

uint16_t sensors_vbat_mv(void)
{
    return (uint16_t)lroundf((float)adc_mv(PIN_VBAT_ADC) * VBAT_DIVIDER);
}

/* ------------------------------------------------------------------ SHT40 */
static uint8_t sht_crc(const uint8_t *d)
{
    uint8_t crc = 0xFF;
    for (int i = 0; i < 2; i++) {
        crc ^= d[i];
        for (int b = 0; b < 8; b++) crc = (crc & 0x80) ? (uint8_t)((crc << 1) ^ 0x31) : (uint8_t)(crc << 1);
    }
    return crc;
}

static bool sht40_read(float *t, float *rh)
{
    for (int attempt = 0; attempt < 2; attempt++) {
        Wire.beginTransmission(SHT40_ADDR);
        Wire.write(SHT40_MEAS_HI);
        if (Wire.endTransmission() != 0) { delay(2); continue; }
        delay(10);                                     /* 8.3 ms max, high repeatability */
        uint8_t d[6];
        if (Wire.requestFrom((uint8_t)SHT40_ADDR, (uint8_t)6) != 6) continue;
        for (int i = 0; i < 6; i++) d[i] = (uint8_t)Wire.read();
        if (sht_crc(d) != d[2] || sht_crc(d + 3) != d[5]) continue;
        uint16_t rt = (uint16_t)(d[0] << 8 | d[1]), rr = (uint16_t)(d[3] << 8 | d[4]);
        *t = -45.0f + 175.0f * (float)rt / 65535.0f;
        float h = -6.0f + 125.0f * (float)rr / 65535.0f;
        *rh = h < 0 ? 0 : (h > 100 ? 100 : h);
        return true;
    }
    return false;
}

/* ------------------------------------------------------------------ public */
void sensors_init(void)
{
    analogReadResolution(12);
    analogSetAttenuation(ADC_11db);                    /* 0-3.1 V: NTC divider and VBAT/2 */
    pinMode(PIN_CHG_ACTIVE, INPUT_PULLUP);
    pinMode(PIN_CHG_DONE, INPUT_PULLUP);
    Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL, 100000);
}

void sensors_read(readings_t *r)
{
    /* air first: SHT40 conversion is independent of the probe */
    if (!sht40_read(&r->t_air, &r->rh_air)) r->t_air = r->rh_air = NAN;

    r->raw_15 = read_osc(PIN_PWR_OSC15, PIN_OSC15_FREQ);
    r->raw_40 = read_osc(PIN_PWR_OSC40, PIN_OSC40_FREQ);

    digitalWrite(PIN_PWR_NTC, HIGH);
    delay(NTC_SETTLE_MS);
    r->t_soil_15 = ntc_c(adc_mv(PIN_NTC15_ADC));
    r->t_soil_40 = ntc_c(adc_mv(PIN_NTC40_ADC));
    digitalWrite(PIN_PWR_NTC, LOW);

    r->vbat_mv = sensors_vbat_mv();
    r->charging = digitalRead(PIN_CHG_ACTIVE) == LOW;
    r->charged = digitalRead(PIN_CHG_DONE) == LOW;
}

bool sensors_ok(const readings_t *r)
{
    return r->raw_15 && r->raw_40 && !isnan(r->t_soil_15) && !isnan(r->t_soil_40) &&
           !isnan(r->t_air) && !isnan(r->rh_air);
}

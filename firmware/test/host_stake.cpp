/*
 * Host test of the field stake firmware (src/stake/) with the mocks in stake_mocks/.
 * Simulates deep-sleep wakes for ~9 h of a stake's life: power-on, rain tips, gateway
 * outage and backlog, button press, interval/LED downlink, unplugged probe, frames for
 * another stake, flat battery. Checks every delivered packet against ground truth.
 *
 *   LoRa build : g++ -std=c++17 -DLINK_LORA ...   (see README)
 *   Wi-Fi build: g++ -std=c++17 -DLINK_WIFI ...   then cross_check.py on the published JSON
 */
#include <deque>
#include <cassert>
#include "Arduino.h"
#include "Wire.h"
#include "RadioLib.h"
#include "WiFi.h"
#include "esp_sntp.h"
#include "esp_sleep.h"
#include "driver/pcnt.h"
#include "pinos.h"
#include "gaiapus_protocol.h"
#include "../src/stake/config.h"

/* ------------------------------------------------------------------ mock state (globals live in stake_mocks/mock.h) */
static int64_t rain_release_us = -1, btn_release_us = -1;
static bool quiet;

extern "C" time_t time(time_t *t) { time_t v = (time_t)(mock_epoch + mock_us / 1000000); if (t) *t = v; return v; }

int digitalRead(int p)
{
    extern bool mock_rx_pending(void);
    if (p == PIN_LORA_DIO1) return mock_rx_pending() ? HIGH : LOW;
    if (p == PIN_RAIN) return mock_us < rain_release_us ? LOW : HIGH;
    if (p == PIN_BTN) return mock_us < btn_release_us ? LOW : HIGH;
    return mock_din[p];
}

double mock_osc_hz(int pin)
{
    int pwr = pin == PIN_OSC15_FREQ ? PIN_PWR_OSC15 : PIN_PWR_OSC40;
    if (!mock_dout[pwr]) return 0.0;
    /* ground truth in the 15 cm count: raw_15 = 10000 + 10 x minute of measurement */
    if (pin == PIN_OSC15_FREQ) return 1.0e6 + 1000.0 * (mock_us / 60e6);
    return mock_freq_hz[pin];
}

/* SHT40: real conversion formulas + CRC */
static uint8_t crc8(const uint8_t *d) { uint8_t c = 0xFF; for (int i = 0; i < 2; i++) { c ^= d[i];
    for (int b = 0; b < 8; b++) c = (c & 0x80) ? (uint8_t)((c << 1) ^ 0x31) : (uint8_t)(c << 1); } return c; }
uint8_t TwoWire::endTransmission() { return mock_sht_ok && cmd == 0xFD ? 0 : 2; }
uint8_t TwoWire::requestFrom(uint8_t, uint8_t n)
{
    if (!mock_sht_ok) return 0;
    uint16_t rt = (uint16_t)lround((mock_air_t + 45.0) * 65535.0 / 175.0);
    uint16_t rr = (uint16_t)lround((mock_air_rh + 6.0) * 65535.0 / 125.0);
    rx[0] = rt >> 8; rx[1] = rt & 0xFF; rx[2] = crc8(rx);
    rx[3] = rr >> 8; rx[4] = rr & 0xFF; rx[5] = crc8(rx + 3);
    rn = n; ri = 0; return n;
}

/* SX1262 + community gateway */
static std::deque<std::vector<uint8_t>> air;          /* frames on the way to the stake */
static bool rx_on; static int64_t rx_ready_us;
bool mock_rx_pending(void) { return rx_on && !air.empty() && mock_us >= rx_ready_us; }
int SX1262::begin(float, float, uint8_t sf, uint8_t, uint8_t sw, int8_t, uint16_t, float, bool)
{ assert(sf == LORA_SF && sw == LORA_SYNC_WORD); delay(5); return RADIOLIB_ERR_NONE; }
int SX1262::transmit(uint8_t *d, size_t n)
{
    delay(206);                                       /* SF9/125k, 25 B */
    mock_tx.push_back({ mock_us, std::vector<uint8_t>(d, d + n), false });
    if (mock_gw_online && n == GP_UPLINK_LEN) {
        gp_downlink_t dl = { mock_gw_led, mock_gw_interval };
        uint8_t f[GP_DOWNLINK_FRAME_LEN];
        if (mock_gw_foreign_first) { gp_encode_downlink_frame(0x0BADF00Du, &dl, f); air.emplace_back(f, f + 6); }
        gp_encode_downlink_frame(gp_get32(d + 1), &dl, f); air.emplace_back(f, f + 6);
        mock_tx.back().acked = true;
    }
    rx_ready_us = mock_us + 200000;
    return RADIOLIB_ERR_NONE;
}
int SX1262::startReceive() { rx_on = true; if (rx_ready_us < mock_us) rx_ready_us = mock_us + 30000; return 0; }
int SX1262::standby() { rx_on = false; return 0; }
size_t SX1262::getPacketLength() { return air.empty() ? 0 : air.front().size(); }
int SX1262::readData(uint8_t *d, size_t n) { memcpy(d, air.front().data(), n); air.pop_front(); rx_ready_us = mock_us + 20000; return 0; }
int SX1262::sleep() { rx_on = false; air.clear(); return 0; }

/* ------------------------------------------------------------------ firmware entry */
void setup(void);

static int wakes;
static uint64_t run_wake(int cause)
{
    mock_wake_cause = cause; wakes++;
    FILE *saved = stdout;
    if (quiet) stdout = fopen("/dev/null", "w");
    uint64_t us = 0;
    try { setup(); assert(!"setup() returned without deep sleep"); }
    catch (DeepSleep &d) { us = d.us; }
    if (quiet) { fclose(stdout); stdout = saved; }
    return us;
}

/* ------------------------------------------------------------------ scenario */
struct Ev { double min; int kind; double hold_s; };       /* kind 0 rain, 1 button */
static double tmin(void) { return mock_us / 60e6; }

static void set_world(void)
{
    double m = tmin();
    mock_freq_hz[PIN_OSC40_FREQ] = (m > 300 && m < 330) ? 0.0 : 2.4e6;       /* probe 40 cm unplugged */
    mock_gw_online = !(m > 65 && m < 170);                                    /* gateway outage */
    mock_wifi_online = mock_gw_online;
    mock_gw_foreign_first = m > 330 && m < 345;
    if (m > 240) { mock_gw_led = GP_LED_YELLOW; mock_gw_interval = 10; mock_retained_down = "{\"led\": 2, \"intervalo_min\": 10}"; }
    mock_mv[PIN_VBAT_ADC] = (m > 360 && m < 400) ? 1425 : 1650;               /* 2850 mV: no radio */
    mock_din[PIN_CHG_ACTIVE] = (m > 420) ? LOW : HIGH;                        /* sun on the panel */
}

int main(int argc, char **argv)
{
    quiet = argc > 1 && !strcmp(argv[1], "-q");
    for (int &v : mock_din) v = HIGH;
    /* NTC: 10k fixed + NTC at 24.31 / 23.10 C, 3.3 V */
    auto ntc_mv = [](double c) { double r = 10000.0 * exp(3380.0 * (1.0 / (c + 273.15) - 1.0 / 298.15)); return (int)lround(3300.0 * r / (r + 10000.0)); };
    mock_mv[PIN_NTC15_ADC] = ntc_mv(24.31); mock_mv[PIN_NTC40_ADC] = ntc_mv(23.10);
    mock_retained_down = "{\"led\": 1, \"intervalo_min\": 30}";
    mock_pub = fopen("/tmp/gp_stake_published.txt", "w");

    std::vector<Ev> ev = { {10, 0, 0.1}, {12, 0, 0.1}, {13.5, 0, 0.1},   /* 3 tips before first cycle   */
                           {200, 1, 0.3},                                 /* short press: measure now    */
                           {230, 0, 0.1}, {231, 0, 0.1},
                           {280, 1, 4.0},                                 /* long press: diagnostics     */
                           {100, 0, 3.0}, {100.2, 0, 0.1} };              /* reed stuck 3 s, then a tip  */
    const double END_MIN = 540;
    int rain_total = 0;
    set_world();
    uint64_t sleep_us = run_wake(0);                                      /* power-on */
    while (tmin() < END_MIN) {
        int64_t wake_at = mock_us + (int64_t)sleep_us;
        int cause = 4;
        for (auto &e : ev) {
            int64_t at = (int64_t)(e.min * 60e6);
            if (at <= mock_us || at >= wake_at) continue;
            if ((e.kind == 0 && !mock_ext0_on) || (e.kind == 1 && !mock_ext1_on)) continue;
            wake_at = at; cause = e.kind == 0 ? 2 : 3;
            if (e.kind == 0) { rain_release_us = at + (int64_t)(e.hold_s * 1e6); rain_total++; }
            else btn_release_us = at + (int64_t)(e.hold_s * 1e6);
            e.min = -1;
            break;
        }
        mock_us = wake_at;
        set_world();
        sleep_us = run_wake(cause);
    }
    fclose(mock_pub);

    /* ------------------------------------------------------------------ checks */
    int fails = 0;
#define CHECK(c, ...) do { if (!(c)) { fails++; printf("FAIL: " __VA_ARGS__); printf("  [%s]\n", #c); } } while (0)
    printf("\n%d wakes in %.0f min\n", wakes, tmin());
#ifdef LINK_LORA
    std::vector<int> seen(400, 0);
    int rain_sum = 0, last_seq = 0, prev_meas_min = -1, n_short = 0, flags_btn = 0, flags_err = 0, flags_chg = 0;
    for (auto &t : mock_tx) {
        gp_uplink_t m; CHECK(gp_decode_uplink(t.data.data(), t.data.size(), &m) == 0, "decode\n");
        double sent_min = t.us / 60e6, meas_min = (m.raw_15 - 10000) / 10.0;
        double obs_min = sent_min - m.age_min;
        if (!quiet) printf("tx %6.1f min seq %3u age %3u  meas@%6.1f obs@%6.1f  rain %u  vbat %u flags %02X %s\n",
                           sent_min, m.seq, m.age_min, meas_min, obs_min, m.rain_pulses, m.vbat_mv, m.flags, t.acked ? "ACK" : "lost");
        /* age_min is whole minutes (floor): observed_at may be up to 1 min after the measurement */
        CHECK(obs_min - meas_min >= -0.1 && obs_min - meas_min <= 1.2, "seq %u observed %.1f vs measured %.1f\n", m.seq, obs_min, meas_min);
        CHECK(m.node_id == 0xC4000110u, "node id\n");
        CHECK(m.t_soil_15 >= 2429 && m.t_soil_15 <= 2433, "t15 %d\n", m.t_soil_15);
        CHECK(m.t_air == 2980 && m.rh_air == 54, "air %d %u\n", m.t_air, m.rh_air);
        CHECK(!(sent_min > 360 && sent_min < 400), "transmitted at %.1f min with a flat battery\n", sent_min);
        if (m.vbat_mv < VBAT_LOW_MV) CHECK(m.flags & GP_FLAG_LOW_BATTERY, "low battery flag\n");
        if (t.acked) {
            CHECK(!seen[m.seq], "seq %u delivered twice\n", m.seq);
            seen[m.seq] = 1; rain_sum += m.rain_pulses;
            if (m.flags & GP_FLAG_BUTTON) flags_btn++;
            if (m.flags & GP_FLAG_SENSOR_ERROR) { flags_err++; CHECK(m.raw_40 == 0, "err flag w/o probe fault\n"); }
            if (m.flags & GP_FLAG_CHARGING) flags_chg++;
        }
        if ((int)m.seq > last_seq) {
            if (prev_meas_min >= 0 && meas_min > 260 && !(m.flags & GP_FLAG_BUTTON)) {
                double gap = meas_min - prev_meas_min;
                if (gap > 8 && gap < 12) n_short++;
            }
            last_seq = m.seq; prev_meas_min = (int)meas_min;
        }
    }
    int missing = 0;
    for (int s = 1; s <= last_seq; s++) if (!seen[s]) missing++;
    printf("measurements %d, delivered %d, missing %d, rain pulses %d (tips %d)\n", last_seq, last_seq - missing, missing, rain_sum, rain_total);
    CHECK(missing <= 1, "%d measurements never delivered\n", missing);       /* the very last may still be queued */
    CHECK(rain_sum == rain_total, "rain %d vs %d\n", rain_sum, rain_total);
    CHECK(flags_btn == 2, "button flags %d\n", flags_btn);
    CHECK(flags_err >= 2, "sensor error flags %d\n", flags_err);
    CHECK(flags_chg >= 5, "charging flags %d\n", flags_chg);
    CHECK(n_short >= 10, "only %d 10-min gaps after the interval downlink\n", n_short);
#else
    printf("published %d JSON messages -> /tmp/gp_stake_published.txt\n", mock_publish_count);
    CHECK(mock_publish_count >= 30, "few publishes\n");
#endif
    printf(fails ? "RESULT: FAIL (%d)\n" : "RESULT: OK\n", fails);
    return fails != 0;
}

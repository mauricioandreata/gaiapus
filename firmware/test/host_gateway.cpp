/*
 * Host test of the gateway firmware (src/gateway/) with the mocks in stake_mocks/.
 * Stakes "transmit" into the mocked SX1262; the backend sends commands through the
 * mocked broker; Wi-Fi goes down and comes back. Checks every reply frame and every
 * published JSON (then cross_check.py compares the JSON with the Python decoder).
 *
 *   g++ -std=c++17 -Istake_mocks -I../include -I../src/stake -I../src/gateway \
 *       host_gateway.cpp ../src/gateway/gateway_main.cpp ../src/stake/radio.cpp -o g && ./g
 *   python3 cross_check.py /tmp/gp_gw_published.txt /tmp/gp_gw_hex.txt
 */
#include <deque>
#include "Arduino.h"
#include "RadioLib.h"
#include "WiFi.h"
#include "PubSubClient.h"
#include "pinos.h"
#include "gaiapus_protocol.h"
#include "../src/stake/config.h"

extern "C" time_t time(time_t *t) { time_t v = (time_t)(mock_epoch + mock_us / 1000000); if (t) *t = v; return v; }

/* ------------------------------------------------------------------ SX1262 at the gateway */
struct AirPkt { int64_t at; std::vector<uint8_t> d; bool crc_error; };
static std::deque<AirPkt> inbound;                      /* stake -> gateway */
struct Reply { int64_t at; std::vector<uint8_t> d; };
static std::vector<Reply> replies;                       /* gateway -> stake */
static bool rx_on;

int digitalRead(int p)
{
    if (p == PIN_LORA_DIO1) return rx_on && !inbound.empty() && inbound.front().at <= mock_us ? HIGH : LOW;
    return HIGH;
}
int SX1262::begin(float, float, uint8_t, uint8_t, uint8_t, int8_t, uint16_t, float, bool) { delay(5); return 0; }
int SX1262::transmit(uint8_t *d, size_t n) { delay(144); replies.push_back({ mock_us, std::vector<uint8_t>(d, d + n) }); rx_on = false; return 0; }
int SX1262::startReceive() { rx_on = true; return 0; }
int SX1262::standby() { rx_on = false; return 0; }
size_t SX1262::getPacketLength() { return inbound.front().d.size(); }
int SX1262::readData(uint8_t *d, size_t n)
{
    AirPkt p = inbound.front();
    inbound.pop_front();
    if (n) memcpy(d, p.d.data(), n);
    return p.crc_error ? RADIOLIB_ERR_CRC_MISMATCH : 0;
}
int SX1262::sleep() { return 0; }

/* ------------------------------------------------------------------ helpers */
void setup(void);
void loop(void);
static void run_until(double s) { while (mock_us < (int64_t)(s * 1e6)) loop(); }
static double now_s(void) { return mock_us / 1e6; }

static std::vector<uint8_t> uplink(uint32_t node, uint16_t seq, uint16_t age, uint8_t version = 1)
{
    gp_uplink_t m = { version, node, seq, 18342, 21011, 2431, 2310, 2980, 54, 2, 3285, age, 0 };
    uint8_t b[GP_UPLINK_LEN];
    gp_encode_uplink(&m, b);
    b[0] = version;
    return std::vector<uint8_t>(b, b + sizeof b);
}

static int fails;
static FILE *hexf;                                       /* bytes of every published uplink, for cross_check.py */
#define CHECK(c, ...) do { if (!(c)) { fails++; printf("FAIL: " __VA_ARGS__); printf("  [%s]\n", #c); } } while (0)

/* sends a packet at time t, runs 2 s, returns the reply frame (empty = none) */
static std::vector<uint8_t> air(double t, std::vector<uint8_t> d, bool crc_error = false)
{
    run_until(t);
    size_t before = replies.size();
    int pubs = mock_publish_count;
    inbound.push_back({ mock_us, d, crc_error });
    int64_t sent = mock_us;
    run_until(t + 2.0);
    if (mock_publish_count > pubs) { for (uint8_t b : d) fprintf(hexf, "%02X", b); fprintf(hexf, "\n"); }
    if (replies.size() == before) return {};
    double dt = (replies.back().at - sent) / 1e3;
    CHECK(dt < 1000, "reply after %.0f ms, stake listens 1500 ms\n", dt);
    return replies.back().d;
}

static bool frame_is(const std::vector<uint8_t> &f, uint32_t node, uint8_t led, uint8_t iv)
{
    gp_downlink_t d;
    return f.size() == GP_DOWNLINK_FRAME_LEN && gp_decode_downlink_frame(f.data(), f.size(), node, &d) == 0 &&
           d.led == led && d.interval_min == iv;
}

int main()
{
    mock_pub = fopen("/tmp/gp_gw_published.txt", "w");
    hexf = fopen("/tmp/gp_gw_hex.txt", "w");
    mock_epoch = 1794659400LL;                           /* 2026-11-14T12:30:00Z, NTP already synced */
    mock_mqtt_inbox.push_back({ "gaiapus/devices/c4000110/down", "{\"led\": 2, \"intervalo_min\": 10}" });  /* retained */
    setup();
    run_until(1.0);

    /* 1. known stake: retained command comes back as the ACK frame */
    auto f = air(2, uplink(0xC4000110u, 5, 0));
    CHECK(frame_is(f, 0xC4000110u, GP_LED_YELLOW, 10), "c4000110 ack frame\n");
    /* 2. unknown stake, buffered measurement (90 min old): default command */
    f = air(4, uplink(0x00000017u, 9, 90));
    CHECK(frame_is(f, 0x00000017u, GP_LED_OFF, 30), "00000017 default ack\n");
    /* 3. live command from the backend, used on the next uplink */
    mock_mqtt_inbox.push_back({ "gaiapus/devices/00000017/down", "{\"led\": 3, \"intervalo_min\": 15}" });
    f = air(7, uplink(0x00000017u, 10, 0));
    CHECK(frame_is(f, 0x00000017u, GP_LED_RED, 15), "00000017 red/15\n");
    /* 4. partial command keeps the other field */
    mock_mqtt_inbox.push_back({ "gaiapus/devices/00000017/down", "{\"led\": 1}" });
    f = air(10, uplink(0x00000017u, 11, 0));
    CHECK(frame_is(f, 0x00000017u, GP_LED_GREEN, 15), "partial command\n");
    /* 5. noise: another gateway's frame, wrong version, CRC error, malformed topic -> no reply */
    mock_mqtt_inbox.push_back({ "gaiapus/devices/XYZ/down", "{\"led\": 3}" });
    CHECK(air(13, std::vector<uint8_t>(f)).empty(), "replied to a downlink frame\n");
    CHECK(air(16, uplink(0xC4000110u, 6, 0, 9)).empty(), "replied to version 9\n");
    CHECK(air(19, uplink(0xC4000110u, 6, 0), true).empty(), "replied to a CRC error\n");
    /* 6. Internet down: no publish, so no ACK (the stake keeps the data) */
    int pubs = mock_publish_count;
    mock_wifi_online = false;
    CHECK(air(30, uplink(0xC4000110u, 7, 0)).empty(), "acked without backend\n");
    CHECK(mock_publish_count == pubs, "published while offline\n");
    mock_wifi_online = true;                              /* back: MQTT reconnects within 5 s */
    f = air(45, uplink(0xC4000110u, 8, 0));
    CHECK(frame_is(f, 0xC4000110u, GP_LED_YELLOW, 10), "ack after reconnect\n");
    f = air(47, uplink(0xC4000110u, 7, 1));               /* the resend of seq 7 */
    CHECK(frame_is(f, 0xC4000110u, GP_LED_YELLOW, 10), "ack of the resend\n");
    /* 7. command removed (empty retained message) -> default again */
    mock_mqtt_inbox.push_back({ "gaiapus/devices/00000017/down", "" });
    f = air(50, uplink(0x00000017u, 12, 0));
    CHECK(frame_is(f, 0x00000017u, GP_LED_OFF, 30), "cleared command\n");
    /* 8. heartbeat */
    run_until(400);
    fclose(mock_pub);
    fclose(hexf);

    int ups = 0, status = 0;
    FILE *in = fopen("/tmp/gp_gw_published.txt", "r");
    char line[1024];
    while (fgets(line, sizeof line, in)) {
        if (strstr(line, "/up ")) {
            ups++;
            CHECK(!strstr(line, "lora_payload_hex"), "gateway JSON must not carry the hex (bench only)\n");
            CHECK(strstr(line, "\"rssi\":-97,\"snr\":7.5"), "rssi/snr: %s", line);
            CHECK(strstr(line, "\"gateway_id\":\"c4000110\""), "gateway_id missing: %s", line);
        }
        if (strstr(line, "gaiapus/gateways/")) status++;
    }
    fclose(in);
    printf("published %d uplinks, %d status messages, %zu reply frames in %.0f s\n", ups, status, replies.size(), now_s());
    CHECK(ups == 7, "expected 7 published uplinks, got %d\n", ups);
    CHECK(replies.size() == 7, "expected 7 ACK frames, got %zu\n", replies.size());
    CHECK(status >= 3, "status messages %d\n", status);
    printf(fails ? "RESULT: FAIL (%d)\n" : "RESULT: OK\n", fails);
    return fails != 0;
}

/*
 * gateway_main.cpp - Gaiapus community gateway: LoRa P2P <-> MQTT.
 *
 * Runs on mains/USB power, never sleeps. Default hardware: a Gaiapus head board
 * (ESP32-S3 + E22-900MM22S) powered from USB-C; any ESP32-S3 + SX1262 board works
 * by overriding the RADIO_* / GW_LED_* pins (see platformio.ini, gateway-heltec-v3).
 *
 * For every valid 25-byte uplink:
 *   1. publish the JSON of docs/protocolo-dados.md on gaiapus/devices/{id}/up, with
 *      "gateway_id" (which community gateway heard the stake: rough location, moved-stake alert)
 *   2. only if the publish went through: answer the stake with the 6-byte frame
 *      node_id + led + intervalo_min (the stake's delivery ACK)
 * No backend -> no ACK -> the stake keeps the measurement in its own 24 h queue.
 * So the gateway needs no storage of its own and loses nothing during outages.
 *
 * LED commands: subscribed on gaiapus/devices/+/down (retained), cached per stake.
 * Health: gaiapus/gateways/{id}/status every 5 min (retained).
 */
#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <time.h>
#include "esp_sntp.h"
#include "esp_mac.h"
#include "gaiapus_protocol.h"
#include "gaiapus_json.h"
#include "pinos.h"
#include "config.h"
#include "radio.h"
#include "gw_config.h"

static WiFiClient net;
static PubSubClient mqtt(net);
static char gw_id[9], topic_status[48];

typedef struct { uint32_t node; gp_downlink_t dl; } cmd_t;
static cmd_t cmds[GW_MAX_NODES];
static int ncmds;

static struct {
    uint32_t rx_ok, rx_bad, rx_other, acked, no_backend;
    float last_rssi, last_snr;
} stats = { 0, 0, 0, 0, 0, NAN, NAN };

static bool radio_ok;
static uint32_t last_packet_ms, last_radio_try_ms, last_mqtt_try_ms, last_status_ms, wifi_lost_ms;

/* ------------------------------------------------------------------ LEDs */
static void led(int pin, bool on) { if (pin >= 0) digitalWrite(pin, on ? HIGH : LOW); }

static bool clock_valid(void) { return time(nullptr) > 1700000000; }

static void leds_update(void)
{
    bool wifi = WiFi.status() == WL_CONNECTED;
    bool backend = wifi && mqtt.connected() && clock_valid();
    led(GW_LED_R, !wifi || !radio_ok);
    led(GW_LED_Y, wifi && !backend);
    led(GW_LED_G, backend && radio_ok);
}

/* ------------------------------------------------------------------ command cache */
static cmd_t *cmd_find(uint32_t node)
{
    for (int i = 0; i < ncmds; i++) if (cmds[i].node == node) return &cmds[i];
    return NULL;
}

static void cmd_set(uint32_t node, const gp_downlink_t *dl)
{
    cmd_t *c = cmd_find(node);
    if (!c) {
        if (ncmds == GW_MAX_NODES) {                    /* full: forget the oldest entry */
            memmove(&cmds[0], &cmds[1], sizeof cmds[0] * (GW_MAX_NODES - 1));
            ncmds--;
        }
        c = &cmds[ncmds++];
        c->node = node;
    }
    c->dl = *dl;
}

static void cmd_clear(uint32_t node)
{
    cmd_t *c = cmd_find(node);
    if (!c) return;
    int i = (int)(c - cmds);
    memmove(&cmds[i], &cmds[i + 1], sizeof cmds[0] * (size_t)(ncmds - i - 1));
    ncmds--;
}

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

/* gaiapus/devices/{8 hex}/down  {"led": 2, "intervalo_min": 30} ; empty payload = command removed */
static void on_mqtt(char *topic, byte *payload, unsigned int len)
{
    char id[9] = "";
    if (sscanf(topic, "gaiapus/devices/%8[0-9a-f]/down", id) != 1 || strlen(id) != 8) return;
    uint32_t node = (uint32_t)strtoul(id, NULL, 16);
    if (len == 0) { cmd_clear(node); Serial.printf("[down] %s cleared\n", id); return; }
    char s[128];
    len = len < sizeof s - 1 ? len : sizeof s - 1;
    memcpy(s, payload, len);
    s[len] = 0;
    cmd_t *old = cmd_find(node);
    uint8_t raw[GP_DOWNLINK_LEN] = { old ? old->dl.led : (uint8_t)GP_LED_OFF,
                                     old ? old->dl.interval_min : (uint8_t)DEFAULT_INTERVAL_MIN };
    long v;
    if (json_int(s, "\"led\"", &v)) raw[0] = (uint8_t)(v < 0 || v > 255 ? 255 : v);
    if (json_int(s, "\"intervalo_min\"", &v)) raw[1] = (uint8_t)(v < 1 ? 1 : (v > 255 ? 255 : v));
    gp_downlink_t dl;
    gp_decode_downlink(raw, sizeof raw, &dl);            /* same validation as the stake */
    cmd_set(node, &dl);
    Serial.printf("[down] %s led=%u interval=%u min (%d stakes cached)\n", id, dl.led, dl.interval_min, ncmds);
}

/* ------------------------------------------------------------------ connectivity */
static void wifi_start(void)
{
    WiFi.persistent(false);
    WiFi.mode(WIFI_STA);
    WiFi.setAutoReconnect(true);
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    configTime(0, 0, "pool.ntp.org", "time.google.com");    /* SNTP keeps syncing in the background */
}

static void publish_status(void)
{
    char js[320], up[16];
    snprintf(up, sizeof up, "%lu", (unsigned long)(millis() / 1000));
    int n = snprintf(js, sizeof js,
        "{\"gateway_id\":\"%s\",\"fw\":\"%s\",\"uptime_s\":%s,\"rx_ok\":%lu,\"rx_bad\":%lu,"
        "\"rx_other\":%lu,\"acked\":%lu,\"no_backend\":%lu,\"stakes_cached\":%d,"
        "\"radio_ok\":%s,\"wifi_rssi\":%d,\"freq_mhz\":%.1f,\"sf\":%d}",
        gw_id, GW_FW_VERSION, up, (unsigned long)stats.rx_ok, (unsigned long)stats.rx_bad,
        (unsigned long)stats.rx_other, (unsigned long)stats.acked, (unsigned long)stats.no_backend,
        ncmds, radio_ok ? "true" : "false", (int)WiFi.RSSI(), (double)LORA_FREQ_MHZ, LORA_SF);
    if (n > 0 && n < (int)sizeof js) mqtt.publish(topic_status, js, true);
}

static void maintain_links(void)
{
    uint32_t now = millis();
    if (WiFi.status() != WL_CONNECTED) {
        if (!wifi_lost_ms) wifi_lost_ms = now ? now : 1;
        if (now - wifi_lost_ms > (uint32_t)GW_REBOOT_OFFLINE_MIN * 60000UL) {
            Serial.println("[gw] no Wi-Fi for too long, restarting");
            ESP.restart();
        }
        return;
    }
    wifi_lost_ms = 0;
    if (!mqtt.connected() && now - last_mqtt_try_ms > GW_MQTT_RETRY_MS) {
        last_mqtt_try_ms = now;
        char cid[24];
        snprintf(cid, sizeof cid, "gaiapus-gw-%s", gw_id);
        if (mqtt.connect(cid)) {
            mqtt.subscribe("gaiapus/devices/+/down");   /* retained commands arrive right away */
            Serial.printf("[mqtt] connected to %s\n", MQTT_HOST);
            publish_status();
            last_status_ms = now;
        } else {
            Serial.printf("[mqtt] connect failed (%d)\n", mqtt.state());
        }
    }
    if (mqtt.connected() && now - last_status_ms > GW_STATUS_EVERY_S * 1000UL) {
        last_status_ms = now;
        publish_status();
    }
}

static void maintain_radio(void)
{
    uint32_t now = millis();
    if (!radio_ok && now - last_radio_try_ms > 10000) {
        last_radio_try_ms = now;
        radio_ok = radio_init() && radio_start_rx();
        if (radio_ok) {
            last_packet_ms = now;
            Serial.printf("[lora] listening %.1f MHz SF%d BW%.0f sync 0x%02X\n",
                          (double)LORA_FREQ_MHZ, LORA_SF, (double)LORA_BW_KHZ, LORA_SYNC_WORD);
        }
    }
    if (radio_ok && now - last_packet_ms > (uint32_t)GW_RADIO_REARM_MIN * 60000UL) {
        last_packet_ms = now;                           /* quiet for long: re-arm, in case the chip hung */
        radio_ok = radio_init() && radio_start_rx();
    }
}

/* ------------------------------------------------------------------ uplink handling */
static void handle_packet(const uint8_t *pkt, size_t len, float rssi, float snr)
{
    last_packet_ms = millis();
    if (len == GP_DOWNLINK_FRAME_LEN) { stats.rx_other++; return; }    /* another gateway's reply */
    gp_uplink_t m;
    if (len != GP_UPLINK_LEN || gp_decode_uplink(pkt, len, &m) != 0) {
        stats.rx_bad++;
        Serial.printf("[lora] ignored %u-byte packet (rssi %.0f)\n", (unsigned)len, (double)rssi);
        return;
    }
    stats.rx_ok++;
    stats.last_rssi = rssi;
    stats.last_snr = snr;
    led(GW_LED_G, false);                               /* blink: off while handling */

    char id[9], topic[48], json[GP_JSON_MAX];
    gp_device_id(m.node_id, id);
    snprintf(topic, sizeof topic, GP_TOPIC_UP_FMT, id);
    bool published = false;
    if (mqtt.connected() && clock_valid() &&
        gp_format_json(json, sizeof json, pkt, time(nullptr), rssi, snr, MM_PER_PULSE, gw_id, 0) > 0)
        published = mqtt.publish(topic, json);

    if (published) {
        cmd_t *c = cmd_find(m.node_id);
        gp_downlink_t dl;                                /* unknown stake: no recommendation yet */
        dl.led = GP_LED_OFF;
        dl.interval_min = DEFAULT_INTERVAL_MIN;
        if (c) dl = c->dl;
        uint8_t frame[GP_DOWNLINK_FRAME_LEN];
        gp_encode_downlink_frame(m.node_id, &dl, frame);
        delay(GW_REPLY_DELAY_MS);
        bool sent = radio_send(frame, sizeof frame);
        if (sent) stats.acked++;
        Serial.printf("[up] %s seq %u age %u min rssi %.0f snr %.1f -> published, ack %s (led %u, %u min)\n",
                      id, m.seq, m.age_min, (double)rssi, (double)snr, sent ? "sent" : "TX FAILED",
                      dl.led, dl.interval_min);
    } else {
        stats.no_backend++;                             /* no ACK: the stake keeps it and resends */
        Serial.printf("[up] %s seq %u: backend unreachable, not acknowledged\n", id, m.seq);
    }
    radio_ok = radio_start_rx();
}

/* ------------------------------------------------------------------ entry */
void setup(void)
{
    Serial.begin(115200);
    for (int p : { GW_LED_G, GW_LED_Y, GW_LED_R }) if (p >= 0) { pinMode(p, OUTPUT); digitalWrite(p, LOW); }
    uint8_t mac[6];
    esp_read_mac(mac, ESP_MAC_WIFI_STA);
    gp_device_id(((uint32_t)mac[2] << 24) | ((uint32_t)mac[3] << 16) | ((uint32_t)mac[4] << 8) | mac[5], gw_id);
    snprintf(topic_status, sizeof topic_status, "gaiapus/gateways/%s/status", gw_id);
    Serial.printf("\n[gw] gaiapus gateway %s (%s)\n", gw_id, GW_FW_VERSION);

    mqtt.setServer(MQTT_HOST, MQTT_PORT);
    mqtt.setCallback(on_mqtt);
    mqtt.setBufferSize(768);
    wifi_start();
    last_radio_try_ms = millis() - 20000;               /* first radio / MQTT attempts right away */
    last_mqtt_try_ms = millis() - GW_MQTT_RETRY_MS - 1;
    maintain_radio();
}

void loop(void)
{
    maintain_links();
    mqtt.loop();
    maintain_radio();
    if (radio_ok && radio_rx_pending()) {
        uint8_t buf[64];
        float rssi = NAN, snr = NAN;
        size_t n = radio_read(buf, sizeof buf, &rssi, &snr);
        if (n) handle_packet(buf, n, rssi, snr);
        else { stats.rx_bad++; radio_ok = radio_start_rx(); }
    }
    leds_update();
    delay(1);
}

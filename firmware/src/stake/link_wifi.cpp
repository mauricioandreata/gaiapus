/*
 * link_wifi.cpp - demo link (D7): the stake PCB talks to the backend over Wi-Fi,
 * publishing exactly the JSON the LoRa gateway would publish (protocolo-dados.md),
 * plus lora_payload_hex with the 25 bytes.
 *
 * Downlink: the backend publishes {"led":N,"intervalo_min":M} on
 * gaiapus/devices/{id}/down with RETAIN, so a stake that wakes every 30 min gets the
 * last command right after subscribing.
 *
 * Clock: the RTC keeps time across deep sleep; NTP on the first connection and once a
 * day. When NTP moves the clock, queued measurements are shifted so their age is kept.
 */
#include "config.h"
#ifdef LINK_WIFI
#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <time.h>
#include <sys/time.h>
#include "esp_sntp.h"
#include "esp_timer.h"
#include "esp_mac.h"
#include "gaiapus_json.h"
#include "link.h"
#include "radio.h"

static WiFiClient net;
static PubSubClient mqtt(net);
static char dev_id[9], topic_up[48], topic_down[48];
static bool dl_seen;
static gp_downlink_t dl_last;

const char *link_name(void) { return "wifi"; }
uint16_t link_min_mv(void) { return VBAT_NO_WIFI_MV; }

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
    memcpy(s, payload, len);
    s[len] = 0;
    long led, iv;
    uint8_t raw[GP_DOWNLINK_LEN] = { GP_LED_OFF, DEFAULT_INTERVAL_MIN };
    if (json_int(s, "\"led\"", &led)) raw[0] = (uint8_t)(led < 0 ? 255 : (led > 255 ? 255 : led));
    if (json_int(s, "\"intervalo_min\"", &iv)) raw[1] = (uint8_t)(iv < 1 ? 1 : (iv > 255 ? 255 : iv));
    if (gp_decode_downlink(raw, sizeof raw, &dl_last) == 0) dl_seen = true;   /* same validation as LoRa */
}

static bool wifi_connect(stake_state_t *s)
{
    WiFi.persistent(false);
    WiFi.mode(WIFI_STA);
    uint32_t t0 = millis();
    if (s->wifi_channel > 0) {                         /* fast path: last AP, no scan */
        WiFi.begin(WIFI_SSID, WIFI_PASS, s->wifi_channel, s->wifi_bssid, true);
        while (WiFi.status() != WL_CONNECTED && millis() - t0 < WIFI_CONNECT_MS / 2) delay(20);
        if (WiFi.status() != WL_CONNECTED) { WiFi.disconnect(); s->wifi_channel = 0; }
    }
    if (WiFi.status() != WL_CONNECTED) {
        WiFi.begin(WIFI_SSID, WIFI_PASS);
        while (WiFi.status() != WL_CONNECTED && millis() - t0 < WIFI_CONNECT_MS) delay(20);
    }
    if (WiFi.status() != WL_CONNECTED) return false;
    s->wifi_channel = (int8_t)WiFi.channel();
    memcpy(s->wifi_bssid, WiFi.BSSID(), 6);
    Serial.printf("[wifi] connected ch %d rssi %d in %lu ms\n", s->wifi_channel, (int)WiFi.RSSI(),
                  (unsigned long)(millis() - t0));
    return true;
}

static void ntp_sync(stake_state_t *s)
{
    time_t before = time(nullptr);
    if (s->ntp_synced_s && before - s->ntp_synced_s < NTP_RESYNC_S) return;
    int64_t mono0 = esp_timer_get_time();
    sntp_set_sync_status(SNTP_SYNC_STATUS_RESET);
    configTime(0, 0, "pool.ntp.org", "time.google.com");
    uint32_t t0 = millis();
    while (sntp_get_sync_status() != SNTP_SYNC_STATUS_COMPLETED && millis() - t0 < 5000) delay(20);
    if (sntp_get_sync_status() != SNTP_SYNC_STATUS_COMPLETED) {
        Serial.println("[wifi] NTP failed");
        return;
    }
    time_t after = time(nullptr);
    int64_t delta = (int64_t)after - ((int64_t)before + (esp_timer_get_time() - mono0) / 1000000);
    if (delta > 2 || delta < -2) core_shift_clock(s, delta);
    s->ntp_synced_s = after;
    Serial.printf("[wifi] NTP ok, clock moved %+lld s\n", (long long)delta);
}

static bool clock_valid(void) { return time(nullptr) > 1700000000; }   /* after 2023-11 */

bool link_begin(stake_state_t *s, bool cold_boot)
{
    if (cold_boot || !s->lora_asleep) {                /* SX1262 powers up in standby (~0.6 mA) */
        radio_init();
        radio_sleep();
        s->lora_asleep = 1;
    }
    uint8_t mac[6];
    esp_read_mac(mac, ESP_MAC_WIFI_STA);               /* same id as the packet (node_id) */
    uint32_t node_id = ((uint32_t)mac[2] << 24) | ((uint32_t)mac[3] << 16) | ((uint32_t)mac[4] << 8) | mac[5];
    gp_device_id(node_id, dev_id);
    snprintf(topic_up, sizeof topic_up, GP_TOPIC_UP_FMT, dev_id);
    snprintf(topic_down, sizeof topic_down, GP_TOPIC_DOWN_FMT, dev_id);

    if (!wifi_connect(s)) { Serial.println("[wifi] no AP"); return false; }
    ntp_sync(s);
    if (!clock_valid()) return false;                  /* observed_at would be 1970: keep queued */

    mqtt.setServer(MQTT_HOST, MQTT_PORT);
    mqtt.setCallback(on_mqtt);
    mqtt.setBufferSize(768);
    char cid[24];
    snprintf(cid, sizeof cid, "gaiapus-%s", dev_id);
    if (!mqtt.connect(cid)) { Serial.printf("[mqtt] connect failed (%d)\n", mqtt.state()); return false; }
    dl_seen = false;
    mqtt.subscribe(topic_down);
    uint32_t t0 = millis();
    while (!dl_seen && millis() - t0 < MQTT_DOWN_WAIT_MS) { mqtt.loop(); delay(10); }
    return true;
}

bool link_send(stake_state_t *s, const uint8_t pkt[GP_UPLINK_LEN], gp_downlink_t *dl, bool *got_dl)
{
    (void)s;
    *got_dl = false;
    if (!mqtt.connected()) return false;
    char json[GP_JSON_MAX];
    if (gp_format_json(json, sizeof json, pkt, time(nullptr), (float)WiFi.RSSI(), NAN, MM_PER_PULSE, NULL, 1) < 0)
        return true;                                   /* corrupt packet: drop it, do not loop on it */
    bool ok = mqtt.publish(topic_up, json);
    mqtt.loop();
    Serial.printf("[mqtt] %s seq %u age %u min\n", ok ? "published" : "publish FAILED", gp_get16(pkt + 5), gp_get16(pkt + 22));
    if (ok && dl_seen) { *dl = dl_last; *got_dl = true; }
    return ok;
}

void link_end(stake_state_t *s)
{
    (void)s;
    mqtt.disconnect();
    WiFi.disconnect(true);
    WiFi.mode(WIFI_OFF);
}
#endif

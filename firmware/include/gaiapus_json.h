/*
 * gaiapus_json.h - 25-byte uplink -> MQTT JSON of docs/protocolo-dados.md.
 * Single C implementation used by the LoRa gateway and by the stake in Wi-Fi mode.
 * Python mirror (reference for the backend): tools/gaiapus_decode.py to_mqtt_json().
 */
#ifndef GAIAPUS_JSON_H
#define GAIAPUS_JSON_H

#include <stdio.h>
#include <time.h>
#include <math.h>
#include "gaiapus_protocol.h"

#define GP_TOPIC_UP_FMT    "gaiapus/devices/%s/up"
#define GP_TOPIC_DOWN_FMT  "gaiapus/devices/%s/down"
#define GP_JSON_MAX        640

/* device_id = node_id as 8 lower-case hex digits */
static inline void gp_device_id(uint32_t node_id, char out[9])
{
    snprintf(out, 9, "%08lx", (unsigned long)node_id);
}

static inline void gp_iso_utc(time_t t, char *out, size_t n)
{
    struct tm tm;
    gmtime_r(&t, &tm);
    strftime(out, n, "%Y-%m-%dT%H:%M:%SZ", &tm);
}

static inline void gp_fmt_temp(int16_t v, char *out, size_t n)
{
    if (v == GP_TEMP_INVALID) snprintf(out, n, "null");
    else snprintf(out, n, "%.2f", v / 100.0);
}

/*
 * pkt          : the 25 bytes as received
 * received     : gateway (or stake) clock, UTC; observed_at = received - idade_min
 * rssi, snr    : link quality; NAN -> null
 * gateway_id   : 8-hex id of the gateway that heard the stake; NULL -> field omitted (stake on Wi-Fi)
 * with_hex     : add "lora_payload_hex" (bench / stake Wi-Fi only)
 * Returns the JSON length, or -1 (bad packet / buffer too small).
 */
static inline int gp_format_json(char *out, size_t n, const uint8_t pkt[GP_UPLINK_LEN], time_t received,
                                 float rssi, float snr, float mm_per_pulse, const char *gateway_id,
                                 int with_hex)
{
    gp_uplink_t m;
    if (gp_decode_uplink(pkt, GP_UPLINK_LEN, &m) != 0) return -1;
    char id[9], obs[24], rec[24], t15[12], t40[12], ta[12], rs[16], sn[16];
    char hex[2 * GP_UPLINK_LEN + 32] = "", gw[32] = "";
    if (gateway_id) snprintf(gw, sizeof gw, ",\"gateway_id\":\"%.8s\"", gateway_id);
    gp_device_id(m.node_id, id);
    gp_iso_utc(received - (time_t)m.age_min * 60, obs, sizeof obs);
    gp_iso_utc(received, rec, sizeof rec);
    gp_fmt_temp(m.t_soil_15, t15, sizeof t15);
    gp_fmt_temp(m.t_soil_40, t40, sizeof t40);
    gp_fmt_temp(m.t_air, ta, sizeof ta);
    if (isnan(rssi)) snprintf(rs, sizeof rs, "null"); else snprintf(rs, sizeof rs, "%d", (int)lroundf(rssi));
    if (isnan(snr)) snprintf(sn, sizeof sn, "null"); else snprintf(sn, sizeof sn, "%.1f", snr);
    if (with_hex) {
        int k = snprintf(hex, sizeof hex, ",\"lora_payload_hex\":\"");
        for (unsigned i = 0; i < GP_UPLINK_LEN; i++) k += snprintf(hex + k, sizeof hex - (size_t)k, "%02X", pkt[i]);
        snprintf(hex + k, sizeof hex - (size_t)k, "\"");
    }
    int len = snprintf(out, n,
        "{\"device_id\":\"%s\",\"seq\":%u,\"observed_at\":\"%s\",\"received_at\":\"%s\","
        "\"readings\":[{\"depth_cm\":15,\"raw_moisture\":%u,\"soil_temp_c\":%s},"
        "{\"depth_cm\":40,\"raw_moisture\":%u,\"soil_temp_c\":%s}],"
        "\"air_temp_c\":%s,\"air_rh_pct\":%u,\"rain_mm\":%.2f,\"battery_mv\":%u,"
        "\"rssi\":%s,\"snr\":%s,\"flags\":%u%s%s}",
        id, m.seq, obs, rec, m.raw_15, t15, m.raw_40, t40, ta, m.rh_air,
        m.rain_pulses * mm_per_pulse, m.vbat_mv, rs, sn, m.flags, gw, hex);
    return (len > 0 && (size_t)len < n) ? len : -1;
}

#endif

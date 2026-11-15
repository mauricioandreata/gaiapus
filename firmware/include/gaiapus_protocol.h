/*
 * gaiapus_protocol.h - LoRa uplink/downlink format of the Gaiapus soil stake.
 * Contract: docs/protocolo-dados.md. Pure C99, no Arduino dependency: the same
 * header is used by the stake firmware, the Wi-Fi bench, Wokwi and the unit test.
 * All multi-byte fields are little-endian.
 */
#ifndef GAIAPUS_PROTOCOL_H
#define GAIAPUS_PROTOCOL_H

#include <stdint.h>
#include <stddef.h>

#define GP_PROTOCOL_VERSION 1u
#define GP_UPLINK_LEN       25u
#define GP_DOWNLINK_LEN     2u
#define GP_DOWNLINK_FRAME_LEN 6u   /* over the air: node_id (4) + downlink (2), see protocolo-dados.md */

/* flags (byte 24) */
#define GP_FLAG_BUTTON       0x01u  /* user pressed the button since last uplink */
#define GP_FLAG_LOW_BATTERY  0x02u  /* vbat below threshold */
#define GP_FLAG_SENSOR_ERROR 0x04u  /* at least one reading is invalid */
#define GP_FLAG_CHARGING     0x08u  /* solar charger active at measurement time (informative) */

/* sentinel for an invalid temperature reading (field also sets GP_FLAG_SENSOR_ERROR) */
#define GP_TEMP_INVALID      INT16_MIN

/* downlink LED states */
enum { GP_LED_OFF = 0, GP_LED_GREEN = 1, GP_LED_YELLOW = 2, GP_LED_RED = 3 };

typedef struct {
    uint8_t  version;       /* = GP_PROTOCOL_VERSION */
    uint32_t node_id;       /* low 32 bits of the MAC */
    uint16_t seq;           /* measurement counter, unchanged on resend */
    uint16_t raw_15;        /* oscillator count, 15 cm electrode */
    uint16_t raw_40;        /* oscillator count, 40 cm electrode */
    int16_t  t_soil_15;     /* 0.01 degC */
    int16_t  t_soil_40;     /* 0.01 degC */
    int16_t  t_air;         /* 0.01 degC */
    uint8_t  rh_air;        /* % */
    uint16_t rain_pulses;   /* pulses in the measurement interval */
    uint16_t vbat_mv;       /* mV */
    uint16_t age_min;       /* minutes since measurement (0 = now, >0 = buffered resend) */
    uint8_t  flags;
} gp_uplink_t;

typedef struct {
    uint8_t led;            /* GP_LED_* */
    uint8_t interval_min;   /* minutes between measurements (default 30) */
} gp_downlink_t;

static inline void gp_put16(uint8_t *p, uint16_t v) { p[0] = (uint8_t)v; p[1] = (uint8_t)(v >> 8); }
static inline void gp_put32(uint8_t *p, uint32_t v) { gp_put16(p, (uint16_t)v); gp_put16(p + 2, (uint16_t)(v >> 16)); }
static inline uint16_t gp_get16(const uint8_t *p) { return (uint16_t)(p[0] | ((uint16_t)p[1] << 8)); }
static inline uint32_t gp_get32(const uint8_t *p) { return (uint32_t)gp_get16(p) | ((uint32_t)gp_get16(p + 2) << 16); }

/* degrees C (float) -> int16 in 0.01 degC, rounded and clamped; NaN -> GP_TEMP_INVALID */
static inline int16_t gp_centi(float c)
{
    if (c != c) return GP_TEMP_INVALID;                 /* NaN */
    float v = c * 100.0f + (c >= 0 ? 0.5f : -0.5f);
    if (v > 32767.0f) return 32767;
    if (v < -32767.0f) return -32767;                   /* -32768 is reserved */
    return (int16_t)v;
}

/* Writes exactly GP_UPLINK_LEN bytes into out. Returns the length. */
static inline size_t gp_encode_uplink(const gp_uplink_t *m, uint8_t out[GP_UPLINK_LEN])
{
    out[0] = m->version;
    gp_put32(out + 1,  m->node_id);
    gp_put16(out + 5,  m->seq);
    gp_put16(out + 7,  m->raw_15);
    gp_put16(out + 9,  m->raw_40);
    gp_put16(out + 11, (uint16_t)m->t_soil_15);
    gp_put16(out + 13, (uint16_t)m->t_soil_40);
    gp_put16(out + 15, (uint16_t)m->t_air);
    out[17] = m->rh_air;
    gp_put16(out + 18, m->rain_pulses);
    gp_put16(out + 20, m->vbat_mv);
    gp_put16(out + 22, m->age_min);
    out[24] = m->flags;
    return GP_UPLINK_LEN;
}

/* Returns 0 on success, -1 on wrong length, -2 on unknown version. */
static inline int gp_decode_uplink(const uint8_t *in, size_t len, gp_uplink_t *m)
{
    if (len != GP_UPLINK_LEN) return -1;
    if (in[0] != GP_PROTOCOL_VERSION) return -2;
    m->version     = in[0];
    m->node_id     = gp_get32(in + 1);
    m->seq         = gp_get16(in + 5);
    m->raw_15      = gp_get16(in + 7);
    m->raw_40      = gp_get16(in + 9);
    m->t_soil_15   = (int16_t)gp_get16(in + 11);
    m->t_soil_40   = (int16_t)gp_get16(in + 13);
    m->t_air       = (int16_t)gp_get16(in + 15);
    m->rh_air      = in[17];
    m->rain_pulses = gp_get16(in + 18);
    m->vbat_mv     = gp_get16(in + 20);
    m->age_min     = gp_get16(in + 22);
    m->flags       = in[24];
    return 0;
}

static inline size_t gp_encode_downlink(const gp_downlink_t *d, uint8_t out[GP_DOWNLINK_LEN])
{
    out[0] = d->led;
    out[1] = d->interval_min;
    return GP_DOWNLINK_LEN;
}

/* Invalid LED value -> GP_LED_OFF; interval 0 -> 30 min. Returns 0 or -1 on wrong length. */
static inline int gp_decode_downlink(const uint8_t *in, size_t len, gp_downlink_t *d)
{
    if (len != GP_DOWNLINK_LEN) return -1;
    d->led = in[0] <= (uint8_t)GP_LED_RED ? in[0] : (uint8_t)GP_LED_OFF;
    d->interval_min = in[1] ? in[1] : 30;
    return 0;
}

/* LoRa downlink frame: every stake in range hears it, so the gateway prefixes the
 * 2-byte command with the node_id of the stake it answers. The frame also acts as the
 * delivery ACK of the uplink just sent (no frame = keep the measurement and resend). */
static inline size_t gp_encode_downlink_frame(uint32_t node_id, const gp_downlink_t *d,
                                              uint8_t out[GP_DOWNLINK_FRAME_LEN])
{
    gp_put32(out, node_id);
    return 4 + gp_encode_downlink(d, out + 4);
}

/* Returns 0 on success, -1 on wrong length, -3 if the frame is for another node. */
static inline int gp_decode_downlink_frame(const uint8_t *in, size_t len, uint32_t my_node_id,
                                           gp_downlink_t *d)
{
    if (len != GP_DOWNLINK_FRAME_LEN) return -1;
    if (gp_get32(in) != my_node_id) return -3;
    return gp_decode_downlink(in + 4, GP_DOWNLINK_LEN, d);
}

#endif /* GAIAPUS_PROTOCOL_H */

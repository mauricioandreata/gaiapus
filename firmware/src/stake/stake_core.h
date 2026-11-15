/*
 * stake_core.h - hardware-free logic of the stake: state kept in RTC RAM across
 * deep sleep, offline queue (F9), scheduling and downlink handling.
 * No Arduino/IDF dependency: compiled as-is by the host tests.
 */
#ifndef GAIAPUS_STAKE_CORE_H
#define GAIAPUS_STAKE_CORE_H

#include <stdint.h>
#include <stdbool.h>
#include "gaiapus_protocol.h"
#include "config.h"

#define STAKE_MAGIC 0x47A1A501u   /* bump when stake_state_t changes layout */

typedef struct {
    uint8_t pkt[GP_UPLINK_LEN];   /* encoded uplink, age_min patched at send time */
    int64_t taken_s;              /* RTC clock at measurement */
} stake_queued_t;

typedef struct {
    uint32_t magic;
    uint16_t seq;                 /* last measurement number */
    uint8_t  interval_min;
    uint8_t  led;                 /* GP_LED_* from the last downlink */
    uint16_t rain_pulses;         /* counted since the last measurement */
    uint8_t  pending_flags;       /* GP_FLAG_BUTTON until the next measurement */
    uint8_t  rain_stuck;          /* reed held closed: do not wake on it until next cycle */
    int64_t  next_due_s;          /* RTC clock of the next scheduled measurement */
    uint32_t rng;                 /* jitter PRNG */
    /* offline queue: ring, newest at (head + count - 1) */
    uint8_t  q_head, q_count;
    stake_queued_t q[BUF_LEN];
    /* statistics (USB log / diagnostics) */
    uint32_t delivered, dropped, fail_streak, boots;
    /* link caches */
    int64_t  ntp_synced_s;        /* 0 = clock never synced (Wi-Fi) */
    uint8_t  wifi_bssid[6];
    int8_t   wifi_channel;        /* 0 = unknown -> full scan */
    uint8_t  lora_asleep;         /* SX1262 put to sleep since power-up */
} stake_state_t;

#ifdef __cplusplus
extern "C" {
#endif

/* Resets the state when RTC RAM is not valid (power-on, brown-out, new layout). Returns true if reset. */
bool core_init(stake_state_t *s, uint32_t seed);

/* Queue: push always succeeds; when full the oldest measurement is dropped. */
void core_queue_push(stake_state_t *s, const uint8_t pkt[GP_UPLINK_LEN], int64_t taken_s);
/* Copies the newest queued packet into out with age_min set for `now`. False if empty. */
bool core_queue_peek_newest(const stake_state_t *s, int64_t now_s, uint8_t out[GP_UPLINK_LEN]);
void core_queue_pop_newest(stake_state_t *s);

/* Wall clock was corrected by delta seconds (NTP): keep queue ages and the schedule. */
void core_shift_clock(stake_state_t *s, int64_t delta_s);

/* After a cycle: plans the next measurement. Returns seconds to sleep (>= 1). */
int64_t core_schedule_next(stake_state_t *s, int64_t now_s);
/* Seconds until the planned measurement (for wakes by rain/button). <= 0 means due now. */
int64_t core_seconds_to_due(const stake_state_t *s, int64_t now_s);

/* Downlink received: LED and interval (already validated by gp_decode_downlink). */
void core_apply_downlink(stake_state_t *s, const gp_downlink_t *d);

/* minutes elapsed, clamped to the uint16 field */
uint16_t core_age_min(int64_t taken_s, int64_t now_s);

#ifdef __cplusplus
}
#endif
#endif

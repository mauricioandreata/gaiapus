/* stake_core.cpp - see stake_core.h. Pure C-style C++, no hardware access. */
#include <string.h>
#include "stake_core.h"

bool core_init(stake_state_t *s, uint32_t seed)
{
    if (s->magic == STAKE_MAGIC && s->q_head < BUF_LEN && s->q_count <= BUF_LEN && s->interval_min)
        return false;
    memset(s, 0, sizeof *s);
    s->magic = STAKE_MAGIC;
    s->interval_min = DEFAULT_INTERVAL_MIN;
    s->led = GP_LED_OFF;
    s->rng = seed ? seed : 0x1234567u;
    return true;
}

static uint32_t rnd(stake_state_t *s)   /* xorshift32 */
{
    uint32_t x = s->rng;
    x ^= x << 13; x ^= x >> 17; x ^= x << 5;
    return s->rng = x ? x : 0x1234567u;
}

uint16_t core_age_min(int64_t taken_s, int64_t now_s)
{
    int64_t m = (now_s - taken_s) / 60;      /* always real minutes (protocol), even in demo time */
    return (uint16_t)(m < 0 ? 0 : (m > 65535 ? 65535 : m));
}

void core_queue_push(stake_state_t *s, const uint8_t pkt[GP_UPLINK_LEN], int64_t taken_s)
{
    if (s->q_count == BUF_LEN) {             /* full: forget the oldest */
        s->q_head = (uint8_t)((s->q_head + 1) % BUF_LEN);
        s->q_count--;
        s->dropped++;
    }
    stake_queued_t *e = &s->q[(s->q_head + s->q_count) % BUF_LEN];
    memcpy(e->pkt, pkt, GP_UPLINK_LEN);
    e->taken_s = taken_s;
    s->q_count++;
}

bool core_queue_peek_newest(const stake_state_t *s, int64_t now_s, uint8_t out[GP_UPLINK_LEN])
{
    if (!s->q_count) return false;
    const stake_queued_t *e = &s->q[(s->q_head + s->q_count - 1) % BUF_LEN];
    memcpy(out, e->pkt, GP_UPLINK_LEN);
    gp_put16(out + 22, core_age_min(e->taken_s, now_s));
    return true;
}

void core_queue_pop_newest(stake_state_t *s)
{
    if (s->q_count) s->q_count--;
}

void core_shift_clock(stake_state_t *s, int64_t delta_s)
{
    for (uint8_t i = 0; i < s->q_count; i++) s->q[(s->q_head + i) % BUF_LEN].taken_s += delta_s;
    if (s->next_due_s) s->next_due_s += delta_s;
}

int64_t core_schedule_next(stake_state_t *s, int64_t now_s)
{
    int64_t period = (int64_t)s->interval_min * SECONDS_PER_MIN;
    int64_t span = period * JITTER_PCT / 100;
    int64_t jitter = span ? (int64_t)(rnd(s) % (uint32_t)(2 * span + 1)) - span : 0;
    int64_t base = s->next_due_s ? s->next_due_s : now_s;
    int64_t next = base + period + jitter;
    if (next <= now_s) next = now_s + period + jitter;   /* overslept (diagnostics, long backlog) */
    if (next <= now_s) next = now_s + 1;
    s->next_due_s = next;
    return next - now_s;
}

int64_t core_seconds_to_due(const stake_state_t *s, int64_t now_s)
{
    return s->next_due_s ? s->next_due_s - now_s : 0;
}

void core_apply_downlink(stake_state_t *s, const gp_downlink_t *d)
{
    s->led = d->led;
    s->interval_min = d->interval_min ? d->interval_min : DEFAULT_INTERVAL_MIN;
}

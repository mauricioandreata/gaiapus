/*
 * link_lora.cpp - product link (D2): LoRa P2P to the community gateway.
 *
 * Per uplink: TX 25 bytes, then listen LORA_RX_WINDOW_MS for the gateway's
 * 6-byte frame (node_id + led + interval). That frame is the ACK: without it the
 * measurement stays in the RTC queue and goes again next cycle with age_min > 0.
 * The stake needs no wall clock: the gateway stamps received_at.
 */
#include "config.h"
#ifdef LINK_LORA
#include <Arduino.h>
#include "link.h"
#include "radio.h"

static bool up;

const char *link_name(void) { return "lora"; }
uint16_t link_min_mv(void) { return VBAT_NO_RADIO_MV; }

bool link_begin(stake_state_t *s, bool cold_boot)
{
    (void)cold_boot;
    up = radio_init();
    s->lora_asleep = 0;
    return up;
}

bool link_send(stake_state_t *s, const uint8_t pkt[GP_UPLINK_LEN], gp_downlink_t *dl, bool *got_dl)
{
    *got_dl = false;
    if (!up) return false;
    uint32_t node_id = gp_get32(pkt + 1);
    if (!radio_send(pkt, GP_UPLINK_LEN)) return false;

    uint32_t t0 = millis();
    while (millis() - t0 < LORA_RX_WINDOW_MS) {        /* ignore frames for other stakes */
        uint8_t rx[16];
        float rssi = 0, snr = 0;
        size_t n = radio_receive(rx, sizeof rx, LORA_RX_WINDOW_MS - (millis() - t0), &rssi, &snr);
        if (!n) break;
        int rc = gp_decode_downlink_frame(rx, n, node_id, dl);
        if (rc == 0) {
            *got_dl = true;
            Serial.printf("[lora] ack seq %u: led=%u interval=%u min (rssi %.0f dBm, snr %.1f dB)\n",
                          gp_get16(pkt + 5), dl->led, dl->interval_min, rssi, snr);
            return true;
        }
    }
    Serial.printf("[lora] no ack for seq %u\n", gp_get16(pkt + 5));
    (void)s;
    return false;
}

void link_end(stake_state_t *s)
{
    radio_sleep();
    s->lora_asleep = 1;
    up = false;
}
#endif

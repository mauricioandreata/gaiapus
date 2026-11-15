/* link.h - how a queued uplink leaves the stake. One implementation is compiled:
 * link_lora.cpp (LINK_LORA, product) or link_wifi.cpp (LINK_WIFI, demo). */
#ifndef GAIAPUS_STAKE_LINK_H
#define GAIAPUS_STAKE_LINK_H

#include <stdint.h>
#include <stdbool.h>
#include "gaiapus_protocol.h"
#include "stake_core.h"

/* Brings the link up. cold_boot = first boot after power-on/reset. */
bool link_begin(stake_state_t *s, bool cold_boot);
/* Sends one 25-byte uplink. Returns true when delivery is confirmed.
 * *got_dl is set when a downlink command came with it (applied by the caller). */
bool link_send(stake_state_t *s, const uint8_t pkt[GP_UPLINK_LEN], gp_downlink_t *dl, bool *got_dl);
/* Powers the link down for deep sleep. */
void link_end(stake_state_t *s);
/* Minimum battery voltage to use this link. */
uint16_t link_min_mv(void);
/* "lora" or "wifi", for the log. */
const char *link_name(void);

#endif

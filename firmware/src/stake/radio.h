/* radio.h - EBYTE E22-900MM22S (SX1262) on the head board, through RadioLib. */
#ifndef GAIAPUS_STAKE_RADIO_H
#define GAIAPUS_STAKE_RADIO_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

bool radio_init(void);                                   /* SPI + SX1262 config, true if the chip answered */
bool radio_send(const uint8_t *data, size_t len);        /* blocking TX */
/* Listens up to timeout_ms; returns the packet length (0 = nothing / CRC error). */
size_t radio_receive(uint8_t *buf, size_t max, uint32_t timeout_ms, float *rssi, float *snr);
void radio_sleep(void);                                  /* cold sleep, ~0.2 uA */

/* Continuous reception (gateway) */
bool radio_start_rx(void);                               /* RX until a packet arrives */
bool radio_rx_pending(void);                             /* DIO1 raised: packet (or CRC error) waiting */
size_t radio_read(uint8_t *buf, size_t max, float *rssi, float *snr);   /* 0 = CRC error / too long */

#endif

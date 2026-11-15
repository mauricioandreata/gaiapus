/*
 * radio.cpp - SX1262 inside the EBYTE E22-900MM22S.
 *  - TCXO powered from DIO3 (module internal) -> tcxoVoltage 1.8 V; if the chip
 *    refuses, retry with the crystal setting (0) so a variant without TCXO still works.
 *  - DIO2 is not connected: the RF switch is driven by the MCU (TXEN / RXEN).
 *    Other boards (gateway on a Heltec V3, ...) override the RADIO_* pins; with
 *    RADIO_RXEN < 0 the module's own DIO2 drives the switch.
 *  - The radio is re-initialised on every wake (the MCU comes back from deep sleep
 *    with a fresh RAM) and put into cold sleep before the MCU sleeps.
 */
#include <Arduino.h>
#include <SPI.h>
#include <RadioLib.h>
#include "pinos.h"
#include "config.h"
#include "radio.h"

/* default = Gaiapus head board (pinos.h) */
#ifndef RADIO_NSS
#define RADIO_NSS   PIN_LORA_NSS
#define RADIO_SCK   PIN_SPI_SCK
#define RADIO_MOSI  PIN_SPI_MOSI
#define RADIO_MISO  PIN_SPI_MISO
#define RADIO_DIO1  PIN_LORA_DIO1
#define RADIO_NRST  PIN_LORA_NRST
#define RADIO_BUSY  PIN_LORA_BUSY
#define RADIO_RXEN  PIN_LORA_RXEN
#define RADIO_TXEN  PIN_LORA_TXEN
#endif

static SPIClass lora_spi(FSPI);
static SX1262 radio = new Module(RADIO_NSS, RADIO_DIO1, RADIO_NRST, RADIO_BUSY,
                                 lora_spi, SPISettings(4000000, MSBFIRST, SPI_MODE0));
static bool ready;

bool radio_init(void)
{
    lora_spi.begin(RADIO_SCK, RADIO_MISO, RADIO_MOSI, RADIO_NSS);
    int st = radio.begin(LORA_FREQ_MHZ, LORA_BW_KHZ, LORA_SF, LORA_CR, LORA_SYNC_WORD,
                         LORA_TX_DBM, LORA_PREAMBLE, LORA_TCXO_V, false);
    if (st != RADIOLIB_ERR_NONE) {
        Serial.printf("[lora] begin with TCXO %.1f V failed (%d), retrying with XTAL\n", LORA_TCXO_V, st);
        st = radio.begin(LORA_FREQ_MHZ, LORA_BW_KHZ, LORA_SF, LORA_CR, LORA_SYNC_WORD,
                         LORA_TX_DBM, LORA_PREAMBLE, 0.0f, false);
    }
    if (st != RADIOLIB_ERR_NONE) {
        Serial.printf("[lora] SX1262 not responding (%d)\n", st);
        ready = false;
        return false;
    }
    if (RADIO_RXEN >= 0) {
        radio.setDio2AsRfSwitch(false);
        radio.setRfSwitchPins(RADIO_RXEN, RADIO_TXEN);
    } else {
        radio.setDio2AsRfSwitch(true);
    }
    if (LORA_TX_DBM > 17) radio.setCurrentLimit(140);
    radio.setCRC(true);
    ready = true;
    return true;
}

bool radio_send(const uint8_t *data, size_t len)
{
    if (!ready) return false;
    int st = radio.transmit((uint8_t *)data, len);
    if (st != RADIOLIB_ERR_NONE) Serial.printf("[lora] tx error %d\n", st);
    return st == RADIOLIB_ERR_NONE;
}

bool radio_start_rx(void)
{
    return ready && radio.startReceive() == RADIOLIB_ERR_NONE;
}

bool radio_rx_pending(void)
{
    return ready && digitalRead(RADIO_DIO1) == HIGH;    /* RX_DONE / CRC_ERR / HEADER_ERR raise DIO1 */
}

size_t radio_read(uint8_t *buf, size_t max, float *rssi, float *snr)
{
    size_t len = radio.getPacketLength();
    if (len == 0 || len > max) {                        /* too long for us: flush it */
        uint8_t junk[256];
        radio.readData(junk, 0);
        return 0;
    }
    int st = radio.readData(buf, len);
    *rssi = radio.getRSSI();
    *snr = radio.getSNR();
    return st == RADIOLIB_ERR_NONE ? len : 0;
}

size_t radio_receive(uint8_t *buf, size_t max, uint32_t timeout_ms, float *rssi, float *snr)
{
    if (!radio_start_rx()) return 0;
    uint32_t t0 = millis();
    while (!radio_rx_pending()) {
        if (millis() - t0 > timeout_ms) { radio.standby(); return 0; }
        delay(1);
    }
    size_t len = radio_read(buf, max, rssi, snr);
    radio.standby();
    return len;
}

void radio_sleep(void)
{
    if (ready) radio.sleep();
    ready = false;
}

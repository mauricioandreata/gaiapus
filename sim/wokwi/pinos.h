/* pinos.h - ESP32-S3 pin map. Source of truth: hardware/tools/gen_kicad.py
 * (see docs/hardware-pinmap.md). Bench/Wokwi use the same GPIO numbers.      */
#ifndef GAIAPUS_PINOS_H
#define GAIAPUS_PINOS_H

#define PIN_BTN          0   /* user/boot button, active low                     */
#define PIN_VBAT_ADC     1   /* 2.2M/2.2M divider (x2)                           */
#define PIN_NTC15_ADC    2   /* soil temp 15 cm, NTC to GND, 10k to PWR_NTC       */
#define PIN_OSC15_FREQ   4   /* moisture 15 cm oscillator -> PCNT                */
#define PIN_OSC40_FREQ   5   /* moisture 40 cm oscillator -> PCNT                */
#define PIN_NTC40_ADC    6   /* soil temp 40 cm                                  */
#define PIN_PWR_NTC      7   /* powers both NTC dividers while measuring         */
#define PIN_I2C_SDA      8   /* SHT40 (0x44)                                     */
#define PIN_I2C_SCL      9
#define PIN_LORA_NSS    10
#define PIN_SPI_MOSI    11
#define PIN_SPI_SCK     12
#define PIN_SPI_MISO    13
#define PIN_LORA_DIO1   14   /* RTC GPIO: wakes from deep sleep                  */
#define PIN_PWR_OSC15   15
#define PIN_PWR_OSC40   16
#define PIN_RAIN        17   /* reed to GND, 470k pull-up; RTC GPIO wake         */
#define PIN_LORA_BUSY   18
#define PIN_LED_R       21
#define PIN_LORA_NRST   38
#define PIN_LORA_TXEN   39
#define PIN_LORA_RXEN   40
#define PIN_LED_G       41
#define PIN_LED_Y       42
#define PIN_CHG_ACTIVE  47   /* CN3058E CHRG, open drain, active low             */
#define PIN_CHG_DONE    48   /* CN3058E DONE, open drain, active low             */

#endif

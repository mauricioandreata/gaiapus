# Hardware pin map (ESP32-S3-MINI-1-N8) and net list

Source of truth: `hardware/tools/gen_kicad.py` (nets) -> `hardware/gaiapus-node/netlist-draft.csv`.
Pin functions from the Espressif datasheet (Table 3-1).

| Module pin | GPIO | Net | Function | Note |
|---|---|---|---|---|
| 3 | 3V3 | +3V3 | supply | 10 uF + 100 nF |
| 45 | EN | EN | reset | 10 k pull-up + 1 uF |
| 4 | IO0 | BTN | user/boot button | strapping: low at reset = download mode |
| 5 | IO1 | VBAT_ADC | battery voltage (2 x 2.2 M divider) | ADC1_CH0 |
| 6 | IO2 | NTC15_ADC | soil temp 15 cm | ADC1_CH1 |
| 10 | IO6 | NTC40_ADC | soil temp 40 cm | ADC1_CH5 |
| 11 | IO7 | PWR_NTC | powers NTC dividers only while measuring | |
| 8 | IO4 | OSC15_FREQ | moisture 15 cm oscillator -> PCNT | |
| 9 | IO5 | OSC40_FREQ | moisture 40 cm oscillator -> PCNT | |
| 19 | IO15 | PWR_OSC15 | powers 74LVC1G14 #1 | |
| 20 | IO16 | PWR_OSC40 | powers 74LVC1G14 #2 | |
| 12 / 13 | IO8 / IO9 | I2C_SDA / I2C_SCL | SHT40 (0x44) | |
| 14 | IO10 | LORA_NSS | SPI CS | FSPICS0 |
| 15 / 16 / 17 | IO11 / IO12 / IO13 | SPI_MOSI / SPI_SCK / SPI_MISO | LoRa SPI | FSPI default pins |
| 18 | IO14 | LORA_DIO1 | IRQ, deep-sleep wake | RTC GPIO |
| 22 | IO18 | LORA_BUSY | | |
| 34 / 35 / 36 | IO38 / IO39 / IO40 | LORA_NRST / TXEN / RXEN | RF switch + reset | |
| 21 | IO17 | RAIN_PULSE | tipping-bucket reed, deep-sleep wake | RTC GPIO |
| 23 / 24 | IO19 / IO20 | USB_DM / USB_DP | native USB (programming) | |
| 25 / 37 / 38 | IO21 / IO41 / IO42 | LED_R / LED_G / LED_Y | status LEDs | |
| 27 / 30 | IO47 / IO48 | CHG_ACTIVE_N / CHG_DONE_N | CN3058E open-drain status | free at 3.3 V on -N8 (quad flash) |
| 39 / 40 | TXD0 / RXD0 | UART_TX / UART_RX | debug pads | |
| 7, 26, 28, 29, 31-33, 41, 44 | IO3, IO26, IO33-37, IO45, IO46 | NC | unused | IO3/45/46 strapping, left open |

Open points to verify in the datasheets before PCB:
1. ~~IO47/48 on -N8~~ resolved: ESP32-S3FN8 uses quad 3.3 V flash, so IO33-37 are free and IO47/48 run at 3.3 V.
2. ~~CN3058E values~~ resolved, see `component-selection.md`.
3. USB-C footprint pad names (A1/B12 ...) match the symbol pin numbers.
4. Footprints still to be drawn in `hardware/lib/footprints/gaiapus.pretty`: E22-900MM22S, TPS63802_VSON-10, SHT4x_DFN-4, ELECTRODE_IDC (probe copper).

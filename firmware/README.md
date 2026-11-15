# Firmware · ESP32-S3

Three firmwares, one packet. The 25-byte uplink in `include/gaiapus_protocol.h` is the same on the bench, in Wokwi, on the stake PCB and at the gateway.

Full description in Portuguese (sensors, boot and identity, LoRa delivery, data formats): [`docs/firmware.md`](../docs/firmware.md).

| Path | What |
|---|---|
| `include/gaiapus_protocol.h` | **The packet.** 25-byte uplink, 2-byte downlink and the 6-byte addressed LoRa downlink frame. Pure C99, shared by every target and the tests. |
| `include/gaiapus_json.h` | **The MQTT JSON.** 25 bytes -> JSON of `docs/protocolo-dados.md`, used by the gateway and the stake in Wi-Fi mode. |
| `include/pinos.h` | GPIO map, same as the schematic (`docs/hardware-pinmap.md`). |
| `src/main.cpp` | **Bench / Wokwi** firmware (dev board, potentiometers, DHT22, Wi-Fi). |
| `src/stake/` | **Field stake** firmware for the Gaiapus PCB (head + probe boards). |
| `src/gateway/` | **Community gateway**: LoRa P2P <-> Wi-Fi/MQTT. |
| `tools/gaiapus_decode.py` | Gateway/backend side: bytes -> MQTT JSON -> app events, downlink frame encoder. `--selftest` |
| `tools/sync_wokwi.py` | Copies the bench firmware + headers into `sim/wokwi/`. |
| `test/` | Packet unit test, bench run on the PC, stake run on the PC (see below). |

## Build targets (`platformio.ini`)
| Env | Board | Link | Use |
|---|---|---|---|
| `bench-esp32s3` | ESP32-S3 dev board | Wi-Fi/MQTT | bench demo with bought sensors |
| `stake-lora` | Gaiapus PCB | LoRa P2P -> gateway -> MQTT | **product** |
| `stake-wifi` | Gaiapus PCB | Wi-Fi/MQTT, gateway JSON published by the stake | demo with the real board and no gateway (D7) |
| `stake-wifi-demo` | Gaiapus PCB | as above, 30 min cycle compressed to 1 min | video / pitch |
| `gateway` | Gaiapus head board on USB-C | LoRa in, Wi-Fi/MQTT out | **product** gateway |
| `gateway-heltec-v3` | Heltec WiFi LoRa 32 V3 | same | off-the-shelf gateway |

```
pio run -e stake-lora -t upload && pio device monitor
```
Wi-Fi credentials: `-DWIFI_SSID=\"name\" -DWIFI_PASS=\"pwd\"` in `build_flags`. All other settings are in `src/stake/config.h`, each overridable with `-D`.

## Stake firmware (`src/stake/`)
| File | Role |
|---|---|
| `config.h` | Intervals, thresholds, LoRa radio settings, NTC/ADC constants, Wi-Fi/MQTT |
| `stake_core.*` | Hardware-free logic: state in RTC RAM, offline queue, schedule, downlink. Tested on the PC. |
| `sensors.*` | PCNT oscillator count, NTC, battery, SHT40 (I2C, CRC), CN3058E status |
| `radio.*` | E22-900MM22S (SX1262) through RadioLib |
| `link.h`, `link_lora.cpp`, `link_wifi.cpp` | How a packet leaves the stake (one is compiled) |
| `stake_main.cpp` | Wake handling, measurement cycle, LEDs, diagnostics, deep sleep |

### Life cycle
The MCU is always in deep sleep. Every wake runs `setup()` from the top and ends in deep sleep again; what must survive (sequence number, queue, LED state, interval, rain count) lives in RTC RAM.

| Wake source | What happens |
|---|---|
| Timer (every `intervalo_min`, +-3 % jitter) | measure -> queue -> send newest first, then up to 3 queued -> sleep |
| Rain gauge reed (GPIO17, ext0) | count one tip, sleep until the planned measurement |
| Button (GPIO0, ext1) | show the status LED for 8 s, measure and send now (flag bit0) |
| Button held 3 s | **diagnostic mode**: live readings on USB every second for 3 min (factory air/water calibration, bench checks); press to leave |
| Power-on / reset | LED sweep, measure and send at once (feedback when installing) |

### Measurement chain
| Quantity | How |
|---|---|
| Soil moisture 15 / 40 cm | oscillator powered by `PWR_OSCxx` (one at a time), edges counted by the PCNT over a 10 ms gate, normalised to exactly 10 ms. `raw = f / 100` (0.5-2 MHz -> 5 000-20 000). `raw = 0` = no oscillation (probe unplugged). Overflow-safe on both IDF 4.4 and 5.x drivers. |
| Soil temperature | NTC 10k/B3380 to GND, 10k from `PWR_NTC` (powered only while reading), 8 samples, `analogReadMilliVolts` |
| Air T/RH | SHT40 0x44, high repeatability, CRC checked, one retry |
| Battery | `VBAT_ADC x 2` (2.2M/2.2M + 100 nF) |
| Rain | reed pulses, counted asleep (wake) and awake (interrupt, 50 ms debounce) |
| Charging | CN3058E CHRG low -> flag bit3 |

### Delivery and offline queue (F9)
- Every measurement goes into a 48-entry ring in RTC RAM (24 h at 30 min); when full, the oldest is dropped.
- **LoRa:** after each uplink the stake listens 1.5 s for the gateway's 6-byte frame `node_id + led + intervalo_min`. That frame is the ACK. No frame = the packet stays queued and goes again next cycle with `idade_min > 0`; the backend de-duplicates by `device_id-seq-depth`.
- **Wi-Fi:** publish success = delivered. The LED command comes from the **retained** message on `gaiapus/devices/{id}/down`. NTP on the first connection and every 24 h; a clock jump shifts the queued timestamps so ages stay right.
- Battery below 2.9 V (LoRa) / 3.1 V (Wi-Fi): measure and queue only, no radio.

### Power details
- Pins held through deep sleep: LoRa NSS/NRST high (radio stays asleep), TXEN/RXEN low (RF switch off), probe power and LEDs low.
- The SX1262 is put in cold sleep after every cycle, including in the Wi-Fi build (it powers up in standby, ~0.6 mA).
- LEDs: steady only for 8 s after a button press, otherwise a 120 ms flash at the end of each cycle. A blink every few seconds would need a wake every few seconds and roughly double the daily consumption.
- A stuck reed (bucket resting on the magnet) would wake the MCU forever: the stake stops waking on rain until the next timer cycle.

### LoRa radio settings
916.8 MHz (inside 915-928 MHz, Anatel / AU915 band), SF9, BW 125 kHz, CR 4/5, sync word 0x12 (private), 14 dBm, CRC on. TCXO 1.8 V from DIO3; if the chip refuses, the firmware retries in crystal mode. The **gateway must use the same settings** and answer within ~1 s with `gp_encode_downlink_frame()` (C) / `encode_downlink_frame()` (Python).

## Gateway firmware (`src/gateway/`)
Mains/USB powered, never sleeps. Uses the same `radio.cpp` and the same `LORA_*` settings as the stake, so the two cannot disagree on frequency, SF or sync word.

For every valid 25-byte uplink:
1. publish the JSON on `gaiapus/devices/{id}/up` (with `rssi` and `snr`, no hex);
2. **only if the publish went through**, answer with the 6-byte frame `node_id + led + intervalo_min`.

No Internet -> no ACK -> the stake keeps the measurement in its own 24 h queue and resends it. The gateway therefore needs no storage and loses nothing during an outage.

| Topic | Direction | Content |
|---|---|---|
| `gaiapus/devices/+/down` | backend -> gateway | `{"led": N, "intervalo_min": M}`, **retained**; partial commands keep the other field; an empty retained message removes the command |
| `gaiapus/devices/{id}/up` | gateway -> backend | measurement JSON |
| `gaiapus/gateways/{gw_id}/status` | gateway -> backend | every 5 min, retained: uptime, packets ok/bad/other, ACKs, uplinks without backend, stakes cached, radio state |

Stake without a command yet: ACK with LED off and 30 min. Ignored: frames of other gateways (6 bytes), other versions, CRC errors. Up to 64 stakes cached.
LEDs on the head board: green = all good (blinks off on each packet), yellow = Wi-Fi ok but MQTT/NTP down, red = no Wi-Fi or radio not answering. Watchdogs: restart after 30 min without Wi-Fi, re-initialise the SX1262 after 15 min without packets.

## Run the tests (any PC with gcc and python3)
```
cd firmware/test
gcc -std=c99 -Wall -Wextra -Werror -I../include test_protocol.c -o t && ./t
python3 ../tools/gaiapus_decode.py --selftest

# bench firmware on the PC
g++ -std=c++17 -Ihost_mocks -I../include host_run.cpp -o h && ./h && python3 cross_check.py /tmp/gp_published.txt

# stake firmware on the PC: 9 h of a stake's life (gateway outage, rain, button, diagnostics,
# interval downlink, unplugged probe, frames for another stake, flat battery, stuck reed)
g++ -std=c++17 -Istake_mocks -I../include -I../src/stake -DLINK_LORA host_stake.cpp ../src/stake/*.cpp -o s && ./s
g++ -std=c++17 -Istake_mocks -I../include -I../src/stake -DLINK_WIFI host_stake.cpp ../src/stake/*.cpp -o w && ./w -q \
  && python3 cross_check.py /tmp/gp_stake_published.txt
```
```
# gateway on the PC: retained/live/partial/cleared commands, unknown stake, noise, Internet outage
g++ -std=c++17 -Istake_mocks -I../include -I../src/stake -I../src/gateway host_gateway.cpp \
    ../src/gateway/gateway_main.cpp ../src/stake/radio.cpp -o g && ./g \
  && python3 cross_check.py /tmp/gp_gw_published.txt /tmp/gp_gw_hex.txt
```
Add `-DESP_IDF_VERSION_MAJOR=4` to exercise the legacy PCNT driver (Arduino core 2.x). On Windows change the `/tmp/...` paths in the harnesses.

The PC run proves the logic, the packet and the JSON. It cannot prove real SX1262 timing, PCNT on real pads or RF: that is the bring-up list below.

## Bring-up checklist on the first assembled board
1. USB-C enumerates; `pio device monitor` shows `[boot] gaiapus stake xxxxxxxx`.
2. Hold the button 3 s -> diagnostics. Probe in the air, then in a glass of water: `raw15/raw40` must change clearly (record both values per probe: factory calibration). `raw = 0` -> oscillator or cable.
3. `t15/t40` close to room temperature; `air` from the SHT40; `vbat` against a multimeter (adjust `VBAT_DIVIDER` if needed).
4. `[lora] begin ... failed` -> check `LORA_TCXO_V` (E22 datasheet) and the SPI lines.
5. Measure the sleep current in series with the battery (target ~25 uA, `power/power_budget.py`).
6. Panel in the sun: `chg=1` in diagnostics, flag bit3 in the packets.
7. With the gateway on: the stake log shows `[lora] ack seq N`, the gateway log `published, ack sent`. Walk away with the stake to find the range (RSSI/SNR in the JSON).

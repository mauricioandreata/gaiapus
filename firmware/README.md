# Firmware · ESP32-S3

| Path | What |
|---|---|
| `include/gaiapus_protocol.h` | **The packet.** 25-byte uplink / 2-byte downlink encoder+decoder, pure C99. Shared by stake, bench, Wokwi and tests. |
| `include/pinos.h` | GPIO map, same as the schematic (`docs/hardware-pinmap.md`). |
| `src/main.cpp` | Bench / Wokwi firmware: measure -> build the LoRa packet -> publish the gateway JSON over Wi-Fi/MQTT -> receive the LED command. |
| `tools/gaiapus_decode.py` | Gateway/backend side: bytes -> MQTT JSON -> app events. `--selftest` |
| `tools/sync_wokwi.py` | Copies `src/` + headers into `sim/wokwi/` (run after every firmware change). |
| `test/test_protocol.c` | Unit test of the packet (byte-exact against the documented example). |
| `test/host_run.cpp` + `cross_check.py` | Runs `main.cpp` on a PC with Arduino mocks and checks every published JSON against the decoder. |

## Run the tests (any PC with gcc and python3)
```
cd firmware/test
gcc -std=c99 -Wall -Wextra -Werror -I../include test_protocol.c -o t && ./t
g++ -std=c++17 -Ihost_mocks -I../include host_run.cpp -o h && ./h && python3 cross_check.py /tmp/gp_published.txt
python3 ../tools/gaiapus_decode.py --selftest
```
(`host_run` writes `/tmp/gp_published.txt`; on Windows change that path in `host_run.cpp`.)

## Bench vs field stake
| | Bench / Wokwi (this code) | Field stake (next step) |
|---|---|---|
| Link | Wi-Fi + MQTT, publishes the gateway JSON itself | LoRa SX1262 (RadioLib) -> community gateway -> MQTT |
| Moisture | potentiometer / analog capacitive sensor, mapped to raw counts | 74LVC1G14 oscillator counted by PCNT |
| Air T/RH | DHT22 | SHT40 (I2C 0x44) |
| Timing | 1 protocol minute = 0.5 s (`DEMO_MS_PER_MIN`) | deep sleep, wake by timer / rain pulse / DIO1 |
| LED | steady (visible on video) | 60 ms flash every 4 s (`LED_STEADY 0`) |

The packet bytes are identical in both; the JSON carries them in `lora_payload_hex` so the jury can see what would go over the air.

## Physical bench
`platformio.ini` targets an ESP32-S3 dev board. A classic ESP32 board has no GPIO 41/42/47/48: change `pinos.h` for it.
For a real Wi-Fi network add `-DWIFI_SSID=... -DWIFI_PASS=... -DWIFI_CHANNEL=0` in `build_flags`.

# Wokwi simulation · virtual prototype

Runs the same firmware as the bench (`firmware/src/main.cpp`, copied here as `sketch.ino` by `firmware/tools/sync_wokwi.py`).

## Run it on wokwi.com (free account)
1. New project -> **ESP32-S3** (Arduino).
2. Replace `sketch.ino` and `diagram.json` with the files of this folder.
3. Add the files `gaiapus_protocol.h`, `pinos.h` and `libraries.txt` (Wokwi editor: "+" next to the tabs).
4. Start. The serial monitor shows the 25-byte LoRa payload and the JSON published to `broker.hivemq.com`, topic `gaiapus/devices/<id>/up` (id printed at boot; with Wokwi's default MAC it is `c4000110`).

## What each part stands for
| Part | GPIO | Stands for |
|---|---|---|
| Potentiometer 1 / 2 | 4 / 5 | soil moisture 15 / 40 cm (turn = wetter/drier) |
| Potentiometer 3 | 1 | battery voltage (2.5-3.65 V) |
| NTC modules | 2 / 6 | soil temperature 15 / 40 cm (click to change) |
| DHT22 | 8 | air T/RH (the PCB uses an SHT40) |
| Blue button | 17 | one rain-gauge tip (0.2 mm, placeholder) |
| Black button | 0 | user button: measure and send now, sets flag bit 0 |
| LEDs G/Y/R | 41 / 42 / 21 | status sent back by the backend |

## Send the LED command (simulates the backend decision)
Any MQTT client (e.g. HiveMQ web client, MQTT Explorer, `mosquitto_pub`):
```
topic:   gaiapus/devices/c4000110/down
payload: {"led": 2, "intervalo_min": 30}
```
led: 0 off, 1 green, 2 yellow, 3 red.

## Honest limits (say it in the pitch)
- Wokwi does not simulate LoRa: the bench publishes the JSON the gateway would publish, with the same 25 bytes inside.
- Moisture and battery are potentiometers, air sensor is a DHT22.
- The public HiveMQ broker is shared and unauthenticated: fine for a demo, not for real data.
- Not yet run inside Wokwi by us: the firmware was compiled and executed on a PC against Arduino mocks. The `diagram.json` pin names (`3V3.1`, `GND.1`, `GND.2`) follow the ESP32-S3-DevKitC-1 board in Wokwi; if a wire shows red, re-attach it in the editor.

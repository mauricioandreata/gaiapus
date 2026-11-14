# Protocolo de dados · contrato hardware ↔ software

Acordo entre estaca/bancada, gateway e backend, alinhado ao esquema de eventos do time de software.
Mudou aqui, avisa o time.

## Uplink LoRa (estaca → gateway): 25 bytes, little-endian

| Byte | Campo | Tipo | Unidade |
|---|---|---|---|
| 0 | `versao` | uint8 | = 1 (byte reservado para evolução do formato) |
| 1–4 | `node_id` | uint32 | últimos 4 octetos do MAC (24:0a:**c4:00:01:10** → 0xC4000110); `device_id` = 8 hex minúsculos (`c4000110`) |
| 5–6 | `seq` | uint16 | contador de medições (não muda no reenvio) |
| 7–8 | `raw_15` | uint16 | contagem do oscilador, eletrodo 15 cm |
| 9–10 | `raw_40` | uint16 | contagem do oscilador, eletrodo 40 cm |
| 11–12 | `t_solo_15` | int16 | 0,01 °C |
| 13–14 | `t_solo_40` | int16 | 0,01 °C |
| 15–16 | `t_ar` | int16 | 0,01 °C |
| 17 | `ur_ar` | uint8 | % |
| 18–19 | `chuva_pulsos` | uint16 | pulsos no intervalo da medição |
| 20–21 | `vbat` | uint16 | mV |
| 22–23 | `idade_min` | uint16 | minutos desde a medição (0 = agora; >0 = reenvio do buffer) |
| 24 | `flags` | uint8 | bit0 botão, bit1 bateria baixa, bit2 erro de sensor |

Umidade sai **bruta**; calibração (fábrica + solo) aplicada no backend.

## Downlink LoRa (gateway → estaca): 2 bytes
| Byte | Campo | Valores |
|---|---|---|
| 0 | `led` | 0 apagado, 1 verde, 2 amarelo, 3 vermelho |
| 1 | `intervalo_min` | minutos entre medições (padrão 30) |

## Gateway / bancada → backend (MQTT ou HTTPS)

Tópico MQTT: `gaiapus/devices/{device_id}/up`. A bancada (Wi-Fi) publica o mesmo JSON direto.

```json
{
  "device_id": "a1b2c3d4",
  "seq": 128,
  "observed_at": "2026-11-14T13:30:00Z",
  "received_at": "2026-11-14T13:30:02Z",
  "readings": [
    {"depth_cm": 15, "raw_moisture": 18342, "soil_temp_c": 24.31},
    {"depth_cm": 40, "raw_moisture": 21011, "soil_temp_c": 23.10}
  ],
  "air_temp_c": 29.80,
  "air_rh_pct": 54,
  "rain_mm": 0.4,
  "battery_mv": 3285,
  "rssi": -97,
  "snr": 7.5,
  "flags": 0
}
```
`observed_at = received_at − idade_min` (o gateway/bancada sincroniza a hora; a estaca não precisa de relógio real). `idade_min` é sempre em minutos reais, inclusive na demo.

Campo extra só da bancada/Wokwi: `lora_payload_hex` (os 25 bytes que iriam pelo LoRa). O backend pode ignorar.

Implementação de referência: `firmware/include/gaiapus_protocol.h` (C) e `firmware/tools/gaiapus_decode.py` (Python, gateway/backend).
`rain_mm = chuva_pulsos × mm_por_pulso` (constante do pluviômetro, definida pela mecânica).

## Backend → esquema de eventos do app (um evento por profundidade)

| Campo do app | Origem |
|---|---|
| `event_id` | `device_id`-`seq`-`depth_cm` (reenvio não duplica) |
| `device_id` | `device_id` |
| `observed_at` (UTC) | `observed_at` |
| `depth_cm` | `readings[].depth_cm` |
| `raw_moisture` | `readings[].raw_moisture` |
| `moisture_m3_m3` | calculado após calibração; vazio se não calibrado |
| `soil_temp_c` | `readings[].soil_temp_c` |
| `battery_mv` | `battery_mv` |
| `quality` | `flags` + faixa válida |

Campos extras propostos ao esquema: `air_temp_c`, `air_rh_pct`, `rain_mm`, `rssi`, `snr`.

Comando: `gaiapus/devices/{device_id}/down` com `{"led": 2, "intervalo_min": 30}`.

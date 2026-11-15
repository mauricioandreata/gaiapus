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
| 24 | `flags` | uint8 | bit0 botão, bit1 bateria baixa, bit2 erro de sensor, bit3 carregando (painel solar, informativo) |

Umidade sai **bruta**; calibração (fábrica + solo) aplicada no backend.

## Downlink LoRa (gateway → estaca): 2 bytes de comando, 6 bytes no ar
| Byte | Campo | Valores |
|---|---|---|
| 0 | `led` | 0 apagado, 1 verde, 2 amarelo, 3 vermelho |
| 1 | `intervalo_min` | minutos entre medições (padrão 30) |

No rádio todas as estacas próximas ouvem o gateway, então o quadro transmitido é
`node_id` (4 bytes, little-endian, o mesmo do uplink) + os 2 bytes acima = **6 bytes**.
Ex.: estaca `c4000110`, amarelo, 10 min → `10 01 00 C4 02 0A`.

- O gateway publica o uplink no MQTT e, **só se a publicação deu certo**, responde logo em seguida (a estaca escuta 1,5 s) com o último comando que tem para aquela estaca (vindo do tópico `down`; estaca sem comando: `led` 0 e 30 min). Sem internet no gateway não há resposta, e a medição continua na fila da estaca.
- Esse quadro é a **confirmação de entrega**. Sem ele a estaca mantém a medição na fila e reenvia no próximo ciclo com `idade_min > 0`. O backend descarta duplicatas por `event_id`.
- Rádio: 916,8 MHz, SF9, BW 125 kHz, CR 4/5, sync word 0x12, CRC ligado.
- Código: `gp_encode_downlink_frame()` (C) / `encode_downlink_frame()` (Python).

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
  "flags": 0,
  "gateway_id": "9f3e0a12"
}
```
`gateway_id`: gateway que ouviu a estaca (8 hex, mesmo formato do `device_id`). Ausente quando a própria estaca publica por Wi-Fi.
Uma estaca pode ser ouvida por dois gateways: chegam duas mensagens iguais com `gateway_id` diferentes, e o `event_id` evita duplicar a medição.
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

Campos extras propostos ao esquema: `air_temp_c`, `air_rh_pct`, `rain_mm`, `rssi`, `snr`, `gateway_id`.

Comando: `gaiapus/devices/{device_id}/down` com `{"led": 2, "intervalo_min": 30}`, **publicado com retain**
(a estaca em Wi-Fi acorda a cada ciclo, assina e recebe o último comando; o gateway LoRa assina `gaiapus/devices/+/down` e guarda o último por estaca).
Comando parcial (só `led`) mantém o outro campo; mensagem retida vazia apaga o comando.

Saúde do gateway: `gaiapus/gateways/{gateway_id}/status` (retido, a cada 5 min) com `uptime_s`, `rx_ok`, `rx_bad`, `rx_other`, `acked`, `no_backend`, `stakes_cached`, `radio_ok`, `wifi_rssi`, `freq_mhz`, `sf`.

## Cadastro da estaca: onde ela está (instalação por QR)

A estaca não tem GPS (fora do escopo da Rev A) e o firmware não sabe onde está. A posição vem do celular de quem instala e fica no backend. É essa posição que liga a estaca aos dados da NASA (POWER, IMERG, SMAP, SRTM são consultados por coordenada) e ao ZARC do município.

### 1. Fábrica / montagem
- O `device_id` aparece no boot pela USB e no modo diagnóstico (botão 3 s): `gaiapus stake c4000110`.
- O backend registra o `device_id` e gera um **código de posse** curto e aleatório (6 caracteres). Sem ele, quem só visse o número da estaca poderia cadastrá-la como sua.
- A etiqueta do case (D22) leva o QR com uma URL do app: `https://<app>/e/{device_id}?c={codigo}`, mais o `device_id` legível embaixo. URL, e não texto, para que a câmera de qualquer celular abra o app/PWA sem instalar nada.
- Os gateways recebem etiqueta igual (`/g/{gateway_id}`): também precisam de posição.

### 2. Instalação no campo
1. Cravar a estaca e escanear o QR: o app abre já com a estaca identificada.
2. O app pega a posição GPS do celular. Precisão pior que 15 m: pedir para esperar ou ajustar o pino no mapa.
3. O produtor confirma fazenda e talhão / zona de manejo (lista do cadastro dele) e, se quiser, tira uma foto.
4. **Apertar o botão da estaca:** ela mede e envia na hora, com `flags` bit0. Quando esse uplink chega, o app mostra "estaca conectada via gateway X, sinal −97 dBm". O instalador sai do campo sabendo que funciona.

### 3. Registro de instalação (backend)
| Campo | Origem |
|---|---|
| `installation_id` | gerado |
| `device_id` | QR |
| `owner_id`, `farm_id`, `field_id` / zona | app (produtor) |
| `lat`, `lon`, `accuracy_m` | GPS do celular |
| `installed_at` (UTC), `installed_by` | app |
| `photo_url` | opcional |
| `home_gateways` | `gateway_id` do primeiro uplink após a instalação (lista, cresce com o uso) |
| `removed_at` | preenchido ao retirar ou reinstalar |

Regras:
- Cada medição pertence à instalação **ativa em `observed_at`**. Estaca mudada de lugar = novo escaneamento = nova instalação. O histórico antigo continua ligado à posição antiga.
- Uma estaca pode ter **uma instalação ativa por vez**.
- O código de posse vale para o primeiro cadastro. Para transferir a estaca, o dono atual libera no app.

### 4. Alertas que saem disso
- **Estaca possivelmente movida ou furtada:** uplink com `gateway_id` fora de `home_gateways` e gateway a mais de ~5 km da instalação (por isso os gateways também têm posição).
- **Estaca muda:** nenhum uplink há mais de 3 × `intervalo_min`. Indica bateria, rádio ou gateway com problema.
- **Sinal fraco:** RSSI abaixo de −120 dBm ou SNR abaixo de −10 dB por vários dias. Indica que a estaca está no limite do alcance.

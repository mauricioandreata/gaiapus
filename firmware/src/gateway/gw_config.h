/* gw_config.h - community gateway settings. Radio settings come from src/stake/config.h
 * (LORA_*), so stake and gateway can never disagree on frequency / SF / sync word. */
#ifndef GAIAPUS_GW_CONFIG_H
#define GAIAPUS_GW_CONFIG_H

#ifndef WIFI_SSID
#define WIFI_SSID          "Wokwi-GUEST"
#endif
#ifndef WIFI_PASS
#define WIFI_PASS          ""
#endif
#ifndef MQTT_HOST
#define MQTT_HOST          "broker.hivemq.com"
#endif
#ifndef MQTT_PORT
#define MQTT_PORT          1883
#endif
#ifndef MM_PER_PULSE
#define MM_PER_PULSE       0.2f    /* rain gauge constant (mechanics), same as the decoder */
#endif

#define GW_MAX_NODES       64      /* stakes with a cached LED command                     */
#define GW_REPLY_DELAY_MS  20      /* let the stake switch from TX to RX                   */
#define GW_STATUS_EVERY_S  300     /* heartbeat on gaiapus/gateways/{id}/status            */
#define GW_MQTT_RETRY_MS   5000
#define GW_REBOOT_OFFLINE_MIN 30   /* no Wi-Fi this long -> restart                        */
#define GW_RADIO_REARM_MIN 15      /* no packet this long -> re-initialise the SX1262      */
#define GW_FW_VERSION      "gw-1.0"

/* status LEDs (default: the Gaiapus head board). -1 = not fitted. */
#ifndef GW_LED_G
#define GW_LED_G           PIN_LED_G   /* on = all good, blinks off on every packet          */
#define GW_LED_Y           PIN_LED_Y   /* on = Wi-Fi ok but backend (MQTT/NTP) down          */
#define GW_LED_R           PIN_LED_R   /* on = no Wi-Fi or radio not answering               */
#endif

#endif

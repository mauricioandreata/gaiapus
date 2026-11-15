/*
 * config.h - build-time settings of the field stake firmware.
 * Every value can be overridden from platformio.ini with -DNAME=value.
 */
#ifndef GAIAPUS_STAKE_CONFIG_H
#define GAIAPUS_STAKE_CONFIG_H

/* ---------- link: exactly one ----------
 * LINK_LORA : product. SX1262 P2P -> community gateway -> MQTT (D2).
 * LINK_WIFI : demo with the real board and no gateway (D7). Publishes the
 *             gateway JSON itself, same as the bench firmware.            */
#if !defined(LINK_LORA) && !defined(LINK_WIFI)
#define LINK_LORA 1
#endif
#if defined(LINK_LORA) && defined(LINK_WIFI)
#error "choose LINK_LORA or LINK_WIFI"
#endif

/* ---------- measurement cycle ---------- */
#ifndef DEFAULT_INTERVAL_MIN
#define DEFAULT_INTERVAL_MIN   30     /* F6; changed by downlink                        */
#endif
#ifndef SECONDS_PER_MIN
#define SECONDS_PER_MIN        60     /* demo: -DSECONDS_PER_MIN=2 makes 30 min = 1 min  */
#endif
#define JITTER_PCT             3      /* +-3 % on every sleep: stakes drift apart, fewer collisions */
#define BUF_LEN                48     /* F9: offline queue in RTC RAM (24 h at 30 min)  */
#define MAX_SENDS_PER_CYCLE    4      /* newest first, then backlog                     */

/* ---------- soil moisture (PCNT on the 74LVC1G14 oscillators) ---------- */
#define OSC_SETTLE_MS          3      /* GPIO powers 100 nF + oscillator               */
#define OSC_GATE_US            10000  /* raw = edges in 10 ms = f / 100 (0.5-2 MHz -> 5k-20k) */
#define OSC_MIN_RAW            50     /* < 5 kHz: oscillator dead / probe unplugged     */

/* ---------- soil temperature (NTC 10k B3380 to GND, 10k from PWR_NTC) ---------- */
#define NTC_BETA               3380.0f
#define NTC_R0                 10000.0f
#define NTC_R_FIXED            10000.0f
#define NTC_SETTLE_MS          2      /* 10k x 10 nF = 0.1 ms                          */
#define ADC_SAMPLES            8

/* ---------- battery (LiFePO4 1S, 2.2M/2.2M divider) ---------- */
#define VBAT_DIVIDER           2.0f
#define VBAT_LOW_MV            3000   /* flag bit1                                      */
#define VBAT_NO_RADIO_MV       2900   /* below: measure and queue, but do not transmit  */
#define VBAT_NO_WIFI_MV        3100   /* Wi-Fi peaks are ~5x LoRa                       */

/* ---------- rain gauge ---------- */
#define RAIN_DEBOUNCE_MS       50
#define RAIN_RELEASE_WAIT_MS   400    /* after a wake by the reed, wait until it opens  */

/* ---------- user interface ---------- */
#define LED_SHOW_MS            8000   /* after a button press: LED steady for 8 s       */
#define LED_FLASH_MS           120    /* after every cycle: short flash of the status   */
#define DIAG_HOLD_MS           3000   /* hold button 3 s -> diagnostic mode on USB      */
#define DIAG_DURATION_S        180

/* ---------- LoRa (E22-900MM22S = SX1262 + TCXO on DIO3, RF switch on TXEN/RXEN) ---------- */
#ifndef LORA_FREQ_MHZ
#define LORA_FREQ_MHZ          916.8f /* inside 915-928 MHz (Anatel, AU915 band)        */
#endif
#ifndef LORA_SF
#define LORA_SF                9
#endif
#define LORA_BW_KHZ            125.0f
#define LORA_CR                5      /* 4/5                                            */
#define LORA_SYNC_WORD         0x12   /* private network (LoRaWAN uses 0x34)            */
#ifndef LORA_TX_DBM
#define LORA_TX_DBM            14     /* power budget assumes 14 dBm; module goes to 22 */
#endif
#define LORA_PREAMBLE          8
#define LORA_TCXO_V            1.8f   /* EBYTE E22: TCXO powered from DIO3              */
#define LORA_RX_WINDOW_MS      1500   /* gateway answers ~200 ms after the uplink       */

/* ---------- Wi-Fi demo link ---------- */
#ifndef WIFI_SSID
#define WIFI_SSID              "Wokwi-GUEST"
#endif
#ifndef WIFI_PASS
#define WIFI_PASS              ""
#endif
#ifndef MQTT_HOST
#define MQTT_HOST              "broker.hivemq.com"
#endif
#ifndef MQTT_PORT
#define MQTT_PORT              1883
#endif
#define WIFI_CONNECT_MS        8000
#define MQTT_DOWN_WAIT_MS      1500   /* retained command arrives right after subscribe */
#define NTP_RESYNC_S           (24L * 3600)
#define MM_PER_PULSE           0.2f   /* placeholder until mechanics defines the bucket */

#endif

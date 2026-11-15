/* Shared state of the host mocks (driven by test/host_stake.cpp and test/host_gateway.cpp). */
#pragma once
#include <cstdint>
#include <cstddef>
#include <cstdio>
#include <vector>
#include <string>
#include <utility>
struct DeepSleep { uint64_t us; };                     /* thrown by esp_deep_sleep_start() */
inline int64_t mock_us;                                /* microseconds since power-on      */
inline int64_t mock_epoch;                             /* time() = mock_epoch + mock_us/1e6 */
inline int mock_dout[64], mock_din[64], mock_mv[64];
inline double mock_freq_hz[64];                        /* oscillator frequency per FREQ pin */
inline int mock_wake_cause;
inline uint64_t mock_sleep_timer_us;
inline bool mock_ext0_on, mock_ext1_on;
inline bool mock_sht_ok = true;
inline float mock_air_t = 29.8f, mock_air_rh = 54.0f;
/* LoRa gateway seen from the stake */
inline bool mock_gw_online = true, mock_gw_foreign_first;
inline uint8_t mock_gw_led = 1, mock_gw_interval = 30;
struct MockTx { int64_t us; std::vector<uint8_t> data; bool acked; };
inline std::vector<MockTx> mock_tx;
/* Wi-Fi / MQTT */
inline bool mock_wifi_online = true;
inline std::string mock_retained_down;                 /* stake: retained command on its down topic */
inline std::vector<std::pair<std::string, std::string>> mock_mqtt_inbox;   /* gateway: (topic, payload) */
inline FILE *mock_pub;
inline int mock_publish_count;

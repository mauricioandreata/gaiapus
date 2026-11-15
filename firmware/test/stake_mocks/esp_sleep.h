#pragma once
#include "mock.h"
typedef enum { ESP_SLEEP_WAKEUP_UNDEFINED = 0, ESP_SLEEP_WAKEUP_ALL = 1, ESP_SLEEP_WAKEUP_EXT0 = 2,
               ESP_SLEEP_WAKEUP_EXT1 = 3, ESP_SLEEP_WAKEUP_TIMER = 4 } esp_sleep_wakeup_cause_t;
typedef enum { ESP_EXT1_WAKEUP_ALL_LOW = 0, ESP_EXT1_WAKEUP_ANY_LOW = 0, ESP_EXT1_WAKEUP_ANY_HIGH = 1 } esp_sleep_ext1_wakeup_mode_t;
typedef int gpio_num_t;
inline esp_sleep_wakeup_cause_t esp_sleep_get_wakeup_cause() { return (esp_sleep_wakeup_cause_t)mock_wake_cause; }
inline void esp_sleep_disable_wakeup_source(int) { mock_ext0_on = mock_ext1_on = false; mock_sleep_timer_us = 0; }
inline void esp_sleep_enable_timer_wakeup(uint64_t us) { mock_sleep_timer_us = us; }
inline void esp_sleep_enable_ext0_wakeup(gpio_num_t, int) { mock_ext0_on = true; }
inline void esp_sleep_enable_ext1_wakeup(uint64_t, esp_sleep_ext1_wakeup_mode_t) { mock_ext1_on = true; }
inline void esp_deep_sleep_start() { throw DeepSleep{mock_sleep_timer_us}; }

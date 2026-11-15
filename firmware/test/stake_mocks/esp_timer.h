#pragma once
#include "mock.h"
inline int64_t esp_timer_get_time() { return ++mock_us; }   /* busy loops advance the clock */

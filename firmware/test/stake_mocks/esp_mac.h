#pragma once
#include <cstring>
#define ESP_MAC_WIFI_STA 0
inline int esp_read_mac(uint8_t *m, int) { const uint8_t w[6] = {0x24, 0x0a, 0xc4, 0x00, 0x01, 0x10}; memcpy(m, w, 6); return 0; }

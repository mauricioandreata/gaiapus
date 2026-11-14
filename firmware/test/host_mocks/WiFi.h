#pragma once
#include "Arduino.h"
#define WL_CONNECTED 3
#define WIFI_STA 1
struct MockWiFi { int status() { return WL_CONNECTED; } void mode(int) {} void begin(const char *, const char *, int) {}
  void macAddress(uint8_t *m) { const uint8_t w[6] = {0x24, 0x0a, 0xc4, 0x00, 0x01, 0x10}; memcpy(m, w, 6); } int RSSI() { return -58; } };
extern MockWiFi WiFi;
struct WiFiClient {};

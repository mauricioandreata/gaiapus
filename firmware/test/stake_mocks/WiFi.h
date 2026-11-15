#pragma once
#include "Arduino.h"
#define WL_CONNECTED 3
#define WIFI_STA 1
#define WIFI_OFF 0
struct MockWiFi {
  int st = 0;
  void persistent(bool) {} void mode(int) {} void setAutoReconnect(bool) {}
  void begin(const char *, const char *, int32_t = 0, const uint8_t * = nullptr, bool = true) { delay(400); st = mock_wifi_online ? WL_CONNECTED : 0; }
  int status() { return mock_wifi_online ? st : 0; } void disconnect(bool = false) { st = 0; }
  int RSSI() { return -61; } int32_t channel() { return 6; }
  uint8_t *BSSID() { static uint8_t b[6] = {1,2,3,4,5,6}; return b; }
};
inline MockWiFi WiFi;
struct WiFiClient {};

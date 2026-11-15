#pragma once
#include "Arduino.h"
struct TwoWire {
  uint8_t cmd = 0, rx[6]; int rn = 0, ri = 0;
  void begin(int, int, uint32_t) {}
  void beginTransmission(uint8_t) {}
  void write(uint8_t c) { cmd = c; }
  uint8_t endTransmission();
  uint8_t requestFrom(uint8_t, uint8_t n);
  int read() { return ri < rn ? rx[ri++] : -1; }
};
inline TwoWire Wire;

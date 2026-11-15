#pragma once
#include "SPI.h"
#define RADIOLIB_ERR_NONE 0
#define RADIOLIB_ERR_CHIP_NOT_FOUND (-2)
#define RADIOLIB_ERR_CRC_MISMATCH (-7)
struct Module { Module(int, int, int, int, SPIClass &, SPISettings) {} };
struct SX1262 {
  SX1262(Module *) {}
  int begin(float freq, float bw, uint8_t sf, uint8_t cr, uint8_t sw, int8_t pwr, uint16_t pre, float tcxo, bool ldo);
  int setDio2AsRfSwitch(bool) { return 0; }
  void setRfSwitchPins(int, int) {}
  int setCurrentLimit(float) { return 0; }
  int setCRC(bool) { return 0; }
  int transmit(uint8_t *d, size_t n);
  int startReceive();
  int standby();
  size_t getPacketLength();
  int readData(uint8_t *d, size_t n);
  float getRSSI() { return -97.0f; }
  float getSNR() { return 7.5f; }
  int sleep();
};

#pragma once
#include "Arduino.h"
#define FSPI 0
#define MSBFIRST 1
#define SPI_MODE0 0
struct SPISettings { SPISettings(uint32_t, int, int) {} };
struct SPIClass { SPIClass(int) {} void begin(int, int, int, int) {} };

#pragma once
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <cmath>
#include <ctime>
#include <cstdarg>
#include <initializer_list>
#include "mock.h"
typedef uint8_t byte;
#define IRAM_ATTR
#define RTC_DATA_ATTR
#define HIGH 1
#define LOW 0
#define INPUT 1
#define INPUT_PULLUP 2
#define OUTPUT 3
#define FALLING 2
#define ADC_11db 3
#define ARDUINO_USB_CDC_ON_BOOT 1
inline uint32_t millis() { return (uint32_t)(mock_us / 1000); }
inline void delay(uint32_t ms) { mock_us += (int64_t)ms * 1000; }
inline void pinMode(int, int) {}
inline void digitalWrite(int p, int v) { mock_dout[p] = v; }
int digitalRead(int p);
inline uint32_t analogReadMilliVolts(int p) { return (uint32_t)mock_mv[p]; }
inline void analogReadResolution(int) {}
inline void analogSetAttenuation(int) {}
inline int digitalPinToInterrupt(int p) { return p; }
inline void attachInterrupt(int, void (*)(void), int) {}
inline void noInterrupts() {}
inline void interrupts() {}
struct MockSerial {
  void begin(int) {} void setTxTimeoutMs(int) {} void flush() {}
  void printf(const char *f, ...) { va_list a; va_start(a, f); vprintf(f, a); va_end(a); }
  void println(const char *s) { printf("%s\n", s); }
};
inline MockSerial Serial;
struct MockESP { [[noreturn]] void restart() { fprintf(stderr, "ESP.restart()\n"); exit(3); } };
inline MockESP ESP;

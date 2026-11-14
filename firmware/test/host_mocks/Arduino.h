/* Minimal host mock of the Arduino/ESP32 API: enough to compile and run src/main.cpp on a PC. */
#pragma once
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <cmath>
#include <ctime>
#include <cstdarg>
#include <initializer_list>
#include <algorithm>
typedef uint8_t byte;
#define IRAM_ATTR
#define HIGH 1
#define LOW 0
#define INPUT_PULLUP 2
#define OUTPUT 3
#define FALLING 2
#ifndef NAN
#define NAN (0.0f/0.0f)
#endif
extern uint32_t mock_ms; extern int mock_adc[64]; extern int mock_dout[64];
inline uint32_t millis() { return mock_ms; }
inline void delay(uint32_t ms) { mock_ms += ms; }
inline int analogRead(int p) { return mock_adc[p]; }
inline void analogReadResolution(int) {}
inline void pinMode(int, int) {}
inline void digitalWrite(int p, int v) { mock_dout[p] = v; }
inline int digitalPinToInterrupt(int p) { return p; }
inline void attachInterrupt(int, void (*)(void), int) {}
inline void noInterrupts() {}
inline void interrupts() {}
inline long map(long x, long a, long b, long c, long d) { return (x - a) * (d - c) / (b - a) + c; }
template <class T, class L, class H> inline T constrain(T x, L lo, H hi) { return x < (T)lo ? (T)lo : (x > (T)hi ? (T)hi : x); }
struct MockSerial { void begin(int) {} void printf(const char *f, ...) { va_list a; va_start(a, f); vprintf(f, a); va_end(a); } };
extern MockSerial Serial;
inline void configTime(long, int, const char *, const char *) {}
inline bool getLocalTime(struct tm *, uint32_t) { return true; }

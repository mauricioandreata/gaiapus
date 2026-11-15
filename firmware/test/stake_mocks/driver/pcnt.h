#pragma once
/* ESP-IDF 4.4 legacy PCNT driver mock; wraps at h_lim and calls the ISR like the hardware. */
#include "../mock.h"
#define ESP_OK 0
typedef int esp_err_t;
#define PCNT_PIN_NOT_USED (-1)
enum { PCNT_CHANNEL_0 }; enum { PCNT_UNIT_0 }; enum { PCNT_COUNT_DIS, PCNT_COUNT_INC }; enum { PCNT_MODE_KEEP };
enum { PCNT_EVT_H_LIM = 1 };
typedef int pcnt_unit_t;
typedef struct { int pulse_gpio_num, ctrl_gpio_num, lctrl_mode, hctrl_mode, pos_mode, neg_mode; int16_t counter_h_lim, counter_l_lim; int unit, channel; } pcnt_config_t;
double mock_osc_hz(int pin);
struct mock_legacy { pcnt_config_t c; int64_t t0; double counted; void (*isr)(void *); };
inline mock_legacy mock_pcnt;
inline esp_err_t pcnt_unit_config(const pcnt_config_t *c) { mock_pcnt.c = *c; return 0; }
inline esp_err_t pcnt_filter_disable(int) { return 0; }
inline esp_err_t pcnt_event_enable(int, int) { return 0; }
inline esp_err_t pcnt_isr_service_install(int) { return 0; }
inline esp_err_t pcnt_isr_handler_add(int, void (*f)(void *), void *) { mock_pcnt.isr = f; return 0; }
inline esp_err_t pcnt_isr_handler_remove(int) { mock_pcnt.isr = nullptr; return 0; }
inline esp_err_t pcnt_counter_pause(int) { double n = mock_osc_hz(mock_pcnt.c.pulse_gpio_num) * (mock_us - mock_pcnt.t0) / 1e6;
  mock_pcnt.counted += n; while (mock_pcnt.counted >= mock_pcnt.c.counter_h_lim) { mock_pcnt.counted -= mock_pcnt.c.counter_h_lim; if (mock_pcnt.isr) mock_pcnt.isr(nullptr); } return 0; }
inline esp_err_t pcnt_counter_clear(int) { mock_pcnt.counted = 0; return 0; }
inline esp_err_t pcnt_counter_resume(int) { mock_pcnt.t0 = mock_us; return 0; }
inline esp_err_t pcnt_get_counter_value(int, int16_t *v) { *v = (int16_t)mock_pcnt.counted; return 0; }

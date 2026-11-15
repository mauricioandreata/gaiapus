#pragma once
/* ESP-IDF 5 PCNT driver mock: counts mock_freq_hz[pin] while the unit runs. */
#include "../mock.h"
#define ESP_OK 0
typedef int esp_err_t;
struct mock_unit { int pin = -1; int64_t t0 = 0; double counted = 0; bool run = false; };
typedef mock_unit *pcnt_unit_handle_t;
typedef mock_unit *pcnt_channel_handle_t;
typedef struct { int low_limit, high_limit, intr_priority; struct { uint32_t accum_count : 1; } flags; } pcnt_unit_config_t;
typedef struct { int edge_gpio_num, level_gpio_num; struct { uint32_t x : 1; } flags; } pcnt_chan_config_t;
enum { PCNT_CHANNEL_EDGE_ACTION_HOLD, PCNT_CHANNEL_EDGE_ACTION_INCREASE };
double mock_osc_hz(int pin);
inline esp_err_t pcnt_new_unit(const pcnt_unit_config_t *c, pcnt_unit_handle_t *u) { if (c->low_limit >= 0 || c->high_limit <= 0) return 1; *u = new mock_unit; return 0; }
inline esp_err_t pcnt_new_channel(pcnt_unit_handle_t u, const pcnt_chan_config_t *c, pcnt_channel_handle_t *ch) { u->pin = c->edge_gpio_num; *ch = u; return 0; }
inline esp_err_t pcnt_channel_set_edge_action(pcnt_channel_handle_t, int, int) { return 0; }
inline esp_err_t pcnt_unit_add_watch_point(pcnt_unit_handle_t, int) { return 0; }
inline esp_err_t pcnt_unit_remove_watch_point(pcnt_unit_handle_t, int) { return 0; }
inline esp_err_t pcnt_unit_enable(pcnt_unit_handle_t) { return 0; }
inline esp_err_t pcnt_unit_disable(pcnt_unit_handle_t) { return 0; }
inline esp_err_t pcnt_unit_clear_count(pcnt_unit_handle_t u) { u->counted = 0; return 0; }
inline esp_err_t pcnt_unit_start(pcnt_unit_handle_t u) { u->t0 = mock_us; u->run = true; return 0; }
inline esp_err_t pcnt_unit_stop(pcnt_unit_handle_t u) { u->counted += mock_osc_hz(u->pin) * (mock_us - u->t0) / 1e6; u->run = false; return 0; }
inline esp_err_t pcnt_unit_get_count(pcnt_unit_handle_t u, int *c) { *c = (int)u->counted; return 0; }
inline esp_err_t pcnt_del_channel(pcnt_channel_handle_t) { return 0; }
inline esp_err_t pcnt_del_unit(pcnt_unit_handle_t u) { delete u; return 0; }

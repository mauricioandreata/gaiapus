/* Drives src/main.cpp on the host: boots, runs cycles, drops the network, presses rain/button, sends a downlink. */
#include "../src/main.cpp"
uint32_t mock_ms = 0; int mock_adc[64]; int mock_dout[64]; MockSerial Serial; MockWiFi WiFi;
bool mock_online = true; FILE *mock_pub; float mock_air_t = 31.2f, mock_air_rh = 58.0f;
static time_t base = 1794659400;   /* 2026-11-14T12:30:00Z */
extern "C" time_t time(time_t *t) { time_t v = base + mock_ms / 1000; if (t) *t = v; return v; }
static void run_ms(uint32_t ms) { uint32_t end = mock_ms + ms; while (mock_ms < end) loop(); }
static int adc_for_ntc(float c, float beta) { float r = expf(beta * (1.0f / (c + 273.15f) - 1.0f / 298.15f)); return (int)lroundf(4095.0f * r / (1.0f + r)); }
int main() {
  mock_pub = fopen("/tmp/gp_published.txt", "w");
  mock_adc[PIN_OSC15_FREQ] = 2048; mock_adc[PIN_OSC40_FREQ] = 1000;
  mock_adc[PIN_NTC15_ADC] = adc_for_ntc(26.40f, NTC_BETA); mock_adc[PIN_NTC40_ADC] = adc_for_ntc(24.85f, NTC_BETA);
  mock_adc[PIN_VBAT_ADC] = 2900;
  setup();
  run_ms(2100);                                  /* first measurement */
  for (int i = 0; i < 6; i++) on_rain(), mock_ms += 100;  /* 6 bucket tips -> 1.2 mm */
  run_ms(15100);                                 /* second (30 "min" later) */
  mock_online = false; run_ms(15100); mock_ms += 180000;  /* third: offline -> buffered, network back 3 min later */
  mock_online = true;  button_pressed = true; run_ms(200);   /* button: flush buffer + new */
  const char *dl = "{\"led\": 2, \"intervalo_min\": 10}";
  mqtt.cb((char *)"t", (byte *)dl, strlen(dl));
  printf("LED pins after downlink: G=%d Y=%d R=%d, interval=%u\n", mock_dout[PIN_LED_G], mock_dout[PIN_LED_Y], mock_dout[PIN_LED_R], interval_min);
  mock_air_t = NAN; run_ms(15100);                 /* DHT failure -> null + sensor flag */
  fclose(mock_pub);
  return 0;
}

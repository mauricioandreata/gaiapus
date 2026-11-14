#pragma once
struct TempAndHumidity { float temperature, humidity; };
extern float mock_air_t, mock_air_rh;
struct DHTesp { enum { DHT22 = 2 }; void setup(int, int) {} TempAndHumidity getTempAndHumidity() { return { mock_air_t, mock_air_rh }; } };

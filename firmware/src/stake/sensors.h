/* sensors.h - field stake sensors (head + probe boards). */
#ifndef GAIAPUS_STAKE_SENSORS_H
#define GAIAPUS_STAKE_SENSORS_H

#include <stdint.h>
#include <stdbool.h>

typedef struct {
    uint16_t raw_15, raw_40;      /* oscillator edges per 10 ms gate (f / 100), 0 = no oscillation */
    float    t_soil_15, t_soil_40;/* degC, NAN if the NTC is open/shorted */
    float    t_air, rh_air;       /* degC / %, NAN if the SHT40 did not answer */
    uint16_t vbat_mv;
    bool     charging;            /* CN3058E CHRG low */
    bool     charged;             /* CN3058E DONE low */
} readings_t;

void     sensors_init(void);
void     sensors_read(readings_t *r);
uint16_t sensors_vbat_mv(void);
bool     sensors_ok(const readings_t *r);   /* every reading valid */

#endif

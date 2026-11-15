/* Host unit test: gcc -std=c99 -Wall -Wextra -Werror -I../include test_protocol.c && ./a.out */
#include <stdio.h>
#include <string.h>
#include "gaiapus_protocol.h"

static int fails = 0;
#define CHECK(c) do { if (!(c)) { printf("FAIL %s:%d  %s\n", __FILE__, __LINE__, #c); fails++; } } while (0)

static void hex(const uint8_t *b, size_t n, char *out) { for (size_t i = 0; i < n; i++) sprintf(out + 3 * i, "%02X ", b[i]); out[3 * n - 1] = 0; }

int main(void)
{
    /* Worked example from docs/protocolo-dados-exemplo.md (stake 23, Uberlandia, 2026-11-14 09:30) */
    gp_uplink_t m = { GP_PROTOCOL_VERSION, 23, 1234, 18450, 21300,
                      gp_centi(26.40f), gp_centi(24.85f), gp_centi(31.20f), 58, 12, 3310, 0, 0 };
    uint8_t b[GP_UPLINK_LEN]; char h[3 * GP_UPLINK_LEN + 1];
    CHECK(gp_encode_uplink(&m, b) == 25);
    hex(b, sizeof b, h);
    printf("example uplink: %s\n", h);
    CHECK(strcmp(h, "01 17 00 00 00 D2 04 12 48 34 53 50 0A B5 09 30 0C 3A 0C 00 EE 0C 00 00 00") == 0);

    gp_uplink_t r;
    CHECK(gp_decode_uplink(b, sizeof b, &r) == 0);
    CHECK(memcmp(&r, &m, sizeof m) == 0 || (r.node_id == 23 && r.seq == 1234 && r.t_soil_40 == 2485 && r.vbat_mv == 3310));

    /* negative temperature and invalid reading round-trip */
    m.t_air = gp_centi(-3.07f); m.t_soil_15 = gp_centi(0.0f / 0.0f); m.flags = GP_FLAG_SENSOR_ERROR;
    gp_encode_uplink(&m, b); gp_decode_uplink(b, sizeof b, &r);
    CHECK(r.t_air == -307);
    CHECK(r.t_soil_15 == GP_TEMP_INVALID);
    CHECK(r.flags == GP_FLAG_SENSOR_ERROR);
    CHECK(gp_centi(1000.0f) == 32767 && gp_centi(-1000.0f) == -32767);

    /* buffered resend: age 90 min -> 5A 00 at bytes 22-23 */
    m.age_min = 90; gp_encode_uplink(&m, b);
    CHECK(b[22] == 0x5A && b[23] == 0x00);

    /* error paths */
    CHECK(gp_decode_uplink(b, 24, &r) == -1);
    b[0] = 2; CHECK(gp_decode_uplink(b, 25, &r) == -2);

    /* downlink: green, 30 min -> 01 1E */
    gp_downlink_t d = { GP_LED_GREEN, 30 }, e; uint8_t db[2];
    gp_encode_downlink(&d, db);
    CHECK(db[0] == 0x01 && db[1] == 0x1E);
    db[0] = 9; db[1] = 0; gp_decode_downlink(db, 2, &e);
    CHECK(e.led == GP_LED_OFF && e.interval_min == 30);

    /* addressed LoRa downlink frame: node c4000110, yellow, 10 min -> 10 01 00 C4 02 0A */
    uint8_t fr[GP_DOWNLINK_FRAME_LEN]; gp_downlink_t f = { GP_LED_YELLOW, 10 }, g;
    CHECK(gp_encode_downlink_frame(0xC4000110u, &f, fr) == 6);
    hex(fr, sizeof fr, h);
    printf("example downlink frame: %s\n", h);
    CHECK(strcmp(h, "10 01 00 C4 02 0A") == 0);
    CHECK(gp_decode_downlink_frame(fr, 6, 0xC4000110u, &g) == 0 && g.led == GP_LED_YELLOW && g.interval_min == 10);
    CHECK(gp_decode_downlink_frame(fr, 6, 0x00000017u, &g) == -3);
    CHECK(gp_decode_downlink_frame(fr, 5, 0xC4000110u, &g) == -1);

    printf(fails ? "RESULT: FAIL (%d)\n" : "RESULT: OK\n", fails);
    return fails != 0;
}

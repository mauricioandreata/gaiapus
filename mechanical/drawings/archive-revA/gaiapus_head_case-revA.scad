// Gaiapus head case - parametric OpenSCAD model (rev A, 2026-11-14)
// Same numbers as mechanical/tools/case_params.py and drawings GAIA-MEC-01..07.
// NOTE: written without OpenSCAD available on the authoring machine -> NOT yet compiled/test-printed.
//       Open it, press F5, compare with the PDF sheets, then export STL per part (set `part`).
//
// Case frame: origin = PCB centre, x right, y toward the PCB FRONT edge (USB-C/LEDs), z up from floor underside.
// The whole model is mirrored in y at the end so that "front" is -y (OpenSCAD front view) and the solid is not mirror-imaged.

part = "assembly";      // "shell" | "lid" | "boot" | "pipe" | "assembly" | "section"
explode = 0;            // extra z gap between parts in "assembly"
$fn = 48;

// ---------------- parameters (mm) ----------------
PCB_W = 90; PCB_H = 50; PCB_T = 1.6;
Z_PCB_BOT = 24.5; Z_PCB_TOP = Z_PCB_BOT + PCB_T;
PCB_HOLES = [[-41,-21],[41,-21],[-41,21],[41,21]];
WALL = 3.5; FLOOR = 3.0;
IN_X = 52; IN_Y0 = -43.5; IN_Y1 = 26.5;
OUT_X = IN_X + WALL; OUT_Y0 = IN_Y0 - WALL; OUT_Y1 = IN_Y1 + WALL;
R_OUT = 11.5; R_IN = 8;
Z_SPLIT = 33; Z_TOP = 38.5; ROOF_T = 4; Z_ROOF_IN = Z_TOP - ROOF_T; CHAMFER = 1.5;
GROOVE_W = 2.2; GROOVE_D = 1.5; GROOVE_OFF = (WALL - GROOVE_W) / 2;
SO_D = 7; INSERT_D = 4.0;
BOSS_D = 6.6; BOSS_X = 49.3;
BOSS_POS = [[-BOSS_X,-38],[BOSS_X,-38],[-BOSS_X,22.4],[BOSS_X,22.4]];
LID_HOLE = 3.4; LID_CB_D = 6.4; LID_CB_DEPTH = 2.4;
PANEL_W = 68; PANEL_H = 37; PANEL_T = 3.2; PANEL_CLR = 0.4; PANEL_REC = 1.6; PANEL_C = [0,-24.2];
WIRE_SLOT = [30,-7,6,2];
SW1 = [-12, 2.6]; BTN_CAP_D = 12; BTN_FLANGE_D = 17; BTN_POCKET_D = 17.4; BTN_HOLE_D = 12.6; BTN_PIN_D = 3.6; SW1_H = 2.0; CAP_PROUD = 1.0; FLANGE_T = 0.8;
LEDS = [[-7.4,22.4],[-3.4,22.4],[0.6,22.4]]; PIPE_CH = 3.2; LED_WIN = [11,3.6]; LED_TOP = Z_PCB_TOP + 0.8;
USB = [-17.4, 9.6, 4.0, Z_PCB_TOP + 1.6];   // x, w, h, z centre
GLAND = [20, 16, 12.5];                      // x, z, hole d (front wall)
SMA = [23.5, 24, 6.4];                       // x, z, hole d (rear wall)
VENT = [16.2, 5, 3.4, 1.8, 6, 25];           // y centre, n, pitch, w, h, z0 (right wall)
QR = [26, 26, -8.5, 17.5];                   // w, h, y centre, z centre (left wall)
TUBE = [0, 4]; COLLAR_D = 44; COLLAR_H = 22; SOCKET_D = 32.4;
SLOT = [0, 10.5, 16, 8];                     // floor cable slot cx, cy, w, h
E = 0.01;

// ---------------- helpers ----------------
module rrect(x0, y0, x1, y1, r, z0, z1) {
    translate([0, 0, z0]) linear_extrude(height = z1 - z0)
        hull() for (x = [x0 + r, x1 - r], y = [y0 + r, y1 - r]) translate([x, y]) circle(r = r);
}
module wall_hole_y(x, z, d, y_from, len) { translate([x, y_from, z]) rotate([-90, 0, 0]) cylinder(d = d, h = len); }

// ---------------- lower shell + collar ----------------
module lower_shell() {
    difference() {
        union() {
            difference() {
                union() {
                    rrect(-OUT_X, OUT_Y0, OUT_X, OUT_Y1, R_OUT, 0, Z_SPLIT);
                    translate([TUBE[0], TUBE[1], -COLLAR_H]) cylinder(d = COLLAR_D, h = COLLAR_H + E);
                }
                rrect(-IN_X, IN_Y0, IN_X, IN_Y1, R_IN, FLOOR, Z_SPLIT + 1);
            }
            for (p = PCB_HOLES) translate([p[0], p[1], FLOOR - E]) cylinder(d = SO_D, h = Z_PCB_BOT - FLOOR + E);
            for (p = BOSS_POS)  translate([p[0], p[1], FLOOR - E]) cylinder(d = BOSS_D, h = Z_SPLIT - FLOOR + E);
        }
        // gasket groove in the rim
        difference() {
            rrect(-OUT_X + GROOVE_OFF, OUT_Y0 + GROOVE_OFF, OUT_X - GROOVE_OFF, OUT_Y1 - GROOVE_OFF, R_OUT - GROOVE_OFF, Z_SPLIT - GROOVE_D, Z_SPLIT + 1);
            rrect(-OUT_X + GROOVE_OFF + GROOVE_W, OUT_Y0 + GROOVE_OFF + GROOVE_W, OUT_X - GROOVE_OFF - GROOVE_W, OUT_Y1 - GROOVE_OFF - GROOVE_W, R_OUT - GROOVE_OFF - GROOVE_W, Z_SPLIT - GROOVE_D - 1, Z_SPLIT + 2);
        }
        // insert holes
        for (p = PCB_HOLES) translate([p[0], p[1], Z_PCB_BOT - 5.5]) cylinder(d = INSERT_D, h = 6);
        for (p = BOSS_POS)  translate([p[0], p[1], Z_SPLIT - 6.5]) cylinder(d = INSERT_D, h = 7);
        // tube socket + floor cable slot
        translate([TUBE[0], TUBE[1], -COLLAR_H - 1]) cylinder(d = SOCKET_D, h = COLLAR_H + 1);
        translate([SLOT[0] - SLOT[2] / 2, SLOT[1] - SLOT[3] / 2, -1]) cube([SLOT[2], SLOT[3], FLOOR + 2]);
        // front wall: USB-C, gland
        translate([USB[0] - USB[1] / 2, IN_Y1 - 0.5, USB[3] - USB[2] / 2]) cube([USB[1], WALL + 1, USB[2]]);
        wall_hole_y(GLAND[0], GLAND[1], GLAND[2], IN_Y1 - 0.5, WALL + 1);
        // rear wall: SMA
        wall_hole_y(SMA[0], SMA[1], SMA[2], OUT_Y0 - 0.5, WALL + 1);
        // right wall: SHT40 vent slots
        for (k = [0 : VENT[1] - 1])
            translate([IN_X - 0.5, VENT[0] + (k - (VENT[1] - 1) / 2) * VENT[2] - VENT[3] / 2, VENT[5]]) cube([WALL + 1, VENT[3], VENT[4]]);
        // left wall: QR label recess 0.3
        translate([-OUT_X - E, QR[2] - QR[0] / 2, QR[3] - QR[1] / 2]) cube([0.3 + E, QR[0], QR[1]]);
    }
}

// ---------------- lid ----------------
module lid() {
    difference() {
        hull() {
            rrect(-OUT_X, OUT_Y0, OUT_X, OUT_Y1, R_OUT, Z_SPLIT, Z_TOP - CHAMFER);
            rrect(-OUT_X + CHAMFER, OUT_Y0 + CHAMFER, OUT_X - CHAMFER, OUT_Y1 - CHAMFER, R_OUT - CHAMFER, Z_SPLIT, Z_TOP);
        }
        rrect(-IN_X, IN_Y0, IN_X, IN_Y1, R_IN, Z_SPLIT - 1, Z_ROOF_IN);                      // underside cavity
        // panel recess + wire slot
        translate([PANEL_C[0] - (PANEL_W + 2 * PANEL_CLR) / 2, PANEL_C[1] - (PANEL_H + 2 * PANEL_CLR) / 2, Z_TOP - PANEL_REC])
            linear_extrude(height = PANEL_REC + 1) offset(r = 2) offset(delta = -2) square([PANEL_W + 2 * PANEL_CLR, PANEL_H + 2 * PANEL_CLR]);
        translate([WIRE_SLOT[0] - WIRE_SLOT[2] / 2, WIRE_SLOT[1] - WIRE_SLOT[3] / 2, Z_ROOF_IN - 1]) cube([WIRE_SLOT[2], WIRE_SLOT[3], ROOF_T + 2]);
        // button hole + boot pocket (from below)
        translate([SW1[0], SW1[1], Z_ROOF_IN - 1]) cylinder(d = BTN_HOLE_D, h = ROOF_T + 2);
        translate([SW1[0], SW1[1], Z_ROOF_IN - 1]) cylinder(d = BTN_POCKET_D, h = 1 + FLANGE_T + 0.2);
        // LED window + pipe flange pocket (from below)
        translate([-3.4 - LED_WIN[0] / 2, 22.4 - LED_WIN[1] / 2, Z_ROOF_IN - 1]) cube([LED_WIN[0], LED_WIN[1], ROOF_T + 2]);
        translate([-3.4 - 6.2, 22.4 - 2.4, Z_ROOF_IN - 1]) cube([12.4, 4.8, 2]);
        // screws
        for (p = BOSS_POS) {
            translate([p[0], p[1], Z_ROOF_IN - 1]) cylinder(d = LID_HOLE, h = ROOF_T + 2);
            translate([p[0], p[1], Z_TOP - LID_CB_DEPTH]) cylinder(d = LID_CB_D, h = LID_CB_DEPTH + 1);
        }
    }
}

// ---------------- TPU button boot ----------------
module boot() {
    translate([SW1[0], SW1[1], 0]) {
        translate([0, 0, Z_ROOF_IN]) cylinder(d = BTN_FLANGE_D, h = FLANGE_T);
        translate([0, 0, Z_ROOF_IN]) cylinder(d = BTN_CAP_D, h = Z_TOP + CAP_PROUD - Z_ROOF_IN);
        translate([0, 0, Z_PCB_TOP + SW1_H + 0.3]) cylinder(d = BTN_PIN_D, h = Z_ROOF_IN - (Z_PCB_TOP + SW1_H + 0.3) + E);
    }
}

// ---------------- 3-channel light pipe (print clear; add 0.4 mm black separators) ----------------
module pipe() {
    for (l = LEDS) translate([l[0] - PIPE_CH / 2, l[1] - PIPE_CH / 2, LED_TOP + 0.3]) cube([PIPE_CH, PIPE_CH, Z_TOP - LED_TOP - 0.3]);
    translate([-3.4 - 5.8, 22.4 - 2.1, Z_ROOF_IN - 1]) cube([11.6, 4.2, 1 + E]);
}

// ---------------- assembly / sections ----------------
module assembly() {
    color("#5d6b4a") lower_shell();
    color("#6f7e58") translate([0, 0, explode]) lid();
    color("#222") translate([0, 0, 2 * explode]) boot();
    color("#d9eef8") translate([0, 0, 2 * explode]) pipe();
    color("#2f8f4e") translate([0, 0, 0.5 * explode]) translate([-PCB_W / 2, -PCB_H / 2, Z_PCB_BOT]) cube([PCB_W, PCB_H, PCB_T]);
    color("#1e2f5a") translate([0, 0, 3 * explode]) translate([PANEL_C[0] - PANEL_W / 2, PANEL_C[1] - PANEL_H / 2, Z_TOP - PANEL_REC]) cube([PANEL_W, PANEL_H, PANEL_T]);
}

module frame() mirror([0, 1, 0]) children();

if (part == "shell") frame() lower_shell();
else if (part == "lid") frame() lid();
else if (part == "boot") frame() boot();
else if (part == "pipe") frame() pipe();
else if (part == "section") frame() difference() { assembly(); translate([SW1[0], -200, -100]) cube([300, 400, 400]); }   // cut at the button plane x = -12
else frame() assembly();

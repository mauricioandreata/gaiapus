// Gaiapus head case rev B - parametric OpenSCAD (2026-11-14)
// Same numbers as mechanical/tools/params.py and drawings GAIA-MEC-B01..B03.
// Not compiled on the authoring machine (no OpenSCAD there): press F5, compare with the PDF, then
// set part = "base" / "lid" / "button" and export STL (F6, then F7).
// Frame: origin = PCB centre, x right, y toward the PCB FRONT edge, z up from the floor underside.
// mirror([0,1,0]) at the end turns this KiCad-like frame into OpenSCAD's (front = -y). Geometry is not mirror-imaged.

part = "assembly";   // "base" | "lid" | "button" | "assembly" | "section"
explode = 0;
$fn = 56;
E = 0.01;

// ---- parameters ----
PCB_HOLES = [[-41,-21],[41,-21],[-41,21],[41,21]];
Z_PCB_BOT = 25; Z_PCB_TOP = 26.6;
WALL = 4; FLOOR = 3;
IN_X = 53; IN_Y0 = -43.5; IN_Y1 = 30.5;
OUT_X = IN_X + WALL; OUT_Y0 = IN_Y0 - WALL; OUT_Y1 = IN_Y1 + WALL;   // 114 x 82
R_OUT = 12; R_IN = 8; CY = (OUT_Y0 + OUT_Y1) / 2;                      // -6.5
Z_SPLIT = 33; Z_TOP = 38.5; ROOF_T = 4; Z_ROOF_IN = Z_TOP - ROOF_T; TOP_R = 3;
LIP_T = 1.2; LIP_H = 2; LIP_GAP = 0.3;
GROOVE_W = 2.2; GROOVE_D = 1.5; GROOVE_OFF = (WALL - GROOVE_W) / 2;
SCREWS = [[-49.5,-40],[49.5,-40],[-49.5,26.5],[49.5,26.5]];
COL_D = 7; Z_MEET = 27; COL_HOLE = 3.4; CB_D = 6.5; CB_DEPTH = 3.5; INSERT_D = 4.0; INSERT_L = 6;
SO_D = 6; SO_PILOT = 2.5; SO_PILOT_DEPTH = 8;
PANEL = [68, 37]; PANEL_CLR = 0.4; PANEL_REC = 1.6; PANEL_C = [0, -24.2]; PANEL_WIRE = [31, -9, 4];
SW1 = [-12, 2.6]; SW1_TOP = 29.35;
BTN_CAP_D = 12; BTN_HOLE_D = 12.4; BTN_FLANGE_D = 16; BTN_FLANGE_T = 1; BTN_POCKET_D = 16.4; BTN_PIN_D = 4; BTN_PROUD = 1;
LEDS = [[-7.4,22.4],[-3.4,22.4],[0.6,22.4]]; LED_HOLE_D = 3.1; LED_STRIP = [14, 5, 0.5]; ROD_HOLDER = [14, 5]; ROD_HOLDER_Z = 29.5;
USB = [-17.4, 28.25, 12.5, 7, 2];                 // x, z, w, h, r  (front wall)
VENT = [35, 5, 4, 2, 19, 9];                      // x centre, n, pitch, w, z0, h (front wall)
SMA = [-30, 20, 6.4];                             // y, z, d (right wall)
QR = [26, 26, -6.5, 17, 0.3];                     // w, h, y, z, depth (left wall)
GLAND = [35, -34, 12.5];                          // floor
SLOT = [0, -15, 13, 6];                           // floor obround
COLLAR_D = 44; COLLAR_H = 22; SOCKET_D = 32.4;

// ---- helpers ----
module rr2(x0, y0, x1, y1, r) { hull() for (x = [x0 + r, x1 - r], y = [y0 + r, y1 - r]) translate([x, y]) circle(r = r); }
module rr(x0, y0, x1, y1, r, z0, z1) { translate([0, 0, z0]) linear_extrude(z1 - z0) rr2(x0, y0, x1, y1, r); }
module outer2(o = 0) { rr2(-OUT_X + o, OUT_Y0 + o, OUT_X - o, OUT_Y1 - o, R_OUT - o); }
module inner2(o = 0) { rr2(-IN_X + o, IN_Y0 + o, IN_X - o, IN_Y1 - o, R_IN - o); }
module obround(cx, cy, L, W, z0, z1) { translate([cx, cy, z0]) linear_extrude(z1 - z0) hull() for (s = [-1, 1]) translate([s * (L - W) / 2, 0]) circle(d = W); }

// ---- 1 base ----
module base() {
    difference() {
        union() {
            difference() {
                union() { linear_extrude(Z_SPLIT) outer2(); translate([0, CY, -COLLAR_H]) cylinder(d = COLLAR_D, h = COLLAR_H + E); }
                translate([0, 0, FLOOR]) linear_extrude(Z_SPLIT) inner2();
            }
            intersection() {   // columns, trimmed to the outer skin
                for (p = SCREWS) translate([p[0], p[1], 0]) cylinder(d = COL_D, h = Z_MEET);
                linear_extrude(Z_MEET) outer2();
            }
            for (p = PCB_HOLES) translate([p[0], p[1], FLOOR - E]) cylinder(d = SO_D, h = Z_PCB_BOT - FLOOR + E);
        }
        translate([0, 0, Z_SPLIT - GROOVE_D]) linear_extrude(GROOVE_D + 1) difference() { outer2(GROOVE_OFF); outer2(GROOVE_OFF + GROOVE_W); }
        for (p = SCREWS) translate([p[0], p[1], 0]) { translate([0, 0, -1]) cylinder(d = COL_HOLE, h = Z_MEET + 2); translate([0, 0, -1]) cylinder(d = CB_D, h = CB_DEPTH + 1); }
        for (p = PCB_HOLES) translate([p[0], p[1], Z_PCB_BOT - SO_PILOT_DEPTH]) cylinder(d = SO_PILOT, h = SO_PILOT_DEPTH + 1);
        translate([0, CY, -COLLAR_H - 1]) cylinder(d = SOCKET_D, h = COLLAR_H + 1);
        obround(SLOT[0], SLOT[1], SLOT[2], SLOT[3], -1, FLOOR + 1);
        translate([GLAND[0], GLAND[1], -1]) cylinder(d = GLAND[2], h = FLOOR + 2);
        // front wall
        translate([USB[0], IN_Y1 - 1, USB[1]]) rotate([-90, 0, 0]) linear_extrude(WALL + 2) rr2(-USB[2] / 2, -USB[3] / 2, USB[2] / 2, USB[3] / 2, USB[4]);
        for (i = [0 : VENT[1] - 1]) translate([VENT[0] + (i - (VENT[1] - 1) / 2) * VENT[2], IN_Y1 - 1, 0])
            rotate([-90, 0, 0]) linear_extrude(WALL + 2) rr2(-VENT[3] / 2, -(VENT[4] + VENT[5]), VENT[3] / 2, -VENT[4], VENT[3] / 2 - E);
        // right wall SMA, left wall QR recess
        translate([IN_X - 1, SMA[0], SMA[1]]) rotate([0, 90, 0]) cylinder(d = SMA[2], h = WALL + 2);
        translate([-OUT_X - 1, QR[2] - QR[0] / 2, QR[3] - QR[1] / 2]) cube([1 + QR[4], QR[0], QR[1]]);
    }
}

// ---- 2 lid ----
module lid() {
    difference() {
        union() {
            hull() {   // body with R3 top edge
                translate([0, 0, Z_SPLIT]) linear_extrude(Z_TOP - TOP_R - Z_SPLIT) outer2();
                translate([0, 0, Z_TOP - TOP_R]) minkowski() { linear_extrude(E) outer2(TOP_R); sphere(r = TOP_R, $fn = 24); }
            }
            translate([0, 0, Z_SPLIT - LIP_H]) linear_extrude(LIP_H + E) difference() { inner2(LIP_GAP); inner2(LIP_GAP + LIP_T); }
            intersection() {
                for (p = SCREWS) translate([p[0], p[1], Z_MEET]) cylinder(d = COL_D, h = Z_ROOF_IN - Z_MEET + E);
                translate([0, 0, Z_MEET]) linear_extrude(Z_TOP) inner2(LIP_GAP);
            }
            translate([LEDS[1][0] - ROD_HOLDER[0] / 2, LEDS[1][1] - ROD_HOLDER[1] / 2, ROD_HOLDER_Z]) cube([ROD_HOLDER[0], ROD_HOLDER[1], Z_ROOF_IN - ROD_HOLDER_Z + E]);
        }
        translate([0, 0, Z_SPLIT - 1]) linear_extrude(Z_ROOF_IN - Z_SPLIT + 1) difference() {   // cavity, keeps bosses + rod holder
            inner2(LIP_GAP + LIP_T); for (p = SCREWS) translate(p) circle(d = COL_D);
            translate([LEDS[1][0] - ROD_HOLDER[0] / 2, LEDS[1][1] - ROD_HOLDER[1] / 2]) square(ROD_HOLDER);
        }
        translate([0, 0, Z_TOP - PANEL_REC]) linear_extrude(PANEL_REC + 4)
            rr2(PANEL_C[0] - PANEL[0] / 2 - PANEL_CLR, PANEL_C[1] - PANEL[1] / 2 - PANEL_CLR, PANEL_C[0] + PANEL[0] / 2 + PANEL_CLR, PANEL_C[1] + PANEL[1] / 2 + PANEL_CLR, 2);
        translate([PANEL_WIRE[0], PANEL_WIRE[1], Z_ROOF_IN - 1]) cylinder(d = PANEL_WIRE[2], h = ROOF_T + 2);
        translate([SW1[0], SW1[1], Z_ROOF_IN - 1]) cylinder(d = BTN_HOLE_D, h = ROOF_T + 2);
        translate([SW1[0], SW1[1], Z_ROOF_IN - 1]) cylinder(d = BTN_POCKET_D, h = 1 + BTN_FLANGE_T);
        translate([LEDS[1][0] - LED_STRIP[0] / 2, LEDS[1][1] - LED_STRIP[1] / 2, Z_TOP - LED_STRIP[2]]) cube([LED_STRIP[0], LED_STRIP[1], 2]);
        for (l = LEDS) translate([l[0], l[1], ROD_HOLDER_Z - 1]) cylinder(d = LED_HOLE_D, h = 20, $fn = 24);
        for (p = SCREWS) translate([p[0], p[1], Z_MEET - 1]) { cylinder(d = INSERT_D, h = INSERT_L + 1); cylinder(d = 2.6, h = Z_ROOF_IN - Z_MEET); }
    }
}

// ---- 3 TPU button cap ----
module button() {
    translate([SW1[0], SW1[1], 0]) {
        translate([0, 0, Z_ROOF_IN]) cylinder(d = BTN_FLANGE_D, h = BTN_FLANGE_T);          // flange sits in the 1 mm roof pocket
        translate([0, 0, Z_ROOF_IN + BTN_FLANGE_T - E]) cylinder(d = BTN_CAP_D, h = Z_TOP + BTN_PROUD - Z_ROOF_IN - BTN_FLANGE_T);
        translate([0, 0, SW1_TOP + 0.3]) cylinder(d = BTN_PIN_D, h = Z_ROOF_IN - SW1_TOP - 0.3 + E);
    }
}

module assembly() {
    color("#5d6b4a") base();
    color("#6c7a55") translate([0, 0, explode]) lid();
    color("#222") translate([0, 0, 2 * explode]) button();
    color("#2f8f4e") translate([-45, -25, Z_PCB_BOT]) cube([90, 50, 1.6]);
    color("#1f2f57") translate([0, 0, 3 * explode]) translate([PANEL_C[0] - PANEL[0] / 2, PANEL_C[1] - PANEL[1] / 2, Z_TOP - PANEL_REC]) cube([PANEL[0], PANEL[1], 3.2]);
}

mirror([0, 1, 0]) {
    if (part == "base") base();
    else if (part == "lid") translate([0, 0, Z_TOP]) rotate([180, 0, 0]) lid();   // print top face down
    else if (part == "button") button();
    else if (part == "section") difference() { assembly(); translate([LEDS[1][0], -100, -50]) cube([200, 200, 200]); }
    else assembly();
}

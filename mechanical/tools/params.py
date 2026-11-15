"""Gaiapus head case rev B - every dimension in one place (mm).

Case frame = KiCad frame moved to the PCB centre: x right, y toward the PCB FRONT edge
(USB-C, LEDs, JST connectors), z up from the underside of the base floor.
x_case = x_kicad - 145 ; y_case = y_kicad - 125 .
[PCB]  read from hardware/gaiapus-node (kicad_pcb + .glb export of 2026-11-14 23:15)
[ASM]  assumption, check on the first print
"""
KX, KY = 145.0, 125.0
def k(x, y): return (round(x - KX, 2), round(y - KY, 2))

# ---------------- PCB [PCB] ----------------
PCB_W, PCB_H, PCB_T, PCB_R = 90.0, 50.0, 1.6, 4.0
PCB_HOLES = [(-41, -21), (41, -21), (-41, 21), (41, 21)]      # D3.2
Z_PCB_BOT = 25.0
Z_PCB_TOP = Z_PCB_BOT + PCB_T                                    # 26.6
# heights of the tallest top parts above the PCB top (from the .glb, board bottom = 0)
H_TOP = {"J5 USB-C": 4.90 - 1.6, "J1/J4 JST-SH 2P": 4.60 - 1.6, "SW1 PTS810": 4.35 - 1.6,
         "U5 E22 LoRa": 4.15 - 1.6, "J3 JST-SH 10P": 4.09 - 1.6, "U4 ESP32-S3": 4.06 - 1.6}
USBC   = k(127.6, 144.4);  USB_FACE_Y = 149.49 - KY   # mating face from the footprint (body -2.26..+5.09)
SW1    = k(133.0, 127.6)
LEDS   = [k(137.6, 147.4), k(141.6, 147.4), k(145.6, 147.4)]    # green, yellow, red
J_PROBE, J_SOLAR, J_RAIN = k(114.0, 145.6), k(156.6, 146.2), k(167.6, 146.2)
JST_FACE_Y = {"J3": 148.1 - KY, "J1": 148.7 - KY, "J4": 148.7 - KY}  # plug entry faces (glb)
UFL    = k(168.54, 104.3)
SHT40  = k(180.0, 141.2)
# 18650 holder on B.Cu [PCB] + cell envelope [ASM]
BATT_X = (102.0 - KX, 188.0 - KX)              # -43 .. 43
BATT_Y = (107.65 - KY, 128.35 - KY)            # -17.35 .. 3.35
BATT_CY = 118.0 - KY                           # -7
BATT_MODEL_DROP = 14.91                        # below PCB underside in the 3D model (holder only)
BATT_DROP = 21.0                               # design envelope with an 18.6 mm cell
CELL_D = 18.6
CELL_ZC = Z_PCB_BOT - 1.2 - CELL_D / 2         # cell axis height

# ---------------- body ----------------
WALL, FLOOR = 4.0, 3.0
IN_X, IN_Y0, IN_Y1 = 53.0, -43.5, 30.5         # inner half-width, inner rear, inner front
OUT_X, OUT_Y0, OUT_Y1 = IN_X + WALL, IN_Y0 - WALL, IN_Y1 + WALL     # 57 / -47.5 / 34.5  -> 114 x 82
R_OUT, R_IN = 12.0, 8.0
CY = (OUT_Y0 + OUT_Y1) / 2                     # -6.5  body centre (tube axis)
Z_SPLIT = 33.0                                 # base rim = parting plane
ROOF_T = 4.0
Z_TOP = 38.5
Z_ROOF_IN = Z_TOP - ROOF_T                     # 34.5
TOP_R = 3.0                                    # lid top edge round
LIP_T, LIP_H, LIP_GAP = 1.2, 2.0, 0.3          # lid locating lip inside the base
GROOVE_W, GROOVE_D, CORD_D = 2.2, 1.5, 2.0
GROOVE_OFF = (WALL - GROOVE_W) / 2             # 0.9 from outer face

# fasteners: 4 x M3x30 from below, into heat-set inserts in the lid
SCREW_POS = [(-49.5, -40.0), (49.5, -40.0), (-49.5, 26.5), (49.5, 26.5)]
COL_D = 7.0
Z_MEET = 27.0                                  # base column top = lid boss bottom
COL_HOLE, CB_D, CB_DEPTH = 3.4, 6.5, 3.5
INSERT_D, INSERT_L = 4.0, 6.0
# PCB: 4 standoffs, thread-forming screws (no inserts)
SO_D, SO_PILOT, SO_PILOT_DEPTH = 6.0, 2.5, 8.0

# ---------------- top (lid) ----------------
PANEL_W, PANEL_H, PANEL_T, PANEL_CLR, PANEL_REC = 68.0, 37.0, 3.2, 0.4, 1.6
PANEL_C = (0.0, -24.2)
PANEL_WIRE = (31.0, -9.0, 4.0)                 # x, y, hole d (sealed with silicone)
BTN_CAP_D, BTN_HOLE_D, BTN_FLANGE_D, BTN_FLANGE_T, BTN_PIN_D, BTN_PROUD = 12.0, 12.4, 16.0, 1.0, 4.0, 1.0
BTN_POCKET_D = 16.4
SW1_TOP = Z_PCB_TOP + H_TOP["SW1 PTS810"]      # 29.35
LED_ROD_D, LED_HOLE_D = 3.0, 3.1
LED_STRIP = (14.0, 5.0, 0.5)                   # dark recess around the 3 rods on the top (w, h, depth)
LED_TOP = Z_PCB_TOP + 0.8
ROD_BOT = LED_TOP + 0.5
ROD_HOLDER_Z = 29.5                            # bottom of the rod holder block under the roof
ROD_HOLDER = (14.0, 5.0)

# ---------------- walls ----------------
USB_OPEN = (12.5, 7.0, 2.0)                    # w, h, corner r : lets the cable overmold in
USB_Z = Z_PCB_BOT + 3.25                       # 28.25 receptacle axis
VENT = dict(x0=35.0, n=5, pitch=4.0, w=2.0, z0=19.0, h=9.0)   # front wall, next to the SHT40
SMA = (57.0, -30.0, 20.0, 6.4)                 # x(wall), y, z, hole d  (right wall)
QR = (26.0, 26.0, -6.5, 17.0, 0.3)             # w, h, y, z, recess depth (left wall)

# ---------------- floor / collar / stake ----------------
GLAND = (35.0, -34.0, 12.5, 17.0)              # x, y, hole d (PG7), nut across corners
SLOT = (0.0, -15.0, 13.0, 6.0)                 # obround cable slot cx, cy, length, width (inside the tube bore)
TUBE_OD, TUBE_ID = 32.0, 27.0
COLLAR_D, COLLAR_H, SOCKET_D = 44.0, 22.0, 32.4
TUBE_LEN, TIP_LEN = 470.0, 60.0
PROBE_W, PROBE_L, PROBE_T, PROBE_TOP_Z = 22.0, 450.0, 1.6, -2.0
PROBE_MAX_H = 4.09 - 1.6                       # tallest probe part above its PCB (J1)
SOIL_Z = -COLLAR_H                             # soil line = collar bottom
ELEC_DEPTHS, ELEC_H = (150.0, 400.0), 40.0

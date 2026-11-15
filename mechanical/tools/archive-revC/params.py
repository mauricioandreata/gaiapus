"""Gaiapus head case rev C - shaped after renders/design-base-v1.jpg. All dimensions in mm.

Case frame: origin = PCB centre (KiCad 145,125), x right, y toward the PCB FRONT edge, z up from the
bottom face of the head (the neck/collar hangs below z = 0).
"""
import math
KX, KY = 145.0, 125.0
def k(x, y): return (round(x - KX, 2), round(y - KY, 2))
t = lambda deg: math.tan(math.radians(deg))

# ---------------- PCB (unchanged boards) ----------------
PCB_W, PCB_H, PCB_T, PCB_R = 90.0, 50.0, 1.6, 4.0
PCB_HOLES = [(-41, -21), (41, -21), (-41, 21), (41, 21)]
Z_PCB_BOT = 42.0                       # PCB raised: frees the bottom for the tapered "chin"
Z_PCB_TOP = Z_PCB_BOT + PCB_T
H_TOP = {"J5 USB-C": 3.3, "J1/J4 JST-SH 2P": 3.0, "SW1 PTS810": 2.75, "U5 E22 LoRa": 2.55, "J3 JST-SH 10P": 2.49, "U4 ESP32-S3": 2.46}
USBC = k(127.6, 144.4); USB_FACE_Y = 149.49 - KY
SW1 = k(133.0, 127.6)
LEDS = [k(137.6, 147.4), k(141.6, 147.4), k(145.6, 147.4)]
J_PROBE, J_SOLAR, J_RAIN = k(114.0, 145.6), k(156.6, 146.2), k(167.6, 146.2)
JST_FACE_Y = {"J3": 148.1 - KY, "J1": 148.7 - KY, "J4": 148.7 - KY}
UFL, SHT40 = k(168.54, 104.3), k(180.0, 141.2)
BATT_X = (102.0 - KX, 188.0 - KX); BATT_Y = (107.65 - KY, 128.35 - KY); BATT_CY = 118.0 - KY
BATT_DROP, CELL_D = 21.0, 18.6
CELL_ZC = Z_PCB_BOT - 1.2 - CELL_D / 2
SW1_TOP = Z_PCB_TOP + H_TOP["SW1 PTS810"]
LED_TOP = Z_PCB_TOP + 1.15                     # LED 3D model top (measured in the .glb)

# ---------------- head: lower body ----------------
WALL = 4.0
IN_X, IN_Y0, IN_Y1 = 53.0, -49.5, 30.5
OUT_X, OUT_Y0, OUT_Y1 = IN_X + WALL, IN_Y0 - WALL, IN_Y1 + WALL     # 114 x 88
R_OUT, R_IN = 14.0, 10.0
CY = (OUT_Y0 + OUT_Y1) / 2                       # -9.5 : tube axis
CHIN = 20.0                                      # 45 deg tapered bottom ("chin"), 20 high / 20 in
CHIN_R = 4.0                                     # blend radius of the chin edges
SHELL = 3.5                                      # wall of the chin
Z_SPLIT = 54.0                                   # seam (gasket)
GROOVE_W, GROOVE_D, CORD_D = 2.2, 1.5, 2.0
GROOVE_OFF = (WALL - GROOVE_W) / 2
SEAM_V = 0.7                                     # small V at the seam, makes the line visible like the render

# ---------------- head: cap (lid) ----------------
CAP_DRAFT = 8.0                                  # sides and front lean in going up
CAP_DRAFT_REAR = 3.0                             # rear face almost vertical: keeps the top long enough for the panel
TOP_SLOPE = 6.0                                  # top falls toward the front
Z_TOP_REAR = 98.0                                # top at the rear outer edge
def z_top(y): return Z_TOP_REAR - (y - OUT_Y0) * t(TOP_SLOPE)
BEVEL_Z = 80.0                                   # front bevel starts on the front face at this height (45 deg)
TOP_BLEND, BEVEL_BLEND = 6.0, 10.0
CAP_WALL, ROOF_T = 3.5, 3.5
LIP_T, LIP_H, LIP_GAP = 1.2, 2.0, 0.3

# ---------------- fixing: 4 screws from below (hidden in the chin) ----------------
SCREW_POS = [(-49.5, -46.0), (49.5, -46.0), (-49.5, 26.5), (49.5, 26.5)]
COL_D, COL_HOLE, CB_D = 7.0, 3.4, 6.5
CB_SEAT = 17.5                                   # counterbore seat height (screw head)
Z_MEET = 24.0                                    # base column top = lid boss bottom
INSERT_D, INSERT_L = 4.0, 7.0
SCREW = "M3 x 12"
SO_D, SO_PILOT, SO_PILOT_DEPTH = 6.0, 2.5, 8.0

# ---------------- top features ----------------
PANEL_W, PANEL_H, PANEL_T, PANEL_CLR, PANEL_REC = 68.0, 37.0, 3.2, 0.4, 1.6
PANEL_C = (0.0, -25.5)
PANEL_WIRE = (31.0, -11.0, 4.0)
BTN_CAP_D, BTN_HOLE_D, BTN_FLANGE_D, BTN_FLANGE_T, BTN_POCKET_D, BTN_PROUD = 16.0, 16.4, 20.0, 1.0, 20.4, 1.5
PLUNGER_D, SLEEVE_ID, SLEEVE_OD, SLEEVE_L = 5.8, 6.4, 9.6, 30.0

# ---------------- front: LED light bar on the cap face ----------------
LED_BAR = dict(x0=-13.4, x1=6.6, z0=70.0, z1=77.0, y_in=20.4, post=3.2, sep=0.6)

# ---------------- base openings / decoration ----------------
USB_OPEN = (12.5, 7.0, 2.0); USB_Z = Z_PCB_BOT + 3.25
VENT = dict(xc=23.0, n=5, pitch=3.6, w=1.8, z0=32.0, h=11.0, pocket=(22.0, 15.0, 1.5, 3.0))   # pocket w, h, depth, r
DROP = dict(xc=38.5, zc=35.0, r=3.6, tip=46.0, proud=2.0)
SMA = (57.0, -36.0, 48.0, 6.4)                   # right wall, near the rear, just under the seam
QR = (26.0, 26.0, 6.0, 37.0, 0.3)                # right wall: w, h, y, z, recess
GLAND = (26.0, -24.0, 8.2, 12.7)                 # M8 cable gland in the bottom face (hole, nut across corners)
SLOT = (0.0, -15.0, 13.0, 6.0)

# ---------------- neck, collar, stake ----------------
NECK_D, NECK_BORE = 40.0, 28.0
COLLAR_D, COLLAR_Z0, COLLAR_Z1, COLLAR_CH = 46.0, -32.0, -20.0, 1.5     # long neck (0..-20) then the collar ring
SOCKET_D, SOCKET_DEPTH = 32.4, 22.0
TUBE_OD, TUBE_ID, TUBE_LEN, TIP_LEN = 32.0, 27.0, 470.0, 60.0
PROBE_W, PROBE_L, PROBE_T = 22.0, 450.0, 1.6
PROBE_TOP_Z = None   # set below: 20 mm above the soil line (D18)
PROBE_MAX_H = 2.49
SOIL_Z = COLLAR_Z0
PROBE_TOP_Z = SOIL_Z + 20.0
ELEC_DEPTHS, ELEC_H = (150.0, 400.0), 40.0

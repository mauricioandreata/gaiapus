#!/usr/bin/env python3
"""Generate the Gaiapus node schematic (KiCad 8) from a Python netlist description.

Run:  python3 hardware/tools/gen_kicad.py
Writes: hardware/lib/symbols/gaiapus.kicad_sym
        hardware/gaiapus-node/gaiapus-node.kicad_sch (+ 5 sub-sheets)
        hardware/gaiapus-node/netlist-draft.csv, bom/bom_from_schematic.csv
Same inputs -> byte-identical outputs (UUIDs are derived, not random).
Pin numbers/names come from the vendor datasheets listed in docs/component-selection.md.
"""
import os, csv, uuid, collections
from kicad_lib import *

HERE = os.path.dirname(os.path.abspath(__file__))
import json as _json
_LF = os.path.normpath(os.path.join(HERE, "..", "lib", "lcsc_footprints.json"))
LCSC_FP = _json.load(open(_LF)) if os.path.exists(_LF) else {}   # filled by apply_lcsc.py after import_lcsc.cmd
HW = os.path.normpath(os.path.join(HERE, ".."))
PRJ = os.path.join(HW, "gaiapus-node")
LIBF = os.path.join(HW, "lib", "symbols", "gaiapus.kicad_sym")
BOMF = os.path.normpath(os.path.join(HW, "..", "bom", "bom_from_schematic.csv"))
PROJECT = "gaiapus-node"
NS = uuid.UUID("0b0d8c3e-6c1f-4f3a-9d2e-5a1f7c9b2e11")
def uid(*p): return str(uuid.uuid5(NS, "|".join(str(x) for x in p)))
ROOT = uid("root")

# ======================================================================
# SYMBOLS
# ======================================================================
S = {}
def add(s): S[s.name] = s; return s

R_FP, C_FP, C8_FP = "Resistor_SMD:R_0603_1608Metric", "Capacitor_SMD:C_0603_1608Metric", "Capacitor_SMD:C_0805_2012Metric"
add(two_pin("R", "R", rect(-1.016, -2.54, 1.016, 2.54, "none"), fp=R_FP, desc="Resistor"))
add(two_pin("C", "C", poly([(0, 2.54), (0, 0.762)]) + poly([(-1.905, 0.762), (1.905, 0.762)]) +
            poly([(-1.905, -0.762), (1.905, -0.762)]) + poly([(0, -0.762), (0, -2.54)]), fp=C_FP, desc="Capacitor"))
add(two_pin("L", "L", rect(-1.016, -2.54, 1.016, 2.54, "outline"), fp="Inductor_SMD:L_Taiyo-Yuden_NR-40xx", desc="Inductor"))
add(two_pin("NTC", "RT", rect(-1.016, -2.54, 1.016, 2.54, "none") + poly([(-2.032, -2.032), (2.032, 2.032)]), fp=R_FP, desc="NTC thermistor"))
add(two_pin("D_Schottky", "D", poly([(0, 2.54), (0, 1.27)]) + poly([(-1.27, 1.27), (1.27, 1.27)]) +
            poly([(-1.27, -1.27), (1.27, -1.27), (0, 1.27), (-1.27, -1.27)], "outline") + poly([(0, -1.27), (0, -2.54)]),
            top=("1", "K", "passive"), bottom=("2", "A", "passive"), fp="Diode_SMD:D_SOD-123", desc="Schottky diode (K up)"))
add(two_pin("D_Zener", "D", poly([(0, 2.54), (0, 1.27)]) + poly([(-1.905, 0.635), (-1.27, 1.27), (1.27, 1.27), (1.905, 1.905)]) +
            poly([(-1.27, -1.27), (1.27, -1.27), (0, 1.27), (-1.27, -1.27)], "outline") + poly([(0, -1.27), (0, -2.54)]),
            top=("1", "K", "passive"), bottom=("2", "A", "passive"), fp="Diode_SMD:D_SOD-123", desc="Zener diode (K up)"))
add(two_pin("LED", "D", poly([(0, 2.54), (0, 1.27)]) + poly([(-1.27, -1.27), (1.27, -1.27)]) +
            poly([(-1.27, 1.27), (1.27, 1.27), (0, -1.27), (-1.27, 1.27)], "outline") + poly([(0, -1.27), (0, -2.54)]) +
            poly([(1.905, 0.635), (3.175, 1.905)]) + poly([(1.905, -0.635), (3.175, 0.635)]),
            top=("2", "A", "passive"), bottom=("1", "K", "passive"), fp="LED_SMD:LED_0603_1608Metric", desc="LED (anode up)"))
add(two_pin("SW_Push", "SW", poly([(0, 2.54), (0, 1.27)]) + poly([(-1.27, 0.635), (1.27, 0.635)]) +
            poly([(0, -2.54), (0, -0.635)]), fp="Button_Switch_SMD:SW_SPST_PTS810", desc="Tactile switch"))
add(Sym("TestPoint", "TP", [Pin("1", "TP", "passive", 0, 0, 270, 1.27)], circle(0, -1.905, 0.635),
        fp="TestPoint:TestPoint_Pad_D1.5mm", desc="Test pad", hide_names=True, hide_nums=True, w=2.54, h=5, name_offset=0))

add(box("JST_SH_2P", "J", right=[("1", "1", "passive"), ("2", "2", "passive")],
        fp="Connector_JST:JST_SH_SM02B-SRSS-TB_1x02-1MP_P1.00mm_Horizontal", desc="JST-SH 1.0 mm 2-pin SMD"))
add(box("JST_SH_10P", "J", right=[(str(i), str(i), "passive") for i in range(1, 11)],
        fp="Connector_JST:JST_SH_SM10B-SRSS-TB_1x10-1MP_P1.00mm_Horizontal", desc="JST-SH 1.0 mm 10-pin SMD side entry (head <-> probe)"))
add(box("Battery_18650", "BT", right=[("1", "+", "power_out"), ("2", "-", "power_out")],
        fp="Battery:BatteryHolder_Keystone_1042_1x18650", desc="18650 holder (SMD)"))
add(box("U.FL", "J", left=[("1", "SIG", "passive")], bottom=[("2", "GND", "passive"), ("3", "GND", "passive")],
        fp="Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical", desc="U.FL coaxial RF connector"))
add(box("Electrode_IDC", "E", left=[("1", "A", "passive")], bottom=[("2", "B", "passive")],
        fp="gaiapus:ELECTRODE_IDC", desc="Interdigitated PCB electrode (copper, no component)", minw=12.7))
S["Electrode_IDC"].in_bom = False
S["Electrode_IDC"].on_board = True      # copper on the PCB, but nothing to buy

add(box("ESP32-S3-MINI-1", "U",
        left=[("45", "EN", "input"), ("4", "IO0", "bidirectional"), ("5", "IO1", "bidirectional"), ("6", "IO2", "bidirectional"),
              ("7", "IO3", "bidirectional"), ("8", "IO4", "bidirectional"), ("9", "IO5", "bidirectional"), ("10", "IO6", "bidirectional"),
              ("11", "IO7", "bidirectional"), ("12", "IO8", "bidirectional"), ("13", "IO9", "bidirectional"), ("14", "IO10", "bidirectional"),
              ("15", "IO11", "bidirectional"), ("16", "IO12", "bidirectional"), ("17", "IO13", "bidirectional"), ("18", "IO14", "bidirectional"),
              ("19", "IO15", "bidirectional"), ("20", "IO16", "bidirectional"), ("21", "IO17", "bidirectional"), ("22", "IO18", "bidirectional")],
        right=[("23", "IO19", "bidirectional"), ("24", "IO20", "bidirectional"), ("25", "IO21", "bidirectional"), ("26", "IO26", "bidirectional"),
               ("27", "IO47", "bidirectional"), ("28", "IO33", "bidirectional"), ("29", "IO34", "bidirectional"), ("30", "IO48", "bidirectional"),
               ("31", "IO35", "bidirectional"), ("32", "IO36", "bidirectional"), ("33", "IO37", "bidirectional"), ("34", "IO38", "bidirectional"),
               ("35", "IO39", "bidirectional"), ("36", "IO40", "bidirectional"), ("37", "IO41", "bidirectional"), ("38", "IO42", "bidirectional"),
               ("39", "TXD0", "bidirectional"), ("40", "RXD0", "bidirectional"), ("41", "IO45", "bidirectional"), ("44", "IO46", "bidirectional")],
        top=[("3", "3V3", "power_in")],
        hidden=[(str(i), "GND", "power_in") for i in [1, 2, 42, 43] + list(range(46, 61))] + [("GND", "GND", "power_in")],
        fp="RF_Module:ESP32-S3-MINI-1",
        ds="https://documentation.espressif.com/esp32-s3-mini-1_mini-1u_datasheet_en.pdf", desc="ESP32-S3 Wi-Fi/BLE module, 8 MB flash"))

add(box("E22-900MM22S", "U",
        left=[("1", "VCC", "power_in"), ("3", "NRST", "input"), ("9", "TXEN", "input"), ("10", "RXEN", "input"),
              ("11", "BUSY", "output"), ("20", "DIO1", "bidirectional"), ("19", "DIO2", "bidirectional"), ("18", "DIO3", "bidirectional")],
        right=[("15", "SCK", "input"), ("12", "MISO", "output"), ("13", "MOSI", "input"), ("14", "NSS", "input"), ("6", "ANT", "passive")],
        bottom=[("2", "GND", "power_in"), ("7", "GND", "power_in"), ("16", "GND", "power_in"),
                ("4", "NC", "no_connect"), ("5", "NC", "no_connect"), ("8", "NC", "no_connect"), ("17", "NC", "no_connect")],
        fp="gaiapus:E22-900MM22S", ds="https://atta.szlcsc.com/upload/public/pdf/source/20221219/F545ECE9DA7873B26F3F8C9597BD3A16.pdf",
        desc="EBYTE SX1262 LoRa module 868/915 MHz, 10x10 mm, ANT = stamp pad"))

add(box("CN3058E", "U",
        left=[("4", "VIN", "power_in"), ("1", "TEMP", "input"), ("2", "ISET", "passive")],
        right=[("5", "BAT", "bidirectional"), ("8", "FB", "input"), ("7", "CHRG", "open_collector"), ("6", "DONE", "open_collector")],
        bottom=[("3", "GND", "power_in"), ("9", "EP", "passive")],
        fp="Package_SO:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.3mm", ds="https://datasheet.lcsc.com/lcsc/1809192034_ShangHai-Consonance-Elec-CN3058E_C112011.pdf",
        desc="1 A linear charger for 1-cell LiFePO4, 3.8-6 V in"))

add(box("HY2112-BB", "U",
        left=[("5", "VDD", "power_in"), ("6", "VSS", "power_in")],
        right=[("1", "OD", "output"), ("2", "CS", "input"), ("3", "OC", "output")],
        bottom=[("4", "NC", "no_connect")],
        fp="Package_TO_SOT_SMD:SOT-23-6", ds="https://elektrotanya.com/sites/default/files/comment/2020/06/hy2112_hycon.pdf",
        desc="1-cell LiFePO4 protection (OV 3.75 V, UV 2.1 V)"))

add(box("FS8205A", "Q",
        left=[("4", "G1", "input"), ("5", "G2", "input")],
        right=[("2", "S1", "passive"), ("3", "S1", "passive"), ("6", "S2", "passive"), ("7", "S2", "passive")],
        top=[("1", "D", "passive"), ("8", "D", "passive")],
        fp="Package_SO:TSSOP-8_4.4x3mm_P0.65mm", ds="https://atta.szlcsc.com/upload/public/pdf/source/20140228/1457706997167.pdf",
        desc="Dual N-MOSFET common drain, TSSOP-8 (pin 1,8 = D; 2,3 = S1; 4 = G1; 5 = G2; 6,7 = S2)"))

add(box("TPS63802", "U",
        left=[("10", "VIN", "power_in"), ("1", "EN", "input"), ("2", "MODE", "input"), ("3", "AGND", "power_in"), ("4", "FB", "input")],
        right=[("6", "VOUT", "power_out"), ("5", "PG", "open_collector"), ("9", "L1", "passive"), ("7", "L2", "passive")],
        bottom=[("8", "GND", "power_in")],
        fp="gaiapus:TPS63802_VSON-10", ds="https://ti.com/lit/pdf/SLVSEU9", desc="2 A buck-boost, 11 uA Iq, adjustable"))

add(box("SHT40", "U",
        left=[("1", "SDA", "bidirectional"), ("2", "SCL", "input")], top=[("3", "VDD", "power_in")], bottom=[("4", "GND", "power_in")],
        fp="gaiapus:SHT4x_DFN-4", ds="https://sensirion.com/resource/datasheet/sht4x", desc="Sensirion SHT40 RH/T, I2C 0x44"))

add(box("74LVC1G14", "U",
        left=[("2", "A", "input"), ("1", "NC", "no_connect")], right=[("4", "Y", "output")],
        top=[("5", "VCC", "power_in")], bottom=[("3", "GND", "power_in")],
        fp="Package_TO_SOT_SMD:SOT-23-5", ds="https://www.lcsc.com/product-detail/C131093.html", desc="Schmitt-trigger inverter (SOT-753)"))

add(box("USBLC6-2SC6", "U",
        left=[("1", "IO1", "passive"), ("3", "IO2", "passive")], right=[("6", "IO1", "passive"), ("4", "IO2", "passive")],
        top=[("5", "VBUS", "passive")], bottom=[("2", "GND", "power_in")],
        fp="Package_TO_SOT_SMD:SOT-23-6", ds="https://www.lcsc.com/product-detail/C7519.html", desc="USB ESD protection"))

add(box("USB_C_Receptacle", "J",
        right=[("A4B9", "VBUS", "passive"), ("B4A9", "VBUS", "passive"),
               ("A6", "D+", "passive"), ("B6", "D+", "passive"), ("A7", "D-", "passive"), ("B7", "D-", "passive"),
               ("A5", "CC1", "passive"), ("B5", "CC2", "passive"), ("A8", "SBU1", "passive"), ("B8", "SBU2", "passive"),
               ("A1B12", "GND", "passive"), ("B1A12", "GND", "passive"),
               ("1", "SHIELD", "passive"), ("2", "SHIELD", "passive"), ("3", "SHIELD", "passive"), ("4", "SHIELD", "passive")],
        fp="Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12", ds="https://www.lcsc.com/product-detail/C165948.html",
        desc="USB-C 16-pin receptacle (USB 2.0 use); pad names as in the LCSC footprint"))

POWER_NETS = ["GND", "+3V3", "VBAT", "VSOL", "VBUS"]
for p in POWER_NETS:
    add(power_sym(p, up=(p != "GND")))
add(pwr_flag())

# ======================================================================
# DESIGN / SHEET MODEL
# ======================================================================
class Design:
    def __init__(self):
        self.cnt = collections.Counter()
        self.netpins = collections.defaultdict(list)   # net -> [(sheet, ref, pin, pinname)]
        self.parts = []                                # for BOM
        self.sheets = []
    def ref(self, prefix):
        self.cnt[prefix] += 1
        if prefix.startswith("#"):
            return f"{prefix}{self.cnt[prefix]:02d}"
        return f"{prefix}{self.cnt[prefix]}"
D = Design()
DIRS = {"L": (-1, 0), "R": (1, 0), "T": (0, -1), "B": (0, 1)}
LANG = {"L": 180, "R": 0, "T": 90, "B": 270}
SIDE_OF = {0: "L", 180: "R", 270: "T", 90: "B"}
NC = "NC"

def prop(k, v, x, y, hide=False, just=None):
    j = f" (justify {just})" if just else ""
    return f"(property {q(k)} {q(v)} (at {n(x)} {n(y)} 0) (effects {FONT}{j}{' hide' if hide else ''}))"

class Sheet:
    def __init__(self, key, fname, title, page, d=None, project=PROJECT, root=None, top=False, board="Gaiapus node"):
        self.key, self.fname, self.title, self.page = key, fname, title, page
        self.d, self.project, self.top, self.board = d or D, project, top, board
        self.root = root or ROOT
        self.uuid = uid("sheet", key)
        self.items, self.labels, self.used = [], [], {}
        self.k = 0
    def _id(self, *p):
        self.k += 1
        return q(uid(self.key, self.k, *p))
    def wire(self, a, b):
        self.items.append(f"(wire (pts (xy {n(a[0])} {n(a[1])}) (xy {n(b[0])} {n(b[1])})) "
                          f"(stroke (width 0) (type default)) (uuid {self._id('w')}))")
    def junction(self, a):
        self.items.append(f"(junction (at {n(a[0])} {n(a[1])}) (diameter 0) (color 0 0 0 0) (uuid {self._id('j')}))")
    def nc(self, a):
        self.items.append(f"(no_connect (at {n(a[0])} {n(a[1])}) (uuid {self._id('nc')}))")
    def text(self, gx, gy, s, size=2.0, bold=True):
        self.items.append(f"(text {q(s)} (exclude_from_sim no) (at {n(gx*U)} {n(gy*U)} 0) "
                          f"(effects (font (size {size} {size}){' bold' if bold else ''}) (justify left bottom)) (uuid {self._id('t')}))")
    def _inst(self, ref, unit=1):
        path = '/' + self.root if self.top else '/' + self.root + '/' + self.uuid
        return (f"(instances (project {q(self.project)} (path {q(path)} "
                f"(reference {q(ref)}) (unit {unit}))))")
    def _sym(self, sym, x, y, rot, ref, value, extra, dnp=False, hide_ref=False, hide_val=False, ref_xy=None, val_xy=None):
        self.used[sym.name] = sym
        bom = sym.in_bom
        if ref_xy is None:
            if sym.hide_names and sym.w:
                ref_xy, val_xy = (x + 2.54, y - 1.27), (x + 2.54, y + 1.27)
            else:
                ref_xy, val_xy = (x - sym.w / 2, y - sym.h / 2 - 1.27), (x - sym.w / 2, y + sym.h / 2 + 1.27)
        L = [f"(symbol (lib_id {q('gaiapus:' + sym.name)}) (at {n(x)} {n(y)} {rot}) (unit 1)",
             f"(exclude_from_sim no) (in_bom {yn(bom)}) (on_board {yn(getattr(sym, 'on_board', bom))}) (dnp {yn(dnp)})",
             f"(uuid {self._id('s', ref)})",
             prop("Reference", ref, ref_xy[0], ref_xy[1], hide_ref, "left"),
             prop("Value", value, val_xy[0], val_xy[1], hide_val, "left"),
             prop("Footprint", extra.get("fp", sym.fp), x, y, True),
             prop("Datasheet", extra.get("ds", sym.ds), x, y, True)]
        for k in ("MPN", "Manufacturer", "LCSC", "Note"):
            if extra.get(k):
                L.append(prop(k, extra[k], x, y, True))
        for p in sym.pins:
            L.append(f"(pin {q(p.num)} (uuid {self._id('p', ref, p.num)}))")
        L.append(self._inst(ref))
        L.append(")")
        self.items.append("\n  ".join(L))

    def power(self, net, pt, side, tag=""):
        sym = S[net]
        ref = self.d.ref("#PWR")
        if net == "GND":
            rot = 180 if side == "T" else 0
            vxy = (pt[0], pt[1] + (3.2 if rot == 0 else -3.2))
        else:
            rot = 180 if side == "B" else 0
            vxy = (pt[0], pt[1] + (3.2 if rot == 180 else -3.2))
        self._sym(sym, pt[0], pt[1], rot, ref, net, {}, hide_ref=True, ref_xy=pt, val_xy=vxy)

    def flag(self, net, gx, gy):
        """PWR_FLAG + a power symbol of `net` below it."""
        x, y = gx * U, gy * U
        ref = self.d.ref("#FLG")
        self._sym(S["PWR_FLAG"], x, y, 0, ref, "PWR_FLAG", {}, hide_ref=True, ref_xy=(x, y), val_xy=(x + 2.54, y - 2.54))
        end = (x, y + U)
        self.wire((x, y), end)
        self.power(net, end, "B" if net != "GND" else "L")
        self.d.netpins[net].append((self.key, ref, "1", "pwr"))

    def flag_label(self, net, gx, gy):
        """PWR_FLAG on a non-power net that is fed through a resistor or a GPIO (silences ERC on purpose)."""
        x, y = gx * U, gy * U
        ref = self.d.ref("#FLG")
        self._sym(S["PWR_FLAG"], x, y, 0, ref, "PWR_FLAG", {}, hide_ref=True, ref_xy=(x, y), val_xy=(x + 2.54, y - 2.54))
        end = (x, y + U)
        self.wire((x, y), end)
        self.labels.append((net, end[0], end[1], 270))
        self.d.netpins[net].append((self.key, ref, "1", "pwr"))

    def place(self, sym, gx, gy, value, nets, mfr="", mpn="", lcsc="TBD", dnp=False, fp=None, note=""):
        x, y = gx * U, gy * U
        ref = self.d.ref(sym.ref)
        sides = {"L": [], "R": [], "T": [], "B": []}
        for p in sym.pins:
            if p.hide:
                self.d.netpins[p.name].append((self.key, ref, p.num, p.name))
                continue
            net = nets.get(p.num)
            if net is None:
                if p.etype == "no_connect":
                    continue
                raise SystemExit(f"[{self.key}] {ref} {sym.name}: pin {p.num} ({p.name}) has no net")
            sides[SIDE_OF[int(p.ang)]].append((p, net))
        used = set(nets) - {p.num for p in sym.pins}
        if used:
            raise SystemExit(f"[{self.key}] {ref} {sym.name}: nets given for unknown pins {sorted(used)}")
        for side, lst in sides.items():
            lst.sort(key=(lambda t: -t[0].y) if side in "LR" else (lambda t: t[0].x))
            i = 0
            while i < len(lst):
                p, net = lst[i]
                pt = (x + p.x, y - p.y)
                if net == NC:
                    self.nc(pt); self.d.netpins["NC:%s.%s" % (ref, p.num)].append((self.key, ref, p.num, p.name)); i += 1; continue
                j = i
                while (j + 1 < len(lst) and lst[j + 1][1] == net and
                       abs(abs((lst[j + 1][0].y - lst[j][0].y) if side in "LR" else (lst[j + 1][0].x - lst[j][0].x)) - U) < 1e-6):
                    j += 1
                dx, dy = DIRS[side]
                ends = []
                for m in range(i, j + 1):
                    pm = lst[m][0]
                    a = (x + pm.x, y - pm.y)
                    e = (a[0] + dx * U, a[1] + dy * U)
                    self.wire(a, e)
                    ends.append(e)
                    self.d.netpins[net].append((self.key, ref, pm.num, pm.name))
                if len(ends) > 1:
                    self.wire(ends[0], ends[-1])
                    for e in ends[1:-1]:
                        self.junction(e)
                if net in POWER_NETS:
                    at_first = net != "GND"
                    self.power(net, ends[0] if at_first else ends[-1], side)
                else:
                    self.labels.append((net, ends[0][0], ends[0][1], LANG[side]))
                i = j + 1
        if lcsc in LCSC_FP:
            fp = "lcsc:" + LCSC_FP[lcsc]
        extra = {"fp": fp or sym.fp, "MPN": mpn, "Manufacturer": mfr, "LCSC": lcsc, "Note": note}
        self._sym(sym, x, y, 0, ref, value, extra, dnp=dnp)
        if sym.in_bom:
            self.d.parts.append((ref, value, fp or sym.fp, mfr, mpn, lcsc, dnp, note, self.key))
        return ref

    # ---- serialization ----
    def label_items(self, global_nets):
        out = []
        for (net, x, y, ang) in self.labels:
            just = "left bottom" if ang in (0, 90) else "right bottom"
            eff = f"(effects {FONT} (justify {just}))"
            if net in global_nets:
                out.append(f"(global_label {q(net)} (shape bidirectional) (at {n(x)} {n(y)} {ang}) {eff} (uuid {self._id('gl', net)})\n"
                           f"  (property \"Intersheetrefs\" \"${{INTERSHEET_REFS}}\" (at {n(x)} {n(y)} 0) (effects {FONT} (justify left) hide)))")
            else:
                out.append(f"(label {q(net)} (at {n(x)} {n(y)} {ang}) {eff} (uuid {self._id('l', net)}))")
        return out

    def render(self, global_nets):
        libs = "\n  ".join(lib_sexp(s, embed=True) for s in self.used.values())
        body = "\n ".join(self.items + self.label_items(global_nets))
        return (f"(kicad_sch\n (version 20231120)\n (generator \"gaiapus_gen\")\n (generator_version \"1.0\")\n"
                f" (uuid {q(self.root if self.top else uid('file', self.key))})\n (paper \"A2\")\n"
                f" (title_block (title {q(self.board + ' · ' + self.title)}) (date \"2026-11-14\") (rev \"A\")"
                f" (company \"Team Gaiapus · NASA Space Apps 2026\")"
                f" (comment 1 \"Generated by hardware/tools/gen_kicad.py - edit the script or edit here and stop regenerating\"))\n"
                f" (lib_symbols\n  {libs}\n )\n {body}\n"
                + (f" (sheet_instances (path \"/\" (page \"1\")))\n" if self.top else "") + ")\n")

MFR = dict(esp="Espressif", ebyte="EBYTE", cn="Consonance", hy="HYCON", ti="Texas Instruments", sens="Sensirion",
           nx="Nexperia", st="STMicroelectronics", hro="HRO", jst="JST", mur="Murata", hir="Hirose", my="MYOUNG")

# ----------------------------------------------------------------------
# helpers for repeated passives
# ----------------------------------------------------------------------
def R(sh, gx, gy, val, top, bot, **kw): return sh.place(S["R"], gx, gy, val, {"1": top, "2": bot}, **kw)
def C(sh, gx, gy, val, top, bot, fp=None, **kw): return sh.place(S["C"], gx, gy, val, {"1": top, "2": bot}, fp=fp, **kw)

# ======================================================================
# SHEET 1: POWER
# ======================================================================
pw = Sheet("power", "power.kicad_sch", "Power: solar charger, LiFePO4 protection, 3.3 V buck-boost", 2)
pw.text(4, 5, "POWER - solar -> CN3058E -> 18650 LiFePO4 (+HY2112 protection) -> TPS63802 -> +3V3")
pw.text(4, 9, "Solar input / charger", 1.5)
pw.place(S["JST_SH_2P"], 10, 16, "SOLAR 5V 60mA", {"1": "VSOL", "2": "GND"}, mfr=MFR["jst"], mpn="SM02B-SRSS-TB",
         note="68x37 mm epoxy panel, Voc<=6.3 V")
pw.place(S["D_Zener"], 24, 16, "BZT52C6V2", {"1": "VSOL", "2": "GND"}, mpn="BZT52C6V2",
         note="clamp below CN3058E abs max 6.5 V; near Voc the panel gives little current -> low dissipation")
C(pw, 31, 16, "10uF", "VSOL", "GND", fp=C8_FP)
pw.place(S["D_Schottky"], 39, 16, "B5819W", {"1": "VSOL", "2": "VBUS"}, note="USB-C -> VSOL OR-ing (programming/charging)")
pw.place(S["CN3058E"], 76, 22, "CN3058E", {"4": "VSOL", "1": "GND", "2": "CN_ISET", "5": "VBAT", "8": "VBAT",
         "7": "CHG_ACTIVE_N", "6": "CHG_DONE_N", "3": "GND", "9": "GND"}, mfr=MFR["cn"], mpn="CN3058E", lcsc="C112011")
R(pw, 64, 34, "24k 1%", "CN_ISET", "GND", note="Ichg = 1218/R = 51 mA (below panel Imp ~60-69 mA, avoids VIN collapse); TEMP grounded = NTC function off")
C(pw, 104, 16, "10uF", "VBAT", "GND", fp=C8_FP)
pw.flag("VSOL", 46, 6)
pw.flag("GND", 52, 6)

pw.text(4, 45, "Battery + protection (HY2112-BB with FS8205A)", 1.5)
pw.place(S["Battery_18650"], 10, 54, "18650 LiFePO4", {"1": "VBAT", "2": "BATT_N"}, mfr=MFR["my"], mpn="BH-18650-B1BA002", lcsc="C2988620")
R(pw, 34, 54, "100", "VBAT", "VDD_PROT", note="HY2112 R1 (100 ohm typ)")
C(pw, 42, 54, "100nF", "VDD_PROT", "BATT_N")
pw.place(S["HY2112-BB"], 72, 56, "HY2112-BB", {"5": "VDD_PROT", "6": "BATT_N", "1": "PROT_OD", "2": "PROT_CS", "3": "PROT_OC"},
         mfr=MFR["hy"], mpn="HY2112-BB", lcsc="C161942")
pw.place(S["FS8205A"], 118, 56, "8205A", {"4": "PROT_OD", "5": "PROT_OC", "2": "BATT_N", "3": "BATT_N", "6": "GND", "7": "GND",
         "1": "PROT_D", "8": "PROT_D"}, mfr="HXY MOSFET", mpn="8205A", lcsc="C5148694", note="TSSOP-8 8205A (Fortune FS8205A C16052 discontinued); same pinout")
R(pw, 96, 66, "2k", "PROT_CS", "GND", note="HY2112 R2 (2k typ, 300R-2k)")
pw.flag_label("VDD_PROT", 50, 46)

pw.text(4, 82, "3.3 V rail + battery voltage sense", 1.5)
C(pw, 14, 94, "10uF", "VBAT", "GND", fp=C8_FP)
pw.place(S["TPS63802"], 50, 96, "TPS63802", {"10": "VBAT", "1": "VBAT", "2": "GND", "3": "GND", "4": "VFB3",
         "6": "+3V3", "5": NC, "9": "SW_L1", "7": "SW_L2", "8": "GND"}, mfr=MFR["ti"], mpn="TPS63802DLAR", lcsc="C2845237")
pw.place(S["L"], 82, 94, "0.47uH", {"1": "SW_L1", "2": "SW_L2"}, note="TI ref: XFL4015-471, Isat>=3A")
C(pw, 96, 94, "22uF", "+3V3", "GND", fp=C8_FP)
R(pw, 106, 94, "511k", "+3V3", "VFB3", note="Vout=0.5*(1+R1/R2)=3.3 V")
R(pw, 112, 94, "91k", "VFB3", "GND")
R(pw, 130, 90, "2.2M", "VBAT", "VBAT_ADC", note="constant 0.8 uA divider")
R(pw, 130, 104, "2.2M", "VBAT_ADC", "GND")
C(pw, 138, 104, "100nF", "VBAT_ADC", "GND")

# ======================================================================
# SHEET 2: MCU
# ======================================================================
mc = Sheet("mcu", "mcu.kicad_sch", "MCU: ESP32-S3-MINI-1", 3)
mc.text(4, 5, "MCU - ESP32-S3-MINI-1-N8 (Wi-Fi demo + LoRa product)")
U4 = mc.place(S["ESP32-S3-MINI-1"], 90, 70, "ESP32-S3-MINI-1-N8", {
    "3": "+3V3", "45": "EN", "4": "BTN", "5": "VBAT_ADC", "6": "NTC15_ADC", "7": NC, "8": "OSC15_FREQ", "9": "OSC40_FREQ",
    "10": "NTC40_ADC", "11": "PWR_NTC", "12": "I2C_SDA", "13": "I2C_SCL", "14": "LORA_NSS", "15": "SPI_MOSI", "16": "SPI_SCK",
    "17": "SPI_MISO", "18": "LORA_DIO1", "19": "PWR_OSC15", "20": "PWR_OSC40", "21": "RAIN_PULSE", "22": "LORA_BUSY",
    "23": "USB_DM", "24": "USB_DP", "25": "LED_R", "26": NC, "27": "CHG_ACTIVE_N", "28": NC, "29": NC, "30": "CHG_DONE_N",
    "31": NC, "32": NC, "33": NC, "34": "LORA_NRST", "35": "LORA_TXEN", "36": "LORA_RXEN", "37": "LED_G", "38": "LED_Y",
    "39": "UART_TX", "40": "UART_RX", "41": NC, "44": NC}, mfr=MFR["esp"], mpn="ESP32-S3-MINI-1-N8", lcsc="C2913206",
    note="-N8 = ESP32-S3FN8, quad 3.3 V flash: IO33-37 and IO47/48 free at 3.3 V")
mc.text(4, 14, "Reset / boot / decoupling", 1.5)
R(mc, 14, 24, "10k", "+3V3", "EN")
C(mc, 20, 24, "1uF", "EN", "GND")
R(mc, 32, 24, "10k", "+3V3", "BTN")
mc.place(S["SW_Push"], 38, 24, "USER/BOOT", {"1": "BTN", "2": "GND"}, note="IO0: hold at reset = USB download mode")
C(mc, 50, 24, "10uF", "+3V3", "GND", fp=C8_FP)
C(mc, 56, 24, "100nF", "+3V3", "GND")
mc.place(S["TestPoint"], 68, 24, "TP_TX", {"1": "UART_TX"})
mc.place(S["TestPoint"], 74, 24, "TP_RX", {"1": "UART_RX"})

# ======================================================================
# SHEET 3: LORA
# ======================================================================
lo = Sheet("lora", "lora.kicad_sch", "LoRa SX1262 module + antenna connector", 4)
lo.text(4, 5, "LORA - EBYTE E22-900MM22S (SX1262, 915 MHz) - antenna: ANT pad -> 0R -> U.FL")
C(lo, 14, 20, "10uF", "+3V3", "GND", fp=C8_FP)
C(lo, 20, 20, "100nF", "+3V3", "GND")
lo.place(S["E22-900MM22S"], 66, 44, "E22-900MM22S", {
    "1": "+3V3", "3": "LORA_NRST", "9": "LORA_TXEN", "10": "LORA_RXEN", "11": "LORA_BUSY", "20": "LORA_DIO1",
    "19": NC, "18": NC, "15": "SPI_SCK", "12": "SPI_MISO", "13": "SPI_MOSI", "14": "LORA_NSS", "6": "RF_MOD",
    "2": "GND", "7": "GND", "16": "GND"}, mfr=MFR["ebyte"], mpn="E22-900MM22S", lcsc="C5333985",
    note="DIO3 = internal TCXO supply (leave open); DIO2 open (TXEN driven by MCU)")
R(lo, 112, 44, "0R", "RF_MOD", "RF_ANT", note="series pi-match; keep trace <5 mm, 50 ohm")
C(lo, 106, 56, "DNP", "RF_MOD", "GND", dnp=True, note="pi-match shunt, tune with VNA")
C(lo, 118, 56, "DNP", "RF_ANT", "GND", dnp=True, note="pi-match shunt, tune with VNA")
lo.place(S["U.FL"], 136, 44, "U.FL-R-SMT-1(80)", {"1": "RF_ANT", "2": "GND", "3": "GND"}, mfr=MFR["hir"], mpn="U.FL-R-SMT-1(80)", lcsc="C88374")

# ======================================================================
# SHEET 4: SENSORS
# ======================================================================
se = Sheet("sensors", "sensors.kicad_sch", "Sensors: probe connector, air T/RH, rain", 5)
se.text(4, 5, "SENSORS (head board) - connector to the probe board, SHT40 air T/RH, rain gauge input")
PROBE_PINS = {"1": "GND", "2": "OSC15_FREQ", "3": "GND", "4": "OSC40_FREQ", "5": "GND",
              "6": "PWR_OSC15", "7": "PWR_OSC40", "8": "PWR_NTC", "9": "NTC15_ADC", "10": "NTC40_ADC"}
se.text(4, 14, "Probe board connector (JST-SH 10P, 1:1 cable). Oscillators and NTCs sit on the probe, next to the electrodes.", 1.5)
se.place(S["JST_SH_10P"], 20, 40, "PROBE", PROBE_PINS, mfr=MFR["jst"], mpn="SM10B-SRSS-TB(LF)(SN)", lcsc="C160409",
         note="GND between the two frequency lines")
C(se, 60, 52, "10nF", "NTC15_ADC", "GND", note="ADC sampling cap")
C(se, 66, 52, "10nF", "NTC40_ADC", "GND")
se.text(150, 64, "Air T/RH (SHT40, I2C 0x44)", 1.5)
se.place(S["SHT40"], 164, 82, "SHT40-AD1B-R2", {"1": "I2C_SDA", "2": "I2C_SCL", "3": "+3V3", "4": "GND"}, mfr=MFR["sens"], mpn="SHT40-AD1B-R2", lcsc="C2909890")
C(se, 150, 76, "100nF", "+3V3", "GND")
R(se, 186, 76, "10k", "+3V3", "I2C_SDA")
R(se, 192, 76, "10k", "+3V3", "I2C_SCL")
se.text(4, 78, "Rain gauge (tipping bucket reed)", 1.5)
se.place(S["JST_SH_2P"], 12, 90, "RAIN", {"1": "RAIN_PULSE", "2": "GND"}, mfr=MFR["jst"], mpn="SM02B-SRSS-TB", note="reed switch to GND, mm/pulse set by mechanics")
R(se, 40, 90, "470k", "+3V3", "RAIN_PULSE")
C(se, 46, 90, "10nF", "RAIN_PULSE", "GND", note="debounce")

# ======================================================================
# SHEET 5: INTERFACE
# ======================================================================
ui = Sheet("interface", "interface.kicad_sch", "Interface: LEDs and USB-C", 6)
ui.text(4, 5, "INTERFACE - 3 status LEDs, USB-C (programming / optional charge) with ESD")
ui.place(S["USB_C_Receptacle"], 24, 50, "USB4105 / TYPE-C-31-M-12", {
    "A4B9": "VBUS", "B4A9": "VBUS", "A6": "USB_DP", "B6": "USB_DP", "A7": "USB_DM", "B7": "USB_DM",
    "A5": "USB_CC1", "B5": "USB_CC2", "A8": NC, "B8": NC, "A1B12": "GND", "B1A12": "GND",
    "1": "GND", "2": "GND", "3": "GND", "4": "GND"},
    mfr=MFR["hro"], mpn="TYPE-C-31-M-12", lcsc="C165948", note="shell legs are through-hole (mechanical strength)")
R(ui, 58, 70, "5.1k", "USB_CC1", "GND", note="UFP pull-down")
R(ui, 64, 70, "5.1k", "USB_CC2", "GND")
ui.place(S["USBLC6-2SC6"], 90, 40, "USBLC6-2SC6", {"1": "USB_DP", "6": "USB_DP", "3": "USB_DM", "4": "USB_DM", "5": "VBUS", "2": "GND"},
         mfr=MFR["st"], mpn="USBLC6-2SC6", lcsc="C7519")
ui.flag("VBUS", 70, 20)
ui.text(120, 14, "Status LEDs (470R ~ 2.8 mA, pulsed by firmware)", 1.5)
for i, (col, net) in enumerate([("green", "LED_G"), ("yellow", "LED_Y"), ("red", "LED_R")]):
    gx = 126 + i * 14
    R(ui, gx, 28, "470", net, f"{net}_A")
    ui.place(S["LED"], gx, 46, f"LED {col}", {"2": f"{net}_A", "1": "GND"}, note="0603; light guide in case")

SHEETS = [pw, mc, lo, se, ui]
D.sheets = SHEETS

# ======================================================================
# PROBE BOARD (own project: hardware/gaiapus-probe), strip 22 mm x ~460 mm
# ======================================================================
PROBE_PROJECT = "gaiapus-probe"
PROBE_ROOT = uid("probe-root")
DP = Design()
pb = Sheet("probe", PROBE_PROJECT + ".kicad_sch", "Probe: electrodes, oscillators, soil temperature", 1,
           d=DP, project=PROBE_PROJECT, root=PROBE_ROOT, top=True, board="Gaiapus probe")
pb.text(4, 5, "PROBE BOARD - strip inside the 32 mm PVC tube (ID ~27 mm), resin filled. Electrodes at 15 cm and 40 cm below soil surface.")
pb.text(4, 9, "Each oscillator + NTC is placed right next to its electrode: only digital frequency and slow analog lines travel up the cable.", 1.5)
pb.place(S["JST_SH_10P"], 14, 46, "HEAD", PROBE_PINS, mfr=MFR["jst"], mpn="SM10B-SRSS-TB(LF)(SN)", lcsc="C160409")
pb.flag("GND", 40, 20)
def moisture(sh, x0, y0, tag, depth):
    sh.text(x0 - 4, y0 - 12, f"Moisture {depth} cm", 1.5)
    sh.place(S["74LVC1G14"], x0 + 14, y0 + 8, "74LVC1G14", {"2": f"OSC{tag}_A", "4": f"OSC{tag}_Y", "5": f"PWR_OSC{tag}", "3": "GND"},
             mfr=MFR["nx"], mpn="74LVC1G14GV,125", lcsc="C131093", note="RC Schmitt oscillator; powered only while measuring")
    C(sh, x0 - 2, y0 - 2, "100nF", f"PWR_OSC{tag}", "GND")
    R(sh, x0 + 32, y0 + 14, "47k", f"OSC{tag}_Y", f"OSC{tag}_A", note="feedback: f~1/(0.8*R*C); target 0.5-2 MHz")
    R(sh, x0 + 40, y0 + 2, "100", f"OSC{tag}_Y", f"OSC{tag}_FREQ", note="series damping for the cable")
    sh.place(S["TestPoint"], x0 + 48, y0 - 2, f"TP_F{tag}", {"1": f"OSC{tag}_FREQ"})
    sh.place(S["Electrode_IDC"], x0 + 2, y0 + 24, f"E{depth}", {"1": f"OSC{tag}_A", "2": "GND"},
             fp="gaiapus:ELECTRODE_IDC_18x40", note="interdigitated electrode (copper under mask), tube-wall coupling")
    C(sh, x0 + 18, y0 + 30, "DNP 10pF", f"OSC{tag}_A", "GND", dnp=True, note="range trim")
    sh.flag_label(f"PWR_OSC{tag}", x0 - 8, y0 - 12)
moisture(pb, 60, 30, "15", 15)
moisture(pb, 130, 30, "40", 40)
pb.text(60, 70, "Soil temperature (NTC 10k next to each electrode)", 1.5)
R(pb, 66, 80, "10k", "PWR_NTC", "NTC15_ADC")
pb.place(S["NTC"], 66, 94, "NTC 10k 15cm", {"1": "NTC15_ADC", "2": "GND"}, mfr=MFR["mur"], mpn="NCP18XH103F03RB", lcsc="C13564", note="NRND: pick active equivalent")
R(pb, 136, 80, "10k", "PWR_NTC", "NTC40_ADC")
pb.place(S["NTC"], 136, 94, "NTC 10k 40cm", {"1": "NTC40_ADC", "2": "GND"}, mfr=MFR["mur"], mpn="NCP18XH103F03RB", lcsc="C13564", note="NRND: pick active equivalent")

# ======================================================================
# CHECKS + OUTPUT
# ======================================================================
def analyse(design, sheets):
    sheets_of = collections.defaultdict(set)
    for net, lst in design.netpins.items():
        for (sk, *_r) in lst:
            sheets_of[net].add(sk)
    for sh in sheets:
        for (net, *_r) in sh.labels:
            sheets_of[net].add(sh.key)
    glob = {net for net, st in sheets_of.items() if len(st) > 1 and net not in POWER_NETS}
    probs = []
    for net, lst in sorted(design.netpins.items()):
        if net.startswith("NC:") or net in POWER_NETS:
            continue
        if len(lst) < 2:
            probs.append(f"net {net}: only {len(lst)} pin(s) -> {lst}")
    for sh in sheets:
        for (net, *_r) in sh.labels:
            if net not in design.netpins:
                probs.append(f"label {net} on sheet {sh.key} has no pins")
    return glob, probs
GLOBAL, problems = analyse(D, SHEETS)
_, probe_problems = analyse(DP, [pb])
problems += ["probe: " + x for x in probe_problems]

os.makedirs(os.path.dirname(LIBF), exist_ok=True)
with open(LIBF, "w", encoding="utf-8") as f:
    f.write('(kicad_symbol_lib\n (version 20231120)\n (generator "gaiapus_gen")\n (generator_version "1.0")\n  '
            + "\n  ".join(lib_sexp(s) for s in S.values()) + "\n)\n")
for sh in SHEETS:
    with open(os.path.join(PRJ, sh.fname), "w", encoding="utf-8") as f:
        f.write(sh.render(GLOBAL))

# root sheet: block diagram (sheet symbols + contents + bus arrows; no electrical meaning)
G = lambda v: round(v / U) * U          # snap to 2.54 mm grid
rk = [0]
def rid(tag): rk[0] += 1; return q(uid("root", tag, rk[0]))
def rtext(x, y, t, size=1.5, bold=False, just="left bottom"):
    return (f"(text {q(t)} (exclude_from_sim no) (at {n(x)} {n(y)} 0) "
            f"(effects (font (size {size} {size}){' bold' if bold else ''}) (justify {just})) (uuid {rid('t')}))")
def rline(pts, w=0.35):
    pp = " ".join(f"(xy {n(a)} {n(b)})" for a, b in pts)
    return f"(polyline (pts {pp}) (stroke (width {w}) (type solid)) (uuid {rid('l')}))"
def arrow(a, b, both=False):
    """straight arrow a->b with V heads (graphic only)"""
    out = [rline([a, b])]
    def head(tip, frm):
        dx, dy = tip[0] - frm[0], tip[1] - frm[1]; L = (dx * dx + dy * dy) ** 0.5; ux, uy = dx / L, dy / L
        return rline([(tip[0] - 2.5 * ux - 1.2 * uy, tip[1] - 2.5 * uy + 1.2 * ux), tip,
                      (tip[0] - 2.5 * ux + 1.2 * uy, tip[1] - 2.5 * uy - 1.2 * ux)])
    out.append(head(b, a))
    if both: out.append(head(a, b))
    return out

LAYOUT = {   # key: (x, y, w, h) in mm
    "interface": (G(165), G(45), G(85), G(38)),
    "power":     (G(35),  G(110), G(95), G(58)),
    "mcu":       (G(165), G(110), G(85), G(58)),
    "lora":      (G(290), G(110), G(90), G(58)),
    "sensors":   (G(165), G(205), G(85), G(55)),
}
CONTENT = {
    "power": ["Solar 5 V 0.3 W (68x37 mm) -> BZT52C6V2 clamp",
              "CN3058E LiFePO4 charger, 51 mA",
              "18650 LiFePO4 + HY2112-BB / FS8205A protection",
              "TPS63802 buck-boost -> +3V3 (11 uA Iq)",
              "VBAT sense: 2 x 2.2 Mohm divider"],
    "mcu": ["ESP32-S3-MINI-1-N8",
            "Wi-Fi (bench/config), deep sleep ~25 uA",
            "Reset RC, USER/BOOT button (IO0)",
            "UART test pads"],
    "lora": ["EBYTE E22-900MM22S (Semtech SX1262)",
             "915 MHz (AU915), up to 22 dBm",
             "ANT pad -> 0 ohm + pi-match (DNP) -> U.FL",
             "pigtail to SMA bulkhead on the enclosure"],
    "sensors": ["Probe connector JST-SH 10P -> probe board",
                "  (separate project hardware/gaiapus-probe)",
                "Air T / RH: Sensirion SHT40 (I2C 0x44)",
                "Rain gauge: reed switch pulse (JST-SH)"],
    "interface": ["USB-C (program / charge) + USBLC6-2SC6 ESD",
                  "Status LEDs: green / yellow / red (light guide)"],
}
names = {"power": "Power", "mcu": "MCU", "lora": "LoRa", "sensors": "Sensors", "interface": "Interface"}
boxes, deco = [], []
for sh in SHEETS:
    x, y, w, h = LAYOUT[sh.key]
    boxes.append(
        f"(sheet (at {n(x)} {n(y)}) (size {n(w)} {n(h)}) (fields_autoplaced yes)\n"
        f"  (stroke (width 0.25) (type solid)) (fill (color 255 255 225 1.0000)) (uuid {q(sh.uuid)})\n"
        f"  {prop('Sheetname', names[sh.key], x, y - 0.7, just='left bottom')}\n"
        f"  {prop('Sheetfile', sh.fname, x, y + h + 0.7, just='left top')}\n"
        f"  (instances (project {q(PROJECT)} (path {q('/' + ROOT)} (page {q(str(sh.page))})))))")
    for i, line in enumerate(CONTENT[sh.key]):
        deco.append(rtext(x + 3, y + 8 + i * 5.5, line, 1.6))
    deco.append(rtext(x + 3, y + h - 3, "double-click to open", 1.2))

P, M, L, Se, I = (LAYOUT[k] for k in ("power", "mcu", "lora", "sensors", "interface"))
# Power -> MCU
y1 = P[1] + 16; deco += arrow((P[0] + P[2], y1), (M[0], y1))
deco.append(rtext(P[0] + P[2] + 2, y1 - 1.5, "+3V3 to all blocks", 1.5, True))
y2 = P[1] + 34; deco += arrow((M[0], y2), (P[0] + P[2], y2))
deco.append(rtext(P[0] + P[2] + 2, y2 - 1.5, "VBAT_ADC, CHG status", 1.4))
# MCU <-> LoRa
y3 = M[1] + 22; deco += arrow((M[0] + M[2], y3), (L[0], y3), both=True)
deco.append(rtext(M[0] + M[2] + 2, y3 - 1.5, "SPI + NSS, BUSY, DIO1 (IRQ),", 1.4))
deco.append(rtext(M[0] + M[2] + 2, y3 + 3.5, "NRST, TXEN, RXEN", 1.4))
# MCU <-> Sensors
x4 = M[0] + M[2] / 2; deco += arrow((x4, M[1] + M[3]), (x4, Se[1]), both=True)
for i, t in enumerate(["OSC15/40 frequency (PCNT)", "NTC15/40 ADC, I2C (SHT40)", "RAIN pulse (wake)", "PWR_OSC / PWR_NTC (power gating)"]):
    deco.append(rtext(x4 + 2, M[1] + M[3] + 7 + i * 4.5, t, 1.4))
# Interface <-> MCU
x5 = I[0] + I[2] / 2; deco += arrow((x5, I[1] + I[3]), (x5, M[1]), both=True)
deco.append(rtext(x5 + 2, I[1] + I[3] + 8, "USB D+/D-, LED G/Y/R", 1.4))
# Interface -> Power (VBUS)
xv = P[0] + P[2] / 2; yv = I[1] + I[3] / 2
deco.append(rline([(I[0], yv), (xv, yv), (xv, P[1])]))
deco += arrow((xv, yv + 10), (xv, P[1]))
deco.append(rtext(xv + 2, yv - 1.5, "VBUS (USB 5 V) -> solar input via Schottky", 1.4))
# off-board items
deco.append(rtext(P[0], P[1] + P[3] + 10, "Off-board: solar panel (JST-SH), 18650 cell in SMD holder", 1.4))
deco.append(rtext(L[0], L[1] + L[3] + 10, "Off-board: 915 MHz antenna (U.FL -> SMA)", 1.4))
deco.append(rtext(Se[0], Se[1] + Se[3] + 10, "Probe board (22 x ~460 mm strip in 32 mm PVC tube, resin filled):", 1.4))
deco.append(rtext(Se[0], Se[1] + Se[3] + 15, "interdigitated electrodes + 74LVC1G14 oscillators + NTC at 15 cm and 40 cm", 1.4))
# title
deco.append(rtext(G(35), G(20), "Gaiapus soil stake node - block diagram", 3, True))
deco.append(rtext(G(35), G(27), "Sheets connect through global labels and power symbols; arrows show the main signal groups (drawing only).", 1.6))
deco.append(rtext(G(35), G(32), "Generated by hardware/tools/gen_kicad.py", 1.3))

with open(os.path.join(PRJ, "gaiapus-node.kicad_sch"), "w", encoding="utf-8") as f:
    f.write(f"(kicad_sch\n (version 20231120)\n (generator \"gaiapus_gen\")\n (generator_version \"1.0\")\n (uuid {q(ROOT)})\n (paper \"A3\")\n"
            f" (title_block (title \"Gaiapus Node - Estaca de solo\") (date \"2026-11-14\") (rev \"A\")"
            f" (company \"Team Gaiapus · NASA Space Apps 2026\") (comment 1 \"Field Shift: Adapting Farms with NASA Data\"))\n"
            f" (lib_symbols)\n " + "\n ".join(deco) + "\n " + "\n ".join(boxes) +
            f"\n (sheet_instances (path \"/\" (page \"1\")))\n)\n")

PRJ_PROBE = os.path.join(HW, PROBE_PROJECT)
os.makedirs(PRJ_PROBE, exist_ok=True)
with open(os.path.join(PRJ_PROBE, pb.fname), "w", encoding="utf-8") as f:
    f.write(pb.render(set()))
for fn in ("sym-lib-table", "fp-lib-table"):
    with open(os.path.join(PRJ, fn), encoding="utf-8") as src, open(os.path.join(PRJ_PROBE, fn), "w", encoding="utf-8") as dst:
        dst.write(src.read())
pro = os.path.join(PRJ_PROBE, PROBE_PROJECT + ".kicad_pro")
if not os.path.exists(pro):
    with open(pro, "w", encoding="utf-8") as f:
        f.write('{\n  "meta": {"filename": "%s.kicad_pro", "version": 1},\n'
                '  "text_variables": {"PROJETO": "Gaiapus Probe - placa-sonda", "REV": "A"}\n}\n' % PROBE_PROJECT)
for (dsg, folder) in ((DP, PRJ_PROBE),):
    with open(os.path.join(folder, "netlist-draft.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["net", "scope", "sheet", "ref", "pin", "pin_name"])
        for net, lst in sorted(dsg.netpins.items()):
            scope = "power" if net in POWER_NETS else ("nc" if net.startswith("NC:") else "local")
            for (sk, ref, pn, nm) in sorted(lst, key=lambda t: (t[0], t[1], t[2])):
                w.writerow([net, scope, sk, ref, pn, nm])

with open(os.path.join(PRJ, "netlist-draft.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["net", "scope", "sheet", "ref", "pin", "pin_name"])
    for net, lst in sorted(D.netpins.items()):
        scope = "power" if net in POWER_NETS else ("global" if net in GLOBAL else ("nc" if net.startswith("NC:") else "local"))
        for (sk, ref, pn, nm) in sorted(lst, key=lambda t: (t[0], t[1], t[2])):
            w.writerow([net, scope, sk, ref, pn, nm])

with open(BOMF, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["Board", "Refs", "Qty", "Value", "Footprint", "Manufacturer", "MPN", "LCSC", "DNP"])
    for board, dsg in (("head", D), ("probe", DP)):
        grp = collections.OrderedDict()
        for (ref, val, fp, mfr, mpn, lcsc, dnp, note, sk) in dsg.parts:
            grp.setdefault((val, fp, mfr, mpn, lcsc, dnp), []).append(ref)
        for (val, fp, mfr, mpn, lcsc, dnp), refs in grp.items():
            w.writerow([board, " ".join(refs), len(refs), val, fp, mfr, mpn, lcsc, "DNP" if dnp else ""])

print(f"probe board: parts {len(DP.parts)}  nets {len([k for k in DP.netpins if not k.startswith('NC:')])}")
print(f"symbols: {len(S)}  head parts: {len(D.parts)}  nets: {len([k for k in D.netpins if not k.startswith('NC:')])}  global nets: {len(GLOBAL)}")
print("custom footprints:", sorted({p[2] for p in D.parts + DP.parts if p[2].startswith('gaiapus:')}))
if problems:
    print("PROBLEMS:"); [print(" -", p) for p in problems]
else:
    print("netlist sanity: OK (every net has >=2 pins)")

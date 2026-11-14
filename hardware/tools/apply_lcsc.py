#!/usr/bin/env python3
"""After import_lcsc.cmd: map LCSC code -> imported footprint, fix 3D paths, check pad numbers.

Writes hardware/lib/lcsc_footprints.json (read by gen_kicad.py) and prints a pad report:
every symbol pin number must exist as a pad in the imported footprint (and vice versa, except
mechanical/unnamed pads). Run, then run gen_kicad.py and check_kicad.py.
"""
import os, re, json, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
SYM, PRETTY = os.path.join(LIB, "lcsc.kicad_sym"), os.path.join(LIB, "lcsc.pretty")
if not os.path.exists(SYM):
    sys.exit("lcsc.kicad_sym not found: run import_lcsc.cmd first")

txt = open(SYM, encoding="utf-8").read()
mapping = {}
EASY_PINS = {}   # LCSC -> {pin number: pin name} from the EasyEDA symbol
for blk in re.split(r'\n  \(symbol "', txt)[1:]:
    lc = re.search(r'\(property\s+"LCSC Part"\s+"(C\d+)"', blk)
    fp = re.search(r'\(property\s+"Footprint"\s+"([^"]*)"', blk)
    if lc and fp:
        mapping[lc.group(1)] = fp.group(1).split(":")[-1]
        EASY_PINS[lc.group(1)] = dict((m[1], m[0]) for m in re.findall(r'\(name\s+"([^"]*)".*?\(number\s+"([^"]*)"', blk, re.S))

fixed = 0
for f in os.listdir(PRETTY):
    if not f.endswith(".kicad_mod"):
        continue
    p = os.path.join(PRETTY, f); s = open(p, encoding="utf-8").read()
    s2 = re.sub(r'\(model "[^"]*?([^"/\\]+\.(?:wrl|step|stp))"',
                lambda m: '(model "${KIPRJMOD}/../lib/lcsc.3dshapes/' + m.group(1) + '"', s, flags=re.I)
    if s2 != s:
        open(p, "w", encoding="utf-8").write(s2); fixed += 1
FILES = [f[:-10] for f in os.listdir(PRETTY) if f.endswith(".kicad_mod")]
for lc, name in list(mapping.items()):          # the symbol's Footprint field can differ from the file name
    if name in FILES:
        continue
    cand = [f for f in FILES if f.startswith(name) or name.startswith(f)]
    if len(cand) == 1:
        print(f"  note: {lc} footprint '{name}' -> file '{cand[0]}'")
        mapping[lc] = cand[0]
    else:
        print(f"  WARNING: {lc} footprint '{name}' not found (candidates {cand})")
json.dump(mapping, open(os.path.join(LIB, "lcsc_footprints.json"), "w"), indent=2, sort_keys=True)
print(f"mapped {len(mapping)} LCSC parts, fixed 3D paths in {fixed} footprints")

# pad check against our symbols
import importlib.util
spec = importlib.util.spec_from_file_location("kl", os.path.join(os.path.dirname(__file__), "kicad_lib.py"))
SYMS_BY_LCSC = {  # LCSC -> symbol name in gen_kicad.py
    "C2913206": "ESP32-S3-MINI-1", "C5333985": "E22-900MM22S", "C112011": "CN3058E", "C161942": "HY2112-BB",
    "C5148694": "FS8205A", "C2845237": "TPS63802", "C2909890": "SHT40", "C131093": "74LVC1G14", "C13564": "NTC",
    "C165948": "USB_C_Receptacle", "C7519": "USBLC6-2SC6", "C2988620": "Battery_18650", "C88374": "U.FL",
    "C160409": "JST_SH_10P"}
libtxt = open(os.path.join(LIB, "symbols", "gaiapus.kicad_sym"), encoding="utf-8").read()
PAD_RE = re.compile(r'\(pad\s+"?([^"\s)]*)"?\s+(?:smd|thru_hole|np_thru_hole|connect)')
PIN_RE = re.compile(r'\(name\s+"([^"]*)".*?\(number\s+"([^"]+)"', re.S)
def sym_pinmap(name):
    i = libtxt.index(f'(symbol "{name}"')
    nxt = [m.start() for m in re.finditer(r'\n  \(symbol "([^"]+)"', libtxt[i + 10:]) if not m.group(1).startswith(name + "_")]
    blk = libtxt[i:(i + 10 + nxt[0]) if nxt else None]
    return dict((m[1], m[0]) for pin in re.findall(r'\(pin [^\n]*', blk) for m in PIN_RE.findall(pin))
def sym_pins(name): return set(sym_pinmap(name))
def norm(x): return re.sub(r'[^A-Z0-9]', '', x.upper().replace("GPIO", "IO"))
bad = 0
for lc, symname in SYMS_BY_LCSC.items():
    if lc not in mapping:
        print(f"  MISSING import for {lc} ({symname})"); bad += 1; continue
    fp = open(os.path.join(PRETTY, mapping[lc] + ".kicad_mod"), encoding="utf-8").read()
    pads = set(x for x in PAD_RE.findall(fp) if x)
    pins = sym_pins(symname)
    if not pins or not pads:
        print(f"  {lc:9} {symname:18} EMPTY COMPARISON (pins {len(pins)}, pads {len(pads)})"); bad += 1; continue
    miss, extra = sorted(pins - pads), sorted(pads - pins)
    st = "OK" if not miss else "PIN NUMBERS NOT IN FOOTPRINT"
    if miss: bad += 1
    print(f"  {lc:9} {symname:18} -> {mapping[lc]:40} {st}" + (f" missing={miss}" if miss else "") + (f" extra_pads={extra}" if extra else ""))
print("\nPin-name cross-check against the EasyEDA symbols (same number, compatible name):")
for lc, symname in SYMS_BY_LCSC.items():
    ours, theirs = sym_pinmap(symname), EASY_PINS.get(lc, {})
    diff = [(num, ours[num], theirs.get(num, "-")) for num in sorted(ours, key=lambda v: (len(v), v))
            if num in theirs and norm(ours[num]) != norm(theirs[num]) and not (norm(ours[num]) in norm(theirs[num]) or norm(theirs[num]) in norm(ours[num]))]
    cmp = sum(1 for k in ours if k in theirs)
    print(f"  {symname:18} compared {cmp:3}  {'same' if (cmp and not diff) else ('NOTHING COMPARED' if not cmp else 'DIFFERENT: ' + ', '.join(f'{a}:{b}/{c}' for a, b, c in diff))}")
print("RESULT:", "OK" if not bad else f"{bad} part(s) need attention")

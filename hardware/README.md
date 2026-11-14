# Hardware

| Folder | What |
|---|---|
| `gaiapus-node/` | KiCad 8 project of the **head board** (ESP32-S3, LoRa, power, SHT40, rain, LEDs, USB). Root sheet = block diagram. |
| `gaiapus-probe/` | KiCad 8 project of the **probe board** (strip 22 x ~460 mm inside the 32 mm PVC tube): electrodes, oscillators, NTCs. |
| `lib/` | `symbols/gaiapus.kicad_sym` (generated), `footprints/gaiapus.pretty` (electrode), `lcsc.*` (imported from LCSC) |
| `tools/` | generators and checks (below) |

## Tools
| Script | Run when |
|---|---|
| `gen_kicad.py` | after any circuit change: writes both schematics, symbol lib, netlists, `bom/bom_from_schematic.csv` |
| `check_kicad.py` | after `gen_kicad.py`: re-derives connectivity from geometry, must print `RESULT: OK` |
| `gen_footprints.py` | electrode footprint (parametric: width, height, finger, gap) |
| `import_lcsc.cmd` | **on Windows, once**: footprints + 3D models of all LCSC parts (needs Python + internet) |
| `apply_lcsc.py` | after the import: maps footprints, fixes 3D paths, checks pin/pad numbers and pin names against the LCSC symbols |
| `autoplace.py` + `check_placement.py` | first-pass placement into the zones, overlap/edge/hole check |
| `place_head.py` | connectivity-driven floorplan of the head board (positions + rotations), strips routing |
| `fpmove.py` | move/rotate footprints in a board file (90-degree steps) |
| `route.py probe\|head` | grid router (2 layers, 45 deg, vias, GND stitching), clearances from the .kicad_dru; `ROUTE_ONLY`, `ROUTE_FIRST`, `ROUTE_BUDGET`, `ROUTE_RIPUP` (seconds of rip-up and reroute), `ROUTE_MAXHITS` env vars |
| `verify_pcb.py board.kicad_pcb` | independent copper check: connectivity, clearance between nets, copper-to-edge |
| `gen_pcb_outline.py` | board outlines, mounting holes, SHT40 slot and placement boxes (refuses to touch a PCB that already has footprints) |

Close KiCad before regenerating (regeneration overwrites the schematic files).

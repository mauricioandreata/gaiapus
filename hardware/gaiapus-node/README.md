# gaiapus-node (KiCad 8)

Schematic is hierarchical, 5 sheets joined by global labels and power symbols (no sheet pins):

| Sheet | File | Content |
|---|---|---|
| Power | `power.kicad_sch` | solar input + zener, CN3058E charger, 18650 holder, HY2112 + FS8205A, TPS63802 3.3 V, battery divider |
| MCU | `mcu.kicad_sch` | ESP32-S3-MINI-1-N8, reset/boot, decoupling, UART test pads |
| LoRa | `lora.kicad_sch` | E22-900MM22S, ANT pad -> 0R -> U.FL |
| Sensors | `sensors.kicad_sch` | 2 x moisture oscillators + electrodes, 2 x NTC, SHT40, rain input |
| Interface | `interface.kicad_sch` | USB-C + ESD, 3 LEDs |

## How these files were made
`python3 hardware/tools/gen_kicad.py` writes the schematic, the symbol library (`../lib/symbols/gaiapus.kicad_sym`), `netlist-draft.csv` and `bom/bom_from_schematic.csv`.
`python3 hardware/tools/check_kicad.py` re-derives connectivity from the raw geometry and compares it with the intended nets (must print `RESULT: OK`).
Pin numbers come from the vendor datasheets (see `docs/component-selection.md`, `docs/hardware-pinmap.md`).

**Rule:** either edit the script and regenerate, or edit in KiCad and stop regenerating (regeneration overwrites the sheets). Close KiCad before regenerating.

## First steps in KiCad
1. Close KiCad (lock files `~*.lck` are from an old session), reopen `gaiapus-node.kicad_pro`.
2. Inspection > Electrical Rules Checker. Send the report back; expected leftovers are pin-type warnings, not missing connections.
3. Tools > Assign Footprints; draw the custom ones (list in `docs/hardware-pinmap.md`).
4. Tools > Update PCB from Schematic.

Symbol fields on every part: Value, Footprint, LCSC, MPN, Manufacturer, Note (hidden).

# Component selection · Gaiapus Node Rev A (draft, 2026-11-12)

Criteria: SMD only, certified radio modules, stocked at LCSC/JLCPCB (assembly-ready), KiCad/EasyEDA model available,
low sleep current, lowest cost at 1k units. Prices are LCSC/JLCPCB references found on 2026-11-12 and change daily.

| Ref | Function | Selected part | LCSC # | Package | Ref. price (USD) | Datasheet / page | Notes |
|---|---|---|---|---|---|---|---|
| U1 | MCU + Wi-Fi/BLE + USB + touch/PCNT | Espressif **ESP32-S3-MINI-1-N8** | C2913206 | Module 15.4×20.5 mm | ~3.26 | https://www.espressif.com/sites/default/files/documentation/esp32-s3-mini-1_mini-1u_datasheet_en.pdf | PCB antenna (Wi-Fi only for demo/setup): keep antenna keep-out at board edge |
| U2 | LoRa radio SX1262 915 MHz | EBYTE **E22-900MM22S** | C5333985 | SMD 10×10 mm, stamp hole + IPEX | ~4 (to confirm) | https://www.lcsc.com/product-detail/C5333985.html | Use the module's own IPEX → pigtail → SMA bulkhead in the case: no 50 Ω trace on our PCB. Check TXEN/RXEN pin handling in datasheet |
| U2 alt | LoRa radio (larger) | EBYTE E22-900M22S | C411293 | SMD 20×14 mm | ~6.60 | https://www.lcsc.com/product-detail/C411293.html | Fallback if MM22S stock is short |
| U3 | LiFePO4 linear charger (solar input) | Consonance **CN3058E** | C112011 | SOP-8-EP | ~0.28 @1k | https://www.lcsc.com/product-detail/C112011.html | Vin 3.8–6 V, 3.6 V CV, <3 µA battery drain without input. Panel Voc must stay ≤ 6 V or add clamp |
| U4 | Battery protection (LiFePO4) | HYCON **HY2112-BB** | C161942 | SOT-23-6 | to confirm | https://jlcpcb.com/partdetail/C161942 | LiFePO4 thresholds (3.75 V OV / 2.1 V UV); needs dual N-MOSFET (e.g. FS8205A) |
| U5 | 3.3 V buck-boost | TI **TPS63802DLAR** | C2845237 | VSON-10 2×3 mm | ~0.64 @1k | https://ti.com/lit/pdf/SLVSEU9 | 1.3–5.5 V in, 11 µA Iq, 2 A: covers LoRa 22 dBm and Wi-Fi peaks; uses 0.47 µH inductor |
| U6 | Air temperature + humidity | Sensirion **SHT40-AD1B-R2** | C2909890 | DFN-4 1.5×1.5 mm | ~1.72 (1 pc) / ~1.1 (reel) | https://www.lcsc.com/datasheet/lcsc_datasheet_2110211930_Sensirion-SHT40-AD1B-R2_C2909890.pdf | Place at vented corner, thermal slots around it |
| U7, U8 | Soil probe oscillators (×2) | Nexperia **74LVC1G14GV,125** | C131093 | SOT-753 (SOT-23-5) | ~0.04 @3k | https://www.lcsc.com/product-detail/C131093.html | Powered from a GPIO only during measurement |
| RT1, RT2 | Soil temperature (×2) | Murata **NCP18XH103F03RB** 10 k / B3380 | C13564 | 0603 | ~0.02 | https://www.lcsc.com/product-detail/C13564.html | Marked "not for new designs" at DigiKey: pick an equivalent 10 k/3380K 0603 on Friday |
| J1 | USB-C (program/debug) | HRO **TYPE-C-31-M-12** | C165948 | SMD 16P | ~0.10–0.17 | https://lcsc.com/product-detail/C165948.html | USB 2.0 only; 5.1 k CC pull-downs |
| D1 | USB ESD | ST **USBLC6-2SC6** | C7519 | SOT-23-6 | ~0.06 @3k | https://www.lcsc.com/product-detail/C7519.html | |
| BT1 | 18650 holder SMD | MYOUNG **BH-18650-B1BA002** | C2988620 | SMD | to confirm | https://www.lcsc.com/product-detail/C2988620.html | Premium alt: Keystone 1042P (~2.80 @1k, DigiKey) |
| J2 | Optional U.FL on PCB | Hirose **U.FL-R-SMT-1(80)** | C88374 | SMD | ~0.07 | https://www.lcsc.com/product-detail/C88374.html | Only if we route antenna through the PCB instead of module IPEX |

## Commodity parts (choose from JLCPCB basic library on Friday)
3 LEDs 0603 (green/yellow/red), 1 tactile SMD button, JST-SH SMD 2-pin (rain gauge) and 2-pin (solar),
Schottky for panel reverse protection, 0.47 µH power inductor for TPS63802, 0402/0603 R and C,
dual N-MOSFET FS8205A for HY2112, battery divider (switched or ≥1 MΩ).

## Rough electronics cost (main ICs, 1k units)
≈ USD 10–11 (ESP32-S3 module + LoRa module ≈ 7.3; rest ≈ 3–4) + passives + PCB + assembly.
To be replaced by the KiCad BOM export on Sunday.

## Design notes triggered by these choices
- No load switch: oscillators and NTC dividers fed from GPIOs during measurement only.
- RF on our board avoided entirely (module IPEX), which lowers layout risk without a prototype.
- Solar panel: 5 V class panel with Voc ≤ 6 V for CN3058E; power budget shows <1 W is enough.

## Solar panel (off-board, wired to the PCB through a JST-SH 2P)

**Selected: generic 5 V / 60 mA polycrystalline epoxy panel, 68 x 37 x 2-3 mm (0.3 W class).**
Reference part with a real datasheet: AMX Solar SP-68x37 (DigiKey, Voc 6.27 V, Vmp 5.28 V, Isc 75 mA, Imp 69.3 mA, 0.37 W max).
Generic equivalents sold as "5V 60mA 68x37mm" (about US$2.50-5 each at retail; cents-level in volume from Chinese factories): Abra SP-5V-60MA-68X37MM, Robot Pi Shop 0.3W 5V 60mA, Tinytronics 001693.

Why this size: it fits on top of a stake cap, the 64 uA average load needs only ~1.5 mAh/day, and `power/power_budget.py` gives with 0.3 W: +211 mAh/day (sun), +51 mAh/day net on a cloudy day. With a 0.15 W / 53x30 mm panel it is still +25 mAh/day net on a cloudy day.

Rejected: Seeed 0.5 W 55x70 (Voc 8.2 V, too high for the CN3058E 6 V input); SparkFun 6 V ETFE 52x52 (Voc 7.09 V); PCBWay 60x60 SunPower (Voc 6.6 V).

Open points:
- Voc of 6.0-6.3 V is at/above the CN3058E 6 V limit: add a ~5.6 V zener clamp (e.g. BZT52C5V6, SOD-123) at the panel input and check the CN3058E datasheet for the absolute maximum and for reverse-leakage at night (series Schottky if needed).
- Request Voc/Vmp/Isc at the actual test conditions from the supplier; buy 2-3 units for the bench demo.

## Corrections after reading the pin tables (2026-11-14)

- **E22-900MM22S antenna:** the module datasheet lists pin 6 `ANT` as a stamp-hole pad; it is a 20-pin 10 x 10 mm module with no U.FL on the module. The earlier idea "use the module's IPEX output" does not apply to this part. The schematic therefore has `ANT -> 0R series (pi-match, DNP shunts) -> U.FL-R-SMT-1(80)` on the board. Keep the pad-to-connector trace under ~5 mm and 50 ohm (JLCPCB impedance calculator for the chosen stack-up); tune with a VNA if one is available.
- **FS8205A:** use the TSSOP-8 part (1,8 = D; 2,3 = S1; 4 = G1; 5 = G2; 6,7 = S2). The SOT-23-6 variant has a different pinout. HY2112-BB wiring: OD -> G1, OC -> G2, CS -> 2 k -> P-, VDD -> 100 R -> B+, 100 nF VDD-VSS (values from the HY2112 datasheet).
- **CN3058E:** SOP-8-EP pins: 1 TEMP, 2 ISET, 3 GND, 4 VIN, 5 BAT, 6 DONE, 7 CHRG, 8 FB. TEMP is biased with 10k/10k (50 % of VIN, inside the 45-80 % window). Open point: confirm V_ISET and the absolute maximum VIN in the datasheet before fixing R_ISET (10 k placeholder) and the 5.6 V zener.
- **SHT40-AD1B:** DFN-4 pins 1 SDA, 2 SCL, 3 VDD, 4 GND (Sensirion SENSEVAL-SHT4x doc), address 0x44, 10 k pull-ups + 100 nF.
- **TPS63802 (DLA, VSON-10):** 1 EN, 2 MODE, 3 AGND, 4 FB, 5 PG, 6 VOUT, 7 L2, 8 GND, 9 L1, 10 VIN; 0.47 uH, 10 uF in, 22 uF out, FB divider 511 k / 91 k for 3.3 V; EN to VIN, MODE to GND (power-save).

### CN3058E values fixed (2026-11-14, from the English datasheet)
- All pins absolute max 6.5 V; VIN operating 3.8-6 V; UVLO 3.2-3.8 V.
- I_CH = 1218 / R_ISET (V_ISET = 1.205 V). **R_ISET = 24 k 1 % -> 51 mA.** The charger has no input-voltage regulation, so the charge current must stay below the panel's Imp (60-69 mA), or VIN collapses to the battery voltage and the charger hiccups through UVLO. 51 mA from a 1500 mAh cell still recharges a full day of use (~1.5 mAh) in under 2 minutes of sun.
- Regulation 3.6 V (3.55-3.65 V). HY2112-BB overcharge trip is 3.75 V, so the two do not fight.
- **TEMP grounded** (datasheet: grounding disables the function). This removes the 10k/10k divider. Uberlandia rarely goes below 0 C; if a cold-climate variant is needed, put an NTC on TEMP.
- CHRG/DONE: open drain, 10 mA sink, 1 uA leakage; read by MCU internal pull-ups (3.3 V is within abs max even with VIN = 0).
- C_IN >= 1 uF (10 uF fitted), C_BAT 4.7-10 uF (10 uF fitted).
- **Zener changed to BZT52C6V2:** panel Voc is 6.0-6.3 V (below abs max 6.5 V). A 6.2 V clamp only conducts near open circuit, where the panel gives little current, so its dissipation stays low. A 5.6 V zener would clamp at the panel's working point and burn up to ~0.4 W in a SOD-123.

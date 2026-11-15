# Datasheets — GaiaPus (head `gaiapus-node` + `gaiapus-probe`)

Baixados em 2026-11-15. Fontes: sites dos fabricantes, LCSC (peças da BOM) e Semtech (cópia V2.1 via Elecrow).

| Ref (KiCad) | Componente | Arquivo |
|---|---|---|
| U4 | ESP32-S3-MINI-1-N8 (Espressif) | ESP32-S3-MINI-1_Espressif.pdf |
| U5 | E22-900MM22S (EBYTE, módulo SX1262) | E22-900MM22S_EBYTE_E22-M_UserManual_EN.pdf |
| (chip do U5) | SX1262 (Semtech) | SX1262_Semtech_SX1261-2_V2.1.pdf |
| U1 | CN3058E (Consonance) | CN3058E_Consonance_EN_rev1.1.pdf / _CN.pdf |
| U2 | HY2112-BB (HYCON) | HY2112-BB_HYCON.pdf |
| Q1 | 8205A (HXY MOSFET) | 8205A_HXY-MOSFET.pdf |
| U3 | TPS63802 (TI) | TPS63802_TI.pdf |
| U6 | SHT40-AD1B-R2 (Sensirion) | SHT4x_Sensirion.pdf |
| U1/U2 probe | 74LVC1G14GV (Nexperia) | 74LVC1G14GV_Nexperia.pdf |
| RT1/RT2 probe | NCP18XH103F03RB (Murata, NRND) | NCP18XH103F03RB_Murata.pdf |
| J5 | TYPE-C-31-M-12 (HRO) | TYPE-C-31-M-12_HRO.pdf |
| U7 | USBLC6-2SC6 (ST) | USBLC6-2SC6_ST.pdf |
| BT1 | BH-18650-B1BA002 (MYOUNG) | BH-18650-B1BA002_MYOUNG.pdf |
| J2 | U.FL-R-SMT-1(80) (Hirose) | U.FL-R-SMT-1_Hirose.pdf |
| J3 / J1 probe | SM10B-SRSS-TB (JST); J1/J4 SM02B-SRSS-TB é da mesma série SH | SM10B-SRSS-TB_JST.pdf |
| D1 | BZT52C6V2 (zener 6,2 V; MPN de fabricante não definido na BOM) | BZT52C6V2_Zener_hongjiacheng.pdf |
| D2 | B5819W (Schottky; fabricante não definido na BOM) | B5819W_Schottky_JSMSEMI.pdf |

## Pendentes / observações
- SW1 (PTS810), L1 (0,47 µH, NR-40xx) e resistores/capacitores/LEDs não têm MPN na BOM: sem datasheet específico.
- BZT52C6V2 e B5819W: datasheets de fabricantes genéricos do LCSC; troque se definir outro MPN.
- NCP18XH103F03RB está NRND (já anotado na BOM).
- CN3058E: a versão em inglês (rev 1.1) veio de cópia de terceiros; a chinesa (LCSC) é o original.

# Mecânica · estaca, case e pluviômetro

## Entregáveis
1. Estaca: corpo que protege a PCB-sonda e permite cravar no solo sem quebrar a placa.
2. Case IP65 da parte eletrônica: painel solar no topo, janela/guia de luz para 3 LEDs, botão, respiro protegido para o SHT40, QR code.
3. Pluviômetro de báscula com reed switch: definir **mm por pulso**.
4. Vista explodida, render e estimativa de custo (impressão 3D e injeção).

## Interfaces com a eletrônica (combinar com o hardware)
- Cotas da PCB (largura, comprimento total, posição dos eletrodos a ~15 e ~40 cm)
- Furos de fixação e posição do porta-bateria 18650
- Posição dos LEDs, botão, USB-C, conector da antena e do pluviômetro

Exporte a PCB do KiCad em STEP (Arquivo > Exportar > STEP) para encaixar no CAD.

---

## Head case, rev B (2026-11-14, current)

Built from the boards as exported on 2026-11-14 (`gaiapus-node.kicad_pcb` + `.glb`/`.step`). All dimensions in `tools/params.py`.

| File | What |
|---|---|
| `drawings/gaiapus-case-revB.pdf` | 3 A3 sheets: **1** overview (assembled + exploded 3D, stake, parts list, board measurements, checks), **2** base, **3** lid + sections A-A/B-B + details |
| `drawings/png/sheet-1..3.png` | previews |
| `drawings/gaiapus-case-revB-views.dxf` | every view as 2D lines (mm) |
| `drawings/clearance-report-revB.md` | 23 clearance checks case vs boards (all OK) |
| `cad/gaiapus_case_revB.scad` | parametric solid: `part = "base" / "lid" / "button"` -> STL (**not compiled yet**) |
| `tools/gen_case_drawings.py` | regenerates PDF + DXF + report (matplotlib); PNG with `pdftoppm -r 110 -png` |
| `drawings/archive-revA/` | superseded rev A |

Head 114 x 82 x 38.5 mm (+ panel 1.6, button 1), collar D44 x 22, tube D32 centred. Two printed parts + TPU button + 3 acrylic rods.

### 3D model of the stake (rev B)

| File | What |
|---|---|
| `cad/stl/gaiapus-revB-base.stl`, `-lid.stl`, `-button.stl`, `-tip.stl` | printable closed meshes, already in print orientation (lid top-down, tip sleeve-down) |
| `cad/gaiapus-stake-revB-assembly.glb` | full stake: case + both boards (from `hardware/*/*.glb`) + 18650 + tube (translucent) + tip + panel + antenna + soil line. Opens in Windows 3D Viewer, Blender, https://gltf-viewer.donmccurdy.com |
| `cad/preview/*.png` | head, section at x = -3.4, whole stake |
| `tools/solid/` | generators (`build_parts.py`, `assemble.py`, `interference.py`); need `pip install scikit-image` |

Interference check (3D): no PCB part, the PCB or the cell touches case material; base/lid/button overlap 0 mm3; closest = button pin 0.3 mm above SW1 (by design).

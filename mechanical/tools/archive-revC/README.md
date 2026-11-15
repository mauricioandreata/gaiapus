# Case rev C tools (shaped after renders/design-base-v1.jpg)

Single source of geometry: `params.py` (numbers) + `parts.py` (solids as signed-distance functions).
Needs Python 3 with `numpy`, `scikit-image`, `matplotlib`, `pillow` (`pip install scikit-image matplotlib pillow`).

| Script | Does |
|---|---|
| `build_parts.py OUT [--stl]` | printable 3MF (and STL) of base, lid, button, plunger, light bar, tip, in print orientation |
| `assemble.py OUT.glb [voxel] [--opaque]` | full stake with the KiCad .glb boards, cell, tube, tip, panel, antenna |
| `checks.py` | 21 geometric / clearance checks |
| `interference.py` | 3D check: every head-PCB part, the PCB, the cell and the probe vs the solids; overlaps between solids |
| `views_cache.py GLB cache` + `drawings_revc.py OUT` | drawing set: shaded ortho views + exact sections cut from the solids |
| `preview.py` | z-buffer renderer used for all images |

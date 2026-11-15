# Solid models (rev B)

Closed meshes made from signed-distance functions of the same numbers as `../params.py`, then marching cubes.
Needs `numpy` and `scikit-image` (`pip install scikit-image`).

| Script | Output |
|---|---|
| `build_parts.py OUT` | `gaiapus-revB-base/lid/button/tip.stl` (voxel 0.3 / 0.3 / 0.12 / 0.25 mm), print orientation |
| `assemble.py OUT.glb` | full stake: case + `hardware/*/*.glb` boards + cell, tube, tip, panel, antenna, soil line |
| `interference.py` | min distance of every PCB part / the cell to case material, and part overlaps |
| `preview.py` | z-buffer render of any .glb (for quick checks) |

Faceting of the voxel method is <= half a voxel (0.15 mm on base and lid): below FDM tolerance.

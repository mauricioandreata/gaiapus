set -e
export GAIAPUS_REPO=/mnt/user-data/uploads/gaiapus
mkdir -p out cache
python3 assemble.py out/gaiapus-stake-revG-assembly.glb 0.5
python3 assemble.py /tmp/g_opaque.glb 0.5 --opaque
python3 assemble.py /tmp/g_head.glb 0.5 --opaque --no-gauge
python3 - <<'PY'
from preview import read, render
from PIL import Image, ImageDraw, ImageFont
T = read("/tmp/g_opaque.glb"); X = read("out/gaiapus-stake-revG-assembly.glb")
case = [it for it in T if it[0][:, :, 2].min() > 0.05]
head = [it for it in case if it[0][:, :, 1].min() > -0.11]
render(head, "out/render-head-front-right.png", az=40, el=22, res=1400)
render(head, "out/render-head-front-left.png", az=-35, el=18, res=1400)
render(head, "out/render-head-rear.png", az=150, el=18, res=1100)
render(case, "out/render-stake.png", az=35, el=12, res=1800)
render(head, "out/render-head-gauge-front.png", az=20, el=20, res=1600)
render(head, "out/render-head-gauge-left.png", az=-60, el=25, res=1500)
gauge_sec = [it for it in X if it[0][:, :, 1].min() > -0.11]
render(gauge_sec, "out/render-section-gauge.png", az=0, el=3, res=1600, cutz=(-9.5 + 125) / 1000)
sec = [it for it in X if it[0][:, :, 1].min() > -0.11 and it[1][3] == 1]
render(sec, "out/render-section-x0.png", az=90, el=5, res=1400, cut=0.145)
d = Image.open("/mnt/user-data/uploads/gaiapus/renders/design-base-v1.jpg").convert("RGB"); W, H = d.size
tiles = [d.crop((int(W * .5), 0, W, H)), Image.open("out/render-head-gauge-front.png").convert("RGB"), d.crop((0, 0, int(W * .5) - 8, H)), Image.open("out/render-stake.png").convert("RGB")]
fit = lambda im, h: im.resize((int(im.width * h / im.height), h), Image.LANCZOS); h = 900
tiles = [fit(t, h) for t in tiles]; pad = 30
out = Image.new("RGB", (sum(t.width for t in tiles) + pad * 5 + 60, h + 110), "white"); dr = ImageDraw.Draw(out); font = ImageFont.truetype("DejaVuSans-Bold.ttf", 32); x = pad
for t, lab in zip(tiles, ["design-base-v1", "rev G", "design-base-v1", "rev G"]):
    out.paste(t, (x, 90)); dr.text((x + 10, 30), lab, fill=(30, 30, 30), font=font); x += t.width + pad
out.save("out/compare-design-vs-revG.png")
PY
python3 views_cache.py /tmp/g_head.glb cache
python3 checks.py > out/checks.txt
python3 interference.py > out/interference.txt
cp out_interf_rg.txt out/interference-raingauge.txt
python3 drawings_revg.py out/drawings
cd out/drawings && pdftoppm -r 110 -png gaiapus-case-revG.pdf sheet && cd ../..
python3 build_parts.py out
echo ALLDONE

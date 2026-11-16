"""
참고 그림(시안 이미지)을 16x16 아이콘으로 줄인다: 칸마다 가운데 픽셀들의 중앙값 색을 고르고,
바질(짙은 올리브)·토마토(빨강)·치즈(밝은 노랑) 칸은 따로 살리며, 나머지는 대표색 8개로 정리한 뒤 따뜻한 외곽선을 두른다.
(피자 아이콘 tools/cooking/art/pizza.png 를 이 도구로 만들었다. 다른 그림에 쓰려면 x0~y1 범위·색 판별을 맞춘다)

사용: python3 -I tools/cooking/downsample_icon.py <참고 그림> <출력.png> <칸 가로> <칸 세로> <x 시작> <y 시작>
  예: ... 시안.png art/pizza.png 14 10 1 3
"""
import sys, os, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "hud"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import png
from food_kit import dark_outline, blank
src = png.read(sys.argv[1])
cols, rows, ox, oy = int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])
x0, x1, y0, y1 = 58, 508, 61, 383                                  # 시안 속 피자 범위 (픽셀)
cells = []
for gy in range(rows):
    line = []
    for gx in range(cols):
        ax, bx = x0 + gx * (x1 - x0) / cols, x0 + (gx + 1) * (x1 - x0) / cols
        ay, by = y0 + gy * (y1 - y0) / rows, y0 + (gy + 1) * (y1 - y0) / rows
        px = [src[int(y)][int(x)][:3] for y in [ay + (by - ay) * (0.15 + 0.7 * i / 6) for i in range(7)]
              for x in [ax + (bx - ax) * (0.15 + 0.7 * j / 6) for j in range(7)]]
        bright = [p for p in px if p[0] > 60 or p[1] > 55]                      # 배경(아주 어두운 갈색) 제외
        if len(bright) < len(px) * 0.5:
            line.append(None); continue
        green = [p for p in bright if p[1] > 55 and p[1] >= p[0] * 0.78 and p[0] < 135 and p[2] < p[1] * 0.6]   # 짙은 올리브 = 바질
        red = [p for p in bright if p[0] > 160 and p[1] < 95]
        cheese = [p for p in bright if p[0] > 225 and p[1] > 185]
        if len(green) > len(bright) * 0.25:
            line.append(("G", green)); continue
        if len(cheese) > len(bright) * 0.4:
            line.append(("C", cheese)); continue
        if len(red) > len(bright) * 0.45:
            line.append(("R", red)); continue
        line.append(("B", bright))
    cells.append(line)
def median(ps):
    ps = sorted(ps, key=lambda p: p[0] + p[1] + p[2])
    return ps[len(ps) // 2]
# 종류별 대표색 (바탕은 k-평균 8색)
base_pts = [median(c[1]) for line in cells for c in line if c and c[0] == "B"]
random.seed(2)
cent = random.sample(base_pts, 8)
for _ in range(30):
    groups = [[] for _ in cent]
    for p in base_pts:
        groups[min(range(len(cent)), key=lambda k: sum((p[d] - cent[k][d]) ** 2 for d in range(3)))].append(p)
    cent = [tuple(sum(p[d] for p in g) // len(g) for d in range(3)) if g else cent[i] for i, g in enumerate(groups)]
img = blank(16)
for gy, line in enumerate(cells):
    for gx, c in enumerate(line):
        if not c:
            continue
        kind, ps = c
        m = median(ps)
        if kind == "G":
            q = (70, 150, 52) if m[1] > 72 else (48, 118, 40)
        elif kind == "C":
            q = (255, 240, 186) if m[1] > 215 else (252, 222, 136)
        elif kind == "R":
            q = (214, 62, 40) if m[0] > 200 else (170, 42, 30)
        else:
            q = min(cent, key=lambda cc: sum((m[d] - cc[d]) ** 2 for d in range(3)))
            mean = sum(q) / 3
            q = tuple(max(0, min(255, int(mean + (v - mean) * 1.2 + 8))) for v in q)
        img[gy + oy][gx + ox] = q + (255,)
img = dark_outline(img)
png.write(sys.argv[2], img)
sheet = png.blank(18, 18)
png.paste(sheet, img, 1, 1)
png.write(sys.argv[2].replace(".png", "_x16.png"), png.scale(sheet, 16))

"""
참고 그림(시안 이미지) 속 물체를 그대로 16x16 아이콘으로 줄인다.

- 물체 범위(x0 y0 x1 y1)의 긴 변을 14칸에 맞추고 16x16 가운데에 놓는다 (가장자리 1칸은 외곽선 자리).
- 칸마다 가운데 70% 픽셀 중 배경(아주 어두운 색)이 아닌 것의 중앙값 색을 고른다. 절반 넘게 배경이면 투명.
- 색을 대표색 N개로 묶어(k-평균) 픽셀 그림답게 정리하고, 따뜻한 짙은 외곽선을 두른다.

사용: python3 -I tools/cooking/shrink_icon.py <참고 그림> <출력.png> <x0> <y0> <x1> <y1> [대표색 수=14]
"""
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "hud"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import png  # noqa: E402
from food_kit import dark_outline, blank  # noqa: E402

BG_SUM = 120      # 이보다 어두우면 배경


def shrink(src, box, colors=14, cells=14):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    cw = max(w, h) / cells
    nx, ny = max(1, round(w / cw)), max(1, round(h / cw))
    ox, oy = (16 - nx) // 2, (16 - ny) // 2
    grid = {}
    for gy in range(ny):
        for gx in range(nx):
            ax, ay = x0 + gx * w / nx, y0 + gy * h / ny
            bx, by = x0 + (gx + 1) * w / nx, y0 + (gy + 1) * h / ny
            px = [src[int(ay + (by - ay) * (0.15 + 0.7 * i / 6))][int(ax + (bx - ax) * (0.15 + 0.7 * j / 6))][:3]
                  for i in range(7) for j in range(7)]
            fg = [p for p in px if sum(p) > BG_SUM]
            if len(fg) < len(px) * 0.5:
                continue
            fg.sort(key=sum)
            grid[(gx + ox, gy + oy)] = fg[len(fg) // 2]
    # 대표색으로 묶기
    pts = list(grid.values())
    rnd = random.Random(3)
    cent = rnd.sample(pts, min(colors, len(pts)))
    for _ in range(30):
        groups = [[] for _ in cent]
        for p in pts:
            groups[min(range(len(cent)), key=lambda k: sum((p[d] - cent[k][d]) ** 2 for d in range(3)))].append(p)
        cent = [tuple(sum(p[d] for p in g) // len(g) for d in range(3)) if g else cent[i] for i, g in enumerate(groups)]
    img = blank(16)
    for (x, y), c in grid.items():
        q = min(cent, key=lambda cc: sum((c[d] - cc[d]) ** 2 for d in range(3)))
        mean = sum(q) / 3
        q = tuple(max(0, min(255, int(mean + (v - mean) * 1.12 + 4))) for v in q)       # 작은 크기에서 또렷하게
        img[y][x] = q + (255,)
    return dark_outline(img)


if __name__ == "__main__":
    src = png.read(sys.argv[1])
    box = tuple(int(v) for v in sys.argv[3:7])
    colors = int(sys.argv[7]) if len(sys.argv) > 7 else 14
    img = shrink(src, box, colors)
    png.write(sys.argv[2], img)
    print("ok", sys.argv[2])

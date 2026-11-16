"""
강화석 시안(art/stones_concept*.png, 왼쪽부터 하급·중급·상급)을 그대로 NxN(기본 32) 아이템 아이콘으로 줄인다.
- 세 강화석에 같은 배율을 쓴다 (상급이 외곽선 포함 N칸에 맞도록) → 시안의 크기 비율을 그대로 유지.
- 칸마다 가운데 70% 픽셀 중 배경(아주 어두운 색)이 아닌 것의 중앙값 색. 절반 넘게 배경이면 투명.
- 물체 범위의 가운데를 캔버스 가운데에 놓고, 원본 아이콘과 같은 짙은 외곽선을 두른다.

사용: python3 tools/hud/shrink_stones.py <시안.png> <출력 폴더> [N=32]
"""
import os
import sys

from PIL import Image

BG_SUM = 120
O = (48, 26, 14, 255)
N = int(sys.argv[3]) if len(sys.argv) > 3 else 32


def bbox(px, x0, x1, h):
    xs, ys = [], []
    for x in range(x0, x1):
        for y in range(h):
            if sum(px[x, y]) > BG_SUM:
                xs.append(x)
                ys.append(y)
    return min(xs), min(ys), max(xs) + 1, max(ys) + 1


def shrink(px, box, cell):
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    out = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    for gy in range(N):
        for gx in range(N):
            sx, sy = cx + (gx - N / 2) * cell, cy + (gy - N / 2) * cell
            pts = [px[int(sx + cell * (0.15 + 0.7 * i / 4)), int(sy + cell * (0.15 + 0.7 * j / 4))]
                   for i in range(5) for j in range(5)]
            solid = sorted((p for p in pts if sum(p) > BG_SUM), key=sum)
            if len(solid) * 2 > len(pts):
                out.putpixel((gx, gy), solid[len(solid) // 2] + (255,))
    filled = {(x, y) for y in range(N) for x in range(N) if out.getpixel((x, y))[3]}
    for y in range(N):                                   # 외곽선 (칠하기 전 모양 기준)
        for x in range(N):
            if (x, y) not in filled and any((x + i, y + j) in filled
                    for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out.putpixel((x, y), O)
    return out


if __name__ == "__main__":
    src = Image.open(sys.argv[1]).convert("RGB")
    px = src.load()
    w, h = src.size
    boxes = [bbox(px, a, b, h) for a, b in ((0, w * 37 // 100), (w * 37 // 100, w * 56 // 100), (w * 56 // 100, w))]
    hi = boxes[2]
    cell = max(hi[2] - hi[0], hi[3] - hi[1]) / (N - 2)  # 상급이 외곽선 포함 N칸
    os.makedirs(sys.argv[2], exist_ok=True)
    for kind, box in zip(("low", "mid", "high"), boxes):
        shrink(px, box, cell).save(os.path.join(sys.argv[2], "stone_icon_%s.png" % kind))
        print(kind, box)

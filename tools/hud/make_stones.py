"""
강화석 아이콘 (사용자 시안 art/stones_concept2.png 를 바닐라 픽셀 크기로 옮겨 그린 픽셀 그림).
다른 GUI·HUD 와 같은 밀도(1칸 = 1픽셀)로 그린다. 모양은 가운데 기준 도형이라 상하좌우 대칭.
  하급: 회색 돌 마름모 + 주황 핵 + 네 방향 황동 징
  중급: 황동 톱니 고리 + 주황 구슬 + 네 방향 징
  상급: 붉은 구슬 + 황동 고리 + 네 방향 보석 끝 + 별빛
크기: 아래 등급은 바로 위 등급의 약 80% (외곽선 포함).
  아이템 칸(16x16 캔버스): 상급 16 · 중급 13 · 하급 11
  사이드바(9x9 캔버스): 상급 9 · 중급 8 · 하급 6 (하급·중급은 사용자 요청으로 1픽셀씩 키움)

사용: python3 -I tools/hud/make_stones.py <textures/item 폴더> <textures/font/hud 폴더> [미리보기 png]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import png  # noqa: E402

T = (0, 0, 0, 0)
O = (40, 21, 21, 255)                                     # 외곽선 (옛 HUD 보석과 같은 색)
BRASS_HI, BRASS, BRASS_LO = (250, 206, 120, 255), (224, 164, 77, 255), (150, 92, 34, 255)
STONE_HI, STONE, STONE_LO = (150, 140, 130, 255), (116, 106, 98, 255), (82, 74, 68, 255)
CORE_HI, CORE, CORE_MID, CORE_LO = (255, 244, 170, 255), (255, 196, 60, 255), (242, 128, 28, 255), (178, 68, 14, 255)
RED_HI, RED, RED_LO = (255, 170, 120, 255), (226, 44, 30, 255), (150, 22, 18, 255)
STAR = (255, 236, 140, 255)


def canvas(n):
    return [[T] * n for _ in range(n)]


def place(dst, src):
    """src(정사각)를 dst 가운데에 놓는다"""
    off = (len(dst) - len(src)) // 2
    for y, row in enumerate(src):
        for x, c in enumerate(row):
            if c[3]:
                dst[y + off][x + off] = c
    return dst


def outline(img):
    n = len(img)
    out = [r[:] for r in img]
    for y in range(n):
        for x in range(n):
            if not img[y][x][3] and any(0 <= x + dx < n and 0 <= y + dy < n and img[y + dy][x + dx][3]
                                        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out[y][x] = O
    return out


def shape(n, paint):
    """n x n (외곽선 1칸 포함). paint(dx, dy, r) → 색 또는 None. dx, dy 는 가운데로부터 거리(칸), r = 안쪽 반지름"""
    img = canvas(n)
    c = (n - 1) / 2
    r = (n - 2) / 2                                          # 외곽선 자리를 뺀 반지름
    for y in range(1, n - 1):
        for x in range(1, n - 1):
            col = paint(x - c, y - c, r)
            if col:
                img[y][x] = col
    return outline(img)


def tip(dx, dy, r, length=1.0):
    """네 방향 끝 (가운데 줄에서 끝으로부터 length 칸)"""
    return (abs(dx) < 0.6 and abs(dy) > r - length) or (abs(dy) < 0.6 and abs(dx) > r - length)


def low(n):
    def paint(dx, dy, r):
        d = abs(dx) + abs(dy)
        if d > r + 0.01:
            return None
        if tip(dx, dy, r, 1.0) and r >= 3:
            return BRASS if (dx + dy) < 0 else BRASS_LO                     # 네 방향 징 (끝 1칸)
        core = r * 0.5
        if d <= core + 0.01:
            return CORE_HI if d < 0.6 else (CORE if (dx + dy) <= 0 else CORE_MID)   # 주황 핵
        return STONE_HI if (dx + dy) < -0.5 else (STONE_LO if (dx + dy) > 0.5 else STONE)   # 회색 돌
    return shape(n, paint)


def mid(n):
    def paint(dx, dy, r):
        d = math.hypot(dx, dy)
        if tip(dx, dy, r + 0.2, 1.0) and r >= 3:
            return BRASS_HI if (dx + dy) < 0 else BRASS                       # 네 방향 징
        if d > r - 0.7:
            tooth = abs(abs(dx) - abs(dy)) < 0.7 and d <= r + 0.3 and r >= 4  # 대각선 톱니
            return (BRASS_LO if (dx + dy) > 0 else BRASS) if tooth else None
        if d > r - (1.7 if r >= 4 else 1.0):
            return BRASS_HI if (dx + dy) < 0 else BRASS_LO                    # 황동 고리 (작은 크기는 더 얇게)
        if dx < 0 and dy < 0 and 0.3 < d < r * 0.5:
            return CORE_HI                                                     # 구슬 반사광
        return CORE if (dx + dy) < 0.5 else (CORE_MID if (dx + dy) < r * 0.6 else CORE_LO)
    return shape(n, paint)


def high(n):
    def paint(dx, dy, r):
        d = math.hypot(dx, dy)
        if r < 4:                                                          # 작은 크기(사이드바): 가장자리 1칸만 황동, 안은 붉은 구슬
            if tip(dx, dy, r, 0.9):
                return BRASS_HI if (dx + dy) < 0 else BRASS
            if d > r - 0.4:
                return None
            if d > r - 1.2:
                return BRASS_HI if (dx + dy) < 0 else BRASS_LO
            if abs(dx) < 0.6 and abs(dy) < 0.6:
                return STAR
            return RED_HI if (dx < 0 and dy < 0) else (RED if (dx + dy) < 1 else RED_LO)
        reach = r * 0.74                                                   # 붉은 구슬을 크게 (붉은 부분이 많이 보이게)
        if ((abs(dx) <= max(0.5, (r - abs(dy)) * 0.45) and abs(dy) > reach) or
                (abs(dy) <= max(0.5, (r - abs(dx)) * 0.45) and abs(dx) > reach)) and max(abs(dx), abs(dy)) <= r + 0.01:
            inner = r >= 5 and ((abs(dx) < 0.6 and reach < abs(dy) < r - 0.9) or (abs(dy) < 0.6 and reach < abs(dx) < r - 0.9))
            return RED if inner else (BRASS_HI if (dx + dy) < 0 else BRASS)  # 네 방향 보석 끝
        if d > reach + 0.5:
            return None
        if d > reach - 0.6:
            return BRASS_HI if (dx + dy) < 0 else BRASS_LO                    # 황동 고리 (1칸)
        if (abs(dx) < 0.6 and abs(dy) < r * 0.22) or (abs(dy) < 0.6 and abs(dx) < r * 0.22):
            return STAR                                                        # 가운데 별빛 (작게)
        if dx < 0 and dy < 0 and d < reach * 0.7:
            return RED_HI
        return RED if (dx + dy) < r * 0.3 else RED_LO
    return shape(n, paint)


ITEM = {"low": (low, 11), "mid": (mid, 13), "high": (high, 16)}
SIDEBAR = {"low": (low, 6), "mid": (mid, 8), "high": (high, 9)}


def build():
    item = {k: place(canvas(16), f(n)) for k, (f, n) in ITEM.items()}
    side = {k: place(canvas(9), f(n)) for k, (f, n) in SIDEBAR.items()}
    return item, side


if __name__ == "__main__":
    item, side = build()
    item_dir, font_dir = sys.argv[1], sys.argv[2]
    for k in ITEM:
        png.write(os.path.join(item_dir, "stone_icon_%s.png" % k), item[k])
        png.write(os.path.join(font_dir, "gem_%s.png" % k), side[k])
    if len(sys.argv) > 3:                                    # 미리보기: 아이템 12배 / 사이드바 21배
        sheet = [[(24, 26, 30, 255)] * (3 * 212) for _ in range(2 * 212 + 10)]
        for i, k in enumerate(("low", "mid", "high")):
            png.paste(sheet, png.scale(item[k], 12), i * 212 + 10, 10)
            png.paste(sheet, png.scale(side[k], 21), i * 212 + 12, 222)
        png.write(sys.argv[3], sheet)
    print("ok")

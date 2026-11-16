"""
강화석 아이템 아이콘 16x16 (지금 32x32 아이콘 art/stone_icon_*.png 를 16x16 으로 다시 그린 것).
  생김새(윤곽·부품 배치)는 가운데 기준 완전 대칭 — 영역은 (|dx|, |dy|) 의 대칭 함수로만 정한다.
  빛·그림자는 대칭이 아니다 — 왼쪽 위 광원으로 부품마다 면 방향을 따져 칠한다.
    보석·구슬: 둥근 면 + 왼쪽 위 반사광 + 오른쪽 아래 굴절광(보석 안으로 들어온 빛)
    회색 돌: 깎인 네 면 (왼쪽 위 면이 가장 밝음)
    황동 고리·징: 도톰한 테 (바깥 왼쪽 위·안쪽 오른쪽 아래가 밝음)
  색은 지금 아이콘에 쓰인 색만 쓴다 (아래 단계표는 모두 원본 색, 어두운 → 밝은 순).
  크기(외곽선 포함): 하급 12 · 중급 14 · 상급 16

사용: python3 tools/hud/retouch_stones.py <출력 폴더>
"""
import math
import os
import sys

from PIL import Image

O = (48, 26, 14, 255)                                   # 원본 외곽선
LIGHT = (-0.55, -0.65, 0.52)                            # 왼쪽 위 앞에서 오는 빛

PAL = {
    "low": {
        "stone": [(70, 46, 39), (87, 56, 48), (109, 69, 56), (130, 87, 71), (148, 103, 84), (176, 126, 103)],
        "gem": [(130, 50, 13), (198, 90, 10), (255, 93, 0), (255, 157, 8), (255, 200, 69), (255, 228, 131)],
        "metal": [(130, 50, 13), (162, 73, 19), (219, 116, 22), (255, 157, 8), (255, 200, 69)],
        "sep": (77, 43, 32),
    },
    "mid": {
        "gem": [(191, 34, 0), (239, 47, 0), (255, 93, 0), (255, 154, 0), (255, 196, 80), (255, 224, 152)],
        "metal": [(130, 44, 4), (157, 63, 6), (187, 79, 8), (207, 102, 20), (230, 126, 24), (250, 165, 44),
                  (255, 196, 80), (255, 224, 152)],
        "sep": (130, 44, 4),
    },
    "high": {
        "gem": [(154, 4, 2), (191, 3, 0), (232, 9, 0), (255, 22, 0), (253, 61, 46), (255, 176, 107), (255, 226, 145)],
        "metal": [(129, 53, 9), (156, 60, 2), (189, 83, 9), (226, 108, 9), (248, 136, 18), (251, 160, 49),
                  (255, 204, 74), (255, 226, 145)],
        "sep": (129, 53, 9),
    },
}


def norm(v):
    n = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / n for c in v)


L = norm(LIGHT)


def diffuse(n):
    return max(0.0, sum(a * b for a, b in zip(norm(n), L)))


def pick(ramp, v):
    v = min(0.999, max(0.0, v))
    return ramp[int(v * len(ramp))] + (255,)


# ── 면 방향 (dx, dy 는 부품 중심 기준, 화면 아래가 +y) ──
def dome(dx, dy, r):
    t = min(0.95, math.hypot(dx, dy) / r)
    return (dx / r, dy / r, math.sqrt(1 - t * t))


def gem(ramp, dx, dy, r, spec=True):
    """둥근 보석: 확산광 + 왼쪽 위 반사광 + 오른쪽 아래 가장자리 굴절광"""
    n = dome(dx, dy, r)
    v = 0.15 + 0.75 * diffuse(n)
    rim = (dx + dy) / (r * 1.41)
    if rim > 0.45 and math.hypot(dx, dy) > r * 0.55:     # 오른쪽 아래 안쪽 굴절광
        v += 0.35
    if spec and -0.75 * r < dx < -0.1 * r and -0.75 * r < dy < -0.1 * r and math.hypot(dx + r * 0.42, dy + r * 0.42) < r * 0.3:
        v = 1.0                                           # 반사광
    return pick(ramp, v)


def facet(ramp, dx, dy):
    """깎인 네 면 (피라미드)"""
    n = (0.8 * (1 if dx > 0 else -1), 0.8 * (1 if dy > 0 else -1), 1.0)
    return pick(ramp, 0.05 + 1.0 * diffuse(n))


def torus(ramp, dx, dy, rc, w):
    """도톰한 테: 단면이 반원인 고리 (rc 중심 반지름, w 반폭)"""
    d = math.hypot(dx, dy) or 1e-6
    t = max(-0.95, min(0.95, (d - rc) / w))
    n = (dx / d * t, dy / d * t, math.sqrt(1 - t * t))
    return pick(ramp, 0.1 + 0.9 * diffuse(n))


def bevel(ramp, dx, dy, hw):
    """도톰한 판 (징·보석 받침): 가장자리만 기울어짐"""
    tx = max(-0.9, min(0.9, dx / hw)) if abs(dx) > hw * 0.45 else 0.0
    ty = max(-0.9, min(0.9, dy / hw)) if abs(dy) > hw * 0.45 else 0.0
    return pick(ramp, 0.1 + 0.9 * diffuse((tx, ty, 1.0)))


# ── 생김새: (a, b) = (|dx|, |dy|) 만 보고 영역을 정한다 (a, b 를 바꿔도 같은 결과 → 8방향 대칭) ──
def region(kind, a, b):
    d = math.hypot(a, b)
    lo, hi = min(a, b), max(a, b)                         # lo: 가로/세로 축에서 떨어진 정도, hi: 축 방향 거리
    if kind == "low":
        m = a + b
        if lo < 1 and 3 < hi < 5:
            return "stud"                                 # 네 방향 끝 징 (2x2)
        if m <= 2:
            return "core"
        if m <= 3:
            return "sep"
        if m <= 5:
            return "stone"
        return None
    if kind == "mid":
        if lo < 1 and 5.5 < hi < 7:
            return "stud"                                 # 네 방향 징 (2x2, 고리 밖으로)
        if lo < 1 and 4.5 < hi < 5.5:
            return "gap"                                  # 징과 고리 사이 짙은 틈
        if abs(a - b) < 1 and 4 < lo < 5:
            return "tooth"                                # 대각선 톱니
        if d <= 3.0:
            return "core"
        if d <= 3.9:
            return "sep"
        if d <= 5.4:
            return "ring"
        return None
    if kind == "high":
        if lo < 1 and 4.5 < hi < 7:
            return "tipgem"                               # 네 방향 붉은 보석 (2x2)
        if lo < 2 and 4.5 < hi < 8 and lo <= 8 - hi:      # 보석을 감싼 황동 받침 (끝이 뾰족)
            return "tip"
        if abs(a - b) < 1 and 4 < lo < 5:
            return "tooth"                                # 대각선 장식 끝
        if d <= 3.6:
            return "core"
        if d <= 4.3:
            return "sep"
        if d <= 5.8:
            return "ring"
        return None


def render(kind):
    pal = PAL[kind]
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    grid = {}
    for y in range(16):
        for x in range(16):
            dx, dy = x - 7.5, y - 7.5
            a, b = abs(dx) + 0.0, abs(dy) + 0.0
            grid[x, y] = region(kind, a, b)
    for (x, y), r in grid.items():
        if not r:
            continue
        dx, dy = x - 7.5, y - 7.5
        if r == "core":
            col = gem(pal["gem"], dx, dy, {"low": 2.2, "mid": 3.6, "high": 4.0}[kind])
        elif r in ("sep", "gap"):
            col = pal["sep"] + (255,)
        elif r == "stone":
            col = facet(pal["stone"], dx, dy)
        elif r == "ring":
            rc = {"mid": 4.65, "high": 5.05}[kind]
            col = torus(pal["metal"], dx, dy, rc, 1.0)
        elif r == "stud":                                 # 징 중심 기준 도톰한 판
            cx = 0 if abs(dx) < 1 else (1 if dx > 0 else -1) * (4 if kind == "low" else 6.5)
            cy = 0 if abs(dy) < 1 else (1 if dy > 0 else -1) * (4 if kind == "low" else 6.5)
            col = bevel(pal["metal"], dx - cx, dy - cy, 1.0)
        elif r == "tooth":
            col = bevel(pal["metal"], dx - math.copysign(4.5, dx), dy - math.copysign(4.5, dy), 1.0)
        elif r in ("tip", "tipgem"):
            ax_x = abs(dx) > abs(dy)                       # 받침이 놓인 축
            cx = math.copysign(5.5, dx) if ax_x else 0.0
            cy = 0.0 if ax_x else math.copysign(5.5, dy)
            col = gem(pal["gem"], dx - cx, dy - cy, 1.4, spec=False) if r == "tipgem" else \
                bevel(pal["metal"], dx - cx, dy - cy, 1.8)
        img.putpixel((x, y), col)
    for y in range(16):                                   # 외곽선 (원본 색)
        for x in range(16):
            if not grid[x, y] and any(grid.get((x + i, y + j)) for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                img.putpixel((x, y), O)
    return img


if __name__ == "__main__":
    out_dir = sys.argv[1]
    os.makedirs(out_dir, exist_ok=True)
    for kind in ("low", "mid", "high"):
        render(kind).save(os.path.join(out_dir, "stone_icon_%s.png" % kind))
    print("ok")

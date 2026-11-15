"""
증폭 공작대 (Enhancement Forge) 모델 — 시안 2026-11-15. 2블록 폭 x 2블록 높이, 앞면 = north. 공용 재질은 machine_kit.py.

- 작업대: 리벳 박힌 황동 상판 + 앞 테두리 철띠, 철판 앞치마, 다리 4개(황동 발·머리 마개), 아래 가로대
- 강화 대: 상판 가운데 팔각 받침 + 빛나는 톱니 문양 판
- 앞 깃발: 상판 앞에 걸린 빨간 천(톱니 문양, 제비꼬리 끝)
- 아치: 좌우 황동 기둥 + 가로대 + 이음쇠, 가운데 피스톤 함 → 에너지 코어(랜턴: 마개·철창·빛나는 결정·뾰족한 끝)
- 오른쪽: 빛나는 유리 탱크(받침·띠·뚜껑) + 피스톤 함에서 꺾여 내려오는 파이프, 뒤로 기운 조작 패널(칼 그림)
- 왼쪽: 책 3권 더미, 깃대와 깃발

좌표는 "플레이어가 정면에서 본 모습" 기준(vx: 왼쪽 -8 → 오른쪽 24)으로 적고, 모델 x로 바꿀 때 좌우를 뒤집는다.
(모델 앞면 north를 정면에서 보면 모델 x가 오른쪽→왼쪽으로 커지기 때문)

사용: python3 -I tools/machines/make_enhancement_machine.py <ItemsAdder rustport resourcepack/assets/rustport>
  → textures/machine/enhancement_machine.png, models/machine/enhancement_machine.json
  PREVIEW=<png> 를 주면 정면·옆면 합성 미리보기를 그린다.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from machine_kit import *  # noqa: E402,F401,F403
import machine_kit  # noqa: E402

random.seed(53)

# ═════════════ 전용 그림 ═════════════
EMBER = [rgb(255, 248, 210), rgb(255, 210, 110), rgb(250, 150, 44), rgb(196, 90, 24), rgb(70, 40, 26)]


def rune_fn(x, y):
    """강화 대 윗면 (32x32): 어두운 판 위에 빛나는 톱니 고리와 가운데 원"""
    c = 15.5
    dx, dy = x - c, y - c
    r = math.hypot(dx, dy)
    ang = math.atan2(dy, dx)
    tooth = math.cos(ang * 8) > 0.35
    if r <= 3.2:
        return EMBER[0]
    if r <= 5:
        return EMBER[3]
    if r <= 8.5:
        return EMBER[1] if r <= 7 else EMBER[2]
    if r <= 10.5 and tooth:
        return EMBER[2]
    if 12.5 <= r <= 13.6:
        return EMBER[2]                        # 바깥 고리
    return rgb(58, 40, 30) if (x + y) % 3 else rgb(66, 46, 34)


RUNE_M = region(32, 32, rune_fn)

CLOTH = [rgb(176, 64, 48), rgb(150, 48, 36), rgb(120, 36, 28), rgb(92, 26, 20)]
EMBLEM = [rgb(232, 196, 140), rgb(196, 150, 96)]


def banner_fn(w, h, gear_cy):
    def fn(x, y):
        # 제비꼬리 끝: 아래 4줄에서 가운데를 V자로 비운다
        tail = h - y
        if tail <= 4 and abs(x - (w - 1) / 2) < (5 - tail) * (w / 10):
            return T
        if y <= 1:
            return BRASS[1] if y == 0 else BRASS[3]          # 위 황동 단
        if x in (0, w - 1):
            return CLOTH[3]
        fold = CLOTH[0] if (x // 3) % 2 == 0 else CLOTH[1]  # 세로 주름
        # 톱니 문양
        c = (w - 1) / 2
        dx, dy = x - c, y - gear_cy
        r = math.hypot(dx, dy)
        ang = math.atan2(dy, dx)
        if r <= 1.6:
            return fold
        if r <= 3.4 or (r <= 4.8 and math.cos(ang * 6) > 0.3):
            return EMBLEM[0] if dy < 0.5 else EMBLEM[1]
        return fold
    return fn


BANNER_M = region(20, 30, banner_fn(20, 30, 13))
FLAG_M = region(14, 22, banner_fn(14, 22, 9))


def panel_fn(x, y):
    """조작 패널 (28x20): 황동 테두리 + 어두운 화면 + 빛나는 칼 그림과 줄 3개"""
    if x <= 1 or y <= 1 or x >= 26 or y >= 18:
        return BRASS[1] if (x <= 0 or y <= 0) else BRASS[3]
    sword = {(4 + i, 14 - i) for i in range(9)} | {(5 + i, 14 - i) for i in range(8)}
    if (x, y) in sword or (x, y) in {(5, 11), (4, 10), (8, 15), (7, 16)}:
        return EMBER[1]
    if y in (6, 10, 14) and 15 <= x <= (23 if y != 14 else 20):
        return EMBER[2]
    return rgb(38, 32, 28) if (x + y) % 2 else rgb(44, 36, 30)


PANEL_M = region(28, 20, panel_fn)
TANK_M = region(8, 16, lambda x, y: EMBER[min(4, abs(x * 2 - 7) // 2 + (1 if y < 2 or y > 13 else 0))])
CORE_M = region(4, 8, lambda x, y: EMBER[min(3, abs(x * 2 - 3) // 2 + (1 if y in (0, 7) else 0))])
LENS_M = region(4, 4, lambda x, y: EMBER[2] if 1 <= x <= 2 and 1 <= y <= 2 else rgb(40, 34, 30))
PAGES_M = region(8, 4, lambda x, y: rgb(236, 226, 196) if y % 2 else rgb(206, 194, 162))
BOOK_COVERS = [region(8, 8, lambda x, y, c=c: c if (x + y) % 5 else lerp(c, rgb(0, 0, 0), 0.25))
               for c in (rgb(132, 46, 36), rgb(112, 78, 46), rgb(52, 88, 84))]


# ═════════════ 정면 기준 좌표 → 모델 좌표 ═════════════
def V(frm, to, mat, light=0, faces=None, skip=(), rotation=None):
    """정면에서 본 좌표(vx 왼쪽→오른쪽)로 큐브를 만든다. 모델 x = 16 - vx, 동·서 면은 서로 바뀐다."""
    mfrm = [16 - to[0], frm[1], frm[2]]
    mto = [16 - frm[0], to[1], to[2]]
    swap = {"east": "west", "west": "east"}
    if faces:
        faces = {swap.get(k, k): v for k, v in faces.items()}
    skip = tuple(swap.get(s, s) for s in skip)
    cube(mfrm, mto, mat, light=light, faces=faces, skip=skip)
    if rotation:
        angle, axis, origin = rotation
        machine_kit.elements[-1]["rotation"] = {"angle": angle, "axis": axis,
                                                "origin": [16 - origin[0], origin[1], origin[2]]}


ALL = ("north", "south", "east", "west", "up", "down")

# ═════════════ 작업대 ═════════════
# 다리 4개: 황동 발 + 철 다리 + 황동 머리 마개
for lx in (-7, 20):
    for lz in (1, 12):
        V([lx - 0.4, 0, lz - 0.4], [lx + 3.4, 1.4, lz + 3.4], BRASS_M)
        V([lx, 1.4, lz], [lx + 3, 10.4, lz + 3], IRON_DARK_M)
        V([lx - 0.3, 10.4, lz - 0.3], [lx + 3.3, 12, lz + 3.3], BRASS_M)
# 아래 가로대 (앞뒤·좌우)
V([-4, 3, 7.4], [20, 4.2, 8.6], IRON_M)
for lx in (-6, 21):
    V([lx, 3, 4], [lx + 1.2, 4.2, 12], IRON_M)
# 앞치마(철판) + 모서리 황동 덧판
V([-6.6, 9, 1.6], [22.6, 12, 14.4], IRON_DARK_M)
for cx in (-6.9, 20.1):
    V([cx, 9, 1.3], [cx + 2.8, 12, 2.0], BRASS_M)
# 상판(황동) + 앞 테두리 철띠 + 리벳 + 모서리 마개
V([-7.6, 12, 0.6], [23.6, 14.6, 15.4], BRASS_M)
V([-7.6, 12.6, 0.3], [23.6, 13.8, 0.6], IRON_M)
for rx in range(-6, 24, 3):
    V([rx, 12.9, 0.05], [rx + 0.5, 13.5, 0.3], BRASS_LIGHT_M)
for cx in (-7.8, 21.8):
    for cz in (0.4, 13.6):
        V([cx, 14.6, cz], [cx + 2, 15.2, cz + 2], BRASS_DARK_M)

# ═════════════ 강화 대 (팔각 받침 + 빛나는 톱니 문양) ═════════════
V([2, 14.6, 3], [14, 15.2, 13], IRON_DARK_M)
V([3, 15.2, 4.6], [13, 15.6, 11.4], BRASS_M, light=15, faces={"up": uv_of(RUNE_M)})
V([4.6, 15.2, 3.6], [11.4, 15.6, 12.4], BRASS_M, light=15, faces={"up": uv_of(RUNE_M)})

# ═════════════ 앞 깃발 (상판 앞에 걸림) ═════════════
V([2.6, 12.0, -0.25], [13.4, 12.6, 0.3], BRASS_M)                      # 거는 막대
V([3.2, 3.8, -0.05], [12.8, 12.2, 0.1], IRON_M,
  faces={"north": uv_of(BANNER_M), "south": uv_of(BANNER_M)}, skip=("east", "west", "up", "down"))

# ═════════════ 아치 + 피스톤 함 + 에너지 코어 ═════════════
AZ0, AZ1 = 7, 9
for px in (-3, 17):
    V([px - 0.6, 14.6, AZ0 - 0.6], [px + 2.6, 16.6, AZ1 + 0.6], BRASS_DARK_M)   # 기둥 받침
    V([px, 16.6, AZ0], [px + 2, 27, AZ1], BRASS_M)                              # 기둥
    for by in (19.5, 23.5):
        V([px - 0.2, by, AZ0 - 0.2], [px + 2.2, by + 0.6, AZ1 + 0.2], IRON_DARK_M)  # 철띠
    V([px - 0.5, 26.4, AZ0 - 0.5], [px + 2.5, 29.6, AZ1 + 0.5], BRASS_DARK_M)  # 모서리 이음쇠
V([-1, 27, AZ0], [17, 29, AZ1], BRASS_M)                                       # 가로대
V([5.6, 26.6, 5.6], [10.4, 31.2, 10.4], BRASS_M)                               # 피스톤 함
V([6.6, 28.0, 5.4], [9.4, 30.2, 5.6], IRON_M, light=8, faces={"north": uv_of(LENS_M)})  # 함 앞 렌즈
V([7.5, 23.6, 7.5], [8.5, 26.6, 8.5], IRON_M)                                  # 매단 대
# 코어 랜턴: 위 마개, 철창, 결정, 아래 마개, 뾰족한 끝
V([5.8, 22.2, 5.8], [10.2, 23.6, 10.2], BRASS_M)
for cx in (5.9, 9.6):
    for cz in (5.9, 9.6):
        V([cx, 17.8, cz], [cx + 0.5, 22.2, cz + 0.5], IRON_DARK_M)
V([6.8, 18.0, 6.8], [9.2, 22.0, 9.2], IRON_M, light=15, faces={f: uv_of(CORE_M) for f in ALL})
V([6.2, 17.0, 6.2], [9.8, 17.8, 9.8], BRASS_M)
V([7.4, 16.2, 7.4], [8.6, 17.0, 8.6], BRASS_DARK_M, light=10,
  faces={f: uv_of(CORE_M, 0, 4, 4, 4) for f in ("north", "south", "east", "west", "down")})

# ═════════════ 오른쪽 탱크 + 파이프 ═════════════
TX0, TX1, TZ0, TZ1 = 18.8, 22.8, 10.0, 14.0
V([TX0 - 0.4, 14.6, TZ0 - 0.4], [TX1 + 0.4, 16.2, TZ1 + 0.4], IRON_DARK_M)     # 받침
V([TX0, 16.2, TZ0], [TX1, 24.0, TZ1], IRON_M, light=15,
  faces={f: uv_of(TANK_M) for f in ("north", "south", "east", "west")})        # 빛나는 유리 탱크
for by in (18.4, 21.6):
    V([TX0 - 0.2, by, TZ0 - 0.2], [TX1 + 0.2, by + 0.5, TZ1 + 0.2], BRASS_M)  # 띠
V([TX0 - 0.4, 24.0, TZ0 - 0.4], [TX1 + 0.4, 25.6, TZ1 + 0.4], IRON_DARK_M)     # 뚜껑
V([TX0 + 1.4, 25.6, TZ0 + 1.4], [TX1 - 1.4, 26.4, TZ1 - 1.4], IRON_M)          # 뚜껑 손잡이
# 파이프: 피스톤 함 오른쪽 → 오른쪽으로 → 뒤로 → 아래로 탱크 뚜껑
PY0, PY1 = 29.4, 30.4
V([10.4, PY0, 7.5], [21.3, PY1, 8.5], BRASS_M)
V([20.3, PY0, 8.5], [21.3, PY1, 12.0], BRASS_M)
V([20.3, 26.4, 11.5], [21.3, PY1, 12.5], BRASS_M)
for jx, jz in ((20.8, 8.0), (20.8, 12.0)):
    V([jx - 0.75, PY0 - 0.25, jz - 0.75], [jx + 0.75, PY1 + 0.25, jz + 0.75], BRASS_DARK_M)  # 꺾이는 이음쇠

# ═════════════ 오른쪽 앞 조작 패널 (뒤로 기울어짐) ═════════════
for sx in (16.2, 20.4):
    V([sx, 14.6, 3.2], [sx + 0.8, 16.8, 4.2], IRON_DARK_M)                    # 받침 다리
V([15.2, 16.4, 2.4], [22.2, 21.4, 3.4], BRASS_M, light=10, faces={"north": uv_of(PANEL_M)},
  rotation=(22.5, "x", [18.7, 16.4, 2.9]))

# ═════════════ 왼쪽: 책 더미 + 깃대와 깃발 ═════════════
for i, (bx0, bx1, by0, bz0, bz1) in enumerate(((-6.4, -1.0, 14.6, 2.2, 7.2), (-6.0, -1.6, 15.8, 2.6, 6.8), (-5.6, -0.8, 17.0, 2.4, 6.6))):
    cover = BOOK_COVERS[i]
    V([bx0, by0, bz0], [bx1, by0 + 1.2, bz1], IRON_M,
      faces={"north": uv_of(cover, 0, 0, 8, 2), "south": uv_of(cover, 0, 0, 8, 2), "up": uv_of(cover), "down": uv_of(cover),
             "east": uv_of(PAGES_M), "west": uv_of(cover, 0, 0, 6, 2)})
# 깃대·깃발은 아치 기둥(vx -3~-1)보다 바깥 왼쪽에 둬서 가리지 않게 한다
V([-7.7, 14.6, 12.4], [-6.7, 31.0, 13.4], BRASS_M)                             # 깃대
V([-8.0, 31.0, 12.1], [-6.4, 32.0, 13.7], BRASS_LIGHT_M)                       # 깃대 꼭지
V([-7.0, 29.4, 12.6], [-3.4, 30.2, 13.2], BRASS_M)                             # 가로 막대
V([-3.8, 29.2, 12.4], [-3.0, 30.4, 13.4], BRASS_DARK_M)                        # 막대 끝 마개
V([-6.7, 21.0, 12.85], [-3.6, 29.4, 12.95], IRON_M,
  faces={"north": uv_of(FLAG_M), "south": uv_of(FLAG_M)}, skip=("east", "west", "up", "down"))

save(sys.argv[1], "enhancement_machine", "BrassField tools/machines/make_enhancement_machine.py", display={
    "gui": {"rotation": [25, 205, 0], "translation": [0, -2, 0], "scale": [0.26, 0.26, 0.26]},
    "ground": {"translation": [0, 2, 0], "scale": [0.2, 0.2, 0.2]},
    "firstperson_righthand": {"rotation": [0, 45, 0], "scale": [0.2, 0.2, 0.2]},
    "thirdperson_righthand": {"rotation": [75, 45, 0], "translation": [0, 2.5, 0], "scale": [0.16, 0.16, 0.16]},
})

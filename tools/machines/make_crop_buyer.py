"""
종자·작물 거래기 (Seed & Crop Trader) 모델 — 시안 2026-11-15. 2블록 폭 x 2블록 높이, 앞면 = north. 공용 재질은 machine_kit.py.

- 위: 아치형 빛나는 간판(새싹) + 양옆 리벳 블록 + 파이프 손잡이, 앞으로 기운 빨강·크림 줄무늬 차양과 물결 테두리
- 왼쪽: 유리 진열장(선반 3단, 씨앗 자루) / 가운데: 열린 선반(밀·당근·감자 나무 상자)
- 오른쪽 기둥: 청록 장바구니 화면, 키패드 2x3, 동전 투입구
- 아래: 황동 계산대 턱, 통풍구 있는 받침, 서랍 손잡이
- 오른쪽 옆: 받침대 파이프에 매단 랜턴(빛남), 큰 톱니, 통으로 내려가는 파이프
- 바닥 소품: 앞 왼쪽 씨앗 자루, 앞 오른쪽 나무 상자, 뒤 오른쪽 나무통

좌표는 정면 기준(vx 왼쪽 -8 → 오른쪽 24, view_cube).

사용: python3 -I tools/machines/make_crop_buyer.py <ItemsAdder rustport resourcepack/assets/rustport>
  → textures/machine/crop_buyer.png, models/machine/crop_buyer.json
  PREVIEW=<png> 를 주면 정면·옆면 합성 미리보기를 그린다.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from machine_kit import *  # noqa: E402,F401,F403

random.seed(67)
V = view_cube
ALL = ("north", "south", "east", "west", "up", "down")
SIDES = ("north", "south", "east", "west")

# ═════════════ 전용 재질·그림 ═════════════
WOOD = [rgb(196, 140, 84), rgb(172, 118, 66), rgb(148, 98, 54), rgb(122, 78, 42), rgb(96, 60, 32)]
BURLAP = [rgb(240, 222, 182), rgb(224, 202, 158), rgb(204, 180, 136), rgb(176, 150, 108)]
SPROUT = [rgb(120, 76, 36), rgb(96, 58, 26)]
STRIPE_RED = [rgb(214, 86, 66), rgb(184, 62, 48), rgb(150, 44, 34)]
STRIPE_CREAM = [rgb(248, 234, 204), rgb(232, 214, 180), rgb(206, 186, 150)]


def wood_fn(x, y):
    # 가로 널빤지: 6px마다 이음매, 결은 가로로 흐르게
    if y % 6 == 5:
        return WOOD[4]
    v = 1 + (1 if (x * 3 + y * 7) % 11 == 0 else 0) + (1 if random.random() < 0.1 else 0)
    return WOOD[min(3, v)]


WOOD_M = region(32, 24, wood_fn)
STAVE_M = region(16, 16, lambda x, y: WOOD[4] if x % 4 == 3 else WOOD[1 + ((x // 4) % 2)])  # 세로 통 널


def crate_fn(x, y):
    # 나무 상자 앞면 (12x10): 진한 테 + 대각 버팀목
    if x in (0, 11) or y in (0, 9):
        return WOOD[3]
    if abs((x - 1) * 8 / 10 - (y - 1)) < 0.9:
        return WOOD[2]
    return WOOD[1] if y % 4 else WOOD[2]


CRATE_M = region(12, 10, crate_fn)
BURLAP_M = region(12, 12, lambda x, y: BURLAP[1 + (x + y) % 2] if (x * y) % 5 else BURLAP[3])


def sack_front_fn(x, y):
    # 씨앗 자루 앞면 (12x12): 삼베 + 새싹 그림
    sprout = {(5, 9), (5, 8), (5, 7), (6, 9), (6, 8), (6, 7), (4, 6), (3, 5), (3, 6), (2, 5), (7, 6), (8, 5), (8, 6), (9, 5), (6, 6), (5, 6)}
    if (x, y) in sprout:
        return SPROUT[0] if y > 6 else SPROUT[1]
    return BURLAP[1 + (x + y) % 2] if (x * y) % 5 else BURLAP[3]


SACK_FRONT_M = region(12, 12, sack_front_fn)

SW, SH = 32, 16   # 간판 발광판 (8 x 4 단위, 4px/단위)


def sign_fn(x, y):
    cx, cy = (SW - 1) / 2, (SH - 1) / 2
    d = max(abs(x - cx) / cx, abs(y - cy) / cy)
    return GLOW[min(3, int(d * 3.6))]


sign = [[sign_fn(x, y) for x in range(SW)] for y in range(SH)]
SPROUT_ICON = ["...LL....LL...",
               "..LLLL..LLLL..",
               ".LLLLLLLLLLLL.",
               "..LLLLLLLLLL..",
               "....LLLLLL....",
               "......SS......",
               "......SS......",
               "......SS......"]
for dy, row in enumerate(SPROUT_ICON):
    for dx, ch in enumerate(row):
        if ch != ".":
            sign[4 + dy][9 + dx] = {"L": rgb(130, 82, 34), "S": rgb(104, 62, 24)}[ch]
SIGN_M = region(SW, SH, lambda x, y: sign[y][x])
SIGN_TOP_M = region(24, 4, lambda x, y: GLOW[min(3, abs(x - 12) // 4 + (1 if y == 3 else 0))])


def awning_fn(x, y):
    # 차양 윗면 (32x16): x 방향 줄무늬, 앞(아래쪽 y)으로 갈수록 살짝 어둡게
    band = STRIPE_RED if (x // 4) % 2 == 0 else STRIPE_CREAM
    return band[0 if y < 5 else (1 if y < 12 else 2)]


AWNING_M = region(32, 16, awning_fn)
AWNING_UNDER_M = region(16, 8, lambda x, y: STRIPE_CREAM[2] if (x // 2) % 2 else STRIPE_RED[2])


def valance_fn(x, y):
    # 물결 테두리 (32x6): 줄무늬 + 아래쪽 반원 물결(투명)
    band = STRIPE_RED if (x // 4) % 2 == 0 else STRIPE_CREAM
    if y >= 3:
        cx = (x // 4) * 4 + 1.5
        if (x - cx) ** 2 + (y - 2.5) ** 2 > 7:
            return T
    return band[1 if y < 4 else 2]


VALANCE_M = region(32, 6, valance_fn)


def cart_fn(x, y):
    # 장바구니 화면 (10x8)
    cart = {(1, 1), (2, 1), (2, 2), (3, 2), (4, 2), (5, 2), (6, 2), (7, 2), (3, 3), (7, 3), (3, 4), (4, 4), (5, 4), (6, 4), (7, 4), (4, 6), (7, 6)}
    if (x, y) in cart:
        return CYAN[0]
    return rgb(22, 56, 62) if (x + y) % 2 else rgb(18, 46, 52)


CART_M = region(10, 8, cart_fn)
SLOT_M = region(4, 6, lambda x, y: DARK[3] if 1 <= x <= 2 and 1 <= y <= 4 else (BRASS[1] if (x + y) % 3 else BRASS[2]))
LAMP_M = region(6, 8, lambda x, y: GLOW[min(3, abs(x * 2 - 5) // 2 + (1 if y in (0, 7) else 0))])
WHEAT_M = region(4, 8, lambda x, y: [rgb(255, 222, 120), rgb(236, 190, 80), rgb(206, 156, 52)][(x + y // 2) % 3] if y < 5 else rgb(196, 160, 80))
CARROT_M = region(4, 4, lambda x, y: [rgb(255, 160, 70), rgb(236, 120, 36), rgb(200, 90, 24)][min(2, (x + y) // 2)])
LEAF_M = region(4, 4, lambda x, y: rgb(96, 170, 70) if (x + y) % 2 else rgb(70, 136, 52))
POTATO_M = region(4, 4, lambda x, y: [rgb(226, 190, 128), rgb(204, 164, 104), rgb(176, 136, 84)][min(2, (x * y) % 3)])


def wood_box(frm, to, front=None, light=0):
    """나무 상자·널: 위·아래·옆은 널빤지, 앞은 지정한 그림"""
    faces = {f: uv_of(WOOD_M, random.uniform(0, 12), random.uniform(0, 8), 16, 12) for f in ALL}
    if front:
        faces["north"] = uv_of(front)
    V(frm, to, IRON_M, light=light, faces=faces)


def burlap_box(frm, to, light=0, front=True):
    """삼베 자루: 앞면에 새싹 그림"""
    faces = {f: uv_of(BURLAP_M) for f in ALL}
    if front:
        faces["north"] = uv_of(SACK_FRONT_M)
    V(frm, to, IRON_M, light=light, faces=faces)


# ═════════════ 받침·계산대 ═════════════
V([-3.4, 0, 2.6], [15.4, 1.2, 13.4], BRASS_DARK_M)                              # 바닥 받침
for cx in (-3.6, 13.8):
    V([cx, 0, 2.4], [cx + 1.8, 1.6, 4.2], BRASS_M)                              # 앞 모서리 쇠붙이
V([-3, 1.2, 3], [15, 8, 13], IRON_DARK_M)                                       # 받침 함
V([2, 2.4, 2.7], [8, 6.6, 3.0], IRON_M, faces={"north": uv_of(HOLE_M)})          # 통풍구 바탕
for vy in (2.8, 3.8, 4.8, 5.8):
    V([2, vy, 2.5], [8, vy + 0.45, 2.7], BRASS_M)                               # 통풍 살
for hx in (-1.6, 10.4):
    V([hx, 4.2, 2.6], [hx + 2.4, 4.8, 3.0], BRASS_LIGHT_M)                      # 서랍 손잡이
for tx in (-3.2, 1.4, 8.6, 14.4):
    V([tx, 1.2, 2.8], [tx + 0.8, 8, 3.1], BRASS_M)                              # 세로 황동 띠
V([-3.6, 8, 1.6], [10.6, 9, 13], BRASS_M)                                        # 계산대 턱

# ═════════════ 위 몸통: 진열장(왼쪽)·열린 선반(가운데)·오른쪽 기둥 ═════════════
CZ = 9            # 진열 칸 깊이 끝
V([-3, 9, CZ], [15, 24, 13], IRON_M)                                             # 뒤 덩어리
V([-3, 9, 3], [-2.2, 24, CZ], IRON_M, faces={"east": uv_of(DARK_M, 0, 0, 12, 26)})   # 왼쪽 벽
V([4.0, 9, 3], [4.8, 24, CZ], BRASS_M)                                            # 진열장·선반 칸막이
V([-2.2, 23, 3], [10, 24, CZ], IRON_M, faces={"down": uv_of(FLOOR_M)})            # 칸 위
V([-2.2, 9, CZ - 0.01], [4.0, 23, CZ], DARK_M, light=5, faces={"north": uv_of(DARK_M)})   # 진열장 뒷벽
V([4.8, 9, CZ - 0.01], [10, 23, CZ], DARK_M, light=4, faces={"north": uv_of(DARK_M)})     # 선반 뒷벽

# 진열장: 선반 2개 + 씨앗 자루 3개 + 유리판 + 황동 테두리
for sy in (13.6, 18.3):
    V([-2.2, sy, 3.6], [4.0, sy + 0.35, CZ], BRASS_M)
for floor_y in (9.0, 13.95, 18.65):
    burlap_box([-0.6, floor_y, 4.6], [2.6, floor_y + 2.8, 7.6], light=5)
    burlap_box([0.2, floor_y + 2.8, 5.4], [1.8, floor_y + 3.6, 6.8], light=5, front=False)   # 자루 목
    V([0.0, floor_y + 2.8, 5.2], [2.0, floor_y + 3.1, 7.0], BRASS_DARK_M)                    # 묶은 끈
V([-2.0, 9.2, 3.25], [3.8, 22.8, 3.3], GLASS_M,
  faces={"north": uv_of(GLASS_M), "south": uv_of(GLASS_M)}, skip=("east", "west", "up", "down"))
V([-2.4, 22.8, 3.0], [4.2, 23.2, 3.4], BRASS_M)
V([-2.4, 8.8, 3.0], [4.2, 9.2, 3.4], BRASS_M)

# 열린 선반: 나무 선반 2개 + 상자 3개 (위 밀, 가운데 당근, 아래 감자)
for sy in (13.6, 18.3):
    wood_box([4.8, sy, 3.4], [10, sy + 0.5, CZ])
for floor_y, crop in ((18.8, "wheat"), (14.1, "carrot"), (9.0, "potato")):
    wood_box([5.4, floor_y, 3.8], [9.4, floor_y + 1.8, 7.8], front=CRATE_M)
    top = floor_y + 1.8
    if crop == "wheat":
        for i, wx in enumerate((5.8, 6.8, 7.8, 8.6)):
            wz = 4.6 + (i % 2) * 0.8
            V([wx, top - 0.6, wz], [wx + 0.6, top + 2.6, wz + 0.6], IRON_M, light=4,
              faces={f: uv_of(WHEAT_M) for f in ALL})
    elif crop == "carrot":
        for cx, cz in ((5.8, 4.4), (7.4, 4.8), (6.6, 6.2)):
            V([cx, top - 0.5, cz], [cx + 1.4, top + 0.5, cz + 1.0], IRON_M, light=4, faces={f: uv_of(CARROT_M) for f in ALL})
            V([cx + 0.4, top + 0.5, cz + 0.2], [cx + 1.0, top + 1.6, cz + 0.8], IRON_M, light=4, faces={f: uv_of(LEAF_M) for f in ALL})
    else:
        for px, pz in ((5.8, 4.2), (7.2, 4.6), (6.4, 5.8), (7.8, 6.0)):
            V([px, top - 0.6, pz], [px + 1.3, top + 0.5, pz + 1.2], IRON_M, light=4, faces={f: uv_of(POTATO_M) for f in ALL})

# 오른쪽 기둥 (화면·키패드·동전 투입구)
V([10, 8, 3], [15, 24, CZ], IRON_M)
V([10.4, 9.0, 2.6], [14.6, 23.6, 3.0], BRASS_DARK_M)                              # 판
V([10.8, 18.4, 2.3], [14.2, 22.6, 2.6], BRASS_M)                                  # 화면 테
V([11.2, 18.8, 2.1], [13.8, 22.2, 2.3], IRON_DARK_M, light=10, faces={"north": uv_of(CART_M)})
for r in range(3):
    for c in range(2):
        bx, by = 11.3 + c * 1.5, 14.2 + r * 1.2
        V([bx, by, 2.2], [bx + 1.0, by + 0.8, 2.6], BRASS_LIGHT_M)                 # 키패드
V([11.4, 10.2, 2.2], [13.6, 13.0, 2.6], BRASS_M, faces={"north": uv_of(SLOT_M)})  # 동전 투입구

# 모서리 기둥 + 위 띠
for px in (-3.4, 14.6):
    V([px, 9, 2.6], [px + 0.8, 24, 3.4], BRASS_M)
V([-3.6, 24, 2.6], [15.6, 25, 13.4], BRASS_M)

# ═════════════ 차양 (앞으로 기울어짐) + 물결 테두리 ═════════════
V([-4.6, 24.6, -2.2], [11.6, 25.4, 6.0], IRON_M,
  faces={"up": uv_of(AWNING_M), "down": uv_of(AWNING_UNDER_M), "north": uv_of(VALANCE_M, 0, 0, 32, 2),
         "east": uv_of(AWNING_UNDER_M, 0, 0, 8, 1), "west": uv_of(AWNING_UNDER_M, 0, 0, 8, 1)},
  rotation=(-22.5, "x", [3.5, 25.0, 6.0]))
V([-4.6, 20.4, -1.75], [11.6, 22.0, -1.65], IRON_M,
  faces={"north": uv_of(VALANCE_M), "south": uv_of(VALANCE_M)}, skip=("east", "west", "up", "down"))

# ═════════════ 아치형 간판 ═════════════
V([0, 25, 5], [10, 29, 8], BRASS_M)                                              # 간판 몸
V([1, 25.5, 4.8], [9, 28.7, 5.0], BRASS_M, light=15, faces={"north": uv_of(SIGN_M)})
V([1.6, 29, 5], [8.4, 30.2, 8], BRASS_M)                                         # 아치 1단
V([2.2, 28.7, 4.8], [7.8, 29.6, 5.0], BRASS_M, light=15, faces={"north": uv_of(SIGN_TOP_M)})
V([3.2, 30.2, 5], [6.8, 31.0, 8], BRASS_M)                                       # 아치 2단
for bx in (-2.2, 10.0):
    V([bx, 25, 4.8], [bx + 2.2, 29, 8.2], BRASS_DARK_M)                           # 양옆 블록
    V([bx + 0.6, 27.6, 4.6], [bx + 1.6, 28.6, 4.8], IRON_DARK_M)                  # 리벳
    V([bx + 0.6, 25.6, 4.6], [bx + 1.6, 26.6, 4.8], IRON_DARK_M)
for hx in (1.8, 7.4):
    V([hx, 30.0, 6.0], [hx + 0.8, 31.4, 7.0], IRON_DARK_M)                       # 손잡이 다리
V([1.8, 31.2, 6.0], [8.2, 32.0, 7.0], IRON_DARK_M)                               # 손잡이

# ═════════════ 왼쪽 파이프 ═════════════
V([-4.4, 14, 10], [-3.4, 27.6, 11], BRASS_M)
V([-4.4, 26.6, 10], [-2.2, 27.6, 11], BRASS_M)
for py in (14.0, 20.5, 26.4):
    V([-4.6, py, 9.8], [-3.2, py + 0.6, 11.2], BRASS_DARK_M)

# ═════════════ 오른쪽: 랜턴(받침대 파이프), 톱니, 통으로 가는 파이프 ═════════════
V([15, 24, 6.5], [16, 30, 7.5], BRASS_M)                                         # 세로 파이프
V([15, 29, 6.5], [19.4, 30, 7.5], BRASS_M)                                       # 팔
V([18.0, 27.6, 6.7], [18.6, 29.0, 7.3], IRON_DARK_M)                             # 매단 고리
V([16.6, 26.8, 5.3], [20.0, 27.6, 8.7], IRON_DARK_M)                             # 랜턴 뚜껑
V([17.1, 23.0, 5.8], [19.5, 26.8, 8.2], IRON_M, light=15, faces={f: uv_of(LAMP_M) for f in SIDES})
for lx in (16.8, 19.4):
    for lz in (5.5, 8.1):
        V([lx, 23.0, lz], [lx + 0.4, 26.8, lz + 0.4], IRON_DARK_M)               # 철창
V([16.6, 22.4, 5.3], [20.0, 23.0, 8.7], IRON_DARK_M)                             # 랜턴 바닥
V([17.9, 21.8, 6.6], [18.7, 22.4, 7.4], BRASS_DARK_M)
V([15.0, 13.0, 3.4], [15.3, 21.0, 11.4], BRASS_M,
  faces={"east": uv_of(GEAR_M), "west": uv_of(GEAR_M)}, skip=("north", "south", "up", "down"))
V([15.3, 16.4, 6.8], [15.9, 17.6, 8.0], BRASS_DARK_M)                            # 톱니 축
V([15.4, 7.0, 10.0], [16.4, 13.0, 11.0], BRASS_M)                                # 통으로 내려가는 파이프
V([15.4, 6.6, 9.4], [18.6, 7.6, 10.4], BRASS_M)
V([15.2, 12.6, 9.8], [16.6, 13.2, 11.2], BRASS_DARK_M)

# ═════════════ 바닥 소품: 나무통 / 나무 상자 / 씨앗 자루 ═════════════
V([16.6, 0, 7.0], [22.0, 7.6, 12.4], IRON_M,
  faces={**{f: uv_of(STAVE_M) for f in SIDES}, "up": uv_of(DARK_M, 0, 0, 10, 10), "down": uv_of(STAVE_M)})
for hy in (1.2, 5.8):
    V([16.4, hy, 6.8], [22.2, hy + 0.6, 12.6], IRON_DARK_M)                      # 쇠테
V([16.4, 7.6, 6.8], [22.2, 8.0, 12.6], IRON_DARK_M)                              # 통 윗테
wood_box([13.0, 0, -1.6], [18.4, 5.2, 3.4], front=CRATE_M)                       # 나무 상자
burlap_box([-7.4, 0, -1.4], [-3.2, 4.2, 2.8])                                    # 씨앗 자루
burlap_box([-6.4, 4.2, -0.4], [-4.2, 5.4, 1.8], front=False)                     # 자루 목
V([-6.6, 4.2, -0.6], [-4.0, 4.6, 2.0], BRASS_DARK_M)                              # 끈

save(sys.argv[1], "crop_buyer", "BrassField tools/machines/make_crop_buyer.py", display={
    "gui": {"rotation": [25, 205, 0], "translation": [0, -2, 0], "scale": [0.26, 0.26, 0.26]},
    "ground": {"translation": [0, 2, 0], "scale": [0.2, 0.2, 0.2]},
    "firstperson_righthand": {"rotation": [0, 45, 0], "scale": [0.2, 0.2, 0.2]},
    "thirdperson_righthand": {"rotation": [75, 45, 0], "translation": [0, 2.5, 0], "scale": [0.16, 0.16, 0.16]},
})

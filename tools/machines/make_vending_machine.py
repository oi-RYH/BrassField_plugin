"""
증기 강화석 자판기 모델 (시안 2026-11-15). 1블록 폭 x 2블록 높이, 앞면 = north.
진열 칸·배출구는 실제로 파낸 공간이고, 화면·키패드·통풍구·랜턴 철창·파이프 이음쇠 등은 작은 큐브로 만든다.
간판·랜턴·화면·진열 칸 조명·배출 표시등은 스스로 빛난다(light_emission). 공용 재질은 machine_kit.py.

사용: python3 -I tools/machines/make_vending_machine.py <ItemsAdder rustport resourcepack/assets/rustport>
  → textures/machine/stone_vending_machine.png, models/machine/stone_vending_machine.json
  PREVIEW=<png> 를 주면 정면·옆면 합성 미리보기를 그린다.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from machine_kit import *  # noqa: E402,F401,F403

random.seed(31)

# 간판 발광판: 4px/단위로 촘촘하게, 가운데 밝고 가장자리 진하게 + 상자 그림
SIGN_W, SIGN_H = 36, 12


def sign_fn(x, y):
    cx, cy = (SIGN_W - 1) / 2, (SIGN_H - 1) / 2
    d = max(abs(x - cx) / cx, abs(y - cy) / cy)
    return GLOW[min(3, int(d * 3.6))]


sign_img = [[sign_fn(x, y) for x in range(SIGN_W)] for y in range(SIGN_H)]
ICON = ["..BBBBBBBBBB..",
        ".BLLLLLLLLLLB.",
        "BLLLLLYYLLLLLB",
        "BDDDDDYYDDDDDB",
        "BDDDDDKKDDDDDB",
        "BDDDDDDDDDDDDB",
        ".BBBBBBBBBBBB."]
ICON_PAL = {"B": rgb(120, 70, 24), "L": rgb(206, 140, 52), "D": rgb(168, 104, 34), "Y": rgb(255, 238, 170), "K": rgb(90, 50, 16)}
for dy, row in enumerate(ICON):
    for dx, ch in enumerate(row):
        if ch != ".":
            sign_img[2 + dy][11 + dx] = ICON_PAL[ch]
SIGN_M = region(SIGN_W, SIGN_H, lambda x, y: sign_img[y][x])

LAMP_M = region(6, 8, lambda x, y: LAMP[min(3, abs(x * 2 - 5) // 2 + (1 if y in (0, 7) else 0))])


def screen_fn(x, y):
    if y in (2, 4) and 1 <= x <= (6 if y == 2 else 4):
        return CYAN[0]
    return CYAN[2] if (x + y) % 2 else rgb(22, 60, 66)


SCREEN_M = region(8, 6, screen_fn)
ARROW_M = region(4, 4, lambda x, y: AMBER if abs(x - 1.5) <= 1.5 - y * 0.5 else rgb(150, 90, 30))


def coin_fn(x, y):
    if 1 <= x <= 2 and 1 <= y <= 4:
        return DARK[3]
    return BRASS[1] if (x + y) % 3 else BRASS[2]


COIN_M = region(4, 6, coin_fn)



chest_m = {}
for grade, (body, lid, edge, band) in CHEST.items():
    def front(x, y, body=body, edge=edge, band=band):
        if y == 3:
            return edge
        if x in (3, 4):
            return band
        return body if x not in (0, 7) else edge
    chest_m[grade] = {
        "front": region(8, 4, front),
        "side": region(6, 4, lambda x, y, body=body, edge=edge: edge if y == 3 or x in (0, 5) else body),
        "lid": region(8, 6, lambda x, y, lid=lid, band=band, edge=edge: band if x in (3, 4) else (edge if y in (0, 5) else lid)),
        "lid_side": region(8, 2, lambda x, y, lid=lid, edge=edge: lid if y == 0 else edge),
        "lock": region(2, 2, lambda x, y, band=band: band),
    }


# ═════════════ 모델 ═════════════
# 다리 4개: 넓은 받침 + 기둥
for fx in (1.5, 12.5):
    for fz in (4.5, 9.5):
        cube([fx - 0.4, 0, fz - 0.4], [fx + 2.4, 0.6, fz + 2.4], BRASS_DARK_M)
        cube([fx, 0.6, fz], [fx + 2, 1.6, fz + 2], BRASS_M)

# 받침대 (철) + 위쪽 황동 턱
cube([1, 1.6, 3.6], [15, 3.4, 12.4], IRON_DARK_M)
cube([0.6, 3.4, 3.2], [15.4, 4, 12.8], BRASS_M)

# 몸통 (철): 진열 칸 x 2~10, y 11.5~24 / 배출구 x 2.5~8.5, y 5~9 를 비워 둔다
BODY_Z0, BODY_Z1 = 4, 12
CAV = (2, 10, 11.5, 24, 9.5)          # x0, x1, y0, y1, 깊이 끝 z
DIS = (2.5, 8.5, 5, 9, 7)             # 배출구 x0, x1, y0, y1, 깊이 끝 z
cube([1, 4, CAV[4]], [15, 25, BODY_Z1], IRON_M)                                   # 진열 칸 뒤 덩어리
cube([1, 4, BODY_Z0], [CAV[0], 25, CAV[4]], IRON_M, faces={"east": uv_of(DARK_M, 0, 0, 10, 26)})  # 왼쪽 벽
cube([CAV[1], 4, BODY_Z0], [15, 25, CAV[4]], IRON_M, faces={"west": uv_of(DARK_M, 0, 0, 10, 26)})  # 오른쪽 기둥
cube([CAV[0], CAV[3], BODY_Z0], [CAV[1], 25, CAV[4]], IRON_M, faces={"down": uv_of(FLOOR_M)})       # 진열 칸 위
# 진열 칸 아래 = 배출구 둘레
cube([CAV[0], 9, BODY_Z0], [CAV[1], CAV[2], CAV[4]], IRON_M, faces={"up": uv_of(FLOOR_M), "down": uv_of(HOLE_M)})
cube([CAV[0], 4, BODY_Z0], [CAV[1], DIS[2], CAV[4]], IRON_M, faces={"up": uv_of(DARK_M, 0, 0, 12, 4)})
cube([CAV[0], DIS[2], BODY_Z0], [DIS[0], 9, CAV[4]], IRON_M, faces={"east": uv_of(HOLE_M)})
cube([DIS[1], DIS[2], BODY_Z0], [CAV[1], 9, CAV[4]], IRON_M, faces={"west": uv_of(HOLE_M)})
cube([DIS[0], DIS[2], DIS[4]], [DIS[1], 9, CAV[4]], IRON_M, faces={"north": uv_of(HOLE_M)})           # 배출구 안쪽 벽
cube([DIS[0] + 0.3, DIS[2], 4.5], [DIS[1] - 0.3, DIS[2] + 0.6, DIS[4]], BRASS_DARK_M)              # 배출구 안 받침
cube([DIS[0], 4, 1.8], [DIS[1], 4.8, BODY_Z0], BRASS_M)                                           # 앞으로 튀어나온 받침 혀
cube([DIS[0] - 0.2, 4.8, 1.6], [DIS[1] + 0.2, 5.2, 2.2], BRASS_LIGHT_M)                           # 혀 끝 턱
cube([5, 9.4, 3.7], [6, 10.2, BODY_Z0], ARROW_M, light=10, faces={"north": uv_of(ARROW_M)})  # 배출 표시등

# 진열 칸: 뒷벽(은은한 빛), 천장 조명 줄, 선반 2개 + 앞 턱
cube([CAV[0], CAV[2], CAV[4] - 0.01], [CAV[1], CAV[3], CAV[4]], DARK_M, light=6, faces={"north": uv_of(DARK_M)})
cube([CAV[0] + 0.3, CAV[3] - 0.4, 4.6], [CAV[1] - 0.3, CAV[3], 5.2], BRASS_LIGHT_M, light=15,
     faces={"down": uv_of(LIGHT_STRIP_M), "north": uv_of(LIGHT_STRIP_M, 0, 0, 16, 1)})
for sy in (15.6, 19.8):
    cube([CAV[0], sy, 4.6], [CAV[1], sy + 0.4, CAV[4]], BRASS_M)
    cube([CAV[0], sy, 4.2], [CAV[1], sy + 0.9, 4.6], BRASS_LIGHT_M)

# 상자 3개 (위에서부터 하급·중급·상급): 몸통 + 뚜껑 + 자물쇠
for floor_y, grade in ((20.2, "low"), (16.0, "mid"), (11.5, "high")):
    c = chest_m[grade]
    x0, x1, z0, z1 = 3.8, 8.2, 5.6, 8.6
    cube([x0, floor_y, z0], [x1, floor_y + 2, z1], IRON_M, light=6,
         faces={"north": uv_of(c["front"]), "south": uv_of(c["side"]), "east": uv_of(c["side"]),
                "west": uv_of(c["side"]), "up": uv_of(c["lid"]), "down": uv_of(c["side"])})
    cube([x0 - 0.2, floor_y + 2, z0 - 0.2], [x1 + 0.2, floor_y + 3, z1 + 0.2], IRON_M, light=6,
         faces={f: uv_of(c["lid_side"]) for f in ("north", "south", "east", "west")}
         | {"up": uv_of(c["lid"]), "down": uv_of(c["lid"])})
    cube([5.6, floor_y + 1.3, z0 - 0.5], [6.4, floor_y + 2.3, z0 - 0.2], IRON_M, light=6,
         faces={f: uv_of(c["lock"]) for f in ("north", "south", "east", "west", "up", "down")})

# 유리창: 황동 테두리 4조각 + 맑은 유리
cube([CAV[0] - 0.3, CAV[2] - 0.3, 3.5], [CAV[1] + 0.3, CAV[2] + 0.3, BODY_Z0], BRASS_M)
cube([CAV[0] - 0.3, CAV[3] - 0.3, 3.5], [CAV[1] + 0.3, CAV[3] + 0.3, BODY_Z0], BRASS_M)
cube([CAV[0] - 0.3, CAV[2] + 0.3, 3.5], [CAV[0] + 0.3, CAV[3] - 0.3, BODY_Z0], BRASS_M)
cube([CAV[1] - 0.3, CAV[2] + 0.3, 3.5], [CAV[1] + 0.3, CAV[3] - 0.3, BODY_Z0], BRASS_M)
cube([CAV[0] + 0.3, CAV[2] + 0.3, 3.75], [CAV[1] - 0.3, CAV[3] - 0.3, 3.8], GLASS_M,
     faces={"north": uv_of(GLASS_M), "south": uv_of(GLASS_M)}, skip=("east", "west", "up", "down"))

# 오른쪽 기둥 장치들 (x 10~14)
cube([10.4, 20.2, 3.6], [13.6, 23.4, BODY_Z0], BRASS_DARK_M)                                    # 화면 테두리
cube([10.8, 20.6, 3.4], [13.2, 23.0, 3.6], IRON_DARK_M, light=10, faces={"north": uv_of(SCREEN_M)})  # 화면
cube([10.4, 14.6, 3.7], [13.6, 18.8, BODY_Z0], BRASS_DARK_M)                                    # 키패드 받침판
for r in range(3):
    for col in range(3):
        bx, by = 10.75 + col * 1.0, 15.0 + r * 1.3
        cube([bx, by, 3.3], [bx + 0.7, by + 0.8, 3.7], BRASS_LIGHT_M)                          # 버튼
cube([10.9, 11.4, 3.4], [13.1, 13.8, BODY_Z0], BRASS_M, faces={"north": uv_of(COIN_M)})         # 동전 투입구
cube([10.4, 5.0, 3.95], [13.6, 9.6, BODY_Z0], IRON_M, faces={"north": uv_of(HOLE_M)})          # 통풍구 바탕
for vy in (5.4, 6.5, 7.6, 8.7):
    cube([10.4, vy, 3.6], [13.6, vy + 0.5, 3.95], BRASS_M)                                      # 통풍 살

# 모서리 기둥 (황동, 앞뒤 네 모서리)
for px0, px1 in ((0.6, 1.6), (14.4, 15.4)):
    for pz0, pz1 in ((3.2, 4.4), (11.6, 12.8)):
        cube([px0, 4, pz0], [px1, 25, pz1], BRASS_M)

# 띠: 진열 칸·배출구 사이, 머리 띠 (턱 포함)
cube([0.6, 10.2, 3.3], [15.4, 11, 12.7], BRASS_M)
cube([0.4, 25, 3.0], [15.6, 26.2, 13.0], BRASS_M)
cube([1.0, 26.2, 3.6], [15.0, 26.8, 12.4], IRON_DARK_M)                                          # 지붕판

# 왼쪽 옆면 덧댄 철판 + 볼트
cube([0.7, 6, 5.2], [1, 23.5, 10.8], IRON_DARK_M)
for by in (6.6, 22.4):
    for bz in (5.8, 9.8):
        cube([0.45, by, bz], [0.7, by + 0.5, bz + 0.5], BRASS_LIGHT_M)

# 뒷면: 통풍 살 + 점검 판 + 볼트
cube([4, 15, 12.0], [12, 22, 12.1], IRON_M, faces={"south": uv_of(HOLE_M)})
for gy in (15.5, 16.8, 18.1, 19.4, 20.7):
    cube([4, gy, 12.1], [12, gy + 0.6, 12.4], IRON_DARK_M)
cube([4.5, 6, 12.0], [11.5, 12, 12.3], IRON_DARK_M)
for bx in (5, 10.5):
    for by in (6.5, 11):
        cube([bx, by, 12.3], [bx + 0.5, by + 0.5, 12.55], BRASS_LIGHT_M)

# 오른쪽 옆면: 세로 파이프 + 이음쇠, 톱니 + 축
cube([15.0, 5.5, 10.0], [16.0, 24.5, 11.0], BRASS_M)
for py in (5.2, 14.5, 24.0):
    cube([14.85, py, 9.85], [16.15, py + 0.7, 11.15], BRASS_DARK_M)
cube([15.05, 14.0, 4.6], [15.35, 20.0, 10.6], BRASS_M,
     faces={"east": uv_of(GEAR_M), "west": uv_of(GEAR_M)}, skip=("north", "south", "up", "down"))
cube([15.35, 16.5, 7.1], [15.9, 17.5, 8.1], BRASS_DARK_M)

# 간판: 황동 틀 + 안쪽 발광판 + 지지대
cube([1.4, 26.8, 5.2], [11.6, 31.2, 9.0], BRASS_M)                                               # 틀
cube([2.0, 27.4, 4.9], [11.0, 30.6, 5.2], BRASS_M, light=15, faces={"north": uv_of(SIGN_M)})     # 발광판
for sx in (2.6, 10.0):
    cube([sx, 26.8, 8.6], [sx + 0.6, 27.6, 9.6], BRASS_DARK_M)                                   # 지지대

# 지붕 파이프 손잡이 (+ 이음쇠)
for hx in (3.4, 8.6):
    cube([hx, 31.2, 6.6], [hx + 1, 31.9, 7.6], BRASS_M)
    cube([hx - 0.15, 31.2, 6.45], [hx + 1.15, 31.45, 7.75], BRASS_DARK_M)
cube([3.4, 31.4, 6.6], [9.6, 32, 7.6], BRASS_M)

# 랜턴 (오른쪽 위): 받침·뚜껑 철 마개, 빛나는 심지, 철창 기둥 4개
LX0, LX1, LZ0, LZ1 = 12.0, 15.0, 6.4, 9.4
cube([LX0 - 0.2, 26.8, LZ0 - 0.2], [LX1 + 0.2, 27.6, LZ1 + 0.2], IRON_DARK_M)
cube([LX0 - 0.2, 31.2, LZ0 - 0.2], [LX1 + 0.2, 32.0, LZ1 + 0.2], IRON_DARK_M)
cube([LX0 + 0.5, 27.6, LZ0 + 0.5], [LX1 - 0.5, 31.2, LZ1 - 0.5], IRON_M, light=15,
     faces={f: uv_of(LAMP_M) for f in ("north", "south", "east", "west")})
for cx in (LX0, LX1 - 0.4):
    for cz in (LZ0, LZ1 - 0.4):
        cube([cx, 27.6, cz], [cx + 0.4, 31.2, cz + 0.4], IRON_DARK_M)

save(sys.argv[1], "stone_vending_machine", "BrassField tools/machines/make_vending_machine.py")

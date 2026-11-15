"""
증기 강화석 자판기 모델: 텍스처(128x128)와 아이템 모델(JSON)을 만든다.

시안(2026-11-15) 기준. 1블록 폭 x 2블록 높이, 앞면 = north.
- 검은 외곽선 없이, 같은 재질의 밝고 어두운 색과 실제 큐브 형태로 입체감을 낸다.
- 철판·황동·내부·유리·발광부 재질 텍스처를 두고, 큐브 면마다 크기에 맞춰 잘라 붙인다 (블록당 32px).
- 진열 칸·배출구는 실제로 파낸 공간이고, 화면·키패드·통풍구·랜턴 철창·파이프 이음쇠 등은 작은 큐브로 만든다.
- 간판·랜턴·화면·진열 칸 조명·배출 표시등은 스스로 빛난다(light_emission).

사용: python3 -I tools/machines/make_vending_machine.py <ItemsAdder rustport resourcepack/assets/rustport>
  → textures/machine/stone_vending_machine.png, models/machine/stone_vending_machine.json
  PREVIEW=<png> 를 주면 정면·옆면 합성 미리보기를 그린다.
"""
import json
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "hud"))
import png  # noqa: E402

random.seed(31)
TEX = 128
PX = 2                       # 1 모델 단위(1/16 블록)당 텍스처 픽셀
S = 16 / TEX                 # 텍스처 픽셀 → UV 단위
T = (0, 0, 0, 0)


def rgb(r, g, b, a=255):
    return (r, g, b, a)


# ── 색 (강화 GUI 배경·상자 그림에서 뽑음) ──
# 금속은 노이즈 없이 매끄러운 단계로: 하이라이트 → 밝음 → 중간 → 그늘 → 어둠
BRASS = [rgb(255, 232, 168), rgb(240, 196, 116), rgb(214, 158, 78), rgb(178, 120, 52), rgb(132, 84, 36)]
IRON = [rgb(214, 218, 222), rgb(176, 180, 186), rgb(146, 150, 156), rgb(116, 120, 126), rgb(86, 89, 94)]
BRASS_DARK = [rgb(214, 170, 98), rgb(184, 128, 58), rgb(156, 102, 42), rgb(124, 78, 32), rgb(94, 58, 24)]
IRON_DARK = [rgb(156, 160, 166), rgb(122, 126, 132), rgb(98, 101, 106), rgb(78, 80, 85), rgb(60, 62, 66)]
DARK = [rgb(44, 38, 32), rgb(36, 31, 26), rgb(30, 26, 22), rgb(24, 20, 17)]
GLOW = [rgb(255, 250, 218), rgb(255, 232, 150), rgb(252, 198, 92), rgb(228, 150, 52)]
LAMP = [rgb(255, 248, 210), rgb(255, 214, 110), rgb(246, 156, 52), rgb(196, 98, 28)]
CYAN = [rgb(150, 245, 250), rgb(80, 210, 225), rgb(30, 90, 100)]
AMBER = rgb(255, 196, 70)
CHEST = {   # 몸통, 뚜껑(밝음), 가장자리(어둠), 띠·자물쇠
    "low": [rgb(122, 116, 108), rgb(156, 150, 140), rgb(92, 88, 82), rgb(196, 192, 184)],
    "mid": [rgb(188, 124, 44), rgb(234, 176, 76), rgb(140, 86, 28), rgb(255, 220, 130)],
    "high": [rgb(162, 46, 34), rgb(210, 78, 56), rgb(118, 30, 22), rgb(240, 186, 80)],
}

tex = png.blank(TEX, TEX)
cursor = [0, 0, 0]


def alloc(w, h):
    if cursor[0] + w > TEX:
        cursor[0], cursor[1], cursor[2] = 0, cursor[1] + cursor[2], 0
    x, y = cursor[0], cursor[1]
    assert y + h <= TEX, "텍스처 공간 부족"
    cursor[0] += w
    cursor[2] = max(cursor[2], h)
    return x, y


def region(w, h, fn):
    """w x h 픽셀 영역을 fn(x, y)로 칠하고 (x, y, w, h)를 돌려준다."""
    x0, y0 = alloc(w, h)
    for y in range(h):
        for x in range(w):
            tex[y0 + y][x0 + x] = fn(x, y)
    return (x0, y0, w, h)


def uv_of(reg, dx=0.0, dy=0.0, w=None, h=None):
    """영역 안에서 (dx, dy) 픽셀부터 w x h 픽셀을 UV로"""
    x0, y0, rw, rh = reg
    w = rw if w is None else min(w, rw)
    h = rh if h is None else min(h, rh)
    dx = max(0.0, min(dx, rw - w))
    dy = max(0.0, min(dy, rh - h))
    return [(x0 + dx) * S, (y0 + dy) * S, (x0 + dx + w) * S, (y0 + dy + h) * S]


# ── 재질 텍스처 (외곽선 없음) ──
def lerp(c1, c2, k):
    return tuple(int(round(c1[i] + (c2[i] - c1[i]) * k)) for i in range(3)) + (255,)


def shade(pal, v):
    """0(하이라이트)~4(어둠) 사이 실수 단계를 색으로 (중간값은 섞음)"""
    v = max(0.0, min(4.0, v))
    i = min(3, int(v))
    return lerp(pal[i], pal[i + 1], v - i)


def plate_fn(pal, brushed):
    """매끄러운 금속 판: 위는 밝고 아래로 갈수록 살짝 어두워지는 명암 + 아주 옅은 결 + 사선 반사띠 + 가장자리 베벨"""
    W = H = 16

    def fn(x, y):
        if y == 0 or x == 0:
            return shade(pal, 0.6)                       # 위·왼쪽 가장자리 반사
        if y == H - 1 or x == W - 1:
            return shade(pal, 3.4)                       # 아래·오른쪽 가장자리 그늘
        v = 1.7 + 0.9 * y / H                            # 부드러운 세로 명암
        grain = ((y * 7) % 5 == 0) if brushed == "h" else ((x * 7) % 5 == 0)
        v += 0.12 if grain else 0.0                      # 아주 옅은 결
        if abs((x + y) - 13) <= 1:
            v -= 0.45                                    # 사선 반사띠
        return shade(pal, v)
    return fn


def rod_fn(pal, vertical):
    """원통 명암: 어둠 → 밝음 → 하이라이트 → 밝음 → 어둠 (vertical=True면 가로 방향으로 변함)"""
    profile = [3.2, 2.2, 1.2, 0.3, 0.9, 1.7, 2.4, 3.3]

    def fn(x, y):
        return shade(pal, profile[x if vertical else y])
    return fn


METALS = {}
for name, pal, brushed in (("iron", IRON, "v"), ("brass", BRASS, "h"), ("iron_dark", IRON_DARK, "v"),
                           ("brass_dark", BRASS_DARK, "h"), ("brass_light", BRASS[:1] * 2 + BRASS[:3], "h")):
    METALS[name] = {
        "plate": region(16, 16, plate_fn(pal, brushed)),
        "rod_v": region(8, 8, rod_fn(pal, True)),
        "rod_h": region(8, 8, rod_fn(pal, False)),
    }
IRON_M, BRASS_M, IRON_DARK_M, BRASS_DARK_M, BRASS_LIGHT_M = "iron", "brass", "iron_dark", "brass_dark", "brass_light"
DARK_M = region(16, 16, lambda x, y: BRASS[3] if random.random() > 0.2 else BRASS[4])
BRASS_LIGHT_M = region(8, 8, lambda x, y: BRASS[0] if (x + y) % 3 else BRASS[1])
IRON_DARK_M = region(16, 16, lambda x, y: IRON[3] if random.random() > 0.2 else IRON[4])
DARK_M = region(16, 26, lambda x, y: DARK[1] if x % 4 else DARK[0])
FLOOR_M = region(16, 10, lambda x, y: DARK[2] if (x + y) % 5 else DARK[1])
HOLE_M = region(8, 8, lambda x, y: DARK[3])
GLASS_M = region(16, 26, lambda x, y: rgb(225, 245, 245, 120) if (x - y // 3) in (3, 4, 10) else rgb(150, 200, 205, 55))
LIGHT_STRIP_M = region(16, 2, lambda x, y: rgb(255, 244, 214))


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


def gear_fn(x, y):
    size = 12
    c = (size - 1) / 2
    dx, dy = x - c, y - c
    r2 = dx * dx + dy * dy
    tooth = (abs(dx) < 1.6 or abs(dy) < 1.6 or abs(abs(dx) - abs(dy)) < 1.3) and r2 <= (c + 0.4) ** 2
    if r2 <= 2.5:
        return BRASS[4]
    if r2 <= (c - 1.6) ** 2:
        if 5 <= r2 <= 9:
            return BRASS[3]      # 바퀴살 사이 홈
        return BRASS[1] if dy < -1 else (BRASS[0] if dy < 0 else BRASS[2])
    return BRASS[2] if tooth else T


GEAR_M = region(12, 12, gear_fn)

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


# ── 큐브 만들기 ──
def face_size(face, frm, to):
    dx, dy, dz = (to[i] - frm[i] for i in range(3))
    return {"north": (dx, dy), "south": (dx, dy), "east": (dz, dy), "west": (dz, dy),
            "up": (dx, dz), "down": (dx, dz)}[face]


elements = []


def cube(frm, to, mat, light=0, faces=None, skip=()):
    """재질 영역에서 면 크기만큼 잘라 붙인 큐브. faces로 특정 면의 UV를 덮어쓴다."""
    out = {}
    dims = sorted(to[i] - frm[i] for i in range(3))
    rod = dims[1] <= 1.5 and dims[2] >= 3 * dims[1]
    for face in ("north", "south", "east", "west", "up", "down"):
        if face in skip:
            continue
        if faces and face in faces:
            out[face] = {"uv": faces[face], "texture": "#0"}
            continue
        w, h = face_size(face, frm, to)
        if isinstance(mat, str):
            # 금속: 두 방향이 얇고(1.5 이하) 한 방향이 긴 큐브(파이프·기둥·철창·띠)만 원통 명암을 길이 방향으로,
            # 나머지(판재)는 매끄러운 판 텍스처를 면 전체에 붙인다
            kind = METALS[mat]
            if rod and h >= 2 * w:
                tile = kind["rod_v"]
            elif rod and w >= 2 * h:
                tile = kind["rod_h"]
            else:
                tile = kind["plate"]
            out[face] = {"uv": uv_of(tile), "texture": "#0"}
            continue
        pw, ph = max(0.5, w * PX), max(0.5, h * PX)
        # 같은 재질이라도 면마다 다른 부분을 쓰도록 위치를 섞는다
        dx = random.uniform(0, max(0.0, mat[2] - pw))
        dy = random.uniform(0, max(0.0, mat[3] - ph))
        out[face] = {"uv": uv_of(mat, dx, dy, pw, ph), "texture": "#0"}
    element = {"from": [round(v, 3) for v in frm], "to": [round(v, 3) for v in to], "faces": out}
    if light:
        element["light_emission"] = light
    elements.append(element)


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

# ═════════════ 저장 ═════════════
assets = sys.argv[1]
os.makedirs(os.path.join(assets, "textures/machine"), exist_ok=True)
os.makedirs(os.path.join(assets, "models/machine"), exist_ok=True)
png.write(os.path.join(assets, "textures/machine/stone_vending_machine.png"), tex)
model = {
    "credit": "BrassField tools/machines/make_vending_machine.py",
    "texture_size": [TEX, TEX],
    "textures": {"0": "rustport:machine/stone_vending_machine", "particle": "rustport:machine/stone_vending_machine"},
    "elements": elements,
    "display": {
        "gui": {"rotation": [20, 205, 0], "translation": [0, -3, 0], "scale": [0.36, 0.36, 0.36]},
        "ground": {"translation": [0, 2, 0], "scale": [0.3, 0.3, 0.3]},
        "firstperson_righthand": {"rotation": [0, 45, 0], "scale": [0.3, 0.3, 0.3]},
        "thirdperson_righthand": {"rotation": [75, 45, 0], "translation": [0, 2.5, 0], "scale": [0.25, 0.25, 0.25]},
    },
}
with open(os.path.join(assets, "models/machine/stone_vending_machine.json"), "w", encoding="utf-8") as f:
    json.dump(model, f, indent=1)

bad = [e for e in elements if not all(-16 <= v <= 32 for v in e["from"] + e["to"])]
assert not bad, "좌표 범위 밖 큐브: %s" % bad[:1]
print("ok, elements:", len(elements))


# ═════════════ 미리보기 (정면 / 오른쪽 옆면, 뒤에서부터 덮어 그리고 반투명은 섞음) ═════════════
def project(view, scale=4):
    # view: "north" → 화면 x = 모델 x, 깊이 = z (작을수록 앞)
    #       "east"  → 화면 x = 16 - z (앞이 왼쪽), 깊이 = -x (클수록 앞)
    img = [[rgb(70, 92, 110)] * (16 * scale) for _ in range(32 * scale)]
    if view == "north":
        order = sorted(elements, key=lambda e: -e["from"][2])
        span = lambda e: (e["from"][0], e["to"][0])
    else:
        order = sorted(elements, key=lambda e: e["to"][0])
        span = lambda e: (16 - e["to"][2], 16 - e["from"][2])
    for e in order:
        face = e["faces"].get(view)
        if not face:
            continue
        u0, v0, u1, v1 = face["uv"]
        px0, py0, px1, py1 = u0 / S, v0 / S, u1 / S, v1 / S
        a, b = span(e)
        x0, x1 = int(round(a * scale)), int(round(b * scale))
        y0, y1 = int(round((32 - e["to"][1]) * scale)), int(round((32 - e["from"][1]) * scale))
        shade = 1.0 if view == "north" else 0.82
        for y in range(y0, y1):
            for x in range(x0, x1):
                if not (0 <= y < len(img) and 0 <= x < len(img[0])):
                    continue
                tx = int(px0 + (x - x0 + 0.5) / max(1, x1 - x0) * (px1 - px0))
                ty = int(py0 + (y - y0 + 0.5) / max(1, y1 - y0) * (py1 - py0))
                c = tex[min(TEX - 1, ty)][min(TEX - 1, tx)]
                if not c[3]:
                    continue
                k = c[3] / 255
                under = img[y][x]
                img[y][x] = tuple(int(c[i] * shade * k + under[i] * (1 - k)) for i in range(3)) + (255,)
    return img


if os.environ.get("PREVIEW"):
    front_v, side_v = project("north"), project("east")
    sheet = png.blank(len(front_v[0]) * 2 + 8, len(front_v))
    png.paste(sheet, front_v, 0, 0)
    png.paste(sheet, side_v, len(front_v[0]) + 8, 0)
    png.write(os.environ["PREVIEW"], png.scale(sheet, 2))

"""
조리대 (Cooking Counter) 모델 — 앞면 3블록 x 옆면(깊이) 1블록 x 높이 2블록 스팀펑크 주방 조리대. 앞면 = north.
키우지 않는다: 1 모델 단위 = 텍스처 1픽셀 = 1/16 블록 (바닐라와 같은 크기). 가운데 블록이 설치한 블록이다.

요리 모드의 주방 구성(Farmer's Delight 화덕·냄비·도마, Cooking for Blockheads 걸레받이·상판·선반, MrCrayfish 서랍·문짝)에
서버 컨셉인 스팀펑크(강화석 자판기·작물 거래기·증폭 공작대처럼 황동 테·리벳 쇠판·구리·게이지·밸브·톱니·증기 파이프)를 씌웠다.
모델·텍스처는 다른 모드에서 가져오지 않고 직접 짰다.

구성 (정면 기준)
- 왼쪽 칸: 가문비 찬장 (긴 황동 손잡이 서랍, 테가 튀어나온 문짝), 황동 테 돌 상판 위 도마·칼·토마토·당근,
  뒤 벽에 톱니 장식, 위 선반에 양념 병 셋
- 가운데 칸: 리벳 박힌 무쇠 화덕 (황동 테 아치 구멍 속 바닐라 모닥불 장작·불 애니메이션), 빛나는 화구 격자,
  속이 빈 무쇠 냄비(수프·국자·김), 위에 황동 후드와 굴뚝
- 오른쪽 칸: 아래는 구리 밸브가 달린 무쇠 찬장, 상판 위에 구리 보일러 탱크(황동 띠, 압력 게이지, 꼭지 밸브),
  보일러에서 후드로 올라가는 구리 증기관
- 뒤: 리벳 쇠판 벽

입체감: 빈 곳은 비우고 채운 곳은 채운다 — 걸레받이·문 가운데·화덕 구멍은 들어가 있고, 서랍·문 테·손잡이·황동 테·상판은
튀어나와 있으며, 냄비는 속이 비어 있다.

재질: 바닐라 블록 텍스처는 모델에서 minecraft:block/... 로 참조만 한다
(가문비·참나무·짙은 참나무 판자, 벗긴 참나무 원목, 윤나는 안산암, 윤나는 흑암, 구리 블록, 깎인 구리, 모닥불 장작, 불).
바닐라에 없는 것(황동, 리벳 쇠판, 화구 격자, 냄비, 수프, 김, 도마, 칼날, 채소, 양념 병, 게이지, 밸브, 톱니)만 16x16으로 직접 그린다.

좌표는 정면 기준 vx 0(왼쪽) → 48(오른쪽), y 0 → 32, z 0(앞) → 16. 저장할 때 모델 x = 32 - vx (가운데 칸 = 모델 0~16).

사용: python3 -I tools/machines/make_cooking_station.py <ItemsAdder rustport resourcepack/assets/rustport>
  → textures/machine/cooking_station/<그림>.png, models/machine/cooking_station.json
  PREVIEW=<png> VANILLA=<바닐라 assets/minecraft/textures/block 폴더> 를 주면 정면·비스듬히 본 미리보기를 그린다.
"""
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "hud"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import png  # noqa: E402
from furniture_kit import FRAMED, FRAMED_TEX, framed_face, face_dims, split_cuts  # noqa: E402  (철판·황동은 면마다 테두리)

T = (0, 0, 0, 0)
X_OFF = 32             # 모델 x = X_OFF - vx


def rgb(r, g, b, a=255):
    return (r, g, b, a)


def blank():
    return [[T] * 16 for _ in range(16)]


def noisy(colors, weights, seed):
    r = random.Random(seed)
    return [[r.choices(colors, weights)[0] for _ in range(16)] for _ in range(16)]


# ═════════════ 직접 그리는 텍스처 (16x16, 바닐라 픽셀 크기) ═════════════
# 황동은 Create 모드 황동처럼: 옅고 따뜻한 금색 (밝음 → 어두움)
BRASS = [rgb(255, 235, 140), rgb(238, 193, 104), rgb(215, 170, 94), rgb(191, 142, 85), rgb(158, 105, 71), rgb(114, 71, 49)]
BRASS_LINE = rgb(247, 203, 108)
BRASS_MID = rgb(206, 160, 90)
BRASS_EDGE = [rgb(172, 120, 80), rgb(140, 94, 62), rgb(116, 70, 52)]   # 테두리 (너무 진하지 않게)
# 쇠는 Create 모드 산업용 철처럼: 중간 회색 (밝음 → 어두움), 테·볼트
IRON = [rgb(117, 113, 113), rgb(89, 88, 88), rgb(73, 72, 72), rgb(58, 57, 60)]
IRON_LIGHT = rgb(103, 97, 97)
IRON_EDGE = rgb(72, 71, 74)       # 테두리 (너무 진하지 않게)
IRON_BOLT = rgb(150, 146, 146)


def brass_tex():
    """황동 (Create 모드 황동 블록 느낌): 옅고 따뜻한 금색에 부드러운 사선 결, 바깥 1픽셀 짙은 갈색 테,
    안쪽 위·왼쪽은 밝은 금빛 줄, 아래·오른쪽은 한 단계 어두운 줄. 네 모서리는 가장 짙다."""
    img = [[T] * 16 for _ in range(16)]
    for y in range(16):
        for x in range(16):
            if x in (0, 15) or y in (0, 15):
                c = BRASS_EDGE[1] if (x == 15 or y == 15) else BRASS_EDGE[0]
                if (x, y) in ((0, 0), (15, 0), (0, 15), (15, 15)):
                    c = BRASS_EDGE[2]
            elif x == 1 or y == 1:
                c = BRASS[0] if (x + y) % 5 == 0 else BRASS_LINE
            elif x == 14 or y == 14:
                c = BRASS[3]
            else:
                d = (x + y) % 7                                     # 왼쪽 아래 → 오른쪽 위로 흐르는 결
                c = BRASS[1] if d == 0 else (BRASS_MID if d in (1, 4) else BRASS[2])
            img[y][x] = c
    return img


def iron_plate_tex():
    """쇠 판 (Create 모드 산업용 철 느낌): 중간 회색 바탕에 가로로 흐르는 흐린 결, 바깥 1픽셀 짙은 테,
    안쪽 위·왼쪽은 밝은 줄·아래·오른쪽은 어두운 줄, 네 모서리에 밝은 볼트"""
    img = [[T] * 16 for _ in range(16)]
    # 얼룩진 회색 바탕에 가로로 흐르는 흐린 결: 줄마다 2~4픽셀 길이의 밝고 어두운 덩어리
    rnd = random.Random(4)
    streaks = []
    for y in range(16):
        row = []
        while len(row) < 16:
            row += [rnd.choices([IRON[1], IRON_LIGHT, IRON[2]], [5, 2, 2])[0]] * rnd.randint(2, 4)
        streaks.append(row[:16])
    for y in range(16):
        for x in range(16):
            if (x, y) in ((0, 0), (15, 0), (0, 15), (15, 15)):
                c = IRON_BOLT
            elif x in (0, 15) or y in (0, 15):
                c = IRON_EDGE
            elif x == 1 or y == 1:
                c = IRON[0]
            elif x == 14 or y == 14:
                c = IRON[2]
            else:
                c = streaks[y][x]
            img[y][x] = c
    return img


def stove_top_tex():
    """화구: 쇠 테두리 + 가운데 쇠 격자, 격자 사이로 불빛"""
    img = noisy(IRON[1:3], [3, 2], 11)
    for y in range(16):
        for x in range(16):
            if x in (0, 15) or y in (0, 15):
                img[y][x] = IRON[0] if (x == 0 or y == 0) else IRON[3]
            elif 3 <= x <= 12 and 3 <= y <= 12:
                bar = x % 3 == 0 or y in (3, 12)
                glow = [rgb(255, 196, 70), rgb(246, 140, 40), rgb(200, 80, 26)][(x + y) % 3]
                img[y][x] = IRON[3] if bar else glow
    return img


def pot_tex():
    """무쇠 냄비: 위 테(밝음) + 어두운 몸통 + 황동 띠"""
    img = noisy([rgb(89, 88, 88), rgb(79, 79, 79), rgb(103, 97, 97)], [4, 3, 2], 12)
    for x in range(16):
        img[0][x] = rgb(132, 134, 140)
        img[1][x] = rgb(100, 102, 108)
        img[5][x] = BRASS[2]
    return img


def board_tex():
    img = noisy([rgb(206, 160, 98), rgb(192, 146, 86), rgb(218, 174, 112)], [4, 3, 2], 13)
    for y in range(16):
        for x in range(16):
            if y % 5 == 4:
                img[y][x] = rgb(176, 130, 74)
            if x in (0, 15) or y in (0, 15):
                img[y][x] = rgb(160, 116, 64)
    return img


def jar_tex(content, seed):
    light = tuple(min(255, c + 40) for c in content[:3]) + (255,)
    img = noisy([content, light], [3, 1], seed)
    for y in range(16):
        img[y][0] = img[y][15] = rgb(200, 226, 230)
    return img


def picture(rows, palette):
    img = blank()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                img[y][x] = palette[ch]
    return img


GAUGE = picture([".bbbb.",
                 "bwwwrb",
                 "bwwrwb",
                 "bwkwwb",
                 "bwwwwb",
                 ".bbbb."],
                {"b": BRASS[1], "w": rgb(242, 232, 208), "r": rgb(176, 40, 32), "k": rgb(60, 44, 34)})
VALVE = picture([".cccccc.",
                 "cc.cc.cc",
                 "c.ccc.ccc"[:8],
                 "cccooccc",
                 "cccooccc",
                 "c.cccc.c",
                 "cc.cc.cc",
                 ".cccccc."],
                {"c": rgb(214, 120, 70), "o": rgb(140, 66, 36)})
GEAR = picture(["...bb...",
                ".bbbbbb.",
                ".bhbbhb.",
                "bbboobbb",
                "bbboobbb",
                ".bhbbhb.",
                ".bbbbbb.",
                "...bb..."],
               {"b": BRASS[2], "h": BRASS[5], "o": BRASS[4]})

CUSTOM = {
    "brass": brass_tex(),
    "iron_plate": iron_plate_tex(),
    "iron": noisy(IRON[1:4], [4, 3, 2], 8),
    "stove_top": stove_top_tex(),
    "pot": pot_tex(),
    "soup": noisy([rgb(236, 150, 60), rgb(222, 124, 44), rgb(248, 184, 94)], [4, 3, 2], 5),
    "steam": noisy([rgb(232, 232, 230), rgb(210, 210, 208), rgb(246, 246, 244), rgb(190, 190, 188)], [4, 3, 3, 1], 6),
    "board": board_tex(),
    "blade": noisy([rgb(214, 218, 222), rgb(190, 194, 200)], [3, 2], 14),
    "tomato": noisy([rgb(214, 48, 36), rgb(184, 34, 26), rgb(236, 84, 64)], [4, 3, 1], 15),
    "carrot": noisy([rgb(240, 132, 36), rgb(220, 104, 24)], [3, 2], 16),
    "leaf": noisy([rgb(84, 156, 50), rgb(62, 128, 38)], [3, 2], 17),
    "jar_red": jar_tex(rgb(186, 52, 36), 21),
    "jar_green": jar_tex(rgb(90, 140, 52), 22),
    "jar_yellow": jar_tex(rgb(222, 176, 60), 23),
    "gauge": GAUGE,
    "valve": VALVE,
    "gear": GEAR,
}
VANILLA = ["spruce_planks", "oak_planks", "dark_oak_planks", "stripped_oak_log", "polished_andesite",
           "polished_blackstone", "copper_block", "cut_copper", "campfire_log_lit", "fire_0"]

# ═════════════ 큐브 ═════════════
elements = []
shapes = []            # 미리보기용 (회전 없는 큐브만)
VIEW_FACE = {"front": "north", "back": "south", "left": "east", "right": "west", "top": "up", "bottom": "down"}


def auto_uv(face, x0, x1, y0, y1, z0, z1):
    """블록 칸 안의 로컬 좌표(모델 방향)로 바닐라 자동 UV — 텍스처가 블록처럼 이어진다"""
    return {
        "north": [16 - x1, 16 - y1, 16 - x0, 16 - y0],
        "south": [x0, 16 - y1, x1, 16 - y0],
        "east": [16 - z1, 16 - y1, 16 - z0, 16 - y0],
        "west": [z0, 16 - y1, z1, 16 - y0],
        "up": [x0, z0, x1, z1],
        "down": [x0, 16 - z1, x1, 16 - z0],
    }[face]


def B(frm, to, tex, light=0, skip=(), faces=None):
    """정면 기준 픽셀 좌표 큐브. tex: 텍스처 이름 또는 {보이는 면 또는 "all": 이름}.
    faces: {보이는 면: (이름, [u0, v0, u1, v1])} 로 그림 직접 지정 (블록 칸 안 큐브만).
    블록 칸(16) 경계에서 잘라 텍스처를 블록처럼 맞춘다."""
    framed = isinstance(tex, str) and tex in FRAMED
    cuts = [split_cuts(frm[a], to[a], framed) for a in range(3)]
    for xa, xb in zip(cuts[0], cuts[0][1:]):
        for ya, yb in zip(cuts[1], cuts[1][1:]):
            for za, zb in zip(cuts[2], cuts[2][1:]):
                hidden = set(skip)
                hidden |= {"left"} if xa != frm[0] else set()
                hidden |= {"right"} if xb != to[0] else set()
                hidden |= {"bottom"} if ya != frm[1] else set()
                hidden |= {"top"} if yb != to[1] else set()
                hidden |= {"front"} if za != frm[2] else set()
                hidden |= {"back"} if zb != to[2] else set()
                _cube((xa, ya, za), (xb, yb, zb), tex, light, hidden, faces)


def _cube(f, t, tex, light, hidden, faces):
    mx0, mx1 = X_OFF - t[0], X_OFF - f[0]
    cx = math.floor(mx0 / 16) * 16
    cy = math.floor(f[1] / 16) * 16
    cz = math.floor(f[2] / 16) * 16
    out = {}
    for view, face in VIEW_FACE.items():
        if view in hidden:
            continue
        if faces and view in faces:
            name, uv = faces[view]
        else:
            name = tex.get(view, tex.get("all")) if isinstance(tex, dict) else tex
            if name is None:
                continue
            if name in FRAMED:
                name, uv = framed_face(name, *face_dims(face, f, t))
            else:
                uv = auto_uv(face, mx0 - cx, mx1 - cx, f[1] - cy, t[1] - cy, f[2] - cz, t[2] - cz)
        out[face] = {"uv": uv, "texture": "#" + name}
    if not out:
        return
    element = {"from": [mx0, f[1], f[2]], "to": [mx1, t[1], t[2]], "faces": out}
    if light:
        element["light_emission"] = light
    elements.append(element)
    shapes.append((f, t, out))


def plate(name, size, x0, y0, z, light=0):
    """그림(size x size)을 앞면에 붙인 1픽셀 두께 판. (x0, y0) = 왼쪽 아래, z = 앞면"""
    B([x0, y0, z], [x0 + size, y0 + size, z + 1], "iron", light=light,
      faces={"front": (name, [0, 0, size, size])})


def raw(frm, to, faces, rotation=None, light=0, shade=True):
    element = {"from": frm, "to": to, "faces": faces}
    if rotation:
        element["rotation"] = rotation
    if light:
        element["light_emission"] = light
    if not shade:
        element["shade"] = False
    elements.append(element)


def fire(vx0, vx1, y0, y1, vz0, vz1):
    """바닐라 불 (애니메이션): 엇갈린 두 판"""
    mx0, mx1 = X_OFF - vx1, X_OFF - vx0
    cx, cz = (mx0 + mx1) / 2, (vz0 + vz1) / 2
    h = y1 - y0
    for angle, du in ((22.5, 0), (-22.5, 2)):
        raw([mx0, y0, cz], [mx1, y1, cz],
            {"north": {"uv": [du, 16 - h, du + mx1 - mx0, 16], "texture": "#fire_0"},
             "south": {"uv": [du, 16 - h, du + mx1 - mx0, 16], "texture": "#fire_0"}},
            rotation={"origin": [cx, y0, cz], "axis": "y", "angle": angle}, light=15, shade=False)


# ═════════════ 왼쪽 칸: 가문비 찬장 (vx 0~16) ═════════════
B([2, 0, 3], [16, 2, 14], "dark_oak_planks")                                    # 걸레받이 (들어감)
B([0, 2, 1], [16, 15, 15], "spruce_planks")                                     # 찬장 몸통
B([0, 0, 0], [2, 15, 1], "brass")                                               # 왼쪽 앞 모서리 황동 띠
B([0, 0, 1], [1, 2, 15], "brass")                                               # 아래 모서리 쇠
B([2, 11, 0], [15, 14, 1], "oak_planks")                                        # 서랍
B([5, 12, -1], [12, 13, 0], "brass")                                            # 서랍 긴 손잡이
for frm, to in (([2, 9, 0], [15, 10, 1]), ([2, 3, 0], [15, 4, 1]),             # 문짝 테 (가운데는 들어감)
                ([2, 4, 0], [3, 9, 1]), ([14, 4, 0], [15, 9, 1])):
    B(frm, to, "oak_planks")
B([12, 6, -1], [13, 7, 0], "brass")                                             # 문 손잡이

# ═════════════ 가운데 칸: 리벳 쇠 화덕 (vx 16~32) ═════════════
B([16, 0, 1], [32, 2, 15], "iron_plate")                                        # 아래
B([16, 10, 1], [32, 15, 15], "iron_plate")                                      # 위
B([16, 2, 1], [19, 10, 15], "iron_plate")                                       # 왼쪽
B([29, 2, 1], [32, 10, 15], "iron_plate")                                       # 오른쪽
B([19, 2, 10], [29, 10, 15], "polished_blackstone")                             # 화덕 안 그을린 뒷벽
B([19, 2, 1], [20, 9, 10], "polished_blackstone")                               # 그을린 옆벽
B([28, 2, 1], [29, 9, 10], "polished_blackstone")
B([19, 9, 1], [29, 10, 10], "polished_blackstone")                              # 그을린 천장
for frm, to in (([18, 1, 0], [30, 2, 1]), ([18, 10, 0], [30, 11, 1]),          # 화덕 구멍 황동 테
                ([18, 2, 0], [19, 10, 1]), ([29, 2, 0], [30, 10, 1])):
    B(frm, to, "brass")
log_side = {"uv": [0, 4, 4, 8], "texture": "#campfire_log_lit"}
for vz in (3, 6):                                                               # 장작 + 불
    raw([X_OFF - 28, 2, vz], [X_OFF - 20, 4, vz + 3],
        {"north": log_side, "south": log_side, "up": {"uv": [0, 0, 8, 3], "texture": "#campfire_log_lit"},
         "east": {"uv": [0, 1, 3, 3], "texture": "#campfire_log_lit"},
         "west": {"uv": [0, 1, 3, 3], "texture": "#campfire_log_lit"}}, light=12)
fire(20, 28, 3, 9, 3, 9)
B([16, 15, 0], [32, 16, 15], {"all": "iron", "top": "stove_top"}, light=8)      # 화구 판 (빛남)
B([16, 13, -1], [32, 15, 0], "brass")                                           # 화덕 위 황동 띠

# ═════════════ 오른쪽 칸: 무쇠 찬장 + 구리 밸브 (vx 32~48) ═════════════
B([32, 0, 3], [46, 2, 14], "dark_oak_planks")                                   # 걸레받이
B([32, 2, 1], [48, 15, 15], "iron_plate")                                       # 몸통
B([46, 0, 0], [48, 15, 1], "brass")                                             # 오른쪽 앞 모서리 황동 띠
B([47, 0, 1], [48, 2, 15], "brass")
for frm, to in (([34, 3, 0], [45, 4, 1]), ([34, 13, 0], [45, 14, 1]),          # 문 황동 테
                ([34, 4, 0], [35, 13, 1]), ([44, 4, 0], [45, 13, 1])):
    B(frm, to, "brass")
plate("valve", 8, 36, 5, -1)                                                    # 구리 밸브 (튀어나옴)

# ═════════════ 상판: 양옆은 황동 테 돌 상판 (앞으로 1픽셀) ═════════════
for x0, x1 in ((0, 16), (32, 48)):
    B([x0, 15, -1], [x1, 17, 15], {"all": "polished_andesite", "front": "brass"})

# 왼쪽 상판: 도마 + 칼 + 토마토 + 당근
B([2, 17, 2], [13, 18, 10], "board")
B([11, 17, 4], [12, 18, 8], "dark_oak_planks")                                  # 도마 손잡이 홈
B([4, 18, 3], [9, 19, 4], "blade")                                              # 칼날
B([9, 18, 3], [12, 19, 4], "dark_oak_planks")                                   # 칼 자루
B([4, 18, 5], [7, 21, 8], "tomato")                                             # 토마토
B([5, 21, 6], [6, 22, 7], "leaf")
for cx in (8, 10):
    B([cx, 18, 6], [cx + 1, 19, 8], "carrot")                                   # 썬 당근

# 가운데: 속이 빈 냄비 + 수프 + 국자 + 김
PX0, PX1, PZ0, PZ1, PY0, PY1 = 19, 29, 2, 12, 16, 24
B([PX0, PY0, PZ0], [PX1, PY1, PZ0 + 1], "pot")
B([PX0, PY0, PZ1 - 1], [PX1, PY1, PZ1], "pot")
B([PX0, PY0, PZ0 + 1], [PX0 + 1, PY1, PZ1 - 1], "pot")
B([PX1 - 1, PY0, PZ0 + 1], [PX1, PY1, PZ1 - 1], "pot")
B([PX0 + 1, PY0, PZ0 + 1], [PX1 - 1, PY1 - 2, PZ1 - 1], {"all": "pot", "top": "soup"}, light=6)
for hx in (PX0 - 2, PX1):
    B([hx, 20, 6], [hx + 2, 21, 8], "brass")                                    # 손잡이
B([26, 20, 5], [27, 27, 6], "stripped_oak_log")                                 # 국자 자루
for sx, sy, sz, s_ in ((22, 24, 5, 3), (23, 26, 6, 2)):
    B([sx, sy, sz], [sx + s_, sy + s_, sz + s_], "steam")                       # 김 (후드로 올라감)

# 오른쪽: 구리 보일러 탱크 (황동 띠, 압력 게이지, 꼭지 밸브)
B([36, 17, 3], [46, 28, 12], "copper_block")
B([37, 17, 2], [45, 28, 13], "copper_block")
for by in (18, 25):
    B([35, by, 2], [47, by + 1, 13], "brass")                                   # 황동 띠
B([38, 28, 4], [44, 29, 11], "copper_block")                                    # 둥근 윗머리
B([40, 29, 6], [42, 31, 8], "brass")                                            # 꼭지 밸브
B([39, 31, 6], [43, 32, 8], "brass")
plate("gauge", 6, 38, 20, 1, light=6)                                           # 압력 게이지

# 보일러 → 후드 구리 증기관
B([31, 22, 7], [36, 24, 9], "cut_copper")                                       # 보일러 왼쪽에서 나와
B([29, 22, 7], [31, 30, 9], "cut_copper")                                       # 위로 올라가 후드 옆으로
B([30, 21, 6], [37, 22, 10], "brass")                                           # 이음 쇠테

# ═════════════ 뒤: 리벳 쇠판 벽, 선반, 톱니, 후드·굴뚝 ═════════════
B([0, 17, 13], [48, 27, 16], "iron_plate")                                      # 리벳 쇠판 벽
B([0, 27, 13], [48, 28, 16], "brass")                                           # 벽 위 황동 테
plate("gear", 8, 4, 18, 12)                                                     # 톱니 장식
B([0, 24, 9], [15, 25, 13], "oak_planks")                                       # 양념 선반 (톱니 위)
B([2, 22, 12], [3, 24, 13], "brass")                                            # 선반 받침
B([12, 22, 12], [13, 24, 13], "brass")
for i, jar in enumerate(("jar_red", "jar_green", "jar_yellow")):
    jx = 2 + i * 4
    B([jx, 25, 10], [jx + 3, 29, 13], jar)                                      # 양념 병
    B([jx + 1, 29, 11], [jx + 2, 30, 12], "dark_oak_planks")                    # 코르크

B([17, 27, 5], [31, 29, 13], "brass")                                           # 황동 후드
B([19, 29, 7], [29, 30, 13], "brass")
B([22, 30, 9], [26, 32, 13], "cut_copper")                                      # 굴뚝 (모델 위 끝 32까지)


# ═════════════ 저장 ═════════════
def save(assets):
    tex_dir = os.path.join(assets, "textures/machine/cooking_station")
    os.makedirs(tex_dir, exist_ok=True)
    for old in os.listdir(tex_dir):
        os.remove(os.path.join(tex_dir, old))
    os.makedirs(os.path.join(assets, "models/machine"), exist_ok=True)
    used = {f["texture"][1:] for e in elements for f in e["faces"].values()}
    textures = {}
    for name in sorted(used):
        if name in CUSTOM or name in FRAMED_TEX:
            png.write(os.path.join(tex_dir, name + ".png"), CUSTOM.get(name) or FRAMED_TEX[name])
            textures[name] = "rustport:machine/cooking_station/" + name
        elif name in VANILLA:
            textures[name] = "minecraft:block/" + name
        else:
            raise AssertionError("텍스처 이름 없음: " + name)
    textures["particle"] = "rustport:machine/cooking_station/iron_plate"
    model = {
        "credit": "BrassField tools/machines/make_cooking_station.py",
        "textures": textures,
        "elements": elements,
        "display": {
            "gui": {"rotation": [25, 205, 0], "translation": [0, -2, 0], "scale": [0.36, 0.36, 0.36]},
            "ground": {"translation": [0, 2, 0], "scale": [0.18, 0.18, 0.18]},
            "firstperson_righthand": {"rotation": [0, 45, 0], "scale": [0.18, 0.18, 0.18]},
            "thirdperson_righthand": {"rotation": [75, 45, 0], "translation": [0, 2.5, 0], "scale": [0.16, 0.16, 0.16]},
        },
    }
    with open(os.path.join(assets, "models/machine/cooking_station.json"), "w", encoding="utf-8") as f:
        json.dump(model, f, indent=1)
    bad = [e for e in elements if not all(-16 <= v <= 32 for v in e["from"] + e["to"])]
    assert not bad, "좌표 범위 밖 큐브: %s" % bad[:1]
    bad_uv = [e for e in elements for fc in e["faces"].values() if not all(0 <= c <= 16 for c in fc["uv"])]
    assert not bad_uv, "UV 범위 밖: %s" % bad_uv[:1]
    print("ok, cooking_station elements: %d" % len(elements))


# ═════════════ 미리보기 (정면 / 왼쪽 앞 위에서 비스듬히; 회전 판·불은 생략) ═════════════
def preview(path, vanilla_dir, scale=10):
    images = dict(CUSTOM)
    for name in VANILLA:
        images[name] = png.read(os.path.join(vanilla_dir, name + ".png"))[:16]
    light = {"north": 1.0, "up": 1.0, "east": 0.72}

    def sample(info, a, b):
        tex = images[info["texture"][1:]]
        u0, v0, u1, v1 = info["uv"]
        tx = min(15, max(0, int(math.floor(u0 + (u1 - u0) * a))))
        ty = min(15, max(0, int(math.floor(v0 + (v1 - v0) * b))))
        return tex[ty][tx]

    def render(project, faces_used, w, h):
        img = [[rgb(70, 92, 110)] * w for _ in range(h)]
        depth = [[-1e9] * w for _ in range(h)]
        for f, t, out in shapes:
            (x0, y0, z0), (x1, y1, z1) = f, t
            for face in faces_used:
                if face not in out:
                    continue
                if face == "north":
                    fw, fh = x1 - x0, y1 - y0
                elif face == "east":
                    fw, fh = z1 - z0, y1 - y0
                else:
                    fw, fh = x1 - x0, z1 - z0
                nx, ny = int(fw * scale * 1.6) + 2, int(fh * scale * 1.6) + 2
                for i in range(nx):
                    for j in range(ny):
                        a, b = (i + 0.5) / nx, (j + 0.5) / ny
                        if face == "north":
                            p = (x0 + fw * a, y1 - fh * b, z0)
                        elif face == "east":
                            p = (x0, y1 - fh * b, z1 - fw * a)
                        else:
                            p = (x1 - fw * a, y1, z0 + fh * b)
                        c = sample(out[face], a, b)
                        if c[3] < 128:
                            continue
                        sx, sy, d = project(p)
                        sx, sy = int(sx), int(sy)
                        if 0 <= sx < w and 0 <= sy < h and d >= depth[sy][sx]:
                            depth[sy][sx] = d
                            img[sy][sx] = tuple(int(c[q] * light[face]) for q in range(3)) + (255,)
        return img

    fw_, fh_ = 54 * scale, 36 * scale
    front = render(lambda p: ((p[0] + 3) * scale, (34 - p[1]) * scale, -p[2]), ("north",), fw_, fh_)
    iw, ih = 62 * scale, 44 * scale
    iso = render(lambda p: ((p[0] * 0.95 + p[2] * 0.55 + 4) * scale,
                            (40 - p[1] - p[2] * 0.45 + p[0] * 0.1) * scale,
                            -p[2] - p[0] * 0.25 + p[1] * 0.2), ("north", "east", "up"), iw, ih)
    sheet = png.blank(fw_ + iw + 8, max(fh_, ih))
    png.paste(sheet, front, 0, 0)
    png.paste(sheet, iso, fw_ + 8, 0)
    png.write(path, sheet)


save(sys.argv[1])
if os.environ.get("PREVIEW"):
    preview(os.environ["PREVIEW"], os.environ["VANILLA"])

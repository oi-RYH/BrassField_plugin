"""
가구 모델 공용 도구 (요리 기기 등): 바닐라 픽셀 크기(1 모델 단위 = 텍스처 1픽셀 = 1/16 블록)로 큐브를 쌓는다.

- 좌표는 정면 기준 vx(왼쪽 → 오른쪽), y(아래 → 위), z(앞 → 뒤) 픽셀. 저장할 때 모델 x = x_off - vx.
- 큐브는 블록 칸(16) 경계에서 잘라 바닐라 텍스처가 실제 블록처럼 이어지게 한다 (자동 UV).
- 텍스처 이름이 CUSTOM 에 있으면 직접 그린 그림(rustport:<폴더>/<이름>), 아니면 바닐라 minecraft:block/<이름> 참조.
- 직접 그리는 그림은 스팀펑크 공용 재질(황동, 리벳 쇠판, 쇠, 김 등)과 기기별 그림.

사용: from furniture_kit import Model, CUSTOM, ...  → m = Model("이름", x_off) → m.box(...) ... → m.save(assets, "machine/cooking")
"""
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "hud"))
import png  # noqa: E402

T = (0, 0, 0, 0)


def rgb(r, g, b, a=255):
    return (r, g, b, a)


def blank():
    return [[T] * 16 for _ in range(16)]


def noisy(colors, weights, seed):
    r = random.Random(seed)
    return [[r.choices(colors, weights)[0] for _ in range(16)] for _ in range(16)]


def picture(rows, palette):
    """글자 그리드(16 이하) → 16x16 그림 ('.' 투명)"""
    img = blank()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                img[y][x] = palette[ch]
    return img


# ═════════════ 공용 재질 (16x16, 바닐라 금속 블록처럼 섞인 색) ═════════════
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


def _brass():
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


def _iron_plate():
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


CUSTOM = {
    "brass": _brass(),
    "iron_plate": _iron_plate(),
    "iron": noisy(IRON[1:4], [4, 3, 2], 8),
    "steam": noisy([rgb(232, 232, 230), rgb(210, 210, 208), rgb(246, 246, 244), rgb(190, 190, 188)], [4, 3, 3, 1], 6),
    "gauge": picture([".bbbb.", "bwwwrb", "bwwrwb", "bwkwwb", "bwwwwb", ".bbbb."],
                     {"b": BRASS[1], "w": rgb(242, 232, 208), "r": rgb(176, 40, 32), "k": rgb(60, 44, 34)}),
    "gear": picture(["...bb...", ".bbbbbb.", ".bhbbhb.", "bbboobbb", "bbboobbb", ".bhbbhb.", ".bbbbbb.", "...bb..."],
                    {"b": BRASS[2], "h": BRASS[5], "o": BRASS[4]}),
}


# ═════════════ 모델 ═════════════
VIEW_FACE = {"front": "north", "back": "south", "left": "east", "right": "west", "top": "up", "bottom": "down"}


def auto_uv(face, x0, x1, y0, y1, z0, z1):
    return {
        "north": [16 - x1, 16 - y1, 16 - x0, 16 - y0],
        "south": [x0, 16 - y1, x1, 16 - y0],
        "east": [16 - z1, 16 - y1, 16 - z0, 16 - y0],
        "west": [z0, 16 - y1, z1, 16 - y0],
        "up": [x0, z0, x1, z1],
        "down": [x0, 16 - z1, x1, 16 - z0],
    }[face]


FRAMED = {"brass", "iron_plate", "juice"}   # 부품 면마다 그 면 크기에 맞춰 그리는 재질 (테두리·수면이 면 가장자리에 오게)
FRAMED_TEX = {}                       # 크기별로 만든 테두리 텍스처 (이름 → 32x32 그림)


def _framed_img(name, w, h):
    """w x h 픽셀 면에 꼭 맞는 테두리 그림 (32x32 캔버스의 왼쪽 위). 산업용 철·Create 황동처럼
    바깥 1픽셀 짙은 테, 안쪽 위·왼쪽 밝은 줄, 아래·오른쪽 어두운 줄, 모서리 볼트(쇠)·짙은 모서리(황동).
    한 변이 4픽셀보다 작으면 그 방향으로는 테를 그리지 않는다 (얇은 띠·손잡이)."""
    img = [[T] * 32 for _ in range(32)]
    rnd = random.Random(w * 37 + h * 101 + (1 if name == "brass" else 0))
    iron = name == "iron_plate"
    runs = []
    for y in range(h):                                     # 쇠: 아주 옅은 가로 결
        row = []
        while len(row) < w:
            row += [rnd.choices([IRON[1], IRON_LIGHT, IRON[2]], [10, 1, 1])[0]] * rnd.randint(2, 5)
        runs.append(row[:w])
    fx, fy = w >= 4, h >= 4
    for y in range(h):
        for x in range(w):
            ex = fx and x in (0, w - 1)
            ey = fy and y in (0, h - 1)
            if iron:
                if ex and ey:
                    c = IRON_BOLT
                elif ex or ey:
                    c = IRON_EDGE
                elif (fx and x == 1) or (fy and y == 1):
                    c = IRON[0]
                elif (fx and x == w - 2) or (fy and y == h - 2):
                    c = IRON[2]
                else:
                    c = runs[y][x]
            else:
                if ex and ey:
                    c = BRASS_EDGE[2]
                elif ex or ey:
                    c = BRASS_EDGE[1] if (x == w - 1 or y == h - 1) else BRASS_EDGE[0]
                elif (fx and x == 1) or (fy and y == 1):
                    c = BRASS_LINE
                elif (fx and x == w - 2) or (fy and y == h - 2):
                    c = BRASS[3]
                else:
                    d = (x + y) % 7
                    c = BRASS[1] if d == 0 else (BRASS_MID if d in (1, 4) else BRASS[2])
            img[y][x] = c
    return img


JUICE = [rgb(255, 222, 140), rgb(252, 194, 84), rgb(246, 166, 52), rgb(232, 140, 38), rgb(212, 116, 30)]


def _liquid_img(w, h, top):
    """주스 (액체): 옆면은 위 수면 줄이 밝고 아래로 갈수록 짙어지는 부드러운 단계 + 세로 유리 반사 + 거품 몇 개,
    윗면은 잔잔한 수면에 옅은 물결"""
    img = [[T] * 32 for _ in range(32)]
    for y in range(h):
        for x in range(w):
            if top:
                c = JUICE[1] if (x + 2 * y) % 7 else JUICE[0]
            elif y == 0:
                c = JUICE[0]                                        # 수면
            else:
                c = JUICE[min(4, 1 + int((y - 1) / max(1, h - 1) * 4))]
                if x == 1 and 1 <= y < h - 1:
                    c = JUICE[1]                                    # 유리 반사
            img[y][x] = c
    if not top and w >= 5 and h >= 6:
        for bx, by in ((w - 3, h - 3), (w - 4, h - 6), (w - 3, h - 9)):
            if 1 <= by < h:
                img[by][bx] = JUICE[0]                              # 거품
    return img


def framed_face(name, w, h, face="north"):
    """테두리·액체 재질 면 → (텍스처 이름, UV). 32x32 그림이라 UV 1 = 2픽셀, 면 1픽셀 = 텍스처 1픽셀 (바닐라 크기 유지)"""
    w, h = max(1, min(32, round(w))), max(1, min(32, round(h)))
    top = face in ("up", "down")
    key = "%s_%dx%d%s" % (name, w, h, "_top" if (top and name == "juice") else "")
    if key not in FRAMED_TEX:
        FRAMED_TEX[key] = _liquid_img(w, h, top) if name == "juice" else _framed_img(name, w, h)
    return key, [0, 0, w / 2, h / 2]


def face_dims(face, f, t):
    dx, dy, dz = (t[i] - f[i] for i in range(3))
    return {"north": (dx, dy), "south": (dx, dy), "east": (dz, dy), "west": (dz, dy), "up": (dx, dz), "down": (dx, dz)}[face]


def split_cuts(lo, hi, framed):
    """큐브를 나눌 위치. 보통은 블록 칸(16) 경계, 테두리 재질은 32픽셀 이하 조각으로만 (테두리가 부품 가장자리에 오게)"""
    if framed:
        n = max(1, math.ceil((hi - lo) / 32))
        return [lo + (hi - lo) * i / n for i in range(n + 1)]
    return [lo, *[c for c in (-16, 0, 16, 32) if lo < c < hi], hi]


class Model:
    def __init__(self, name, x_off=16):
        self.name = name
        self.x_off = x_off
        self.elements = []

    def box(self, frm, to, tex, light=0, skip=(), faces=None):
        """정면 기준 픽셀 큐브. tex: 이름 또는 {보이는 면 또는 "all": 이름(None = 면 없음)}.
        faces: {보이는 면: (이름, [u0, v0, u1, v1])} 로 그림 직접 지정 (블록 칸 안의 큐브만)."""
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
                    self._cube((xa, ya, za), (xb, yb, zb), tex, light, hidden, faces)

    def _cube(self, f, t, tex, light, hidden, faces):
        mx0, mx1 = self.x_off - t[0], self.x_off - f[0]
        cx, cy, cz = (math.floor(v / 16) * 16 for v in (mx0, f[1], f[2]))
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
                    name, uv = framed_face(name, *face_dims(face, f, t), face)
                else:
                    uv = auto_uv(face, mx0 - cx, mx1 - cx, f[1] - cy, t[1] - cy, f[2] - cz, t[2] - cz)
            out[face] = {"uv": uv, "texture": "#" + name}
        if not out:
            return
        element = {"from": [mx0, f[1], f[2]], "to": [mx1, t[1], t[2]], "faces": out}
        if light:
            element["light_emission"] = light
        self.elements.append(element)

    def plate(self, name, w, h, x0, y0, z, light=0, depth=1):
        """그림(w x h 픽셀)을 앞면에 붙인 얇은 판. (x0, y0) = 왼쪽 아래, z = 앞면"""
        self.box([x0, y0, z], [x0 + w, y0 + h, z + depth], "iron", light=light, faces={"front": (name, [0, 0, w, h])})

    def raw(self, frm, to, faces, rotation=None, light=0, shade=True):
        element = {"from": frm, "to": to, "faces": faces}
        if rotation:
            element["rotation"] = rotation
        if light:
            element["light_emission"] = light
        if not shade:
            element["shade"] = False
        self.elements.append(element)

    def fire(self, vx0, vx1, y0, y1, vz):
        """바닐라 불 (애니메이션): 엇갈린 두 판, 가운데 깊이 vz"""
        mx0, mx1 = self.x_off - vx1, self.x_off - vx0
        cx = (mx0 + mx1) / 2
        h = y1 - y0
        for angle, du in ((22.5, 0), (-22.5, 2)):
            uv = [du, 16 - h, du + mx1 - mx0, 16]
            self.raw([mx0, y0, vz], [mx1, y1, vz], {"north": {"uv": uv, "texture": "#fire_0"}, "south": {"uv": uv, "texture": "#fire_0"}},
                     rotation={"origin": [cx, y0, vz], "axis": "y", "angle": angle}, light=15, shade=False)

    def logs(self, vx0, vx1, y0, vzs):
        """바닐라 모닥불 장작 (빛남)"""
        side = {"uv": [0, 4, 4, 8], "texture": "#campfire_log_lit"}
        n = vx1 - vx0
        for vz in vzs:
            self.raw([self.x_off - vx1, y0, vz], [self.x_off - vx0, y0 + 2, vz + 3],
                     {"north": side, "south": side, "up": {"uv": [0, 0, n, 3], "texture": "#campfire_log_lit"},
                      "east": {"uv": [0, 1, 3, 3], "texture": "#campfire_log_lit"},
                      "west": {"uv": [0, 1, 3, 3], "texture": "#campfire_log_lit"}}, light=12)

    def save(self, assets, folder, custom, display=None):
        """모델 → assets/<ns>/models/<folder>/<name>.json, 직접 그린 그림 → textures/<folder>/<name>/"""
        tex_dir = os.path.join(assets, "rustport/textures", folder, self.name)
        model_dir = os.path.join(assets, "rustport/models", folder)
        os.makedirs(tex_dir, exist_ok=True)
        os.makedirs(model_dir, exist_ok=True)
        for old in os.listdir(tex_dir):
            os.remove(os.path.join(tex_dir, old))
        used = {f["texture"][1:] for e in self.elements for f in e["faces"].values()}
        custom = {**custom, **FRAMED_TEX}
        textures = {}
        for name in sorted(used):
            if name in custom:
                png.write(os.path.join(tex_dir, name + ".png"), custom[name])
                textures[name] = "rustport:%s/%s/%s" % (folder, self.name, name)
            else:
                textures[name] = "minecraft:block/" + name
        textures["particle"] = textures.get("iron_plate") or next(iter(textures.values()))
        model = {"credit": "BrassField tools/machines", "textures": textures, "elements": self.elements,
                 "display": display or {
                     "gui": {"rotation": [25, 205, 0], "translation": [0, -1, 0], "scale": [0.5, 0.5, 0.5]},
                     "ground": {"translation": [0, 2, 0], "scale": [0.25, 0.25, 0.25]},
                     "firstperson_righthand": {"rotation": [0, 45, 0], "scale": [0.3, 0.3, 0.3]},
                     "thirdperson_righthand": {"rotation": [75, 45, 0], "translation": [0, 2.5, 0], "scale": [0.25, 0.25, 0.25]},
                 }}
        with open(os.path.join(model_dir, self.name + ".json"), "w", encoding="utf-8") as f:
            json.dump(model, f, indent=1)
        bad = [e for e in self.elements if not all(-16 <= v <= 32 for v in e["from"] + e["to"])]
        assert not bad, "%s: 좌표 범위 밖 큐브 %s" % (self.name, bad[:1])
        bad_uv = [e for e in self.elements for fc in e["faces"].values() if not all(0 <= c <= 16 for c in fc["uv"])]
        assert not bad_uv, "%s: UV 범위 밖 %s" % (self.name, bad_uv[:1])
        print("ok, %s elements: %d" % (self.name, len(self.elements)))
        return os.path.join(model_dir, self.name + ".json")

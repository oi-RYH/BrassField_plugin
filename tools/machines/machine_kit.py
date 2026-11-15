"""
거래 기계 모델 공용 도구: 재질 텍스처(128x128, 블록당 32px)와 큐브 만들기, 저장, 미리보기.

- 금속(철·황동)은 노이즈 없이 매끄러운 명암: 판재는 베벨·사선 반사띠, 막대(파이프·기둥)는 원통 명암.
- 검은 외곽선 없이 같은 재질의 밝고 어두운 색과 실제 큐브 형태로 입체감을 낸다.
- 각 기계 스크립트는 `from machine_kit import *` 후 region()으로 전용 그림을 더하고 cube()로 모델을 쌓은 뒤 save()한다.
  (스크립트마다 프로세스가 따로라 텍스처·큐브 목록은 기계마다 새로 시작한다)
"""
import json
import math
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
DARK_M = region(16, 26, lambda x, y: DARK[1] if x % 4 else DARK[0])
FLOOR_M = region(16, 10, lambda x, y: DARK[2] if (x + y) % 5 else DARK[1])
HOLE_M = region(8, 8, lambda x, y: DARK[3])
GLASS_M = region(16, 26, lambda x, y: rgb(225, 245, 245, 120) if (x - y // 3) in (3, 4, 10) else rgb(150, 200, 205, 55))
LIGHT_STRIP_M = region(16, 2, lambda x, y: rgb(255, 244, 214))



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


# ═════════════ 저장 ═════════════
def save(assets, name, credit, display=None):
    """텍스처와 모델을 assets/textures|models/machine/<name> 로 저장하고 큐브 좌표 범위를 검사한다."""
    os.makedirs(os.path.join(assets, "textures/machine"), exist_ok=True)
    os.makedirs(os.path.join(assets, "models/machine"), exist_ok=True)
    png.write(os.path.join(assets, "textures/machine/%s.png" % name), tex)
    model = {
        "credit": credit,
        "texture_size": [TEX, TEX],
        "textures": {"0": "rustport:machine/" + name, "particle": "rustport:machine/" + name},
        "elements": elements,
        "display": display or {
            "gui": {"rotation": [20, 205, 0], "translation": [0, -3, 0], "scale": [0.36, 0.36, 0.36]},
            "ground": {"translation": [0, 2, 0], "scale": [0.3, 0.3, 0.3]},
            "firstperson_righthand": {"rotation": [0, 45, 0], "scale": [0.3, 0.3, 0.3]},
            "thirdperson_righthand": {"rotation": [75, 45, 0], "translation": [0, 2.5, 0], "scale": [0.25, 0.25, 0.25]},
        },
    }
    with open(os.path.join(assets, "models/machine/%s.json" % name), "w", encoding="utf-8") as f:
        json.dump(model, f, indent=1)
    bad = [e for e in elements if not all(-16 <= v <= 32 for v in e["from"] + e["to"])]
    assert not bad, "좌표 범위 밖 큐브: %s" % bad[:1]
    bad_uv = [e for e in elements for fc in e["faces"].values() if not all(0 <= c <= 16 for c in fc["uv"])]
    assert not bad_uv, "UV 범위 밖 큐브: %s" % bad_uv[:1]
    print("ok, %s elements: %d" % (name, len(elements)))
    if os.environ.get("PREVIEW"):
        front_v, side_v = project("north"), project("east")
        sheet = png.blank(len(front_v[0]) + len(side_v[0]) + 8, len(front_v))
        png.paste(sheet, front_v, 0, 0)
        png.paste(sheet, side_v, len(front_v[0]) + 8, 0)
        png.write(os.environ["PREVIEW"], png.scale(sheet, 2))


# ═════════════ 미리보기 (정면 / 오른쪽 옆면, 뒤에서부터 덮어 그리고 반투명은 섞음) ═════════════

def project(view, scale=4):
    """정면(north) 또는 옆면(east)을 플레이어가 보는 방향 그대로 평면 합성한다. (회전 큐브는 회전 없이 그림)
    정면: 모델 x가 클수록 화면 왼쪽 / 옆면(동쪽에서 서쪽을 봄): 앞(z 작음)이 화면 오른쪽"""
    xs = [v for e in elements for v in (e["from"][0], e["to"][0])]
    zs = [v for e in elements for v in (e["from"][2], e["to"][2])]
    x_min, x_max, z_min, z_max = min(xs), max(xs), min(zs), max(zs)
    width = (x_max - x_min) if view == "north" else (z_max - z_min)
    img = [[rgb(70, 92, 110)] * int(math.ceil(width * scale)) for _ in range(32 * scale)]
    if view == "north":
        order = sorted(elements, key=lambda e: -e["from"][2])
        span = lambda e: (x_max - e["to"][0], x_max - e["from"][0])
    else:
        order = sorted(elements, key=lambda e: e["to"][0])
        span = lambda e: (z_max - e["to"][2], z_max - e["from"][2])
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

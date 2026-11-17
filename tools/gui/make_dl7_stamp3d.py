"""
DL-7 납품 도장 3D 모델 (아이템 모델 JSON + 색 판 텍스처) 과 영수증 위에서 찍히는 연출 장면.
  모델: 붉은 고무면 · 나무 받침 · 황동 고리 · 나무 목 · 둥근(정육면체) 나무 손잡이를 쌓은 직육면체 5개.
        텍스처는 4x4 색 칸 16x16 한 장(item/gui/dl7_stamp3d.png), 면마다 해당 색 칸을 쓴다.
  연출: 영수증 쪽 칸 하나(STAMP_SLOT)에 장면 모델을 차례로 넣는다. 장면마다 창 안 표시(display.gui)의 위치만 달라
        도장이 영수증 자국 자리 위에서 내려와 찍히고(살짝 눌림) 들어 올려진다.
  미리보기: 창 안 각도(블록 아이콘처럼 위에서 비스듬히)로 직육면체를 간단히 투영해 그린다 (게임 화면과 조금 다를 수 있음).
"""
import json
import math
import sys

from PIL import Image, ImageDraw

COLORS = {"wood": (162, 74, 40), "wood_hi": (214, 120, 76), "wood_lo": (104, 44, 24), "brass": (196, 140, 60),
          "brass_hi": (242, 196, 112), "red": (196, 40, 30), "red_lo": (130, 22, 16), "dark": (40, 20, 12)}
CELL = {name: (i % 4, i // 4) for i, name in enumerate(COLORS)}
# 직육면체: (이름, from, to, 윗면 색, 옆면 색, 아랫면 색)
PARTS = [
    ("rubber", (3, 0, 5), (13, 1, 11), "red", "red", "red_lo"),
    ("base", (3, 1, 5), (13, 4, 11), "wood", "wood_lo", "wood_lo"),
    ("collar", (5, 4, 6), (11, 5, 10), "brass_hi", "brass", "brass"),
    ("neck", (7, 5, 7), (9, 10, 9), "wood", "wood", "wood_lo"),
    ("knob", (5.5, 10, 5.5), (10.5, 15, 10.5), "wood_hi", "wood", "wood_lo"),
]
GUI_ROTATION = [30, 225, 0]
GUI_SCALE = 1.0
# 장면: (이름, 위로 띄우는 높이, 세로 눌림 배율)  — PRESS_FRAME 장면에서 자국을 남긴다
FRAMES = [("high", 14, 1.0), ("mid", 7, 1.0), ("press", 0, 0.88), ("lift", 6, 1.0)]
PRESS_FRAME = 2
STAMP_SLOT = (2, 8)                       # 도장을 넣는 칸 (줄, 열) — 영수증 오른쪽 아래
MARK_CENTER = (155, 65)                   # 영수증 위 자국 가운데 (창 기준)
# 칸 가운데 → 자국 자리로 옮기는 기본 위치 (창 안 표시 단위 = 1px, y 는 위로 +).
# 도장면 가운데(모델 8,0,8)는 30도 기울여 보면 칸 가운데보다 8·cos30·배율 만큼 아래에 오므로 그만큼 올려 자국 가운데에 맞춘다.
SLOT_CENTER = (7 + STAMP_SLOT[1] * 18 + 9, 17 + STAMP_SLOT[0] * 18 + 9)
BASE_OFFSET = (MARK_CENTER[0] - SLOT_CENTER[0],
               round(8 * math.cos(math.radians(GUI_ROTATION[0])) * GUI_SCALE - (MARK_CENTER[1] - SLOT_CENTER[1])))


def atlas():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for name, (cx, cy) in CELL.items():
        d.rectangle([cx * 4, cy * 4, cx * 4 + 3, cy * 4 + 3], fill=COLORS[name] + (255,))
    return img


def uv(color):
    cx, cy = CELL[color]
    return [cx * 4 + 0.5, cy * 4 + 0.5, cx * 4 + 3.5, cy * 4 + 3.5]


def model(texture, frame):
    _, lift, squash = frame
    elements = []
    for name, a, b, top, side, bottom in PARTS:
        faces = {f: {"uv": uv(side), "texture": "#0"} for f in ("north", "south", "east", "west")}
        faces["up"] = {"uv": uv(top), "texture": "#0"}
        faces["down"] = {"uv": uv(bottom), "texture": "#0"}
        elements.append({"name": name, "from": list(a), "to": list(b), "faces": faces})
    return {
        "textures": {"0": texture, "particle": texture},
        "elements": elements,
        "display": {"gui": {"rotation": GUI_ROTATION,
                            "translation": [BASE_OFFSET[0], BASE_OFFSET[1] + lift, 0],
                            "scale": [GUI_SCALE, GUI_SCALE * squash, GUI_SCALE]}},
        "gui_light": "side",
    }


def model_json(texture, frame):
    return json.dumps(model(texture, frame), ensure_ascii=False)


# ── 간이 미리보기: 창 안 표시 변환을 흉내 내 직육면체를 투영 ──
def _rot(v, rx, ry):
    x, y, z = v
    c, s = math.cos(math.radians(ry)), math.sin(math.radians(ry))
    x, z = x * c + z * s, -x * s + z * c
    c, s = math.cos(math.radians(rx)), math.sin(math.radians(rx))
    y, z = y * c - z * s, y * s + z * c
    return x, y, z


def render_on(img, frame, k=1):
    """img(창 그림을 k 배로 키운 것) 위에 장면 frame 의 도장을 그린다"""
    _, lift, squash = frame
    sc, ox, oy, lift = GUI_SCALE * k, BASE_OFFSET[0] * k, BASE_OFFSET[1] * k, lift * k
    slot_center = (SLOT_CENTER[0] * k, SLOT_CENTER[1] * k)
    d = ImageDraw.Draw(img)
    faces = []
    shade = {"up": 1.0, "south": 0.8, "west": 0.6, "north": 0.8, "east": 0.6, "down": 0.5}
    for name, a, b, top, side, bottom in PARTS:
        xs, ys, zs = (a[0], b[0]), (a[1], b[1]), (a[2], b[2])
        quads = {"up": [(x, ys[1], z) for x, z in ((xs[0], zs[0]), (xs[1], zs[0]), (xs[1], zs[1]), (xs[0], zs[1]))],
                 "down": [(x, ys[0], z) for x, z in ((xs[0], zs[0]), (xs[1], zs[0]), (xs[1], zs[1]), (xs[0], zs[1]))],
                 "south": [(x, y, zs[1]) for x, y in ((xs[0], ys[0]), (xs[1], ys[0]), (xs[1], ys[1]), (xs[0], ys[1]))],
                 "north": [(x, y, zs[0]) for x, y in ((xs[0], ys[0]), (xs[1], ys[0]), (xs[1], ys[1]), (xs[0], ys[1]))],
                 "east": [(xs[1], y, z) for y, z in ((ys[0], zs[0]), (ys[1], zs[0]), (ys[1], zs[1]), (ys[0], zs[1]))],
                 "west": [(xs[0], y, z) for y, z in ((ys[0], zs[0]), (ys[1], zs[0]), (ys[1], zs[1]), (ys[0], zs[1]))]}
        for f, quad in quads.items():
            col = COLORS[top if f == "up" else bottom if f == "down" else side]
            pts = []
            for x, y, z in quad:
                v = _rot(((x - 8) * sc, (y - 8) * sc * squash, (z - 8) * sc), GUI_ROTATION[0], GUI_ROTATION[1])
                pts.append(v)
            depth = sum(p[2] for p in pts) / 4
            faces.append((depth, [(slot_center[0] + p[0] + ox, slot_center[1] - p[1] - oy - lift) for p in pts],
                          tuple(int(c * shade[f]) for c in col)))
    for _, pts, col in sorted(faces, key=lambda t: t[0]):
        d.polygon(pts, fill=col + (255,), outline=(30, 16, 10, 255))
    return img


if __name__ == "__main__":                 # 미리보기: python3 make_dl7_stamp3d.py <dl7_bg.png> <자국.png> <출력.png>
    from PIL import ImageFont
    bg = Image.open(sys.argv[1]).convert("RGBA").crop((0, 0, 176, 90))
    mark = Image.open(sys.argv[2]).convert("RGBA")
    k, panels = 8, []
    for i, frame in enumerate(FRAMES):
        layer = bg.copy()
        if i >= PRESS_FRAME:
            layer.alpha_composite(mark, (MARK_CENTER[0] - mark.width // 2, MARK_CENTER[1] - mark.height // 2))
        big = layer.resize((176 * k, 90 * k), Image.NEAREST)
        render_on(big, frame, k)
        panels.append(big.crop((112 * k, 0, 176 * k, 90 * k)).resize((64 * 5, 90 * 5)))
    sheet = Image.new("RGBA", (len(panels) * 335 + 10, 90 * 5 + 40), (40, 40, 40, 255))
    d = ImageDraw.Draw(sheet)
    f = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", 20, index=6)
    for i, (panel, label) in enumerate(zip(panels, ["1. 높이", "2. 내려옴", "3. 쾅 (자국)", "4. 들어 올림"])):
        sheet.alpha_composite(panel, (10 + i * 335, 34))
        d.text((10 + i * 335, 6), label, font=f, fill=(230, 220, 200))
    sheet.save(sys.argv[3])
    print("offset", BASE_OFFSET)

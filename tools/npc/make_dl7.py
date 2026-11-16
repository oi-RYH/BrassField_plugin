"""
DL-7 (요리 납품 로봇): 사용자 시안(art/dl7_machine_sheet.png, 이동형 화물 기계)을 보고 만든 ItemsAdder 가구용 3D 모델.

- 몸 (body): 바닥에 서는 가구. 양옆 무한궤도(황동 바퀴 3개) + 크림색 흙받이·차체 + 앞 전조등 +
  집게팔 두 개가 든 나무 납품 상자(포크·나이프 문양) + 등의 큰 나무 화물칸(끈·등불) + 빨간 천.
- 머리 (head_<표정>): 몸 위에 따로 띄우는 표시 엔티티용 모델 (플레이어 쪽으로 고개를 돌릴 수 있게 분리).
  모니터 얼굴 + 위 문양 판 + 양옆 빛나는 황동 램프 + 요리사 모자. 표정 8종은 화면 그림만 다르다.
- 크기: 시안 1.6 × 1.2 × 1.4m (모자 제외) 비율. 텍스처는 1칸 = 1픽셀 (바닐라 단위, 다른 기계와 같음).

사용: python3 -I tools/npc/make_dl7.py <ItemsAdder rustport assets 폴더> [미리보기 모델 출력 경로]
  → models/machine/dl7/{body,head_<표정>}.json, textures/machine/dl7/*.png
"""
import json
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "hud"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import png  # noqa: E402
from pixelart import rgb, blank  # noqa: E402

rnd = random.Random(710)
CREAM = [rgb(244, 232, 216), rgb(236, 222, 204), rgb(240, 228, 210)]
CREAM_SHADE = [rgb(212, 192, 170), rgb(202, 182, 160)]
HAT = [rgb(252, 246, 238), rgb(246, 238, 228), rgb(238, 228, 216)]
WOOD = [rgb(196, 120, 48), rgb(182, 108, 42), rgb(204, 130, 56)]
WOOD_LINE = rgb(132, 74, 30)
BRASS = [rgb(236, 168, 48), rgb(218, 148, 36)]
BRASS_DARK = rgb(150, 90, 24)
GLOW = rgb(255, 214, 104)
GLOW_EDGE = rgb(222, 150, 46)
SCREEN = rgb(42, 30, 25)
SCREEN_EDGE = rgb(60, 44, 36)
BLUSH = rgb(178, 52, 40)
RUBBER = [rgb(58, 48, 44), rgb(50, 41, 38)]
IRON = [rgb(92, 78, 70), rgb(82, 70, 63)]
PLATE = [rgb(92, 60, 40), rgb(84, 54, 36)]
RED = [rgb(176, 50, 38), rgb(158, 40, 32)]
CLAW = [rgb(226, 224, 220), rgb(212, 210, 206)]
FACES = ("normal", "happy", "focus", "sparkle", "surprised", "thinking", "heart", "sleepy")
FULL = {f: [0, 0, 16, 16] for f in ("north", "south", "east", "west", "up", "down")}


def noise(cols):
    return [[rnd.choice(cols) for _ in range(16)] for _ in range(16)]


def wood():
    """나무 판자: 3칸마다 짙은 결"""
    img = noise(WOOD)
    for y in range(0, 16, 3):
        for x in range(16):
            img[y][x] = WOOD_LINE
    return img


def emblem(img, x0, y0, w, h, c=None):
    """포크·나이프 X 문양 (w x h 칸)"""
    c = c or BRASS[0]
    n = min(w, h)
    for i in range(n):
        fx = x0 + round(i * (w - 1) / max(1, n - 1))
        img[y0 + i][fx] = c                                        # 나이프 (왼쪽 위 → 오른쪽 아래)
        img[y0 + i][x0 + w - 1 - (fx - x0)] = c                    # 포크 (오른쪽 위 → 왼쪽 아래)
    img[y0][x0 + w - 2] = img[y0 + 1][x0 + w - 1] = c             # 포크 갈래
    img[y0][x0 + 1] = c                                            # 나이프 날
    return img


def crate_front():
    """앞 납품 상자 정면 (12x7): 나무 + 황동 테두리 + 문양"""
    img = wood()
    for y in range(7):
        img[y][0] = img[y][11] = BRASS[1]
    for x in range(12):
        img[0][x] = img[6][x] = BRASS[1]
    return emblem(img, 3, 1, 6, 5)


def cargo_back():
    """등 화물칸 뒷면 (12x11): 나무 + 세로 끈 두 줄 + 문양"""
    img = wood()
    for y in range(11):
        img[y][2] = img[y][9] = rgb(110, 64, 30)
    return emblem(img, 3, 3, 6, 5)


def track_side():
    """무한궤도 옆면 (16x6): 고무 + 황동 바퀴 3개"""
    img = noise(RUBBER)
    for cx in (3, 8, 13):
        for y in range(1, 5):
            for x in range(cx - 2, cx + 2):
                img[y][x] = BRASS[0] if (y in (1, 4) or x in (cx - 2, cx + 1)) else BRASS_DARK
        img[2][cx - 1] = img[3][cx] = rgb(70, 50, 36)
    return img


def tread():
    img = noise(RUBBER)
    for y in range(0, 16, 2):
        for x in range(16):
            img[y][x] = rgb(40, 33, 30)
    return img


def lamp():
    """램프·전조등: 빛나는 유리 + 황동 위아래 테"""
    img = [[GLOW if 2 <= x <= 13 else GLOW_EDGE for x in range(16)] for _ in range(16)]
    for x in range(16):
        img[0][x] = img[15][x] = BRASS[0]
    return img


def plate():
    """머리 위 문양 판 (10x3): 짙은 갈색 + 빛나는 X 문양"""
    img = noise(PLATE)
    for x, y in ((3, 0), (4, 1), (5, 2), (6, 0), (5, 1), (4, 2)):
        img[y][x] = GLOW
    return img


def screen(face):
    """모니터 앞면 (13x9): 크림 테두리 + 짙은 화면 + 빛나는 표정"""
    img = blank(16)
    for y in range(9):
        for x in range(13):
            img[y][x] = rnd.choice(CREAM) if x in (0, 12) or y in (0, 8) else SCREEN
    for x in range(1, 12):
        img[1][x] = SCREEN_EDGE

    def px(x, y, c=GLOW):
        img[y][x] = c

    if face == "normal":                                   # ‖ ‖ 기본
        for ex in (4, 8):
            for y in (3, 4, 5):
                px(ex, y)
    elif face == "happy":                                  # ^ ^ 행복 (+ 볼 홍조)
        for ex in (3, 7):
            px(ex, 5)
            px(ex + 1, 4)
            px(ex + 2, 5)
        px(2, 6, BLUSH)
        px(10, 6, BLUSH)
    elif face == "focus":                                  # > < 집중
        for x, y in ((3, 3), (4, 4), (3, 5), (9, 3), (8, 4), (9, 5)):
            px(x, y)
    elif face == "sparkle":                                # ✦ ✦ 반짝
        for ex in (4, 8):
            for dx, dy in ((0, -1), (0, 0), (0, 1), (-1, 0), (1, 0)):
                px(ex + dx, 4 + dy)
    elif face == "surprised":                              # o o 놀람
        for ex in (3, 7):
            for dx, dy in ((1, 0), (0, 1), (2, 1), (1, 2)):
                px(ex + dx, 3 + dy)
    elif face == "thinking":                               # · · · 생각 중
        for x in (4, 6, 8):
            px(x, 5)
    elif face == "heart":                                  # ♡ ♡ 하트
        for ex in (3, 7):
            for dx, dy in ((0, 0), (2, 0), (0, 1), (1, 1), (2, 1), (1, 2)):
                px(ex + dx, 3 + dy)
    else:                                                  # — — 졸림
        for ex in (3, 7):
            for dx in (0, 1, 2):
                px(ex + dx, 5, GLOW_EDGE)
    return img


def textures():
    return dict({"cream": noise(CREAM), "shade": noise(CREAM_SHADE), "hat": noise(HAT), "wood": wood(),
                 "crate": crate_front(), "cargo": cargo_back(), "brass": noise(BRASS), "lamp": lamp(),
                 "track": track_side(), "tread": tread(), "iron": noise(IRON), "plate": plate(),
                 "red": noise(RED), "claw": noise(CLAW)},
                **{"screen_" + f: screen(f) for f in FACES})


class Builder:
    def __init__(self):
        self.els = []

    def box(self, frm, to, tex, faces=None, uv=None):
        """tex: 모든 면 텍스처, faces: {면: 텍스처}, uv: {면: [u0,v0,u1,v1]} (기본: 면 크기만큼, 16 넘으면 16)"""
        dims = {"north": (to[0] - frm[0], to[1] - frm[1]), "south": (to[0] - frm[0], to[1] - frm[1]),
                "east": (to[2] - frm[2], to[1] - frm[1]), "west": (to[2] - frm[2], to[1] - frm[1]),
                "up": (to[0] - frm[0], to[2] - frm[2]), "down": (to[0] - frm[0], to[2] - frm[2])}
        out = {}
        for f, (w, h) in dims.items():
            out[f] = {"texture": "#" + (faces or {}).get(f, tex),
                      "uv": (uv or {}).get(f, [0, 0, min(16, round(w, 3)), min(16, round(h, 3))])}
        self.els.append({"from": [round(v, 3) for v in frm], "to": [round(v, 3) for v in to], "faces": out})


HEAD_BASE = (14.5, 5.5)         # 머리 아래끝 높이, 머리 가운데 z (몸 좌표). 머리 x 가운데는 8
LIFT = 5                        # 바퀴 폭을 줄인 만큼 몸체를 올린 높이


def body():
    """몸 (바닥 y=0, 정면 = 북쪽(작은 z)). 가로 x -1.8..17.8, 앞뒤 z -2.6..17.7.
    좌우 무한궤도는 안쪽으로 당겨 폭을 줄이고, 몸체(차체 위·상자·집게팔·화물칸)는 그만큼(LIFT) 올렸다."""
    b = Builder()
    for x0, x1, side in ((-0.5, 4, "west"), (12, 16.5, "east")):            # 무한궤도 (앞뒤 끝은 한 단 깎음)
        faces = {side: "track"}
        b.box([x0, 1, 0], [x1, 5, 16], "tread", faces=faces, uv={side: [0, 1, 16, 5]})
        b.box([x0, 0, 1], [x1, 5.6, 15], "tread", faces=faces, uv={side: [1, 0, 15, 5.6]})
        b.box([x0 - 0.3, 5.6, 0.5], [x1 + 0.3, 7, 15.5], "cream", faces={"down": "shade"})   # 흙받이
    for x0 in (-0.8, 14.8):                                                 # 전조등 (흙받이 앞)
        b.box([x0, 3, -0.6], [x0 + 2, 5.2, 0.6], "lamp", uv=FULL)
    b.box([4, 2, 1], [12, 9, 15], "iron")                                   # 트랙 사이 아래 차체
    n = len(b.els)
    b.box([1.5, 2, 1], [14.5, 9.5, 15], "iron", faces={"up": "cream"})      # 차체 (짙은 철)
    b.box([1.2, 7, 0.6], [14.8, 9.5, 9], "cream", faces={"down": "shade"})   # 앞 운전석 받침
    b.box([2, 2.8, -2.6], [14, 9.8, 1.4], "wood", faces={"north": "crate"}, uv={"north": [0, 0, 12, 7]})   # 앞 납품 상자
    for x0, x1 in ((0, 2.4), (13.6, 16)):                                   # 집게팔 (상자를 옆에서 잡음)
        b.box([x0, 6, -1.8], [x1, 8.4, 4], "claw")
        b.box([x0 + (0.6 if x0 < 8 else 0), 5.2, -2.2], [x1 - (0 if x0 < 8 else 0.6), 6, -0.4], "claw")
    b.box([2, 7, 9], [14, 18, 17.5], "wood", faces={"south": "cargo"}, uv={"south": [0, 0, 12, 11]})     # 등 화물칸
    for x0 in (4, 11.4):                                                    # 화물칸 끈
        b.box([x0, 6.8, 8.8], [x0 + 0.6, 18.2, 17.7], "iron")
    for x0, x1 in ((1.4, 2), (14, 14.6)):                                   # 화물칸 옆 등불
        b.box([x0, 11, 12], [x1, 14, 14], "lamp", uv=FULL)
    b.box([2.6, 18, 9.4], [13.4, 18.8, 13], "red")                         # 화물칸 위 빨간 천
    b.box([2.6, 15.5, 8.9], [3.4, 18, 13], "red")
    for e in b.els[n:]:                                                     # 몸체를 올린다
        e["from"][1] = round(e["from"][1] + LIFT, 3)
        e["to"][1] = round(e["to"][1] + LIFT, 3)
    return b.els


def head(face):
    """머리 (아래끝 y=0, 가운데 x·z 8): 모니터 13x9x9 + 위 문양 판 + 양옆 램프 + 요리사 모자."""
    b = Builder()
    b.box([1.5, 0, 3.5], [14.5, 9, 12.5], "cream", faces={"north": "screen_" + face, "down": "shade"},
          uv={"north": [0, 0, 13, 9]})                                     # 모니터
    for x0, x1 in ((-0.6, 1.5), (14.5, 16.6)):                             # 양옆 빛나는 램프 (황동 위아래 테)
        b.box([x0, 2, 5.5], [x1, 7, 10.5], "lamp", uv=FULL)
        b.box([x0 - 0.2, 1.4, 5.2], [x1 + 0.2, 2, 10.8], "brass")
        b.box([x0 - 0.2, 7, 5.2], [x1 + 0.2, 7.6, 10.8], "brass")
    b.box([3, 9, 4], [13, 12, 5.4], "plate", uv={"north": [0, 0, 10, 3]})  # 문양 판
    b.box([4, 9, 5.4], [12, 12.5, 12], "hat")                              # 모자 띠
    b.box([2.6, 12.5, 4.4], [13.4, 17, 13.2], "hat")                       # 볼록한 모자 (십자 두 판)
    b.box([3.2, 12.51, 3.8], [12.8, 16.99, 13.8], "hat")
    for cx, cz in ((5.4, 6.6), (10.6, 6.6), (8, 11)):                      # 모자 위 주름 덩이
        b.box([cx - 2.3, 17, cz - 1.7], [cx + 2.3, 18.8, cz + 1.7], "hat")
        b.box([cx - 1.7, 17.01, cz - 2.3], [cx + 1.7, 18.79, cz + 2.3], "hat")
    return b.els


def model(els, prefix):
    used = sorted({f["texture"][1:] for e in els for f in e["faces"].values()})
    tex = {t: prefix + t for t in used}
    tex["particle"] = prefix + "cream"
    return {"credit": "BrassField tools/npc/make_dl7.py", "textures": tex, "elements": els}


if __name__ == "__main__":
    assets = sys.argv[1]
    tdir, mdir = os.path.join(assets, "textures", "machine", "dl7"), os.path.join(assets, "models", "machine", "dl7")
    os.makedirs(tdir, exist_ok=True)
    os.makedirs(mdir, exist_ok=True)
    for name, img in textures().items():
        png.write(os.path.join(tdir, name + ".png"), img)
    prefix = "rustport:machine/dl7/"
    with open(os.path.join(mdir, "body.json"), "w", encoding="utf-8") as f:
        json.dump(model(body(), prefix), f, indent=1)
    for face in FACES:
        with open(os.path.join(mdir, "head_%s.json" % face), "w", encoding="utf-8") as f:
            json.dump(model(head(face), prefix), f, indent=1)
    if len(sys.argv) > 2:                                  # 미리보기: 몸 위 머리 자리에 머리를 올린다
        els = body()
        y0, cz = HEAD_BASE
        for e in head("happy"):
            e["from"] = [e["from"][0], e["from"][1] + y0, e["from"][2] + cz - 8]
            e["to"] = [e["to"][0], e["to"][1] + y0, e["to"][2] + cz - 8]
            els.append(e)
        with open(sys.argv[2], "w", encoding="utf-8") as f:
            json.dump(model(els, prefix), f, indent=1)
    print("ok")

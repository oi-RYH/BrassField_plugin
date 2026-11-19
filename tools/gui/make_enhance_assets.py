"""
강화 창(6줄) 그림 · 글꼴 그림 · 카드용 작은 아이템 모델을 만든다.

- 배경 rustport:enhance_bg : 3줄 강화 창 그림(art/enhance_bg_3row.png) 아래에 장비 목록 3줄을 끼우고
  (make_enhance_bg6.build), 목록 자리에 가로 2칸 카드 4개 x 3줄 + 오른쪽 끝 쪽 넘기기 칸(위 화살표 · 쪽 번호 · 아래 화살표)을 그린다.
  카드 = 황동 테두리 + 왼쪽 음각 받침(아이템 아이콘 자리) + 오른쪽 강화 단계 자리.
- 글꼴 그림 (1배, 그림 높이 = scale_ratio): 강화 단계 숫자 "+0~9"(3x5 도트) 와 "/" 를 목록 3줄 높이마다 하나씩,
  착용 중 카드의 검붉은 테두리 (줄마다 하나). y_position = 13 - (창 기준 그림 윗줄 y).
- 카드 모델: customitem 무기 · 방어구 모델을 부모로 하고 인벤토리 표시(gui)만 90% 로 줄인 모델과 아이템 정의
  (rustport:card/<아이템 이름>). 플러그인이 목록에 띄우는 복사본에만 item_model 로 붙인다.

좌표·이름은 com.brassfield.enhancement.EnhanceList 와 맞춘다.
사용: python3 tools/gui/make_enhance_assets.py <ItemsAdder contents 폴더>
"""
import json
import os
import re
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_enhance_bg6  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

LIST_TOP = 71          # 목록 첫 줄 카드 윗줄 (6줄 창의 3번째 줄 칸 테두리)
CARD_X0 = 7            # 첫 카드 왼쪽 x
CARD_W = 36            # 카드 = 칸 2개
CARD_H = 18
COLS, ROWS = 4, 3
NAV_X = CARD_X0 + 8 * 18
WELL = 14              # 음각 받침 크기 (카드 안쪽 x+2, y+2)
CARD_SCALE = 0.9       # 카드에 띄우는 아이템 크기

DK = (13, 10, 7, 255)
BRASS = (187, 127, 54, 255)
BRASS_HI = (226, 179, 99, 255)
FILL = (40, 33, 26, 255)
WELL_FILL = (52, 44, 35, 255)
WELL_SHADOW = (24, 19, 14, 255)
WELL_LIGHT = (92, 78, 60, 255)
WORN = (118, 30, 26, 255)
WORN_HI = (158, 52, 40, 255)
LEVEL = (110, 230, 110, 255)
PAGE = (240, 226, 200, 255)

DIGITS = {
    '0': ['###', '#.#', '#.#', '#.#', '###'], '1': ['.#.', '##.', '.#.', '.#.', '###'],
    '2': ['###', '..#', '###', '#..', '###'], '3': ['###', '..#', '.##', '..#', '###'],
    '4': ['#.#', '#.#', '###', '..#', '..#'], '5': ['###', '#..', '###', '..#', '###'],
    '6': ['###', '#..', '###', '#.#', '###'], '7': ['###', '..#', '.#.', '.#.', '.#.'],
    '8': ['###', '#.#', '###', '#.#', '###'], '9': ['###', '#.#', '###', '..#', '###'],
    '+': ['...', '.#.', '###', '.#.', '...'], '/': ['..#', '..#', '.#.', '#..', '#..'],
}
KEYS = {'+': 'plus', '/': 'slash'}
DIGIT_TOP = 6          # 카드 윗줄에서 숫자 윗줄까지


def plate(d, x, y, w):
    d.rectangle((x, y, x + w - 1, y + CARD_H - 1), fill=DK)
    d.rectangle((x + 1, y + 1, x + w - 2, y + CARD_H - 2), fill=BRASS)
    d.line((x + 1, y + 1, x + w - 2, y + 1), fill=BRASS_HI)
    d.rectangle((x + 2, y + 2, x + w - 3, y + CARD_H - 3), fill=FILL)


def well(d, x, y):
    s = WELL
    d.rectangle((x, y, x + s - 1, y + s - 1), fill=WELL_FILL)
    d.line((x, y, x + s - 1, y), fill=WELL_SHADOW)
    d.line((x, y, x, y + s - 1), fill=WELL_SHADOW)
    d.line((x + 1, y + s - 1, x + s - 1, y + s - 1), fill=WELL_LIGHT)
    d.line((x + s - 1, y + 1, x + s - 1, y + s - 1), fill=WELL_LIGHT)


def arrow(d, cx, top, down):
    rows = [(0, 0), (-1, 1), (0, 1), (1, 1), (-2, 2), (-1, 2), (0, 2), (1, 2), (2, 2)]
    for dx, dy in rows:
        d.point((cx + dx, top + (2 - dy if down else dy)), fill=BRASS_HI)


def background():
    img = make_enhance_bg6.build(os.path.join(HERE, "art", "enhance_bg_3row.png"))
    d = ImageDraw.Draw(img)
    for r in range(ROWS):
        y = LIST_TOP + r * CARD_H
        for c in range(COLS):
            x = CARD_X0 + c * CARD_W
            plate(d, x, y, CARD_W)
            well(d, x + 2, y + 2)
        plate(d, NAV_X, y, CARD_H)
    arrow(d, NAV_X + 9, LIST_TOP + 7, False)
    arrow(d, NAV_X + 9, LIST_TOP + 2 * CARD_H + 8, True)
    return img


def digit_img(ch, color):
    rows = DIGITS[ch]
    img = Image.new("RGBA", (3, 5))
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            if c == '#':
                img.putpixel((x, y), color)
    return img


def worn_frame():
    w, h = CARD_W - 2, CARD_H - 2
    img = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, w - 1, h - 1), outline=WORN)
    d.line((0, 0, w - 1, 0), fill=WORN_HI)
    return img


def card_models(content):
    """customitem 무기 · 방어구 모델마다 gui 표시만 줄인 카드 모델 + 아이템 정의"""
    src_models = os.path.join(content, "customitem", "resourcepack", "assets", "customitem", "models")
    out = os.path.join(content, "rustport", "resourcepack", "assets", "rustport")
    names = []
    for cfg in ("weapon.yml", "armor.yml"):
        text = open(os.path.join(content, "customitem", "configs", cfg), encoding="utf-8").read()
        for item, path in re.findall(r"\n  (\w+):\n(?:    .*\n)*?      model_path: (?:customitem:)?([\w/]+)", text):
            names.append((item, path))
    os.makedirs(os.path.join(out, "models", "item", "card"), exist_ok=True)
    os.makedirs(os.path.join(out, "items", "card"), exist_ok=True)
    for item, path in names:
        with open(os.path.join(src_models, path + ".json"), encoding="utf-8") as f:
            parent = json.load(f)
        gui = parent.get("display", {}).get("gui", {"rotation": [0, 0, 0], "translation": [0, 0, 0], "scale": [1, 1, 1]})
        gui = {
            "rotation": gui.get("rotation", [0, 0, 0]),
            "translation": [round(v * CARD_SCALE, 3) for v in gui.get("translation", [0, 0, 0])],
            "scale": [round(v * CARD_SCALE, 3) for v in gui.get("scale", [1, 1, 1])],
        }
        model = {"parent": "customitem:" + path, "display": {"gui": gui}}
        with open(os.path.join(out, "models", "item", "card", item + ".json"), "w") as f:
            json.dump(model, f, separators=(",", ":"))
        definition = {"model": {"type": "minecraft:model", "model": "rustport:item/card/" + item}}
        with open(os.path.join(out, "items", "card", item + ".json"), "w") as f:
            json.dump(definition, f, separators=(",", ":"))
    return [n for n, _ in names]


def main(content):
    rp = os.path.join(content, "rustport", "resourcepack", "assets", "rustport", "textures")
    background().save(os.path.join(rp, "gui", "enhance_bg.png"))

    font_dir = os.path.join(rp, "font", "enhance")
    os.makedirs(font_dir, exist_ok=True)
    lines = ["info:", "  namespace: rustport", "",
             "# 자동 생성 파일 (BrassField tools/gui/make_enhance_assets.py) — 강화 창 장비 목록 글꼴 그림. 직접 수정하지 말 것.",
             "font_images:"]

    def glyph(name, img, top, color_note=""):
        img.save(os.path.join(font_dir, name + ".png"))
        lines.extend(["  %s:" % name, "    path: font/enhance/%s" % name, "    suggest_in_command: false",
                      "    scale_ratio: %d" % img.height, "    y_position: %d" % (13 - top)])

    for r in range(ROWS):
        top = LIST_TOP + r * CARD_H
        for ch in DIGITS:
            glyph("enh_lv_r%d_%s" % (r, KEYS.get(ch, ch)), digit_img(ch, PAGE if ch == '/' else LEVEL), top + DIGIT_TOP)
            if ch != '+':
                glyph("enh_pg_r%d_%s" % (r, KEYS.get(ch, ch)), digit_img(ch, PAGE), top + DIGIT_TOP)
        glyph("enh_worn_r%d" % r, worn_frame(), top + 1)
    with open(os.path.join(content, "rustport", "configs", "enhance_gui.yml"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    cards = card_models(content)
    print("glyph rows", ROWS, "card models", len(cards))


if __name__ == "__main__":
    main(sys.argv[1])

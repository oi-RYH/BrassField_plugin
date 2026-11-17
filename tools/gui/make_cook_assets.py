"""
요리 기기 창 서버 자료 한 번에 만들기 (ItemsAdder rustport 콘텐츠 폴더에 쓴다).
  배경      textures/gui/cook_kettle_bg.png · cook_generic_bg.png (make_cook_bg.py) · cook_book_bg.png (make_book_bg.py)
  글꼴 그림  textures/font/cook/*.png
            cook_gauge_<0..8>        솥 게이지 눈금판 + 바늘 (진행 0/8 ~ 8/8)
            cook_cnt_r<0|1>_<k>      구름 위 재료 개수 (짙은 갈색 + 연기색 테, 칸 오른쪽 위), 줄 0 · 1
            cook_plate_<k>           접시 아래 명찰 완성품 개수 (짙은 갈색)
            cook_need_r<3|4>_<k>     책 오른쪽 필요 재료 개수 (짙은 갈색 + 종이색 테)
            cook_times_<k|x>         책 큰 요리 오른쪽 "×N" (한 번에 나오는 개수)
            cook_pick_r<2|3|4>       책 목록에서 보고 있는 요리 금색 테
            cook_pin_r<2|3|4>        책 목록에서 지금 걸린 요리 빨간 핀
            (k = 0~9 · comma · dot · k — 1,000 넘는 재료 개수는 "1.2k")
  큰 요리   models/item/gui/cook_big/<요리>.json — 요리 아이콘(textures/item/food/<요리>.png)을 창 안에서 2배로 그리는 모델 (책)
            models/item/gui/cook_plate/<요리>.json — 같은 2배 모델을 접시 2x2 칸 가운데로 옮겨 그린다 (왼쪽 위 칸에 넣음)
  불 버튼   textures/item/gui/cook_fire_on.png · cook_fire_off.png — 화덕 문 자리 조리 시작·멈춤 버튼 아이콘
  설정      configs/cook_gui.yml (자동 생성 — 직접 고치지 말 것)
글꼴 그림 이동량 = 그림 폭. y_position = 13 - (창 기준 그림 윗줄 y). Java 쪽 이름·위치는 com.brassfield.cooking.CookGlyphs 와 맞춘다.

사용: python3 tools/gui/make_cook_assets.py <enhance_bg.png> <rustport 콘텐츠 폴더> <BrassField config.yml>
"""
import json
import math
import os
import re
import sys

from PIL import Image

import make_book_bg as book
import make_cook_bg as cook
from gui_kit import slot_box
from make_crop_bg import DIGITS

INK = (70, 40, 20, 255)
SMOKE_HALO = (236, 228, 214, 255)
PAPER_HALO = (255, 236, 200, 255)
NEEDLE = (60, 30, 20, 255)
NEEDLE_TIP = (190, 40, 30, 255)
TICK = (120, 90, 64, 255)
GOLD = [(255, 230, 140, 255), (232, 168, 40, 255)]
PIN = [(214, 50, 40, 255), (130, 20, 16, 255), (255, 170, 150, 255)]
GAUGE_STEPS = 8
CHARS = [(str(d), str(d)) for d in range(10)] + [(",", "comma"), (".", "dot"), ("k", "k")]
PATTERNS = dict(DIGITS, **{".": ["0", "0", "0", "0", "1"], "k": ["100", "101", "110", "101", "101"]})
TIMES = ["101", "010", "101"]                                    # × (3x3, 숫자 가운데 높이)


def width_pixel(img):
    """오른쪽 끝 열에 거의 투명한 점: 이동량을 그림 폭으로 고정"""
    if not any(img.getpixel((img.width - 1, y))[3] for y in range(img.height)):
        img.putpixel((img.width - 1, 0), (0, 0, 0, 1))
    return img


def digit(ch, halo=None):
    """3x5 숫자(쉼표 1x5). halo 가 있으면 둘레 1px 테를 두른 (w+2)x7, 없으면 오른쪽 틈 1열을 둔 (w+1)x5"""
    pattern = PATTERNS[ch]
    w = len(pattern[0])
    pad = 1 if halo else 0
    img = Image.new("RGBA", (w + 2 * pad + (0 if halo else 1), 5 + 2 * pad), (0, 0, 0, 0))
    ink = [(x + pad, y + pad) for y, line in enumerate(pattern) for x, c in enumerate(line) if c == "1"]
    if halo:
        for x, y in ink:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    img.putpixel((x + dx, y + dy), halo)
    for p in ink:
        img.putpixel(p, INK)
    return width_pixel(img)


def gauge(level, mask):
    """게이지 눈금판(mask)을 새로 칠하고 눈금 · 바늘(축에서 5칸, 끝 빨강)을 그린다. 7시(225도) → 5시(-45도) 시계 방향.
    눈금 9개 중 지나온 눈금은 빨갛게."""
    xs, ys = [p[0] for p in mask], [p[1] for p in mask]
    x0, y0 = min(xs), min(ys)
    img = Image.new("RGBA", (max(xs) - x0 + 1, max(ys) - y0 + 1), (0, 0, 0, 0))
    inside = mask_set(mask)
    for x, y in mask:
        img.putpixel((x - x0, y - y0), cook.FACE + (255,))
    cx, cy = cook.gauge_center()
    for step in range(GAUGE_STEPS + 1):
        a = math.radians(225 - 270 * step / GAUGE_STEPS)
        px, py = round(cx + 5 * math.cos(a)), round(cy - 5 * math.sin(a))
        if (px, py) in inside:
            img.putpixel((px - x0, py - y0), NEEDLE_TIP if step <= level and level > 0 else TICK)
    a = math.radians(225 - 270 * level / GAUGE_STEPS)
    for i in range(0, 5):
        px, py = round(cx + i * math.cos(a)), round(cy - i * math.sin(a))
        if (px, py) in inside:
            img.putpixel((px - x0, py - y0), NEEDLE_TIP if i == 4 else NEEDLE)
    img.putpixel((cx - x0, cy - y0), (30, 16, 10, 255))
    return width_pixel(img), (x0, y0)


_mask_cache = {}


def mask_set(mask):
    key = id(mask)
    if key not in _mask_cache:
        _mask_cache[key] = set(mask)
    return _mask_cache[key]


def pick_frame():
    """책 목록 칸 둘레 금색 테 (칸 바깥 1px 까지, 20x20, 모서리 깎음)"""
    img = Image.new("RGBA", (20, 20), (0, 0, 0, 0))
    for i in range(1, 19):
        for x, y in ((i, 0), (i, 19), (0, i), (19, i)):
            img.putpixel((x, y), GOLD[1])
        for x, y in ((i, 1), (i, 18), (1, i), (18, i)):
            if 1 <= x <= 18 and 1 <= y <= 18:
                img.putpixel((x, y), GOLD[0])
    return img


def pin():
    """칸 왼쪽 위에 꽂힌 작은 빨간 핀 (머리 3x3 + 침 2칸)"""
    rows = [".AA.", "ABBA", "ABBA", ".AA.", "..C.", "...C"]
    colors = {"A": PIN[1], "B": PIN[0], "C": (110, 90, 70, 255)}
    img = Image.new("RGBA", (4, 6), (0, 0, 0, 0))
    for y, line in enumerate(rows):
        for x, c in enumerate(line):
            if c in colors:
                img.putpixel((x, y), colors[c])
    img.putpixel((1, 1), PIN[2])
    return width_pixel(img)


def recipe_results(config_path):
    """config.yml 의 cooking.stations.*.recipes 요리 키 (들여쓰기로 읽는다)"""
    results, in_stations, in_recipes = [], False, False
    for line in open(config_path, encoding="utf-8"):
        if re.match(r"^  stations:", line):
            in_stations = True
            continue
        if in_stations and re.match(r"^  \S", line):
            break
        if not in_stations:
            continue
        if re.match(r"^      recipes:", line):
            in_recipes = True
        elif re.match(r"^      \S", line) or re.match(r"^    \S", line):
            in_recipes = False
        elif in_recipes:
            m = re.match(r"^        ([a-z0-9_:]+):\s*$", line)
            if m:
                key = m.group(1)
                results.append(key if ":" in key else "rustport:" + key)
    return results


def big_model(texture, shift=(0, 0)):
    """창 안에서 2배 크기. shift = 칸 가운데에서 옮길 픽셀 (x 오른쪽 +, y 아래 +)"""
    return {"parent": "minecraft:item/generated", "textures": {"layer0": texture},
            "display": {"gui": {"rotation": [0, 0, 0], "translation": [shift[0], -shift[1], 0], "scale": [2, 2, 2]}},
            "gui_light": "front"}


FACE_COLOR = None


def main(enh_path, content, config_path):
    global FACE_COLOR
    tex = os.path.join(content, "resourcepack", "assets", "rustport", "textures")
    models = os.path.join(content, "resourcepack", "assets", "rustport", "models", "item", "gui", "cook_big")
    os.makedirs(os.path.join(tex, "font", "cook"), exist_ok=True)
    os.makedirs(models, exist_ok=True)
    plate_models = os.path.join(os.path.dirname(models), "cook_plate")
    os.makedirs(plate_models, exist_ok=True)
    px, py = slot_box(*cook.PLATE_SLOT)
    fx, fy = cook.food_center()
    plate_shift = (fx - (px + 9), fy - (py + 9))
    enh = Image.open(enh_path).convert("RGBA")
    cook.build_kettle(enh).save(os.path.join(tex, "gui", "cook_kettle_bg.png"))
    cook.build_generic(enh).save(os.path.join(tex, "gui", "cook_generic_bg.png"))
    book.build(enh).save(os.path.join(tex, "gui", "cook_book_bg.png"))

    glyphs = {}                                                 # 이름 → (그림, 윗줄 y)
    mask = cook.gauge_mask()
    for level in range(GAUGE_STEPS + 1):
        img, (_, top) = gauge(level, mask)
        glyphs["cook_gauge_%d" % level] = (img, top)
    for row in (0, 1):
        top = slot_box(row, 0)[1]                               # 칸 오른쪽 위 (작물 별 표시가 오른쪽 아래라 피한다)
        for ch, key in CHARS:
            glyphs["cook_cnt_r%d_%s" % (row, key)] = (digit(ch, SMOKE_HALO), top)
    for ch, key in CHARS:
        glyphs["cook_plate_%s" % key] = (digit(ch), cook.label_box()[1] + 2)
    for row in (3, 4):
        top = slot_box(row, 0)[1] + 12 - 1
        for ch, key in CHARS:
            glyphs["cook_need_r%d_%s" % (row, key)] = (digit(ch, PAPER_HALO), top)
    times_top = book.dish_center()[1] - 2
    for ch, key in CHARS:
        glyphs["cook_times_%s" % key] = (digit(ch), times_top)
    x_img = Image.new("RGBA", (4, 5), (0, 0, 0, 0))
    for y, line in enumerate(TIMES):
        for x, c in enumerate(line):
            if c == "1":
                x_img.putpixel((x, y + 1), INK)
    glyphs["cook_times_x"] = (width_pixel(x_img), times_top)
    for row in (2, 3, 4):
        y = slot_box(row, 0)[1]
        glyphs["cook_pick_r%d" % row] = (pick_frame(), y - 1)
        glyphs["cook_pin_r%d" % row] = (pin(), y - 2)
    for name, (img, _) in glyphs.items():
        img.save(os.path.join(tex, "font", "cook", name + ".png"))

    os.makedirs(os.path.join(tex, "item", "gui"), exist_ok=True)
    for state in ("on", "off"):
        cook.fire_icon(state).save(os.path.join(tex, "item", "gui", "cook_fire_%s.png" % state))
    items = []
    for result in recipe_results(config_path):
        ns, name = result.split(":", 1)
        if ns != "rustport" or not os.path.exists(os.path.join(tex, "item", "food", name + ".png")):
            print("아이콘 없음, 큰 모델 건너뜀:", result)
            continue
        with open(os.path.join(models, name + ".json"), "w") as f:
            f.write(json.dumps(big_model("%s:item/food/%s" % (ns, name))) + "\n")
        with open(os.path.join(plate_models, name + ".json"), "w") as f:
            f.write(json.dumps(big_model("%s:item/food/%s" % (ns, name), plate_shift)) + "\n")
        items.append(name)

    lines = ["info:", "  namespace: rustport", "",
             "# 자동 생성 파일 (BrassField tools/gui/make_cook_assets.py) — 요리 기기 창. 직접 수정하지 말 것.",
             "items:"]
    for name in items:
        for kind in ("big", "plate"):
            lines += ["  cook_%s_%s:" % (kind, name), '    display_name: " "', "    resource:", "      material: PAPER",
                      "      generate: false", "      model_path: item/gui/cook_%s/%s" % (kind, name)]
    for state in ("on", "off"):
        lines += ["  cook_fire_%s:" % state, '    display_name: " "', "    resource:", "      material: PAPER",
                  "      generate: true", "      textures:", "        - item/gui/cook_fire_%s" % state]
    lines += ["font_images:"]
    for bg in ("cook_kettle_bg", "cook_generic_bg", "cook_book_bg"):
        lines += ["  %s:" % bg, "    path: gui/%s" % bg, "    suggest_in_command: false", "    scale_ratio: 256",
                  "    y_position: 13"]
    for name, (img, top) in glyphs.items():
        lines += ["  %s:" % name, "    path: font/cook/%s" % name, "    suggest_in_command: false",
                  "    scale_ratio: %d" % img.height, "    y_position: %d" % (13 - top)]
    with open(os.path.join(content, "configs", "cook_gui.yml"), "w") as f:
        f.write("\n".join(lines) + "\n")
    gx = min(m[0] for m in mask)
    print("big items", len(items), "glyphs", len(glyphs), "gauge x", gx, "gauge width", glyphs["cook_gauge_0"][0].width,
          "label", cook.label_box(), "plate shift", plate_shift, "dish", book.dish_center())


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])

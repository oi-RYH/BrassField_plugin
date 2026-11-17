"""
종자·작물 거래기 GUI 서버 자료 한 번에 만들기 (ItemsAdder rustport 콘텐츠 폴더에 쓴다).
  배경        textures/gui/crop_sell_bg.png · seed_shop_bg.png       (make_crop_bg.py)
  버튼 아이콘  textures/item/gui/crop_*.png                           (make_sell_button.py · make_crop_icons.py · 도마 탭)
  씨앗 봉투    textures/item/gui/seed_packet_<작물>.png               (make_seed_icons.py)
  글꼴 그림    textures/font/crop/*.png — 창 제목 글자로 띄우는 숫자
               amber_*   : 금액 창·페이지 번호 창 숫자 (3x5 호박색, 5줄 y=114)
               tag<줄>_* : 씨앗 가격표 조각 (왼쪽 끝 = 테+금화, 숫자 칸, 오른쪽 끝). 줄마다 높이가 달라 4벌
               tip_*     : 매입 가격표 설명 창 — 작물 그림(일반·은별·금별, 16px, 설명 두 줄에 걸침)과 가격표 조각
                           (작물 그림은 서버의 작물 아이템 그림을 복사 — CustomCrops 그림이라 저장소에는 넣지 않는다)
  설정        configs/crop_gui.yml (자동 생성 — 직접 고치지 말 것)

글꼴 그림의 이동량 = 그림 폭 (오른쪽 빈 칸에는 alpha 1 점을 찍어 폭을 고정, 강화 창 배경과 같은 규칙).
y_position = 13 - (창 기준 그림 윗줄 y). 배경은 간판 여백 PAD_TOP 만큼 올린 21.
Java 쪽 이름·이동량은 com.brassfield.market.CropFont 와 맞춘다.

사용: python3 tools/gui/make_crop_assets.py <enhance_bg.png> <rustport 콘텐츠 폴더> <customcrops 콘텐츠 폴더>
"""
import os
import sys

from PIL import Image

import make_crop_bg as bg
import make_crop_icons
import make_seed_icons
import make_sell_button
from gui_kit import DARK, cut_black, shrink_art

TAG_ROW_TOPS = {row: bg.slot_box(row, 0)[1] + 4 for row in (1, 2, 3, 4)}    # 가격표 윗줄 y (봉투 칸 y + 4)
AMBER_TOP = bg.slot_box(5, 0)[1] + 7                                       # 금액·페이지 숫자 윗줄 y
AMBER = (255, 196, 80)
TIP_ICON_ASCENT = 8                     # 설명 줄 윗줄보다 1px 위에서 시작해 두 줄(20px)에 걸치는 16px 작물 그림
TIP_TAG_ASCENT = 4                      # 가격표(9px)는 작물 그림 세로 가운데
TIP_GRADES = {"n": "", "s": "_silver_star", "g": "_golden_star"}
CREAM = (253, 226, 150)
B0, B2 = bg.BRASS[0], bg.BRASS[2]


def keep_width(img):
    """맨 오른쪽 열이 비어 있으면 alpha 1 점을 찍어 글꼴 폭(이동량)을 그림 폭으로 고정"""
    p = img.load()
    x = img.width - 1
    if all(p[x, y][3] == 0 for y in range(img.height)):
        p[x, 0] = (0, 0, 0, 1)
    return img


def amber_glyph(ch):
    pattern = bg.DIGITS[ch]
    w = len(pattern[0])
    img = Image.new("RGBA", (w + 1, 5), (0, 0, 0, 0))
    for y, line in enumerate(pattern):
        for x, c in enumerate(line):
            if c == "1":
                img.putpixel((x, y), AMBER + (255,))
    return keep_width(img)


def tag_columns(kind):
    """가격표 조각의 세로줄들 (높이 9). kind: edge 테두리 · rim 황동 · inner 안쪽(내용은 따로)"""
    col = {"edge": [DARK] * 9,
           "rim": [DARK, B0] + [B2] * 6 + [DARK],
           "inner": [DARK, B0] + [bg.SCREEN] * 5 + [B2, DARK]}[kind]
    return list(col)


def tag_piece(kind, ch=None):
    if kind == "left":                                                   # 테두리 · 황동 · 금화 5 · 틈
        cols = [tag_columns("edge"), tag_columns("rim")] + [tag_columns("inner") for _ in range(6)]
        img = columns_image(cols)
        for j, line in enumerate(bg.COIN5):
            for i, c in enumerate(line):
                if c != ".":
                    img.putpixel((2 + i, 2 + j), bg.COIN5_PAL[c] + (255,))
        return img
    if kind == "right":                                                  # 황동 · 테두리
        return columns_image([tag_columns("rim"), tag_columns("edge")])
    pattern = bg.DIGITS[ch]                                              # 숫자 3 + 틈 1
    img = columns_image([tag_columns("inner") for _ in range(len(pattern[0]) + 1)])
    for j, line in enumerate(pattern):
        for i, c in enumerate(line):
            if c == "1":
                img.putpixel((i, 2 + j), CREAM + (255,))
    return img


def columns_image(cols):
    img = Image.new("RGBA", (len(cols), 9), (0, 0, 0, 0))
    for x, col in enumerate(cols):
        for y, c in enumerate(col):
            img.putpixel((x, y), c + (255,))
    return img


def board_tab_icon():
    """[작물 판매] 탭: 도마 시안을 16px 폭으로 줄여 세로 가운데에"""
    board = shrink_art(cut_black(Image.open(bg.BOARD_ART)), bg.BOARD_BOX, 16 / (bg.BOARD_BOX[2] - bg.BOARD_BOX[0]))
    icon = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    icon.alpha_composite(board, (0, (16 - board.height) // 2))
    return icon


def crop_texture(name, suffix, content, customcrops):
    """작물 아이템 그림 (CustomCrops 작물이면 customcrops 폴더, 쌀·양파는 rustport 폴더)"""
    for base in (os.path.join(customcrops, "resourcepack", "assets", "customcrops", "textures", "item", "crop"),
                 os.path.join(content, "resourcepack", "assets", "rustport", "textures", "item", "crop")):
        path = os.path.join(base, name, name + suffix + ".png")
        if os.path.exists(path):
            return Image.open(path).convert("RGBA")
    raise FileNotFoundError(name + suffix)


def full_width(img):
    """오른쪽 끝 열에 alpha 1 점 (이동량을 그림 폭으로 고정)"""
    img = img.copy()
    p = img.load()
    if all(p[img.width - 1, y][3] == 0 for y in range(img.height)):
        p[img.width - 1, 0] = (0, 0, 0, 1)
    return img


def main(enh_path, content, customcrops):
    tex = os.path.join(content, "resourcepack", "assets", "rustport", "textures")
    for sub in ("gui", "item/gui", "font/crop"):
        os.makedirs(os.path.join(tex, sub), exist_ok=True)
    enh = Image.open(enh_path).convert("RGBA")
    bg.build_sell(enh).save(os.path.join(tex, "gui", "crop_sell_bg.png"))
    bg.build_seed(enh).save(os.path.join(tex, "gui", "seed_shop_bg.png"))

    items = {"crop_sell_button": make_sell_button.draw(), "crop_sell_tab": board_tab_icon()}
    for name, rows in make_crop_icons.ICONS.items():
        items["crop_" + name] = make_crop_icons.draw(rows)
    _, packets = make_seed_icons.build()
    for name, icon in packets.items():
        items["seed_packet_" + name] = icon
    for name, icon in items.items():
        icon.save(os.path.join(tex, "item", "gui", name + ".png"))

    glyphs = {}                                                          # 이름 → (그림, 윗줄 y)
    for ch, key in [(str(d), str(d)) for d in range(10)] + [(",", "comma"), ("/", "slash")]:
        glyphs["crop_amber_" + key] = (amber_glyph(ch), AMBER_TOP)
    for row, top in TAG_ROW_TOPS.items():
        glyphs["crop_tag%d_left" % row] = (tag_piece("left"), top)
        glyphs["crop_tag%d_right" % row] = (tag_piece("right"), top)
        for d in range(10):
            glyphs["crop_tag%d_%d" % (row, d)] = (tag_piece("digit", str(d)), top)
    tips = {}                                                            # 이름 → (그림, ascent)
    for crop in bg.SEED_ORDER:
        for key, suffix in TIP_GRADES.items():
            tips["crop_tip_%s_%s" % (crop, key)] = (full_width(crop_texture(crop, suffix, content, customcrops)),
                                                    TIP_ICON_ASCENT)
    tips["crop_tip_tag_left"] = (tag_piece("left"), TIP_TAG_ASCENT)
    tips["crop_tip_tag_right"] = (tag_piece("right"), TIP_TAG_ASCENT)
    for d in range(10):
        tips["crop_tip_tag_%d" % d] = (tag_piece("digit", str(d)), TIP_TAG_ASCENT)
    for name, (img, _) in list(glyphs.items()) + list(tips.items()):
        img.save(os.path.join(tex, "font", "crop", name + ".png"))

    lines = ["info:", "  namespace: rustport", "",
             "# 자동 생성 파일 (BrassField tools/gui/make_crop_assets.py) — 종자·작물 거래기 GUI. 직접 수정하지 말 것.",
             "items:"]
    for name in items:
        lines += ["  %s:" % name, '    display_name: " "', "    resource:", "      material: PAPER",
                  "      generate: true", "      textures:", "        - item/gui/%s" % name]
    lines += ["font_images:"]
    for name in ("crop_sell_bg", "seed_shop_bg"):                         # 배경 (간판 여백 8px 위로)
        lines += ["  %s:" % name, "    path: gui/%s" % name, "    suggest_in_command: false",
                  "    scale_ratio: 256", "    y_position: 21"]
    for name, (img, top) in glyphs.items():
        lines += ["  %s:" % name, "    path: font/crop/%s" % name, "    suggest_in_command: false",
                  "    scale_ratio: %d" % img.height, "    y_position: %d" % (13 - top)]
    for name, (img, ascent) in tips.items():                             # 설명 창 글자: 그 줄 기준 높이
        lines += ["  %s:" % name, "    path: font/crop/%s" % name, "    suggest_in_command: false",
                  "    scale_ratio: %d" % img.height, "    y_position: %d" % ascent]
    with open(os.path.join(content, "configs", "crop_gui.yml"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("items", len(items), "glyphs", len(glyphs) + len(tips))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])

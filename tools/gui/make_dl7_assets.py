"""
DL-7 납품 창 서버 자료 한 번에 만들기 (ItemsAdder rustport 콘텐츠 폴더에 쓴다).
  배경      textures/gui/dl7_bg.png (make_dl7_bg.py, 간판 없음 → y_position 13)
  글꼴 그림  textures/font/dl7/ink<줄>_*.png — 영수증 숫자 (3x5 짙은 잉크색). 줄 1 = 올린 요리 개수, 줄 2 = 총 금액
            textures/font/dl7/dl7_stamp_mark.png — 납품하면 영수증에 찍히는 붉은 도장 자국 (원 안에 요리사 모자)
  도장 연출  3D 도장 (make_dl7_stamp3d.py): 색 판 textures/item/gui/dl7_stamp3d.png + 장면별 모델
            models/item/gui/dl7_stamp3d_<장면>.json (창 안 위치만 다름). 영수증 쪽 칸 하나에 장면을 차례로 넣는다
  설정      configs/dl7_gui.yml (자동 생성 — 직접 고치지 말 것)
글꼴 그림 이동량 = 그림 폭 (숫자 4, 쉼표 2). y_position = 13 - (창 기준 그림 윗줄 y).
Java 쪽 이름·위치는 com.brassfield.market.FoodSellGui 와 맞춘다.

사용: python3 tools/gui/make_dl7_assets.py <enhance_bg.png> <rustport 콘텐츠 폴더>
"""
import os
import sys

from PIL import Image

import make_crop_bg
import make_dl7_bg as dl7
import make_dl7_stamp3d as stamp

INK = (70, 40, 20)
STAMP_INK = (176, 34, 26)
MARK_AT = (148, 58)                      # 영수증 위 도장 자국 왼쪽 위 (창 기준) — 가운데 = make_dl7_stamp3d.MARK_CENTER
MARK = [                                 # 붉은 원 안에 요리사 모자 (R = 잉크)
    "....RRRRRR....",
    "..RR......RR..",
    ".R...RRRR...R.",
    ".R..RRRRRR..R.",
    "R..RRRRRRRR..R",
    "R..RRRRRRRR..R",
    "R...RRRRRR...R",
    "R....RRRR....R",
    "R....R..R....R",
    "R....RRRR....R",
    ".R...RRRR...R.",
    ".R..........R.",
    "..RR......RR..",
    "....RRRRRR....",
]


def ink_glyph(ch):
    pattern = make_crop_bg.DIGITS[ch]
    w = len(pattern[0])
    img = Image.new("RGBA", (w + 1, 5), (0, 0, 0, 0))
    for y, line in enumerate(pattern):
        for x, c in enumerate(line):
            if c == "1":
                img.putpixel((x, y), INK + (255,))
    img.putpixel((w, 0), (0, 0, 0, 1))                                # 오른쪽 틈 열: 이동량을 그림 폭으로 고정
    return img


def stamp_mark():
    """영수증에 찍히는 자국: 잉크가 고르지 않게 군데군데 옅게"""
    img = Image.new("RGBA", (len(MARK[0]), len(MARK)), (0, 0, 0, 0))
    for y, row in enumerate(MARK):
        for x, c in enumerate(row):
            if c == "R":
                img.putpixel((x, y), STAMP_INK + (150 if (x * 7 + y * 3) % 5 == 0 else 235,))
    return img


def receipt_line_tops():
    """영수증 개수 줄 · 총 금액 줄 숫자 윗줄 y (창 기준) — make_dl7_bg 미리보기와 같은 계산"""
    k = dl7.RECEIPT_WIDTH / (dl7.RECEIPT[2] - dl7.RECEIPT[0])
    return [dl7.RECEIPT_TOP + round((line - dl7.RECEIPT[1]) * k) - 2 for line in dl7.RECEIPT_LINES]


def main(enh_path, content):
    tex = os.path.join(content, "resourcepack", "assets", "rustport", "textures")
    os.makedirs(os.path.join(tex, "font", "dl7"), exist_ok=True)
    dl7.build(Image.open(enh_path).convert("RGBA")).save(os.path.join(tex, "gui", "dl7_bg.png"))
    glyphs = {}
    for line, top in enumerate(receipt_line_tops(), start=1):
        for ch, key in [(str(d), str(d)) for d in range(10)] + [(",", "comma")]:
            glyphs["dl7_ink%d_%s" % (line, key)] = (ink_glyph(ch), top)
    glyphs["dl7_stamp_mark"] = (stamp_mark(), MARK_AT[1])
    for name, (img, _) in glyphs.items():
        img.save(os.path.join(tex, "font", "dl7", name + ".png"))
    os.makedirs(os.path.join(tex, "item", "gui"), exist_ok=True)
    items = []
    stamp.atlas().save(os.path.join(tex, "item", "gui", "dl7_stamp3d.png"))
    models = os.path.join(content, "resourcepack", "assets", "rustport", "models", "item", "gui")
    os.makedirs(models, exist_ok=True)
    for frame in stamp.FRAMES:
        name = "dl7_stamp3d_" + frame[0]
        with open(os.path.join(models, name + ".json"), "w") as f:
            f.write(stamp.model_json("rustport:item/gui/dl7_stamp3d", frame) + "\n")
        items.append(name)
    lines = ["info:", "  namespace: rustport", "",
             "# 자동 생성 파일 (BrassField tools/gui/make_dl7_assets.py) — DL-7 납품 창. 직접 수정하지 말 것.",
             "items:"]
    for name in items:
        lines += ["  %s:" % name, '    display_name: " "', "    resource:", "      material: PAPER",
                  "      generate: false", "      model_path: item/gui/%s" % name]
    lines += ["font_images:",
             "  dl7_bg:", "    path: gui/dl7_bg", "    suggest_in_command: false", "    scale_ratio: 256",
             "    y_position: %d" % (13 + dl7.PAD)]
    for name, (img, top) in glyphs.items():
        lines += ["  %s:" % name, "    path: font/dl7/%s" % name, "    suggest_in_command: false",
                  "    scale_ratio: %d" % img.height, "    y_position: %d" % (13 - top)]
    with open(os.path.join(content, "configs", "dl7_gui.yml"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("items", len(items), "glyphs", len(glyphs), "receipt tops", receipt_line_tops(),
          "digits right x", 170 - 1 - dl7.RECEIPT_WIDTH + dl7.RECEIPT_DIGITS_RIGHT)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

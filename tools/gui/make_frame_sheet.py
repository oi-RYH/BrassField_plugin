"""
강화 창 테두리 양식 뽑기: 강화 창 배경(enhance_bg.png)에서 테두리 부품을 잘라 art/frame/ 에 저장하고, 정리표 한 장을 만든다.
  부품 (강화 창 그림 좌표, 창 기준):
    pillar_left / pillar_right : 옆 기둥 한 마디 7x18 (y 18~36). 위아래로 18px 마다 이어 붙인다 (구리 고리 5줄).
                                 안쪽 끝 한 줄은 밝은 회색 (176,155,117)
    beam_top                   : 위 구리 들보 30x7 (x 22~52). 가로로 이어 붙인다
    beam_mid                   : 창 칸 / 가방 칸 사이 구리 들보 30x8 (y 73~81)
    beam_bottom                : 맨 아래 구리 들보 30x7 (y 160~167)
    corner_tl                  : 왼쪽 위 큰 톱니 22x22
    corner_tr / corner_bl / corner_br : 나머지 모서리 볼트 판 12x8
    slot_cell                  : 가방 칸 한 칸 18x18 (밝은 테 + 안쪽 그늘)
  색: 구리 들보 단면 6줄 · 기둥 세로줄 6줄 · 바탕 판 · 가방 칸

사용: python3 tools/gui/make_frame_sheet.py <enhance_bg.png> <부품 폴더> <정리표.png>
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

PARTS = {
    "pillar_left": (0, 18, 7, 36), "pillar_right": (169, 18, 176, 36),
    "beam_top": (22, 0, 52, 7), "beam_mid": (22, 73, 52, 81), "beam_bottom": (22, 160, 52, 168),
    "corner_tl": (0, 0, 22, 22), "corner_tr": (164, 0, 176, 8),
    "corner_bl": (0, 160, 12, 168), "corner_br": (164, 160, 176, 168),
    "slot_cell": (7, 83, 25, 101),
}
NOTES = {
    "pillar_left": "옆 기둥 7x18 · 18px 마다 반복 (구리 고리 5줄)",
    "pillar_right": "오른쪽 기둥 (같은 모양)",
    "beam_top": "위 구리 들보 · 가로 반복",
    "beam_mid": "창 칸 / 가방 칸 사이 들보",
    "beam_bottom": "맨 아래 들보",
    "corner_tl": "왼쪽 위 큰 톱니 22x22",
    "corner_tr": "오른쪽 위 볼트 판",
    "corner_bl": "왼쪽 아래 볼트 판",
    "corner_br": "오른쪽 아래 볼트 판",
    "slot_cell": "가방 칸 18x18",
}
COLORS = [
    ("구리 들보 단면 (위→아래)", [(13, 10, 7), (226, 179, 99), (187, 127, 54), (146, 83, 40), (74, 43, 24), (13, 10, 7)]),
    ("기둥 세로줄 (바깥→안)", [(23, 18, 14), (73, 60, 48), (161, 141, 107), (73, 60, 48), (104, 80, 58), (73, 60, 48),
                         (176, 155, 117)]),
    ("바탕 판 (+ 어두운·밝은 점)", [(42, 35, 28), (44, 37, 30), (46, 39, 32), (39, 31, 24), (58, 53, 45)]),
    ("가방 칸 (테 · 그늘 · 안)", [(176, 155, 117), (174, 157, 125), (36, 35, 31), (73, 69, 60)]),
    ("짙은 테두리", [(13, 10, 7)]),
]


def main(enh_path, out_dir, sheet_path):
    enh = Image.open(enh_path).convert("RGBA")
    os.makedirs(out_dir, exist_ok=True)
    parts = {name: enh.crop(box) for name, box in PARTS.items()}
    for name, img in parts.items():
        img.save(os.path.join(out_dir, name + ".png"))

    k = 6
    f = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", 22, index=6)
    fs = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", 17, index=2)
    sheet = Image.new("RGBA", (1500, 1420), (30, 25, 21, 255))
    d = ImageDraw.Draw(sheet)
    d.text((24, 16), "강화 창 테두리 양식", font=f, fill=(240, 195, 122))
    x, y, row_h = 24, 60, 0
    for name, img in parts.items():
        big = img.resize((img.width * k, img.height * k), Image.NEAREST)
        if x + big.width > 1480:
            x, y, row_h = 24, y + row_h + 50, 0
        sheet.alpha_composite(big, (x, y))
        d.text((x, y + big.height + 4), name, font=fs, fill=(240, 220, 190))
        d.text((x, y + big.height + 24), NOTES[name], font=fs, fill=(180, 160, 135))
        x += max(big.width, 300) + 24
        row_h = max(row_h, big.height + 40)
    y += row_h + 70
    for label, cols in COLORS:
        d.text((24, y), label, font=fs, fill=(240, 220, 190))
        for i, c in enumerate(cols):
            d.rectangle([300 + i * 150, y, 300 + i * 150 + 36, y + 24], fill=c, outline=(90, 75, 60))
            d.text((300 + i * 150 + 42, y + 2), "%d,%d,%d" % c, font=fs, fill=(180, 160, 135))
        y += 40
    full = enh.crop((0, 0, 176, 168)).resize((176 * 3, 168 * 3), Image.NEAREST)
    sheet.alpha_composite(full, (24, y + 40))
    d.text((24, y + 12), "원본 (강화 창 배경)", font=fs, fill=(180, 160, 135))
    sheet.save(sheet_path)
    print("ok")


if __name__ == "__main__":
    main(*sys.argv[1:4])

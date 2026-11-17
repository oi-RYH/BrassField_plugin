"""
작물 거래기 버튼 아이템 아이콘 16x16 (픽셀을 직접 찍은 그림, 빛은 왼쪽 위).
  seed_tab   [씨앗 사기]  새싹이 인쇄된 종이 씨앗 봉투 (위 접힌 선, 아래 초록 띠)
  price_list [가격표]     줄마다 금화 점이 찍힌 가격 쪽지
  sell_all   [모두 팔기]  토마토·양배추·옥수수가 담긴 바구니
  page_prev / page_next [이전·다음 페이지]  황동 판 위 짙은 화살표 (판매 버튼처럼 모서리 깎은 판)

사용: python3 tools/gui/make_crop_icons.py <출력 폴더>
"""
import os
import sys

from PIL import Image

PAL = {
    "O": (82, 52, 26),                                              # 외곽선
    # 종이
    "a": (238, 214, 164), "b": (214, 182, 128), "c": (182, 146, 94),
    "w": (246, 238, 214), "v": (214, 200, 168), "l": (120, 92, 62),
    # 초록·빨강·노랑
    "g": (122, 192, 80), "h": (70, 132, 50), "r": (222, 64, 44), "R": (156, 34, 22), "W": (255, 236, 220),
    "y": (252, 206, 72), "Y": (204, 148, 32),
    # 바구니
    "A": (226, 176, 104), "B": (176, 120, 62), "C": (136, 88, 42),
    # 황동 판 · 화살표
    "H": (252, 214, 130), "M": (226, 179, 99), "S": (187, 127, 54), "k": (70, 38, 14),
}

SEED_TAB = [
    "................",
    "..OOOOOOOOOOOO..",
    "..OaaaaaaaaabO..",
    "..OccccccccccO..",
    "..OaaaaaaaaabO..",
    "..OaaagaahaabO..",
    "..OaaaghghaabO..",
    "..OaaaahaaaabO..",
    "..OaaaahaaaabO..",
    "..OaaaaaaaaabO..",
    "..OgggggggggbO..",
    "..OhhhhhhhhhcO..",
    "..OaaaaaaaaabO..",
    "..ObbbbbbbbbcO..",
    "..OOOOOOOOOOOO..",
    "................",
]

PRICE_LIST = [
    "................",
    "..OOOOOOOOOOOO..",
    "..OwwwwwwwwwvO..",
    "..OwlllllwwyvO..",
    "..OwwwwwwwwwvO..",
    "..OwllllwwwyvO..",
    "..OwwwwwwwwwvO..",
    "..OwlllllwwyvO..",
    "..OwwwwwwwwwvO..",
    "..OwllllwwwyvO..",
    "..OwwwwwwwwwvO..",
    "..OwlllwwwwyvO..",
    "..OwwwwwwwwwvO..",
    "..OvvvvvvvvvvO..",
    "..OOOOOOOOOOOO..",
    "................",
]

SELL_ALL = [
    "................",
    "................",
    "......OOOO......",
    "..OOOOgggOO.OO..",
    ".OrrOgWgghgOyyO.",
    ".OrWrOgggghOyYO.",
    ".OrrrOhgghOOyYO.",
    "..ORRROhhOOyyYO.",
    ".OOOOOOOOOOOOOO.",
    ".OAAAAAAAAAAAAO.",
    ".OBBBBBBBBBBBBO.",
    "..OACACACACACO..",
    "..OCACACACACAO..",
    "...OACACACACO...",
    "...OOOOOOOOOO...",
    "................",
]

PAGE_PLATE = [                                                   # 화살표 버튼 판 (왼쪽 위 밝음)
    "................",
    "................",
    "...OOOOOOOOOO...",
    "..OHHHHHHHHHMO..",
    ".OHMMMMMMMMMMSO.",
    ".OHMMMMMMMMMMSO.",
    ".OHMMMMMMMMMMSO.",
    ".OHMMMMMMMMMMSO.",
    ".OHMMMMMMMMMMSO.",
    ".OHMMMMMMMMMMSO.",
    ".OHMMMMMMMMMMSO.",
    ".OHMMMMMMMMMMSO.",
    "..OMSSSSSSSSSO..",
    "...OOOOOOOOOO...",
    "................",
    "................",
]
ARROW = ["...k...", "...kk..", "kkkkkk.", "kkkkkkk", "kkkkkk.", "...kk..", "...k..."]   # 오른쪽 화살표 7x7
ARROW_AT = (4, 5)


def with_arrow(flip):
    rows = [list(r) for r in PAGE_PLATE]
    for j, line in enumerate(ARROW):
        for i, c in enumerate(line[::-1] if flip else line):
            if c == "k":
                rows[ARROW_AT[1] + j][ARROW_AT[0] + i + (1 if flip else 0)] = "k"
    return ["".join(r) for r in rows]


PAGE_NEXT = with_arrow(False)
PAGE_PREV = with_arrow(True)

ICONS = {"seed_tab": SEED_TAB, "price_list": PRICE_LIST, "sell_all": SELL_ALL,
         "page_prev": PAGE_PREV, "page_next": PAGE_NEXT}


def draw(rows):
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        assert len(row) == 16, (y, row)
        for x, c in enumerate(row):
            if c != ".":
                img.putpixel((x, y), PAL[c] + (255,))
    return img


if __name__ == "__main__":
    for name, rows in ICONS.items():
        draw(rows).save(os.path.join(sys.argv[1], name + ".png"))
    print("ok")

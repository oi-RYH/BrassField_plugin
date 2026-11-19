"""
강화 창 6줄 배경 (rustport:enhance_bg): 3줄 강화 창 그림(enhance_bg_3row.png) 위쪽은 그대로 두고,
그 아래에 강화 가능한 장비 목록 3줄(9x3 칸)을 끼워 넣는다. 목록 칸은 가방 칸 줄 그림을 그대로 이어 붙인다.

좌표는 창 기준 (아이템 칸 = 18px, 6줄 창의 3~5줄 아이템 y = 72·90·108, 테두리는 1px 위).
사용: python3 tools/gui/make_enhance_bg6.py <enhance_bg_3row.png> <출력 enhance_bg.png>
"""
import sys
from PIL import Image

SPLIT = 71          # 원래 그림에서 위 강화 판(구리 띠 포함)이 끝나는 줄 — 여기에 목록을 끼워 넣는다
SLOT_ROW = (84, 102)  # 원래 그림의 가방 첫 줄 (테두리 위 줄 ~ 아래 밝은 줄) — 18px 한 줄
LIST_ROWS = 3


STONE_BOX = (22, 46)     # 강화석 칸 액자의 x 범위 — 아래 테두리(71·72줄)를 69·70줄로 올려 목록 칸에 잘리지 않게
CLEAN_X = (60, 100)      # 무늬 없는 판 바닥 x 범위 — 목록 아래로 내려간 71~74줄의 잘린 조각을 이 무늬로 덮는다
SIDE = 8                 # 좌우 테두리 폭 (그대로 둔다)


def build(src):
    old = Image.open(src).convert("RGBA")
    w = 176
    h = 168 + LIST_ROWS * 18
    new = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    top = old.crop((0, 0, w, SPLIT))
    for dy in (0, 1):
        for x in range(*STONE_BOX):
            top.putpixel((x, 69 + dy), old.getpixel((x, 71 + dy)))
    new.paste(top, (0, 0))
    row = old.crop((0, SLOT_ROW[0], w, SLOT_ROW[1]))
    for i in range(LIST_ROWS):
        new.paste(row, (0, SPLIT + i * 18))
    rest = old.crop((0, SPLIT, w, 168))
    span = CLEAN_X[1] - CLEAN_X[0]
    for y in range(0, 75 - SPLIT):                        # 71~74줄: 액자·톱니 조각 지우기
        for x in range(SIDE, w - SIDE + 2):
            rest.putpixel((x, y), old.getpixel((CLEAN_X[0] + (x - SIDE) % span, SPLIT + y)))
    new.paste(rest, (0, SPLIT + LIST_ROWS * 18))
    assert new.getbbox()[3] == h
    return new


def main(src, out):
    build(src).save(out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

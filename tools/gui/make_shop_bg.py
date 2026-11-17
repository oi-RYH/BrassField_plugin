"""
강화석 상점 창 배경 (4줄 상자 창). 공통 부품은 gui_kit.py (강화 창 그림 부품 재사용).

상점 배치 (StoneShopGui): 2줄 8열 보유 골드 / 1~3줄 1열 강화석 아이콘, 4·5·6열 1개·10개·64개 구매 버튼(숫자 아이템).
제목은 간판 그림(art/sign_stone_shop_120.png, make_sign.py 로 만든 폭 120 간판)을 위 가운데에 단다. 게임 제목 글자는 쓰지 않는다.
  간판 아래 끝은 구매 버튼 테 바로 위(y=31), 윗부분은 창 위로 7px 넘친다 (guis.yml y_position 21).

사용: python3 tools/gui/make_shop_bg.py <enhance_bg.png> <출력.png> [미리보기.png <아이템 텍스처 폴더> <클라이언트 jar> [숫자 아이템 폴더]]
"""
import os
import sys

from PIL import Image

from gui_kit import CIRCUIT_GEAR, CIRCUIT_LINK, TUBE, Preview, Window, slot_box

ROWS = 4
SIGN_IMAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "art", "sign_stone_shop_120.png")
SIGN_BOTTOM = 31                          # 간판 아래 끝 y (구매 버튼 테 y=33 위)


def build(enh):
    win = Window(enh, ROWS, enh_seam=True)                         # 아래 경계 두 줄은 지금 배포본과 같게
    # ── 강화석 아이콘 (1~3줄 1열) · 구매 버튼 (1~3줄 4~6열): 각각 하나의 테로 묶는다 ──
    ix, iy = slot_box(1, 1)
    bx, by = slot_box(1, 4)
    for row in (1, 2, 3):                                         # 아이콘 → 버튼 파이프와 가운데 톱니
        y = slot_box(row, 1)[1]
        win.pipe_h(ix + 20, bx - 2, y + 7)
        win.gear_small(ix + 27, y + 1)
    win.frame_slots(1, 1, rows=3)
    win.frame_slots(1, 4, rows=3, cols=3)
    # ── 보유 골드 (2줄 8열): 버튼 묶음 가운데 줄에서 파이프로 이어진 칸 ──
    gx, gy = slot_box(2, 8)
    win.copy(TUBE, (6, 26))                                       # 왼쪽 유리관
    win.pipe_h(bx + 56, gx - 2, gy + 7)
    win.frame_slots(2, 8)
    # ── 바탕 판 회로선: 간판 오른쪽 빈자리, 버튼 묶음 오른쪽 아래 빈자리 ──
    win.copy(CIRCUIT_GEAR, (148, 16))
    win.copy(CIRCUIT_LINK, (137, 74))
    win.corner_gears()
    return win.finish(SIGN_IMAGE, SIGN_BOTTOM)


if __name__ == "__main__":
    enh = Image.open(sys.argv[1]).convert("RGBA")
    out = build(enh)
    out.save(sys.argv[2])
    if len(sys.argv) > 3:                                         # 미리보기: 아이템을 올려 3배 확대
        items, numbers = sys.argv[4], (sys.argv[6] if len(sys.argv) > 6 else None)
        prev = Preview(out, ROWS, sys.argv[5])
        prev.item(2, 8, prev.vanilla("gold_ingot"))
        for row, key in ((1, "low"), (2, "mid"), (3, "high")):
            prev.item(row, 1, Image.open("%s/stone_icon_%s.png" % (items, key)).convert("RGBA"))
            for i, n in enumerate(("1", "10", "64")):
                if numbers:
                    prev.item(row, 4 + i, Image.open("%s/number_%s.png" % (numbers, n)).convert("RGBA"))
                else:
                    prev.item(row, 4 + i, prev.vanilla("gold_nugget"), n if n != "1" else None)
        prev.save(sys.argv[3])
    print("ok")

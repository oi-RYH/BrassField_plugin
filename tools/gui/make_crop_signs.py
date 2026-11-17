"""
작물 거래기 간판 두 개: 사용자 시안(art/signs_crop_shop.png, 검은 바탕 위 위아래로 "작물 판매"·"씨앗 구매")에서
간판마다 검은 바탕을 지우고 높이 HEIGHT 로 줄인다 (이전 간판과 같은 높이 → 글자 약 12px).
간판 양 끝 톱니가 옆 기둥 가까이 닿아 간판 자체가 기계와 이어진 모습이 된다.
줄이면서 흐려진 글자 획 칸은 TOUCH_UP 에 적어 둔 칸만 간판 글자색으로 채운다 ("작" 의 ㅈ 윗획·삐침 끝).

사용: python3 tools/gui/make_crop_signs.py <출력 폴더>   (sign_crop_sell.png · sign_seed_shop.png)
"""
import os
import sys
from collections import Counter

from PIL import Image

from gui_kit import cut_black, shrink_art

ART = os.path.join(os.path.dirname(os.path.abspath(__file__)), "art", "signs_crop_shop.png")
HEIGHT = 38
SPLIT_Y = 345                              # 위 간판 / 아래 간판 경계 (두 간판 사이 빈 줄)
NAMES = ["sign_crop_sell.png", "sign_seed_shop.png"]
TOUCH_UP = {0: [(54, 14), (55, 14), (56, 14), (57, 14), (54, 18), (53, 19)]}   # 간판 번호 → 흐려진 글자 칸


def touch_up(sign, cells):
    """cells 를 간판 글자색(밝기 합 600 넘는 칸 중 가장 흔한 색)으로 채운다"""
    p = sign.load()
    bright = Counter(p[x, y] for y in range(sign.height) for x in range(sign.width) if sum(p[x, y][:3]) > 600)
    text = bright.most_common(1)[0][0]
    for x, y in cells:
        p[x, y] = text


def build():
    src = Image.open(ART).convert("RGB")
    w, h = src.size
    out = []
    for y0, y1 in ((0, SPLIT_Y), (SPLIT_Y, h)):
        part = cut_black(src.crop((0, y0, w, y1)), threshold=60)
        box = part.split()[3].point(lambda a: 255 if a > 128 else 0).getbbox()
        out.append(shrink_art(part, box, HEIGHT / (box[3] - box[1])))
    for i, cells in TOUCH_UP.items():
        touch_up(out[i], cells)
    return out


if __name__ == "__main__":
    for name, sign in zip(NAMES, build()):
        sign.save(os.path.join(sys.argv[1], name))
        print(name, sign.size)

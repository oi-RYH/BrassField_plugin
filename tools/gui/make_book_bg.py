"""
요리 기기 레시피 책 창 배경 (6줄 상자 창). 사용자 시안(art/recipe_book_concept.png, 펼친 요리책)을 창 폭으로 줄이고
페이지 안 내용(예시 요리·글자·명판)을 종이로 지운 뒤 칸 자리를 다시 그린다. 이름은 아이템 설명(마우스 올림)으로만 보인다.

칸 배치 (RecipeBookGui):
  왼쪽 페이지  요리 목록 3x3 = 2~4줄 1~3열 (한 쪽 9개) / 1줄 1열·3열 = 이전·다음 쪽 (그 사이 요리사 모자·월계수)
  오른쪽 페이지 고른 요리 = 1줄 6열 (2배 크기 모델, 누르면 걸고 솥 화면으로) + 오른쪽에 나오는 개수
              필요 재료 = 3줄 5~7열 + 4줄 5~6열 (최대 5가지)
  책갈피 = 5줄 3열 (돌아가기)

사용: python3 tools/gui/make_book_bg.py <enhance_bg.png> <출력.png> [미리보기.png <클라이언트 jar>]
"""
import os
import random
import sys

from PIL import Image

from gui_kit import Preview, Window, shrink_art, slot_box

ART = os.path.join(os.path.dirname(os.path.abspath(__file__)), "art", "recipe_book_concept.png")
BOOK_BOX = (10, 4, 1532, 1022)                 # 시안에서 책 범위
BOOK_TOP = 11                                  # 창 기준 책 위 끝 y (아래 끝이 창 칸 끝 조금 아래)
PAGES = [(22, 13, 85, 97), (90, 13, 157, 97)]  # 책 그림 기준 지울 페이지 안쪽 (왼쪽, 오른쪽)
HAT_BOX = (42, 13, 73, 25)                     # 책 그림 기준 요리사 모자·월계수 (아래 명판 위까지)
HAT_TOP = 29                                   # 창 기준 모자 위 끝 y (1줄 가운데 열, 이전·다음 쪽 버튼 사이)
LIST_SLOTS = [(r, c) for r in (2, 3, 4) for c in (1, 2, 3)]
PREV_SLOT, NEXT_SLOT = (1, 1), (1, 3)
DISH_SLOT = (1, 6)
NEED_SLOTS = [(3, 5), (3, 6), (3, 7), (4, 5), (4, 6)]
BACK_SLOT = (5, 3)
LINE = (214, 156, 100)                         # 페이지 테 · 칸 테 (종이보다 짙은 갈색 선)
LINE_HI = (255, 236, 200)
RAY = (236, 170, 50)


def page_paper(book, box, rnd):
    """box 안을 종이로: 세로줄마다 밝은 칸들의 중앙값(페이지 굴곡 음영 유지) + 아주 옅은 얼룩"""
    p = book.load()
    x0, y0, x1, y1 = box
    for x in range(x0, x1):
        col = sorted((p[x, y] for y in range(y0, y1) if sum(p[x, y][:3]) > 600), key=lambda c: sum(c[:3]))
        base = col[len(col) // 2][:3] if col else (250, 208, 155)
        for y in range(y0, y1):
            k = rnd.choice((0.985, 1.0, 1.0, 1.0, 1.0, 1.01))
            p[x, y] = tuple(min(255, int(c * k)) for c in base) + (255,)


def hat_sprite(book):
    """요리사 모자·월계수: HAT_BOX 를 종이째 떼어 낸다 (모자 흰색이 종이와 비슷해 칸을 가려내지 않는다)"""
    return book.crop(HAT_BOX)


def page_border(d, box):
    """지운 페이지 안쪽 가는 테 (모서리 1px 깎음)"""
    x0, y0, x1, y1 = box
    x0, y0, x1, y1 = x0 + 2, y0 + 2, x1 - 3, y1 - 3
    d.line([(x0 + 1, y0), (x1 - 1, y0)], fill=LINE)
    d.line([(x0 + 1, y1), (x1 - 1, y1)], fill=LINE)
    d.line([(x0, y0 + 1), (x0, y1 - 1)], fill=LINE)
    d.line([(x1, y0 + 1), (x1, y1 - 1)], fill=LINE)


def slot_cell(d, x, y):
    """종이 위 칸 자리: 살짝 짙은 바탕 + 갈색 테(모서리 깎음) + 아래·오른쪽 밝은 줄"""
    d.rectangle([x + 1, y + 1, x + 16, y + 16], fill=(244, 196, 140))
    d.line([(x + 1, y), (x + 16, y)], fill=LINE)
    d.line([(x + 1, y + 17), (x + 16, y + 17)], fill=LINE_HI)
    d.line([(x, y + 1), (x, y + 16)], fill=LINE)
    d.line([(x + 17, y + 1), (x + 17, y + 16)], fill=LINE_HI)


def dish_center():
    x, y = slot_box(*DISH_SLOT)
    return x + 9, y + 9


def build(enh):
    rnd = random.Random(7)
    src = Image.open(ART).convert("RGBA")
    book = shrink_art(src, BOOK_BOX, 176 / (BOOK_BOX[2] - BOOK_BOX[0]))
    hat = hat_sprite(book)
    for box in PAGES:
        page_paper(book, box, rnd)
    win = Window(enh, 6, pad_top=0)
    win.corner_gears(bottom_right=False, top_left=False)
    win.img.alpha_composite(book, (0, BOOK_TOP))
    d = win.d
    for box in PAGES:
        page_border(d, (box[0], box[1] + BOOK_TOP, box[2], box[3] + BOOK_TOP))
    win.img.alpha_composite(hat, (slot_box(*PREV_SLOT)[0] + 27 - hat.width // 2, HAT_TOP))
    for r, c in LIST_SLOTS + NEED_SLOTS:
        slot_cell(d, *slot_box(r, c))
    # 고른 요리(2배 크기, 32px): 아래 그림자 타원 + 둘레 햇살
    cx, cy = dish_center()
    d.ellipse([cx - 15, cy + 11, cx + 14, cy + 17], fill=(238, 188, 132))
    for dx, dy, ex, ey in ((-21, -8, -18, -7), (-22, 1, -19, 1), (18, -7, 21, -8), (19, 1, 22, 1),
                           (-14, -17, -12, -15), (12, -15, 14, -17), (0, -20, 0, -18)):
        d.line([(cx + dx, cy + dy), (cx + ex, cy + ey)], fill=RAY)
    return win.finish()


if __name__ == "__main__":
    enh = Image.open(sys.argv[1]).convert("RGBA")
    out = build(enh)
    out.save(sys.argv[2])
    if len(sys.argv) > 3:
        p = Preview(out, 6, sys.argv[4], pad_top=0)
        foods = ["rabbit_stew", "mushroom_stew", "beetroot_soup", "suspicious_stew", "bread", "cookie", "pumpkin_pie",
                 "baked_potato", "cooked_beef"]
        for (r, c), name in zip(LIST_SLOTS, foods):
            p.item(r, c, p.vanilla(name))
        p.item(*PREV_SLOT, p.vanilla("arrow"))
        p.item(*NEXT_SLOT, p.vanilla("spectral_arrow"))
        x, y = slot_box(*DISH_SLOT)                                # 2배 크기 미리보기
        p.img.alpha_composite(p.vanilla("rabbit_stew").resize((32, 32), Image.NEAREST), (x - 7, y - 7))
        for (r, c), name in zip(NEED_SLOTS, ["carrot", "potato", "beef", "beetroot", "bowl"]):
            p.item(r, c, p.vanilla(name))
        p.save(sys.argv[3])
    print("ok")

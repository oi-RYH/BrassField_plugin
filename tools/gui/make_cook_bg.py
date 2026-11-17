"""
요리 기기 창 배경 (6줄 상자 창, 간판 없음). 공통 틀은 gui_kit.py.

솥 화면 (CookingMachine):
  왼쪽 기계 그림(대형 솥: art/cauldron_concept.png 를 그대로 줄임) + 솥 입에서 오르는 원래 김 위에 큰 구름
  (art/cauldron_concept2.png 의 연기 윗부분). 걸어 둔 요리의 재료가 구름 위 다섯 칸에 떠 있다 (위 3칸, 아래 왼쪽 2칸).
  오른쪽: 접시(완성품 2x2 칸, 음식은 2배 크기 모델) + 아래 개수 명찰 / 오른쪽 위 레시피 책 그림(2x2 칸, art/recipe_book_icon.png)
  / 오른쪽 아래 부산물(빈 그릇) 두 칸. 빈 바탕에는 잔점 · 파이프 · 톱니 · 희미한 회로선.
  진행 표시는 솥 오른쪽 압력 게이지(원래 그림 자리에 칸 하나 크기로 키워 덮음) 바늘 (글꼴 그림, make_cook_assets.py).
  게이지가 걸친 두 칸(GAUGE_SLOTS)에 마우스를 올리면 남은 시간.
그림이 아직 없는 기기는 기계 그림 대신 재료 칸 황동 테와 같은 자리 작은 게이지를 그린다 (build_generic).

사용: python3 tools/gui/make_cook_bg.py <enhance_bg.png> <출력 폴더> [미리보기 폴더 <클라이언트 jar>]
"""
import colorsys
import os
import sys
from collections import deque

from PIL import Image

from gui_kit import Preview, Window, shrink_art, slot_box

ART = os.path.join(os.path.dirname(os.path.abspath(__file__)), "art")
ROWS = 6
POT_BOX, POT_SCALE, POT_AT = (172, 57, 1207, 1109), 0.080, (10, 41)
CLOUD_REGION, CLOUD_WIDTH, CLOUD_BOTTOM = (400, 0, 960, 320), 74, 52      # 시안2 연기 윗부분 · 줄인 폭 · 아래 끝 y
CLOUD_CENTER_X = 52                                                     # 재료 1~3열 가운데
INGREDIENT_SLOTS = [(0, 1), (0, 2), (0, 3), (1, 1), (1, 2)]
PLATE_SLOT = (2, 6)                            # 완성품 2x2 칸의 왼쪽 위 (2~3줄 6~7열)
BOOK_SLOT = (0, 6)                             # 레시피 책 2x2 칸의 왼쪽 위 (0~1줄 6~7열)
BOOK_ICON_BOX, BOOK_ICON_HEIGHT = (158, 16, 1128, 1166), 34
BYPRODUCT_SLOTS = [(5, 7), (5, 8)]
GAUGE_CENTER = (67, 41)                        # 솥 그림 기준 원래 게이지 가운데 — 칸 하나 크기로 키운 게이지를 그 자리에 덮어 그린다
GAUGE_BEZEL, GAUGE_FACE_R = 8.4, 6.3           # 황동 테 · 눈금판 반지름 (지름 17 = 칸 하나 정도)
GAUGE_SLOTS = [(3, 3), (3, 4)]                 # 게이지가 걸친 두 칸: 마우스를 올리면 남은 시간
FACE = (246, 232, 204)
FIRE_SLOT = (4, 2)                             # 조리 시작·멈춤 버튼 (화덕 문 자리). 칸에는 불 아이콘 아이템 (켜짐·꺼짐)
FIRE_BORDER = 3                                # 버튼 판 테 두께 (칸 둘레 사방 같게 → 24x24 정사각형)
FIRE = {"on": {"R": (196, 40, 24), "O": (246, 122, 30), "Y": (255, 204, 52), "W": (255, 246, 206)},
        "off": {"R": (64, 62, 66), "O": (108, 106, 112), "Y": (146, 144, 150), "W": (178, 176, 182)}}
FLAME = ["................",
         ".......R........",
         "......RR........",
         "......ROR...R...",
         ".....ROOR..RR...",
         "....ROOOORRROR..",
         "....ROOYOOOOOR..",
         "...ROOYYOOYOOR..",
         "...ROYYYYOYYOR..",
         "..ROOYYWYYYYOOR.",
         "..ROYYWWWYYYYOR.",
         "..ROYYWWWWYYYOR.",
         "..ROOYWWWWYYOOR.",
         "...ROOYYYYYOOR..",
         "....RROOOOORR...",
         "......RRRRR....."]
BRASS = [(96, 52, 26), (187, 127, 54), (242, 196, 112), (40, 22, 12)]   # 테 그늘 · 테 · 테 빛 · 외곽선
PLATE = [(206, 198, 182), (110, 92, 74), (238, 232, 218), (196, 188, 172)]   # 접시 테 · 외곽선 · 안쪽 · 안쪽 그늘
LABEL = [(214, 198, 166), (110, 80, 50)]                                     # 개수 명찰 바탕 · 테


def food_center():
    """완성 음식(2배 크기) 가운데 = 2x2 칸 가운데"""
    x, y = slot_box(*PLATE_SLOT)
    return x + 18, y + 18


def plate_center():
    cx, cy = food_center()
    return cx, cy + 12


def label_box():
    cx, cy = plate_center()
    return cx - 12, cy + 9, cx + 11, cy + 17


def gauge_center():
    return POT_AT[0] + GAUGE_CENTER[0], POT_AT[1] + GAUGE_CENTER[1]


def pot():
    return shrink_art(Image.open(os.path.join(ART, "cauldron_concept.png")).convert("RGBA"), POT_BOX, POT_SCALE)


def cloud():
    """시안2 연기 윗부분: 채도 낮고 밝은 칸만 잘라 줄이고, 짙은 칸·10칸 미만 부스러기를 지운다"""
    src = Image.open(os.path.join(ART, "cauldron_concept2.png")).convert("RGBA")
    steam = Image.new("RGBA", src.size, (0, 0, 0, 0))
    sp, p = steam.load(), src.load()
    x0, y0, x1, y1 = CLOUD_REGION
    for y in range(y0, y1):
        for x in range(x0, x1):
            r, g, b, a = p[x, y]
            if a >= 60:
                _, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
                if s < 0.25 and v > 0.55:
                    sp[x, y] = (r, g, b, 255)
    box = steam.getbbox()
    out = shrink_art(steam, box, CLOUD_WIDTH / (box[2] - box[0]))
    q = out.load()
    w, h = out.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = q[x, y]
            if a and (r + g + b) / 3 < 150:
                q[x, y] = (0, 0, 0, 0)
    seen = set()
    for y in range(h):
        for x in range(w):
            if not q[x, y][3] or (x, y) in seen:
                continue
            comp, todo = [], deque([(x, y)])
            seen.add((x, y))
            while todo:
                cx, cy = todo.popleft()
                comp.append((cx, cy))
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= nx < w and 0 <= ny < h and q[nx, ny][3] and (nx, ny) not in seen:
                        seen.add((nx, ny))
                        todo.append((nx, ny))
            if len(comp) < 10:
                for c in comp:
                    q[c] = (0, 0, 0, 0)
    for _ in range(3):                         # 구름 안 구멍(짙은 칸을 지운 자리) 메우기: 이웃 셋 이상이 구름이면 평균색
        fill = {}
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                if q[x, y][3]:
                    continue
                nb = [q[n] for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)) if q[n][3]]
                if len(nb) >= 3:
                    fill[(x, y)] = tuple(sum(c[i] for c in nb) // len(nb) for i in range(3)) + (255,)
        for xy, c in fill.items():
            q[xy] = c
    return out


def _disk(r):
    cx, cy = gauge_center()
    n = int(r) + 1
    return [(cx + dx, cy + dy) for dy in range(-n, n + 1) for dx in range(-n, n + 1) if dx * dx + dy * dy <= r * r]


def gauge_mask():
    """키운 게이지 눈금판 칸들 (창 기준). 바늘 글꼴 그림이 이 칸들을 새로 칠한다"""
    return _disk(GAUGE_FACE_R)


def draw_gauge(win):
    """칸 하나 크기 압력 게이지: 외곽선 · 황동 테(왼쪽 위 밝고 오른쪽 아래 그늘) · 크림색 눈금판"""
    cx, cy = gauge_center()
    for x, y in _disk(GAUGE_BEZEL + 1):
        win.img.putpixel((x, y), BRASS[3] + (255,))
    for x, y in _disk(GAUGE_BEZEL):
        dx, dy = x - cx, y - cy
        k = 2 if dx + dy < -5 else 0 if dx + dy > 5 else 1
        win.img.putpixel((x, y), BRASS[k] + (255,))
    for x, y in _disk(GAUGE_FACE_R + 0.8):
        win.img.putpixel((x, y), BRASS[3] + (255,))
    for x, y in _disk(GAUGE_FACE_R):
        win.img.putpixel((x, y), FACE + (255,))


def fire_icon(state):
    """불 버튼 아이콘 (16x16): on = 타오르는 불꽃, off = 꺼진 회색 불꽃"""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y, line in enumerate(FLAME):
        for x, c in enumerate(line):
            if c != ".":
                img.putpixel((x, y), FIRE[state][c] + (255,))
    return img


def draw_fire_button(win):
    """화덕 문 자리에 튀어나온 정사각형 황동 버튼 판 (칸 둘레 사방 FIRE_BORDER 같은 두께):
    외곽선 · 위왼쪽 밝고 아래오른쪽 어두운 테 · 네 귀 리벳 · 가운데 움푹한 짙은 판"""
    d = win.d
    sx, sy = slot_box(*FIRE_SLOT)
    x0, y0, x1, y1 = sx - FIRE_BORDER, sy - FIRE_BORDER, sx + 17 + FIRE_BORDER, sy + 17 + FIRE_BORDER
    d.rounded_rectangle([x0, y0, x1, y1], radius=3, fill=BRASS[3])
    d.rounded_rectangle([x0 + 1, y0 + 1, x1 - 1, y1 - 1], radius=2, fill=BRASS[0])
    d.rounded_rectangle([x0 + 1, y0 + 1, x1 - 2, y1 - 2], radius=2, fill=BRASS[2])
    d.rectangle([x0 + 2, y0 + 2, x1 - 2, y1 - 2], fill=BRASS[1])
    d.rectangle([sx, sy, sx + 17, sy + 17], fill=(52, 28, 20))               # 움푹한 판 (칸 18x18, 아이콘 자리)
    d.line([(sx, sy), (sx + 17, sy)], fill=(30, 16, 10))
    d.line([(sx, sy), (sx, sy + 17)], fill=(30, 16, 10))
    for rx, ry in ((x0 + 2, y0 + 2), (x1 - 2, y0 + 2), (x0 + 2, y1 - 2), (x1 - 2, y1 - 2)):
        d.point((rx, ry), (255, 236, 170))


def draw_plate(win):
    cx, cy = plate_center()
    d = win.d
    d.ellipse([cx - 23, cy - 7, cx + 22, cy + 7], fill=PLATE[0], outline=PLATE[1])
    d.ellipse([cx - 17, cy - 5, cx + 16, cy + 4], fill=PLATE[2])
    d.arc([cx - 17, cy - 5, cx + 16, cy + 4], 180, 360, fill=PLATE[3])
    d.rectangle(label_box(), fill=LABEL[0], outline=LABEL[1])


def draw_book(win):
    src = Image.open(os.path.join(ART, "recipe_book_icon.png")).convert("RGBA")
    box = BOOK_ICON_BOX
    icon = shrink_art(src, box, BOOK_ICON_HEIGHT / (box[3] - box[1]))
    x, y = slot_box(*BOOK_SLOT)
    win.img.alpha_composite(icon, (x + 18 - icon.width // 2, y + 18 - icon.height // 2))


def grain(win, seed=17):
    """바탕 판 잔점: 기존 바탕 색(PANEL) 칸만 조금 어둡게·밝게 (강화 창 바탕처럼 거칠게)"""
    import random
    from gui_kit import PANEL
    rnd = random.Random(seed)
    p = win.img.load()
    panel = {c + (255,) for c in PANEL}
    for y in range(win.top):
        for x in range(176):
            if p[x, y] in panel:
                r = rnd.random()
                if r < 0.05:
                    p[x, y] = (34, 28, 22, 255)
                elif r < 0.08:
                    p[x, y] = (56, 48, 40, 255)
                elif r < 0.09:
                    p[x, y] = (64, 56, 46, 255)


def decor(win):
    """빈 바탕 장식: 솥 → 접시 파이프(가운데 작은 톱니), 희미한 회로선, 빈 그릇 칸 황동 테"""
    from gui_kit import CIRCUIT_GEAR, CIRCUIT_LINK
    px, py = plate_center()
    win.pipe_h(92, px - 24, py - 2)                                   # 솥 오른쪽 배관 → 접시
    win.gear_small(97, py - 8)
    win.copy(CIRCUIT_GEAR, (92, 16))
    win.copy(CIRCUIT_LINK, (100, 106))
    for r, c in BYPRODUCT_SLOTS:
        win.frame_slots(r, c)



def base(enh):
    win = Window(enh, ROWS, pad_top=0)
    win.corner_gears(bottom_right=False, top_left=False)
    grain(win)
    decor(win)
    return win


def build_kettle(enh):
    win = base(enh)
    win.img.alpha_composite(pot(), POT_AT)
    draw_gauge(win)
    draw_fire_button(win)
    c = cloud()
    win.img.alpha_composite(c, (CLOUD_CENTER_X - c.width // 2, CLOUD_BOTTOM - c.height))
    draw_plate(win)
    draw_book(win)
    return win.finish()


def build_generic(enh):
    """기계 그림이 아직 없는 기기: 재료 칸 황동 테 + 솥과 같은 자리에 게이지"""
    win = base(enh)
    for r, c in INGREDIENT_SLOTS:
        win.frame_slots(r, c)
    draw_gauge(win)
    draw_fire_button(win)
    draw_plate(win)
    draw_book(win)
    return win.finish()


if __name__ == "__main__":
    enh = Image.open(sys.argv[1]).convert("RGBA")
    out_dir = sys.argv[2]
    kettle, generic = build_kettle(enh), build_generic(enh)
    kettle.save(os.path.join(out_dir, "cook_kettle_bg.png"))
    generic.save(os.path.join(out_dir, "cook_generic_bg.png"))
    if len(sys.argv) > 3:
        for name, img in (("kettle", kettle), ("generic", generic)):
            p = Preview(img, ROWS, sys.argv[4], pad_top=0)
            for (r, c), item in zip(INGREDIENT_SLOTS, ("carrot", "potato", "beetroot", "beef", "mushroom_stew")):
                p.item(r, c, p.vanilla(item))
            cx, cy = food_center()
            p.img.alpha_composite(p.vanilla("rabbit_stew").resize((32, 32), Image.NEAREST), (cx - 16, cy - 16))
            p.item(*BYPRODUCT_SLOTS[0], p.vanilla("bucket"))
            p.save(os.path.join(sys.argv[3], "2026-11-17_cook_%s.png" % name))
    print("ok")

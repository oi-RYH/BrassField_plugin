"""
요리 기기 창 배경 (6줄 상자 창, 간판 없음). 공통 틀은 gui_kit.py.

솥 화면 (CookingMachine):
  왼쪽 기계 그림(대형 솥: art/cauldron_concept.png 를 그대로 줄임) + 솥 입에서 오르는 원래 김 위에 큰 구름
  (art/cauldron_concept2.png 의 연기 윗부분). 걸어 둔 요리의 재료가 구름 위 다섯 칸에 떠 있다 (위 3칸, 아래 왼쪽 2칸).
  오른쪽: 접시(완성품 2x2 칸, 음식은 2배 크기 모델) + 아래 개수 명찰 / 오른쪽 위 레시피 책 그림(2x2 칸, art/recipe_book_icon.png)
  / 오른쪽 아래 부산물(빈 그릇) 두 칸. 빈 바탕에는 잔점 · 파이프 · 톱니 · 희미한 회로선.
  진행 표시는 솥 오른쪽 압력 게이지(원래 그림 자리에 칸 하나 크기로 키워 덮음) 바늘 (글꼴 그림, make_cook_assets.py).
  게이지가 걸친 두 칸(GAUGE_SLOTS)에 마우스를 올리면 남은 시간.
그림이 아직 없는 기기는 기계 그림 없이 같은 자리에 주문서 · 게이지 · 불 버튼 (build_generic).
조리대는 화면을 꽉 채우는 따로 배치 (build_counter, CookLayout.COUNTER).

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
INGREDIENT_SLOTS = [(0, 1), (0, 2), (0, 3), (1, 1), (1, 2)]   # 주문서 본문 (0줄 1~3열, 1줄 1~2열)
KETTLE_NOTE_AT = (20, -13)                     # 솥 화면 주문서 왼쪽 위 (연기 자리). 집게·머리가 창 위로 튀어나온다
KETTLE_PAD = 13                                # 창 위로 튀어나온 만큼 그림 맨 위 여백 (cook_gui.yml y_position = 13 + KETTLE_PAD)
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


def food_center(slot=None):
    """완성 음식(2배 크기) 가운데 = 2x2 칸 가운데 (slot = 2x2 칸 왼쪽 위, 기본 솥 접시)"""
    x, y = slot_box(*(slot or PLATE_SLOT))
    return x + 18, y + 18


def plate_center(slot=None):
    cx, cy = food_center(slot)
    return cx, cy + 12


def label_box(slot=None):
    """접시 아래 개수 명찰. 명찰 숫자 글꼴 그림(cook_plate_*)은 높이가 정해져 있어 접시는 어느 기기든 2·3줄에 둔다"""
    cx, cy = plate_center(slot)
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


def _disk(r, center=None):
    cx, cy = center or gauge_center()
    n = int(r) + 1
    return [(cx + dx, cy + dy) for dy in range(-n, n + 1) for dx in range(-n, n + 1) if dx * dx + dy * dy <= r * r]


def gauge_mask(center=None):
    """키운 게이지 눈금판 칸들 (창 기준). 바늘 글꼴 그림이 이 칸들을 새로 칠한다"""
    return _disk(GAUGE_FACE_R, center)


NEEDLE_COLORS = dict(needle=(60, 30, 20, 255), tip=(190, 40, 30, 255), tick=(120, 90, 64, 255), hub=(30, 16, 10, 255))


def needle_pixels(level, steps, mask, center):
    """게이지 눈금판(mask)을 새로 칠할 색: 크림색 판 · 눈금 steps+1 개(지나온 눈금은 빨강) · 바늘(축에서 5칸, 끝 빨강).
    7시(225도) → 5시(-45도) 시계 방향. {(x, y): 색}"""
    import math
    inside = set(mask)
    out = {p: FACE + (255,) for p in mask}
    cx, cy = center
    for step in range(steps + 1):
        a = math.radians(225 - 270 * step / steps)
        p = (round(cx + 5 * math.cos(a)), round(cy - 5 * math.sin(a)))
        if p in inside:
            out[p] = NEEDLE_COLORS["tip"] if step <= level and level > 0 else NEEDLE_COLORS["tick"]
    a = math.radians(225 - 270 * level / steps)
    for i in range(5):
        p = (round(cx + i * math.cos(a)), round(cy - i * math.sin(a)))
        if p in inside:
            out[p] = NEEDLE_COLORS["tip"] if i == 4 else NEEDLE_COLORS["needle"]
    out[(cx, cy)] = NEEDLE_COLORS["hub"]
    return out


def draw_gauge(win, center=None):
    """칸 하나 크기 압력 게이지: 외곽선 · 황동 테(왼쪽 위 밝고 오른쪽 아래 그늘) · 크림색 눈금판"""
    center = center or gauge_center()
    cx, cy = center
    for x, y in _disk(GAUGE_BEZEL + 1, center):
        win.img.putpixel((x, y), BRASS[3] + (255,))
    for x, y in _disk(GAUGE_BEZEL, center):
        dx, dy = x - cx, y - cy
        k = 2 if dx + dy < -5 else 0 if dx + dy > 5 else 1
        win.img.putpixel((x, y), BRASS[k] + (255,))
    for x, y in _disk(GAUGE_FACE_R + 0.8, center):
        win.img.putpixel((x, y), BRASS[3] + (255,))
    for x, y in _disk(GAUGE_FACE_R, center):
        win.img.putpixel((x, y), FACE + (255,))


def fire_icon(state):
    """불 버튼 아이콘 (16x16): on = 타오르는 불꽃, off = 꺼진 회색 불꽃"""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y, line in enumerate(FLAME):
        for x, c in enumerate(line):
            if c != ".":
                img.putpixel((x, y), FIRE[state][c] + (255,))
    return img


def draw_fire_button(win, slot=None, extend=0):
    """화덕 문 자리에 튀어나온 정사각형 황동 버튼 판 (칸 둘레 사방 FIRE_BORDER 같은 두께):
    외곽선 · 위왼쪽 밝고 아래오른쪽 어두운 테 · 네 귀 리벳 · 가운데 움푹한 짙은 판"""
    d = win.d
    sx, sy = slot_box(*(slot or FIRE_SLOT))
    x0, y0, x1, y1 = sx - FIRE_BORDER, sy - FIRE_BORDER, sx + 17 + FIRE_BORDER, sy + 17 + FIRE_BORDER + extend
    d.rounded_rectangle([x0, y0, x1, y1], radius=3, fill=BRASS[3])
    d.rounded_rectangle([x0 + 1, y0 + 1, x1 - 1, y1 - 1], radius=2, fill=BRASS[0])
    d.rounded_rectangle([x0 + 1, y0 + 1, x1 - 2, y1 - 2], radius=2, fill=BRASS[2])
    d.rectangle([x0 + 2, y0 + 2, x1 - 2, y1 - 2], fill=BRASS[1])
    d.rectangle([sx, sy, sx + 17, sy + 17 + extend], fill=(52, 28, 20))      # 움푹한 판 (칸 18x18, 아이콘 자리 · extend 만큼 아래로 길게)
    d.line([(sx, sy), (sx + 17, sy)], fill=(30, 16, 10))
    d.line([(sx, sy), (sx, sy + 17)], fill=(30, 16, 10))
    for rx, ry in ((x0 + 2, y0 + 2), (x1 - 2, y0 + 2), (x0 + 2, y1 - 2), (x1 - 2, y1 - 2)):
        d.point((rx, ry), (255, 236, 170))


def draw_plate(win, slot=None, label=True):
    """2x2 접시 (label: 아래 개수 명찰 — 없으면 개수는 요리 오른쪽 위 칸 숫자)"""
    cx, cy = plate_center(slot)
    d = win.d
    d.ellipse([cx - 23, cy - 7, cx + 22, cy + 7], fill=PLATE[0], outline=PLATE[1])
    d.ellipse([cx - 17, cy - 5, cx + 16, cy + 4], fill=PLATE[2])
    d.arc([cx - 17, cy - 5, cx + 16, cy + 4], 180, 360, fill=PLATE[3])
    if label:
        d.rectangle(label_box(slot), fill=LABEL[0], outline=LABEL[1])


def draw_book(win):
    src = Image.open(os.path.join(ART, "recipe_book_icon.png")).convert("RGBA")
    box = BOOK_ICON_BOX
    icon = outlined(shrink_art(src, box, BOOK_ICON_HEIGHT / (box[3] - box[1])), BOOK_OUTLINE)
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
    win = Window(enh, ROWS, pad_top=KETTLE_PAD)
    win.corner_gears(bottom_right=False, top_left=False)
    grain(win)
    decor(win)
    return win


def build_kettle(enh):
    win = base(enh)
    win.img.alpha_composite(pot(), POT_AT)
    draw_gauge(win)
    draw_fire_button(win)
    draw_plate(win)
    draw_book(win)
    return finish_with_note(win)


def finish_with_note(win):
    """창을 KETTLE_PAD 만큼 내려 놓고 주문서를 건다 (집게·머리가 창 위로 튀어나오게, 솥 윗부분을 조금 덮는다)"""
    out = win.finish()
    out.alpha_composite(note(), (KETTLE_NOTE_AT[0], KETTLE_PAD + KETTLE_NOTE_AT[1]))
    return out


def build_generic(enh):
    """기계 그림이 아직 없는 기기: 재료 칸 황동 테 + 솥과 같은 자리에 게이지"""
    win = base(enh)
    draw_gauge(win)
    draw_fire_button(win)
    draw_plate(win)
    draw_book(win)
    return finish_with_note(win)


# ── 조리대 (화면을 꽉 채우는 가로 그림, art/counter_concept3.png) ──
# 칸 배치는 com.brassfield.cooking.CookLayout.COUNTER 와 맞춘다.
COUNTER_BOX = (62, 20, 1476, 996)              # 시안에서 조리대 범위
COUNTER_WIDTH, COUNTER_TOP = 162, 22           # 줄인 폭 · 창 기준 위 끝 y (가운데 정렬, 한 칸 내림)
COUNTER_BOOK_AT = (1230, 315)                  # 시안 기준 책 가운데 (오른쪽 벽에 걸린 프라이팬 자리). 누르는 칸은 CookLayout.COUNTER 의 1·2줄 7열
COUNTER_BOOK_HEIGHT = 26
BOOK_OUTLINE = (255, 255, 255)                 # 나무 그림 위에서도 보이게 두르는 흰 테두리
COUNTER_FIRE_SLOT = (5, 4)                     # 화덕 창
COUNTER_GAUGE_AT = (750, 560)                  # 시안 기준 냄비 앞면 가운데 → 게이지
NOTE_BOX, NOTE_SCALE = (86, 8, 1002, 1388), 0.0692   # 주문서 시안(art/order_note.png) 범위 · 줄임 배율
NOTE_CUTS = [(650, 900), (1256, 1284)]         # 시안에서 잘라 내는 띠 (y): 본문 가운데(재료 두 줄만 남김) · 아래 테와 찢어진 끝 사이 여백
NOTE_AT = (4, 22)                              # 창 기준 주문서 왼쪽 위 — 황동 집게가 들보에 물리고, 재료 칸(2~3줄 0~2열)이 본문에 온다


def counter_scale():
    return COUNTER_WIDTH / (COUNTER_BOX[2] - COUNTER_BOX[0])


def counter_point(x, y):
    """시안 좌표 → 창 좌표"""
    s = counter_scale()
    return round((176 - COUNTER_WIDTH) // 2 + (x - COUNTER_BOX[0]) * s), round(COUNTER_TOP + (y - COUNTER_BOX[1]) * s)


def counter_gauge_center():
    return counter_point(*COUNTER_GAUGE_AT)


def draw_note(win, at=None):
    """들보에 황동 집게로 물린 재료 주문서 (사용자 시안을 그대로 줄임). 밝은 종이라 재료 아이콘과 개수 숫자가 잘 보인다.
    NOTE_CUTS 띠를 잘라 재료 두 줄만 들어가게 납작하게 만든다.
    위 요리사 모자 머리 아래 본문에 재료 칸, 오른쪽 아래 비는 칸 자리에 도장 그림이 보인다."""
    src = Image.open(os.path.join(ART, "order_note.png")).convert("RGBA")
    win.img.alpha_composite(note(), at or NOTE_AT)


def _bands(lo, hi, cuts):
    keep, top = [], lo
    for c0, c1 in cuts:
        keep.append((top, c0))
        top = c1
    keep.append((top, hi))
    return keep


def note(cuts=None, xcuts=(), scale=NOTE_SCALE):
    """주문서 시안에서 가로 띠(cuts, y)·세로 띠(xcuts, x)를 잘라 이어 붙이고 scale 로 줄인 그림"""
    src = Image.open(os.path.join(ART, "order_note.png")).convert("RGBA")
    x0, y0, x1, y1 = NOTE_BOX
    rows, cols = _bands(y0, y1, NOTE_CUTS if cuts is None else cuts), _bands(x0, x1, xcuts)
    cut = Image.new("RGBA", (sum(b - a for a, b in cols), sum(b - a for a, b in rows)), (0, 0, 0, 0))
    y = 0
    for a, b in rows:
        x = 0
        for l, r in cols:
            cut.alpha_composite(src.crop((l, a, r, b)), (x, y))
            x += r - l
        y += b - a
    return shrink_art(cut, (0, 0) + cut.size, scale)


def outlined(img, color):
    """그림 둘레에 1px 테두리 (상하좌우로 맞닿은 빈 칸을 color 로)"""
    w, h = img.size
    out = Image.new("RGBA", (w + 2, h + 2), (0, 0, 0, 0))
    a = img.split()[3].load()
    o = out.load()
    for y in range(h):
        for x in range(w):
            if a[x, y] > 128:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (0, 0)):
                    o[x + 1 + dx, y + 1 + dy] = color + (255,)
    out.alpha_composite(img, (1, 1))
    return out


def build_counter(enh):
    """조리대: 그림을 가운데 크게, 오른쪽 벽에 걸린 프라이팬 자리에 흰 테두리 레시피 책, 냄비 앞면에 게이지, 화덕 창에 불 버튼.
    재료는 들보에 매단 주문서 종이 위 (draw_note), 완성품 · 빈 그릇은 오른쪽 도마 위."""
    win = Window(enh, ROWS, pad_top=0)
    win.corner_gears(bottom_right=False, top_left=False)
    grain(win)
    src = Image.open(os.path.join(ART, "counter_concept3.png")).convert("RGBA")
    art = shrink_art(src, COUNTER_BOX, counter_scale())
    win.img.alpha_composite(art, ((176 - art.width) // 2, COUNTER_TOP))
    book = shrink_art(Image.open(os.path.join(ART, "recipe_book_icon.png")).convert("RGBA"), BOOK_ICON_BOX,
                      COUNTER_BOOK_HEIGHT / (BOOK_ICON_BOX[3] - BOOK_ICON_BOX[1]))
    book = outlined(book, BOOK_OUTLINE)
    bx, by = counter_point(*COUNTER_BOOK_AT)
    win.img.alpha_composite(book, (bx - book.width // 2, by - book.height // 2))
    draw_note(win)
    draw_gauge(win, counter_gauge_center())
    draw_fire_button(win, COUNTER_FIRE_SLOT)
    return win.finish()


# ── 착즙기 (art/juicer_concept.png 의 압착기 · 꼭지 · 유리병을 잘라 얹음) ──
# 칸 배치는 com.brassfield.cooking.CookLayout.JUICER 와 맞춘다.
JUICER_ART = "juicer_concept.png"
PRESS_BOX, PRESS_SCALE, PRESS_AT = (500, 40, 1052, 540), 0.19, (50, 1)     # 압착기 (위 들보 · 나사 · 유리통 · 꼭지 · 압력계)
                                               # + 둘레 바탕 장식 (왼쪽 톱니 · 오른쪽 회로선)이 잘리지 않게 넉넉히
PRESS_FRAME_CUT = (995, 40, 1052, 125)         # 그 안에 걸린 시안 창 테 오른쪽 위 모서리는 비운다
PRESS_BOX_CUT = (700, 485, 920, 540)           # 시안 완성품 칸 테 윗부분 · 화살표도 비운다
JAR_BOX = (548, 430, 668, 582)                 # 유리병만 (아래 받침 · 물방울 제외 — 물방울은 압착기 조각에 남는다)
JAR_SLOTS = [(4, 3), (3, 3)]                   # 병이 걸친 세로 2칸 = 완성품 칸 (아래 칸에 주스 아이콘, 병 안에 담긴 듯)
JAR_DROP = 4                                   # 병을 2칸보다 아래로 내린 만큼 (px)
JAR_INTERIOR = (98, 69, 55)                    # 시안 주스(주황)를 지운 자리 — 병 윗부분 빈 유리 안쪽 색
JUICER_NOTE_CUTS = [(1256, 1284)]              # 작은 주문서: 자르지 않고 통째로 줄인다 (테 · 모자 장식 · 도장 그대로, 아래 여백만 잘라 냄)
JUICER_NOTE_SCALE = 0.049
JUICER_NOTE_AT = (12, 3)                       # 작은 주문서 왼쪽 위: 재료 칸(1줄 1열)이 본문 가운데
JUICER_INGREDIENT = (1, 1)
JUICER_BOOK_AT = (34, 86)                      # 주문서 아래 레시피 책 가운데 (흰 테두리). 누르는 칸은 CookLayout.JUICER 의 3·4줄 1열
JUICER_START = (4, 5)                          # 시작 버튼: 압착기 아래 나무 받침대 앞면 가운데
STAND = (84, 79, 129, 114)                     # 압착기 나무 받침을 아래로 늘린 받침대 (창 기준 x0, y0, x1, y1 — 원래 받침 판을 덮는다)
STAND_PLANK_BOX = (522, 582, 696, 612)         # 시안 유리병 받침 나무 판 → 받침대 가로 판으로 쌓는다
STAND_OUTLINE = (40, 20, 10)
BAR = (28, 115, 150, 125)                      # 진행 막대 바깥 (x0, y0, x1, y1) — 안쪽을 글꼴 그림이 채운다
BAR_GEAR_AT = (12, 112)
BAR_GEAR_BOX = (312, 628, 392, 702)            # 시안 진행 막대 왼쪽 톱니


def _concept_bg(c):
    """시안 바탕 (짙은 갈색 잔점, 가장 밝은 채널 100 미만). 톱니 장식(124,72,35) · 압착기 · 회로선은 남는다"""
    r, g, b, a = c
    return a < 128 or max(r, g, b) < 100


def concept_piece(box, scale, clear=None, fill=0.3, art=JUICER_ART, is_bg=None):
    """시안의 box 를 잘라 바깥 바탕을 지우고 scale 로 줄인다. clear: 따로 얹는 그림 자리(시안 좌표)는 비운다"""
    from gui_kit import cut_outside
    src = Image.open(os.path.join(ART, art)).convert("RGBA")
    for box_ in clear or ():
        src.paste((0, 0, 0, 0), box_)
    src = src.crop(box)
    src = cut_outside(src, is_bg or _concept_bg, step=6, close=3, keep=3)
    return shrink_art(src, (0, 0) + src.size, scale, fill)


def press_point(x, y):
    return round(PRESS_AT[0] + (x - PRESS_BOX[0]) * PRESS_SCALE), round(PRESS_AT[1] + (y - PRESS_BOX[1]) * PRESS_SCALE)


def bar_inner():
    x0, y0, x1, y1 = BAR
    return x0 + 2, y0 + 2, x1 - 2, y1 - 2


def draw_bar(win):
    """진행 막대: 외곽선 · 황동 테 · 짙은 홈 (안쪽은 bar_inner, 글꼴 그림이 진행만큼 채운다)"""
    d = win.d
    x0, y0, x1, y1 = BAR
    d.rounded_rectangle([x0, y0, x1, y1], radius=4, fill=BRASS[3])
    d.rounded_rectangle([x0 + 1, y0 + 1, x1 - 1, y1 - 1], radius=3, fill=BRASS[1])
    d.line([(x0 + 3, y0 + 1), (x1 - 3, y0 + 1)], fill=BRASS[2])
    d.line([(x0 + 3, y1 - 1), (x1 - 3, y1 - 1)], fill=BRASS[0])
    ix0, iy0, ix1, iy1 = bar_inner()
    d.rectangle([ix0, iy0, ix1, iy1], fill=BAR_EMPTY)
    d.line([(ix0, iy0), (ix1, iy0)], fill=BAR_EMPTY_SHADE)


BAR_EMPTY, BAR_EMPTY_SHADE = (52, 36, 26), (34, 22, 16)
GEAR_ICON = {"on": {"O": (60, 30, 14), "H": (250, 210, 128), "B": (204, 140, 58), "S": (140, 84, 34)},
             "off": {"O": (36, 34, 38), "H": (168, 166, 172), "B": (118, 116, 122), "S": (80, 78, 84)}}
GEAR = ["................",
        ".......OO.......",
        "...OO.OHHO.OO...",
        "..OHHOHHHHOBBO..",
        "..OHHHHHHBBBBO..",
        "...OHHHOOBBBO...",
        "..OHHHO..OBBSO..",
        ".OHHHO....OBSSO.",
        ".OHHBO....OSSSO.",
        "..OHBBO..OSSSO..",
        "...OBBBOOSSSO...",
        "..OBBBBBSSSSSO..",
        "..OBBOBSSSOSSO..",
        "...OO.OSSO.OO...",
        ".......OO.......",
        "................"]


def gear_icon(state):
    """착즙기 시작 버튼 아이콘 (16x16 톱니): on = 황동, off = 회색. 가운데 축 구멍은 비워 버튼 판이 보인다"""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y, line in enumerate(GEAR):
        for x, ch in enumerate(line):
            if ch != ".":
                img.putpixel((x, y), GEAR_ICON[state][ch] + (255,))
    return img


CORNER_GEARS = [((108, 512, 212, 645), 0.14, (7, 76)),   # 시안 왼쪽 아래 큰 톱니 (창 테에 반쯤 가린 채) → 책 왼쪽
                ((960, 582, 1052, 672), 0.19, (151, 92))]  # 오른쪽 아래 톱니 → 진행 막대 오른쪽 위
CONCEPT_BG_PATCHES = [(170, 440, 280, 490), (500, 110, 540, 140), (920, 520, 980, 590), (500, 420, 560, 500)]


CONCEPT_BG_BLEND = 0.7                         # 시안 색을 가운데 색 쪽으로 당기는 정도 (클수록 매끈)


def concept_texture(win, seed=23, art=JUICER_ART, patches=None):
    """바탕 판(PANEL · 잔점 색) 칸을 시안 바탕 색감으로 바꾼다: 시안의 깨끗한 바탕 조각들에서 색을 무작위로 뽑되
    가운데(중앙값) 색 쪽으로 CONCEPT_BG_BLEND 만큼 당겨 잔점을 옅게 한다"""
    import random
    from gui_kit import PANEL, SPECKS
    src = Image.open(os.path.join(ART, art)).convert("RGB")
    pool = [c for box in patches or CONCEPT_BG_PATCHES for c in src.crop(box).getdata() if sum(c) < 200]
    mid = tuple(sorted(c[i] for c in pool)[len(pool) // 2] for i in range(3))
    k = CONCEPT_BG_BLEND
    pool = [tuple(round(mid[i] * k + c[i] * (1 - k)) for i in range(3)) for c in pool]
    panel = {c + (255,) for c in PANEL} | {c + (255,) for c, _ in SPECKS} | \
            {(34, 28, 22, 255), (56, 48, 40, 255), (64, 56, 46, 255)}
    rnd = random.Random(seed)
    p = win.img.load()
    for y in range(win.h):
        for x in range(176):
            if p[x, y] in panel:
                p[x, y] = rnd.choice(pool) + (255,)


def extend_beam(img, press, k=1):
    """압착기 조각에 딸려 온 시안 위 테 파이프(양쪽 끝이 잘린 가로줄들)를 창 양옆 기둥까지 이어 그린다:
    조각 왼쪽 끝 열과 오른쪽 끝 열이 모두 칠해진 줄만 파이프로 보고, 끝 색을 그대로 늘린다 (k = 해상도 배율)"""
    p = press.load()
    w, h = press.size
    right = max(x for x in range(w) if p[x, 7 * k][3])
    ax, ay = PRESS_AT[0] * k, PRESS_AT[1] * k
    for y in range(h):
        if p[0, y][3] and p[right, y][3] and p[right // 2, y][3]:
            for x in range(PILLAR_X0 * k, ax):
                img.putpixel((x, ay + y), p[1, y])
            for x in range(ax + right + 1, PILLAR_X1 * k):
                img.putpixel((x, ay + y), p[right - 1, y])


PILLAR_X0, PILLAR_X1 = 7, 169


def empty_jar(height=36):
    """시안 유리병에서 주황 주스를 빈 유리 색으로 지우고 세로 2칸(36px) 높이로 줄인 그림 — 완성된 주스 아이콘이 병 안에 보인다.
    바깥 바탕을 먼저 지운 뒤 주스를 칠한다 (빈 유리 색이 바탕과 비슷해 거꾸로 하면 병 아랫부분이 바깥으로 잘린다)"""
    from gui_kit import cut_outside
    src = Image.open(os.path.join(ART, JUICER_ART)).convert("RGBA").crop(JAR_BOX)
    src = cut_outside(src, _concept_bg, step=6, close=3, keep=3)
    p = src.load()
    for y in range(src.height):
        for x in range(src.width):
            r, g, b, a = p[x, y]
            if a and r > 150 and r - b > 80 and g > 70:
                p[x, y] = JAR_INTERIOR + (255,)
    return shrink_art(src, (0, 0) + src.size, height / src.height, 0.3)


def stand(k):
    """압착기 아래 나무 받침대 한 덩어리: 시안 받침 나무 판을 받침대 크기로 늘리고 짙은 외곽선 (k 배 해상도)"""
    x0, y0, x1, y1 = STAND
    w, h = (x1 - x0 + 1) * k, (y1 - y0 + 1) * k
    src = Image.open(os.path.join(ART, JUICER_ART)).convert("RGBA").crop(STAND_PLANK_BOX)
    img = src.resize((w, h), Image.BOX)
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    for i in range(k):
        d.rectangle([i, i, w - 1 - i, h - 1 - i], outline=STAND_OUTLINE)
    return img


# 유리통 주스: 2배 그림 좌표. 통 안쪽 칸마다 원래 그림의 빈 유리 줄 · 주스 줄을 위아래로 이어 붙여 수면 높이만 바꾼다
# 1배로 쓴다: 이 ItemsAdder 베타에서는 그림 크기와 표시 크기가 다른(2배) 글꼴 그림이 게임에 나오지 않았다 (조각으로 나눠도 마찬가지)
JUICER_K = 1
# 해상도별 유리통 값: 글꼴 그림 범위 (x0, y0, x1, y1 — 끝 제외) · 유리 안쪽 위·아래 끝 (y, 아래 끝 제외)
# · 시안 빈 유리 무늬 시작 줄 · 시안 주스 수면 줄 · 수면 밝은 줄 수 · 빈 유리 무늬로 쓰는 줄 끝 (그 아래는 주스 빛이 비쳐 주황기)
BARRELS = {1: dict(box=(96, 42, 115, 62), glass=(43, 61), empty_top=43, juice_top=50, surface=1, empty_end=47),
           2: dict(box=(192, 84, 228, 122), glass=(85, 121), empty_top=86, juice_top=101, surface=2, empty_end=95)}
BARREL = BARRELS[JUICER_K]["box"]


def barrel_frame(bg, fraction, k=JUICER_K):
    """유리통 안쪽을 주스가 fraction(1 = 가득, 0 = 빔)만큼 찬 모습으로 그린 조각 (bg 는 시안 주스가 그대로인 k 배 배경)"""
    b = BARRELS[k]
    x0, y0, x1, y1 = b["box"]
    g0, g1 = b["glass"]
    et, jt = b["empty_top"], b["juice_top"]
    SURFACE_ROWS, EMPTY_END = b["surface"], b["empty_end"]
    surface = round(g0 + (1 - fraction) * (g1 - g0))
    src = bg.load()
    out = bg.crop(b["box"])
    o = out.load()
    for x in range(x0, x1):
        for y in range(g0, g1):
            if y >= surface + SURFACE_ROWS:       # 주스 몸통: 시안 몸통 줄을 남은 높이로 늘리거나 줄인다 (이음매 없이)
                span = g1 - surface - SURFACE_ROWS
                sy = jt + SURFACE_ROWS + (y - surface - SURFACE_ROWS) * (g1 - jt - SURFACE_ROWS) // max(1, span)
            elif y >= surface:                    # 수면 (밝은 줄) 그대로
                sy = jt + (y - surface)
            elif y < et:
                sy = y
            else:                                 # 빈 유리: 시안 빈 유리 줄을 수면 위 높이로 늘리거나 줄인다
                sy = et + (y - et) * (EMPTY_END - et) // max(1, surface - et)
            o[x - x0, y - y0] = src[x, sy]
    return out


JUICER_GAUGE_X, JUICER_GAUGE_TOP = BAR[0], 42   # 게이지 글꼴 그림 왼쪽 위 (창 기준 1배 좌표, CookLayout.JUICER gaugeX 와 맞춘다)
BAR_FILL = [(255, 214, 110), (246, 168, 36), (196, 112, 18)]   # 진행 막대 채움: 윗줄 빛 · 몸 · 아랫줄 그늘


def juicer_gauge(raw, level, steps):
    """착즙기 게이지 한 단계 (2배 그림): 유리통 주스 (가득 → 빔) + 진행 막대 채움 (빔 → 가득).
    raw = build_juicer(bake=False). 돌려주는 그림의 왼쪽 위는 창 (JUICER_GAUGE_X, JUICER_GAUGE_TOP)"""
    k = JUICER_K
    x0, y0 = JUICER_GAUGE_X * k, JUICER_GAUGE_TOP * k
    w, h = (BAR[2] + 1) * k - x0, (BAR[3] + 1) * k - y0
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    img.paste(barrel_frame(raw, 1 - level / steps, k), (BARRELS[k]["box"][0] - x0, BARRELS[k]["box"][1] - y0))
    ix0, iy0, ix1, iy1 = bar_inner()
    fill = round((ix1 - ix0 + 1) * k * level / steps)
    if fill:
        from PIL import ImageDraw
        d = ImageDraw.Draw(img)
        bx, by, bh = ix0 * k - x0, iy0 * k - y0, (iy1 - iy0 + 1) * k
        d.rectangle([bx, by, bx + fill - 1, by + bh - 1], fill=BAR_FILL[1])
        d.rectangle([bx, by, bx + fill - 1, by + k - 1], fill=BAR_FILL[0])
        d.rectangle([bx, by + bh - k, bx + fill - 1, by + bh - 1], fill=BAR_FILL[2])
    return img


def build_juicer(enh, k=JUICER_K, bake=True):
    """착즙기: 왼쪽 작은 주문서(재료 1칸)와 그 아래 흰 테두리 책 · 오른쪽 압착기 → 꼭지 → 유리병(완성품 세로 2칸),
    압력계 아래 시작 버튼, 맨 아래 진행 막대 (막대가 걸친 칸에 마우스를 올리면 남은 시간).
    k: 해상도 배율. 창 틀 · 바탕 · 버튼 · 막대는 1배로 그려 k 배로 키우고, 시안 그림(압착기 · 병 · 톱니 · 주문서 · 책)은
    k 배 해상도로 줄여 얹는다 (글꼴 그림 scale_ratio 를 256 으로 두면 같은 크기로 k 배 촘촘하게 보인다)"""
    win = Window(enh, ROWS, pad_top=0)
    win.corner_gears(bottom_right=False, top_left=False)
    concept_texture(win)
    draw_bar(win)
    top = Window.__new__(Window)                   # 그림 위에 다시 얹는 1배 층 (시작 버튼)
    top.img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    from PIL import ImageDraw
    top.d = ImageDraw.Draw(top.img)
    draw_fire_button(top, JUICER_START)
    up = lambda im: im if k == 1 else im.resize((im.width * k, im.height * k), Image.NEAREST)
    out = up(win.finish())
    put = lambda im, xy: out.alpha_composite(im, (round(xy[0] * k), round(xy[1] * k)))
    for box, scale, at in CORNER_GEARS + [(BAR_GEAR_BOX, PRESS_SCALE, BAR_GEAR_AT)]:
        put(concept_piece(box, scale * k), at)
    press = concept_piece(PRESS_BOX, PRESS_SCALE * k, clear=(JAR_BOX, PRESS_FRAME_CUT, PRESS_BOX_CUT))
    extend_beam(out, press, k)
    put(press, PRESS_AT)
    put(stand(k), STAND[:2])
    jar = empty_jar(36 * k)
    x, y = slot_box(*JAR_SLOTS[1])
    out.alpha_composite(jar, ((x + 9) * k - jar.width // 2, (y + 36 + JAR_DROP) * k - jar.height))
    put(note(JUICER_NOTE_CUTS, scale=JUICER_NOTE_SCALE * k), JUICER_NOTE_AT)
    book = shrink_art(Image.open(os.path.join(ART, "recipe_book_icon.png")).convert("RGBA"), BOOK_ICON_BOX,
                      COUNTER_BOOK_HEIGHT / (BOOK_ICON_BOX[3] - BOOK_ICON_BOX[1]))
    book = up(outlined(book, BOOK_OUTLINE))         # 책은 1배 그림을 그대로 키운다 (다른 기기 책과 같은 모습)
    bx, by = JUICER_BOOK_AT
    out.alpha_composite(book, (bx * k - book.width // 2, by * k - book.height // 2))
    out.alpha_composite(up(top.img))
    if bake:                                       # 쉬는 동안은 유리통 가득 (bake=False: 시안 주스 그대로 — 단계 그림 원본)
        out.paste(barrel_frame(out, 1.0, k), BARRELS[k]["box"][:2])
    return out


# ── 제빵 오븐 (art/oven_concept.png 배치 + art/oven_machine.png 오븐을 가운데에 줄여 얹음) ──
# 칸 배치는 com.brassfield.cooking.CookLayout.OVEN 과 맞춘다.
OVEN_ART, OVEN_CONCEPT = "oven_machine.png", "oven_concept.png"
OVEN_BOX = (178, 168, 962, 1262)               # 오븐 그림 (굴뚝 위 연기 · 받침 다리 제외 — 다리가 가방 칸 위 황동 띠에 걸리지 않게)
OVEN_SCALE = 0.1
OVEN_AT = (87, 14)                             # 창 기준 오븐 왼쪽 위 (오른쪽 끝). 시작 버튼 칸(4줄 6열)은 화실 문보다 5px 아래
OVEN_WINDOW = (263, 415, 765, 737)             # 오븐 그림 기준 굽는 칸 창 (황동 테 포함)
OVEN_PIE = (395, 555, 648, 662)                # 창 안 파이 (게이지: 굽는 정도)
OVEN_DIAL = (842, 575, 70)                     # 오븐 그림 온도계 가운데 · 반지름 → 그 자리에 솥과 같은 계기판을 덮어 그린다
OVEN_INGREDIENTS = [(1, 1), (1, 2)]            # 주문서 위 가로 두 칸
OVEN_NOTE_SCALE = 0.0635                       # 재료 두 칸이 가로로 들어가는 폭
OVEN_NOTE_CUTS = [(560, 1000), (1256, 1284)]   # 본문 가운데를 잘라 키를 줄인다 (재료 한 줄)
OVEN_NOTE_AT = (14, 3)
OVEN_BOOK_AT = (34, 110)                       # 탁자 아래 4·5줄 1열
OVEN_START = (4, 6)                            # 화실 문
OVEN_START_EXTEND = 0                          # 버튼 판을 아래로 늘리는 만큼 (정사각형)
OVEN_OUTPUT = (3, 1)                           # 주문서 아래 탁자 위 (재료 칸 바로 아래)
OVEN_BYPRODUCT = (3, 2)                        # 탁자 위 완성품 오른쪽 빈 병 칸
TABLE = (16, 88, 70, 94)                       # 주문서와 책 사이 나무 탁자 (x0, y0, x1, y1 — 상판 4px + 양끝 다리)
                      # 식힘망 (x0, y0, x1, y1)
OVEN_DECOR = [((359, 157, 421, 220), 0.17, (58, 106)),    # 시안 희미한 톱니 → 책 오른쪽
              ((1009, 157, 1046, 264), 0.17, (75, 100)),  # 회로선 → 톱니 오른쪽
              ((984, 451, 1027, 489), 0.17, (17, 70))]    # 탁자 위 반짝임


def _black_bg(c):
    r, g, b, a = c
    return a < 128 or max(r, g, b) < 28


def oven_point(x, y):
    """오븐 그림 좌표 → 창 좌표"""
    return OVEN_AT[0] + (x - OVEN_BOX[0]) * OVEN_SCALE, OVEN_AT[1] + (y - OVEN_BOX[1]) * OVEN_SCALE


def oven_box(box):
    x0, y0 = oven_point(*box[:2])
    x1, y1 = oven_point(*box[2:])
    return round(x0), round(y0), round(x1), round(y1)


def draw_table(win):
    """주문서 아래 나무 탁자: 상판(시안 나무 판을 늘림, 위 밝은 줄) + 양 끝 다리, 짙은 외곽선"""
    x0, y0, x1, y1 = TABLE
    src = Image.open(os.path.join(ART, JUICER_ART)).convert("RGBA").crop(STAND_PLANK_BOX)
    top = src.resize((x1 - x0 + 1, 4), Image.BOX)
    d = win.d
    for lx in (x0 + 3, x1 - 5):
        d.rectangle([lx - 1, y0 + 4, lx + 3, y1], fill=STAND_OUTLINE)
        d.rectangle([lx, y0 + 5, lx + 2, y1 - 1], fill=(120, 66, 30))
        d.line([(lx, y0 + 5), (lx, y1 - 1)], fill=(160, 96, 46))
    d.rectangle([x0 - 1, y0 - 1, x1 + 1, y0 + 4], fill=STAND_OUTLINE)
    win.img.alpha_composite(top, (x0, y0))
    d.line([(x0, y0), (x1, y0)], fill=(214, 150, 84))


def oven_dial():
    """창 기준 온도계 가운데 · 바늘이 지나는 눈금판 칸들 (밝은 크림색 칸만)"""
    cx, cy, r = OVEN_DIAL
    x, y = oven_point(cx, cy)
    return (round(x), round(y)), r * OVEN_SCALE


def build_oven(enh, bake=True):
    """제빵 오븐: 왼쪽 주문서(재료 2칸) · 그 아래 책, 가운데 스팀펑크 2단 오븐(위 굽는 칸 창 · 옆 온도계 · 아래 화실 문 = 시작 버튼),
    오른쪽 식힘망(완성품) · 빈 병 칸. 진행은 온도계 바늘 + 창 안 파이가 노릇해지고 불빛이 밝아짐 (글꼴 그림 oven_gauge)"""
    win = Window(enh, ROWS, pad_top=0)
    win.corner_gears(bottom_right=False, top_left=False)
    concept_texture(win)
    draw_table(win)                                                # 완성품 · 빈 병은 칸 테 없이 탁자 위에 그대로
    out = win.finish()
    for box, scale, at in OVEN_DECOR:
        out.alpha_composite(concept_piece(box, scale, art=OVEN_CONCEPT), at)
    oven = concept_piece(OVEN_BOX, OVEN_SCALE, art=OVEN_ART, is_bg=_black_bg)
    out.alpha_composite(oven, OVEN_AT)
    out.alpha_composite(note(OVEN_NOTE_CUTS, scale=OVEN_NOTE_SCALE), OVEN_NOTE_AT)
    book = shrink_art(Image.open(os.path.join(ART, "recipe_book_icon.png")).convert("RGBA"), BOOK_ICON_BOX,
                      COUNTER_BOOK_HEIGHT / (BOOK_ICON_BOX[3] - BOOK_ICON_BOX[1]))
    book = outlined(book, BOOK_OUTLINE)
    bx, by = OVEN_BOOK_AT
    out.alpha_composite(book, (bx - book.width // 2, by - book.height // 2))
    top = Window.__new__(Window)
    top.img = out
    from PIL import ImageDraw
    top.d = ImageDraw.Draw(out)
    draw_fire_button(top, OVEN_START, OVEN_START_EXTEND)
    draw_gauge(top, oven_dial()[0])                # 솥 · 조리대와 같은 계기판을 오븐 온도계 자리에 덮어 그린다
    if bake:
        g, at = oven_gauge(out, 0, 8)
        out.alpha_composite(g, at)
    return out


DOUGH = (236, 214, 170)
OVEN_DARK = (84, 44, 26)


def oven_gauge_box():
    wx0, wy0, wx1, wy1 = oven_box(OVEN_WINDOW)
    (cx, cy), _ = oven_dial()
    r = int(GAUGE_FACE_R) + 1
    return wx0, min(wy0, cy - r), max(wx1, cx + r + 1), max(wy1, cy + r + 1)


def oven_gauge(raw, level, steps):
    """오븐 게이지 한 단계: 창 안 파이가 반죽색 → 원래 노릇한 색, 창 불빛이 어두움 → 밝음, 계기판 바늘 7시 → 5시 (솥과 같은 바늘).
    raw = build_oven(bake=False). 돌려주는 그림과 창 기준 왼쪽 위"""
    x0, y0, x1, y1 = oven_gauge_box()
    img = raw.crop((x0, y0, x1, y1))
    p = img.load()
    f = level / steps
    wx0, wy0, wx1, wy1 = oven_box(OVEN_WINDOW)
    px0, py0, px1, py1 = oven_box(OVEN_PIE)
    rp = raw.load()
    glow = 0.55 + 0.45 * f                        # 불빛: 어두운 갈색 쪽으로 당긴다 (곱하면 노란 등이 풀색이 된다)
    for y in range(wy0 + 3, wy1 - 2):
        bgc = rp[px0 - 1, y]
        for x in range(wx0 + 3, wx1 - 2):
            c = rp[x, y]
            r, g, b = c[:3]
            if not (r > 150 and r > b + 60):          # 창 안 따뜻한 칸만 (테 · 쟁반 회색은 그대로)
                continue
            if px0 <= x < px1 and py0 <= y < py1 and sum(abs(c[i] - bgc[i]) for i in range(3)) > 60:
                lum = (r + g + b) / 3 / 200
                dough = tuple(min(255, round(DOUGH[i] * (0.75 + 0.3 * lum))) for i in range(3))
                p[x - x0, y - y0] = tuple(round(dough[i] * (1 - f) + c[i] * f) for i in range(3)) + (255,)
            else:
                p[x - x0, y - y0] = tuple(round(c[i] * glow + OVEN_DARK[i] * (1 - glow)) for i in range(3)) + (255,)
    center = oven_dial()[0]
    for (x, y), c in needle_pixels(level, steps, gauge_mask(center), center).items():
        p[x - x0, y - y0] = c
    return img, (x0, y0)


# ── 발효조 (art/fermenter_concept.png 배치 + art/fermenter_machine.png 발효 탱크를 가운데에 줄여 얹음) ──
# 칸 배치는 com.brassfield.cooking.CookLayout.FERMENTER 와 맞춘다.
FERM_ART, FERM_CONCEPT = "fermenter_machine.png", "fermenter_concept.png"
FERM_BOX = (132, 37, 1012, 1240)               # 탱크 그림 (받침 다리 제외 — 가방 칸 위 황동 띠에 걸리지 않게)
FERM_SCALE = 0.1
FERM_AT = (77, 5)                              # 창 기준 왼쪽 위 (오른쪽으로 붙임 — 압력계가 창 테에 닿기 직전). 전원 버튼은 시작 버튼 판(5줄 4열) 안
FERM_GLASS = (297, 447, 717, 875)              # 탱크 그림 기준 유리창 안쪽 (게이지: 내용물 색)
FERM_DIAL = (892, 225)                         # 압력계 가운데 → 솥과 같은 계기판을 덮어 그린다
FERM_DIAL_R = 10.5                             # 원래 압력계 반지름 (창 기준) — 이만큼 황동 테로 덮는다
FERM_BAR = (408, 1133, 770, 1173)              # 받침대 진행 막대 안쪽 (게이지: 채움)
FERM_INGREDIENTS = [(1, 1), (1, 2), (2, 1)]    # 2x2 주문서 위 (1줄 1·2열, 2줄 1열)
FERM_NOTE_CUTS = [(650, 892), (1256, 1284)]    # 본문 가운데를 잘라 재료 두 줄 높이로
FERM_NOTE_SCALE = 0.0635                       # 재료 두 칸 폭 (오븐 주문서와 같은 폭)
FERM_NOTE_AT = (14, 3)
FERM_BOOK_AT = (34, 110)                       # 주문서 아래 4·5줄 1열
FERM_START = (5, 4)                            # 받침대 전원 버튼 자리 작동 버튼 (착즙기와 같은 톱니)
FERM_OUTPUT = (3, 1)                           # 주문서 아래 탁자 위
FERM_BYPRODUCT = (3, 2)                        # 탁자 위 완성품 오른쪽 빈 그릇
FERM_DECOR = [((355, 120, 410, 180), 0.17, (78, 8)),      # 시안 희미한 별 톱니 → 탱크 왼쪽 위
              ((975, 170, 1030, 260), 0.17, (56, 100))]   # 회로선 → 책 오른쪽
MILK = (226, 210, 168)                         # 게이지 0 단계 내용물 색 (발효 전)


def ferm_point(x, y):
    return FERM_AT[0] + (x - FERM_BOX[0]) * FERM_SCALE, FERM_AT[1] + (y - FERM_BOX[1]) * FERM_SCALE


def ferm_box(box):
    x0, y0 = ferm_point(*box[:2])
    x1, y1 = ferm_point(*box[2:])
    return round(x0), round(y0), round(x1), round(y1)


def ferm_dial():
    x, y = ferm_point(*FERM_DIAL)
    return round(x), round(y)


def build_fermenter(enh, bake=True):
    """발효조: 왼쪽 2x2 주문서(재료 3칸) · 그 아래 탁자 위 완성품 · 빈 그릇 · 그 아래 책, 오른쪽 구리 발효 탱크(유리창 · 압력계 ·
    받침대 전원 버튼 자리 톱니 작동 버튼 · 진행 막대).
    진행은 탱크 내용물 색(우유색 → 노란 발효액) + 계기판 바늘 + 받침대 막대 채움 (글꼴 그림 fermenter_gauge)"""
    win = Window(enh, ROWS, pad_top=0)
    win.corner_gears(bottom_right=False, top_left=False)
    concept_texture(win)
    draw_table(win)                                # 오븐과 같은 탁자 (완성품 · 빈 그릇은 칸 테 없이)
    out = win.finish()
    for box, scale, at in FERM_DECOR:
        out.alpha_composite(concept_piece(box, scale, art=FERM_CONCEPT), at)
    tank = concept_piece(FERM_BOX, FERM_SCALE, art=FERM_ART, is_bg=lambda c: c[3] < 128)
    out.alpha_composite(tank, FERM_AT)
    from PIL import ImageDraw
    d = ImageDraw.Draw(out)
    bx0, by0, bx1, by1 = ferm_box(FERM_BAR)
    d.rectangle([bx0, by0, bx1 - 1, by1 - 1], fill=BAR_EMPTY)          # 시안 막대 채움을 비운다 (글꼴 그림이 채움)
    d.line([(bx0, by0), (bx1 - 1, by0)], fill=BAR_EMPTY_SHADE)
    out.alpha_composite(note(FERM_NOTE_CUTS, scale=FERM_NOTE_SCALE), FERM_NOTE_AT)
    book = shrink_art(Image.open(os.path.join(ART, "recipe_book_icon.png")).convert("RGBA"), BOOK_ICON_BOX,
                      COUNTER_BOOK_HEIGHT / (BOOK_ICON_BOX[3] - BOOK_ICON_BOX[1]))
    book = outlined(book, BOOK_OUTLINE)
    bx, by = FERM_BOOK_AT
    out.alpha_composite(book, (bx - book.width // 2, by - book.height // 2))
    top = Window.__new__(Window)
    top.img, top.d = out, d
    cx, cy = ferm_dial()                           # 원래 압력계(솥 계기판보다 큼)를 넓은 황동 테로 덮고 그 위에 솥과 같은 계기판
    for x, y in _disk(FERM_DIAL_R + 1, (cx, cy)):
        out.putpixel((x, y), BRASS[3] + (255,))
    for x, y in _disk(FERM_DIAL_R, (cx, cy)):
        dx, dy = x - cx, y - cy
        out.putpixel((x, y), BRASS[2 if dx + dy < -6 else 0 if dx + dy > 6 else 1] + (255,))
    draw_gauge(top, (cx, cy))
    draw_fire_button(top, FERM_START)
    if bake:
        g, at = fermenter_gauge(out, 0, 8)
        out.alpha_composite(g, at)
    return out


FOAM_MIN, FOAM_GROW = 2, 5                     # 거품층 두께: 0 단계 2px → 8 단계 원래 두께 + 5px
BUBBLES = 22                                   # 8 단계 발효액 속 기포 수 (단계마다 앞에서부터 늘어난다)
BUBBLE = [(255, 240, 180), (250, 214, 120)]    # 기포 빛 · 테


def _is_foam(c):
    r, g, b = c[:3]
    return min(r, g, b) > 175 and max(r, g, b) - min(r, g, b) < 70


def ferm_foam(p, rp, origin, f):
    """탱크 유리 안 거품층을 진행(f)만큼 두껍게: 칸마다 원래 거품 위 끝(F0) · 아래 끝(S)을 찾아, 아래 끝은 두고
    위 끝을 새 두께로 올리거나 내린다 (빈 유리 줄 · 거품 줄을 그 높이로 늘이거나 줄임). 발효액 속 기포도 f 만큼."""
    import random
    x0, y0 = origin
    gx0, gy0, gx1, gy1 = ferm_box(FERM_GLASS)
    bottoms = []
    for x in range(gx0, gx1):
        col = [p[x - x0, y - y0] for y in range(gy0, gy1)]
        foam = [y for y in range(gy0 + 3, gy1) if _is_foam(rp[x, y])]
        if not foam:
            continue
        top = foam[0]
        bottom = top
        while bottom + 1 < gy1 and _is_foam(rp[x, bottom + 1]):
            bottom += 1
        bottom += 1                                   # 거품 아래 끝 (제외)
        bottoms.append(bottom)
        t0 = bottom - top
        t = round(FOAM_MIN + (t0 + FOAM_GROW - FOAM_MIN) * f)
        new_top = max(gy0 + 2, bottom - t)
        for y in range(gy0, bottom):
            if y < new_top:
                sy = gy0 + (y - gy0) * (top - gy0) // max(1, new_top - gy0)
            else:
                sy = top + (y - new_top) * (bottom - top) // max(1, bottom - new_top)
            p[x - x0, y - y0] = col[sy - gy0]
    if not bottoms:
        return
    rnd = random.Random(7)
    lo = max(bottoms) + 2
    spots = [(rnd.randrange(gx0 + 2, gx1 - 2), rnd.randrange(lo, gy1 - 2)) for _ in range(BUBBLES)]
    for i, (bx, by) in enumerate(spots[:round(BUBBLES * f)]):
        if i % 4 == 0:                                # 큰 기포 (2x2: 빛 한 점 + 테)
            for dx, dy in ((1, 0), (0, 1), (1, 1)):
                p[bx + dx - x0, by + dy - y0] = BUBBLE[1] + (255,)
        p[bx - x0, by - y0] = BUBBLE[0] + (255,)


def fermenter_gauge_box():
    gx0, gy0, gx1, gy1 = ferm_box(FERM_GLASS)
    bx0, by0, bx1, by1 = ferm_box(FERM_BAR)
    cx, cy = ferm_dial()
    r = int(GAUGE_FACE_R) + 1
    return min(gx0, bx0), cy - r, max(gx1, bx1, cx + r + 1), by1


def fermenter_gauge(raw, level, steps):
    """발효조 게이지 한 단계: 탱크 노란 발효액이 우유색 → 원래 색 · 거품층이 얇음 → 두껍게 · 기포가 늘어남,
    계기판 바늘 7시 → 5시, 받침대 막대 빔 → 가득.
    raw = build_fermenter(bake=False). 돌려주는 그림과 창 기준 왼쪽 위"""
    x0, y0, x1, y1 = fermenter_gauge_box()
    img = raw.crop((x0, y0, x1, y1))
    p = img.load()
    rp = raw.load()
    f = level / steps
    gx0, gy0, gx1, gy1 = ferm_box(FERM_GLASS)
    for y in range(gy0, gy1):
        for x in range(gx0, gx1):
            r, g, b = rp[x, y][:3]
            if r > 180 and g > 110 and r - b > 90:      # 노란 발효액 (거품 · 유리 빛은 그대로)
                lum = (r + g + b) / 3 / 170
                milk = tuple(min(255, round(MILK[i] * (0.8 + 0.2 * lum))) for i in range(3))
                p[x - x0, y - y0] = tuple(round(milk[i] * (1 - f) + rp[x, y][i] * f) for i in range(3)) + (255,)
    ferm_foam(p, rp, (x0, y0), f)
    center = ferm_dial()
    for (x, y), c in needle_pixels(level, steps, gauge_mask(center), center).items():
        p[x - x0, y - y0] = c
    bx0, by0, bx1, by1 = ferm_box(FERM_BAR)
    fill = round((bx1 - bx0) * f)
    if fill:
        from PIL import ImageDraw
        d = ImageDraw.Draw(img)
        X, Y, H = bx0 - x0, by0 - y0, by1 - by0
        d.rectangle([X, Y, X + fill - 1, Y + H - 1], fill=BAR_FILL[1])
        d.line([(X, Y), (X + fill - 1, Y)], fill=BAR_FILL[0])
        d.line([(X, Y + H - 1), (X + fill - 1, Y + H - 1)], fill=BAR_FILL[2])
    return img, (x0, y0)


# ── 훈연기 (art/smoker_concept.png + art/smoker_machine.png 훈연 캐비닛을 오른쪽에 줄여 얹음, 배치는 발효조와 같은 방식) ──
# 칸 배치는 com.brassfield.cooking.CookLayout.SMOKER 와 맞춘다.
SMK_ART, SMK_CONCEPT = "smoker_machine.png", "smoker_concept.png"
SMK_BOX = (202, 183, 1018, 1263)               # 캐비닛 그림 (굴뚝 위 연기 · 받침 다리 제외)
SMK_SMOKE_CUT = (600, 0, 1018, 240)            # 굴뚝 오른쪽 위 연기 끝자락은 비운다
SMK_SCALE = 0.115
SMK_AT = (73, 1)                               # 창 기준 왼쪽 위 (오른쪽으로 붙임). 재생 버튼은 작동 버튼 판(5줄 4열) 안
SMK_WINDOW = (342, 575, 742, 983)              # 캐비닛 그림 기준 유리창 안쪽 (게이지: 연기 · 고기 색)
SMK_MEAT = (370, 712, 690, 890)                # 창 안 고기 (갈고리 아래)
SMK_DIAL = (913, 472)                          # 압력계 가운데 → 솥과 같은 계기판
SMK_DIAL_R = 12.5                              # 원래 압력계(테 포함) 반지름 (창 기준) — 이만큼 황동 테로 덮는다
SMK_BAR = (444, 1182, 776, 1215)               # 받침대 진행 막대 안쪽
SMK_INGREDIENT = (1, 1)
SMK_NOTE_CUTS = [(230, 390), (1256, 1284)]     # 머리 장식 아래 여백을 잘라 착즙기 주문서보다 낮게 (재료 칸 아래 여백은 남긴다)
SMK_NOTE_AT = (12, 3)
SMK_OUTPUT = (2, 1)                            # 주문서 아래 2x2 접시 (2~3줄 1~2열, 왼쪽 위 칸)
SMK_BOOK_AT = (34, 108)                        # 접시 아래 4·5줄 1열
SMK_COUNT = (2, 69)                            # 완성품 개수 숫자 (줄, 오른쪽 끝 x) — 2배 요리 그림 오른쪽 위 바깥 (CookLayout.SMOKER)
SMK_START = (5, 4)                             # 받침대 재생 버튼 자리 작동 버튼
SMK_DECOR = [((985, 160, 1050, 225), 0.17, (56, 104)),    # 시안 희미한 톱니 → 책 오른쪽
             ((1010, 325, 1060, 410), 0.17, (62, 12))]    # 회로선 → 주문서 오른쪽 위 (완성품 개수 숫자 자리를 비운다)
SMOKE = (118, 104, 96)                         # 게이지 8 단계 연기 색


def smk_point(x, y):
    return SMK_AT[0] + (x - SMK_BOX[0]) * SMK_SCALE, SMK_AT[1] + (y - SMK_BOX[1]) * SMK_SCALE


def smk_box(box):
    x0, y0 = smk_point(*box[:2])
    x1, y1 = smk_point(*box[2:])
    return round(x0), round(y0), round(x1), round(y1)


def smk_dial():
    x, y = smk_point(*SMK_DIAL)
    return round(x), round(y)


def build_smoker(enh, bake=True):
    """훈연기: 왼쪽 작은 주문서(재료 1칸) · 그 아래 접시 위 완성품 · 그 아래 책, 오른쪽 스팀펑크 훈연 캐비닛(유리창 안 고기 ·
    압력계 · 받침대 재생 버튼 자리 작동 버튼 · 진행 막대).
    진행은 고기 색(생고기 → 짙은 훈제색) + 창 안 연기 짙어짐 + 계기판 바늘 + 받침대 막대 채움 (글꼴 그림 smoker_gauge)"""
    win = Window(enh, ROWS, pad_top=0)
    win.corner_gears(bottom_right=False, top_left=False)
    concept_texture(win)
    draw_plate(win, SMK_OUTPUT, label=False)       # 솥과 같은 2x2 접시 (2배 크기 요리, 개수는 요리 오른쪽 위)
    out = win.finish()
    for box, scale, at in SMK_DECOR:
        out.alpha_composite(concept_piece(box, scale, art=SMK_CONCEPT), at)
    cab = concept_piece(SMK_BOX, SMK_SCALE, clear=(SMK_SMOKE_CUT,), art=SMK_ART, is_bg=lambda c: c[3] < 128)
    out.alpha_composite(cab, SMK_AT)
    from PIL import ImageDraw
    d = ImageDraw.Draw(out)
    bx0, by0, bx1, by1 = smk_box(SMK_BAR)
    d.rectangle([bx0, by0, bx1 - 1, by1 - 1], fill=BAR_EMPTY)
    d.line([(bx0, by0), (bx1 - 1, by0)], fill=BAR_EMPTY_SHADE)
    out.alpha_composite(note(SMK_NOTE_CUTS, scale=JUICER_NOTE_SCALE), SMK_NOTE_AT)
    book = shrink_art(Image.open(os.path.join(ART, "recipe_book_icon.png")).convert("RGBA"), BOOK_ICON_BOX,
                      COUNTER_BOOK_HEIGHT / (BOOK_ICON_BOX[3] - BOOK_ICON_BOX[1]))
    book = outlined(book, BOOK_OUTLINE)
    bx, by = SMK_BOOK_AT
    out.alpha_composite(book, (bx - book.width // 2, by - book.height // 2))
    top = Window.__new__(Window)
    top.img, top.d = out, d
    cx, cy = smk_dial()
    for x, y in _disk(SMK_DIAL_R + 1, (cx, cy)):
        out.putpixel((x, y), BRASS[3] + (255,))
    for x, y in _disk(SMK_DIAL_R, (cx, cy)):
        dx, dy = x - cx, y - cy
        out.putpixel((x, y), BRASS[2 if dx + dy < -6 else 0 if dx + dy > 6 else 1] + (255,))
    draw_gauge(top, (cx, cy))
    draw_fire_button(top, SMK_START)
    if bake:
        g, at = smoker_gauge(out, 0, 8)
        out.alpha_composite(g, at)
    return out


def smoker_gauge_box():
    gx0, gy0, gx1, gy1 = smk_box(SMK_WINDOW)
    bx0, by0, bx1, by1 = smk_box(SMK_BAR)
    cx, cy = smk_dial()
    r = int(GAUGE_FACE_R) + 1
    return min(gx0, bx0), min(gy0, cy - r), max(gx1, bx1, cx + r + 1), by1


def smoker_gauge(raw, level, steps):
    """훈연기 게이지 한 단계: 창 안 고기가 생고기색 → 짙은 훈제색, 창 안 연기가 옅음 → 짙음,
    계기판 바늘 7시 → 5시, 받침대 막대 빔 → 가득. raw = build_smoker(bake=False). 돌려주는 그림과 창 기준 왼쪽 위"""
    x0, y0, x1, y1 = smoker_gauge_box()
    img = raw.crop((x0, y0, x1, y1))
    p = img.load()
    rp = raw.load()
    f = level / steps
    gx0, gy0, gx1, gy1 = smk_box(SMK_WINDOW)
    mx0, my0, mx1, my1 = smk_box(SMK_MEAT)
    for y in range(gy0, gy1):
        for x in range(gx0, gx1):
            c = rp[x, y][:3]
            r, g, b = c
            if mx0 <= x < mx1 and my0 <= y < my1 and r > 120 and r - b > 50:     # 고기 (줄무늬 포함)
                raw_c = (min(255, r + 18), round(g * 0.72), round(b * 0.78))
                smoked = (round(r * 0.52), round(g * 0.40), round(b * 0.34))
                p[x - x0, y - y0] = tuple(round(raw_c[i] * (1 - f) + smoked[i] * f) for i in range(3)) + (255,)
            else:                                                                 # 창 안 연기
                k = 0.55 * f
                p[x - x0, y - y0] = tuple(round(c[i] * (1 - k) + SMOKE[i] * k) for i in range(3)) + (255,)
    center = smk_dial()
    for (x, y), c in needle_pixels(level, steps, gauge_mask(center), center).items():
        p[x - x0, y - y0] = c
    bx0, by0, bx1, by1 = smk_box(SMK_BAR)
    fill = round((bx1 - bx0) * f)
    if fill:
        from PIL import ImageDraw
        d = ImageDraw.Draw(img)
        X, Y, H = bx0 - x0, by0 - y0, by1 - by0
        d.rectangle([X, Y, X + fill - 1, Y + H - 1], fill=BAR_FILL[1])
        d.line([(X, Y), (X + fill - 1, Y)], fill=BAR_FILL[0])
        d.line([(X, Y + H - 1), (X + fill - 1, Y + H - 1)], fill=BAR_FILL[2])
    return img, (x0, y0)


if __name__ == "__main__":
    enh = Image.open(sys.argv[1]).convert("RGBA")
    out_dir = sys.argv[2]
    kettle, generic, counter = build_kettle(enh), build_generic(enh), build_counter(enh)
    kettle.save(os.path.join(out_dir, "cook_kettle_bg.png"))
    generic.save(os.path.join(out_dir, "cook_generic_bg.png"))
    counter.save(os.path.join(out_dir, "cook_counter_bg.png"))
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

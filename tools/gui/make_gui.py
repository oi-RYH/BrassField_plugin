"""
BrassField 창 배경 (ItemsAdder font_image 용): 강화 창 배경(enhance_bg)과 같은 스팀펑크 톤.
짙은 갈색 리벳 판 + 구리 테두리·파이프 + 톱니, 아이템이 들어가는 칸에만 칸 테두리를 그리고 나머지는 장식으로 채운다.
제목은 클라이언트가 그리므로 위쪽에 밝은 황동 띠를 깔아 기본 제목 글자(짙은 회색)가 읽히게 한다.

바닐라 상자 화면 좌표: 폭 176, 높이 114 + 줄 수 × 18. 창 칸 (8 + 열×18, 18 + 줄×18) 의 1px 바깥이 칸 테두리.
가방 3줄은 창 칸 아래 13px 띄우고, 단축바는 가방 아래 4px 띄운다. 그림은 256x256 캔버스 왼쪽 위에 그린다.

사용: python3 -I tools/gui/make_gui.py <출력 폴더> [미리보기 png]
  → <출력>/<이름>.png (dl7_bg, crop_sell_bg, seed_shop_bg, stone_shop_bg, cooking_bg, recipe_bg)
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "hud"))
import png  # noqa: E402

rnd = random.Random(900)
PANEL = [(44, 37, 30), (46, 39, 32), (42, 35, 28), (43, 36, 29), (45, 38, 31)]
DARK = (27, 23, 19)
DARKER = (13, 10, 7)
SLOT_IN = (73, 69, 60)
SLOT_EDGE = (36, 35, 31)
SLOT_LIGHT = (174, 157, 125)
COPPER_HI = (226, 179, 99)
COPPER = (187, 127, 54)
COPPER_LO = (146, 83, 40)
COPPER_DK = (74, 43, 24)
PLATE = [(176, 155, 117), (174, 157, 125), (170, 150, 114)]
PLATE_EDGE = (120, 100, 72)
GLASS = (240, 140, 60)
GLASS_HI = (255, 214, 140)


class Canvas:
    def __init__(self, rows):
        self.rows = rows
        self.w, self.h = 176, 114 + rows * 18
        self.img = [[(0, 0, 0, 0)] * 256 for _ in range(256)]

    def px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.img[y][x] = tuple(c[:3]) + (255,)

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1):
            for x in range(x0, x1):
                self.px(x, y, rnd.choice(c) if isinstance(c, list) else c)

    # ── 바탕 ──
    def base(self):
        self.rect(0, 0, self.w, self.h, PANEL)
        for x in range(self.w):                                   # 구리 테두리 (위·아래)
            for y, c in ((0, COPPER_LO), (1, COPPER_HI), (2, COPPER), (3, COPPER_DK)):
                self.px(x, y, c)
                self.px(x, self.h - 1 - y, c)
        for y in range(self.h):                                   # 옆 테두리
            for x, c in ((0, COPPER_LO), (1, COPPER_HI), (2, COPPER), (3, COPPER_DK)):
                self.px(x, y, c)
                self.px(self.w - 1 - x, y, c)
        for y in range(8, self.h - 8, 18):                        # 옆 테두리 이음쇠
            for x in (0, self.w - 4):
                self.rect(x, y, x + 4, y + 2, COPPER_HI)
        for cx, cy in ((1, 1), (self.w - 5, 1), (1, self.h - 5), (self.w - 5, self.h - 5)):   # 모서리 리벳
            self.rect(cx, cy, cx + 4, cy + 4, COPPER_LO)
            self.rect(cx + 1, cy + 1, cx + 3, cy + 3, COPPER_HI)
        self.rect(5, 4, self.w - 5, 15, PLATE)                    # 제목 띠 (밝은 황동판)
        for x in range(5, self.w - 5):
            self.px(x, 4, PLATE_EDGE)
            self.px(x, 15, PLATE_EDGE)
        for x in (5, self.w - 6):
            for y in range(4, 16):
                self.px(x, y, PLATE_EDGE)

    def slot(self, sx, sy):
        """칸 테두리 (sx, sy = 칸 아이템 자리 왼쪽 위 - 1)"""
        self.rect(sx, sy, sx + 18, sy + 18, SLOT_IN)
        for i in range(18):
            self.px(sx + i, sy, SLOT_EDGE)
            self.px(sx, sy + i, SLOT_EDGE)
            self.px(sx + i, sy + 17, SLOT_LIGHT)
            self.px(sx + 17, sy + i, SLOT_LIGHT)

    def big_slot(self, sx, sy):
        """결과 칸처럼 강조하는 칸: 바깥에 구리 테"""
        self.rect(sx - 3, sy - 3, sx + 21, sy + 21, COPPER_LO)
        self.rect(sx - 2, sy - 2, sx + 20, sy + 20, COPPER)
        for i in range(-2, 20):
            self.px(sx + i, sy - 2, COPPER_HI)
            self.px(sx - 2, sy + i, COPPER_HI)
        self.slot(sx, sy)
        for cx, cy in ((sx - 3, sy - 3), (sx + 19, sy - 3), (sx - 3, sy + 19), (sx + 19, sy + 19)):
            self.rect(cx, cy, cx + 2, cy + 2, COPPER_HI)

    def cell(self, row, col, big=False):
        x, y = 7 + col * 18, 17 + row * 18
        (self.big_slot if big else self.slot)(x, y)

    def player_inventory(self):
        top = 17 + self.rows * 18 + 13
        for row in range(3):
            for col in range(9):
                self.slot(7 + col * 18, top + row * 18)
        for col in range(9):
            self.slot(7 + col * 18, top + 58 + 0)
        y = 17 + self.rows * 18 + 2                               # 창과 가방 사이 구리 띠
        self.pipe_h(5, self.w - 5, y + 3)

    # ── 장식 ──
    def pipe_h(self, x0, x1, y):
        for x in range(x0, x1):
            for dy, c in enumerate((COPPER_DK, COPPER_HI, COPPER, COPPER_LO, COPPER_DK)):
                self.px(x, y + dy, c)
        for x in range(x0 + 6, x1 - 4, 24):                       # 이음쇠
            self.rect(x, y - 1, x + 3, y + 6, COPPER_LO)
            self.rect(x + 1, y, x + 2, y + 5, COPPER_HI)

    def pipe_v(self, x, y0, y1):
        for y in range(y0, y1):
            for dx, c in enumerate((COPPER_DK, COPPER_HI, COPPER, COPPER_LO, COPPER_DK)):
                self.px(x + dx, y, c)

    def gear(self, cx, cy, r, teeth=8):
        for y in range(cy - r - 2, cy + r + 3):
            for x in range(cx - r - 2, cx + r + 3):
                d = math.hypot(x - cx, y - cy)
                a = math.atan2(y - cy, x - cx)
                tooth = (math.cos(a * teeth) > 0.3) and d <= r + 2
                if d <= r or tooth:
                    c = COPPER if d > r * 0.75 else (COPPER_LO if d > r * 0.35 else COPPER_DK)
                    if d <= r * 0.2:
                        c = DARKER
                    if y < cy - r * 0.4 and d > r * 0.6:
                        c = COPPER_HI
                    self.px(x, y, c)

    def gauge(self, cx, cy, r):
        """압력계: 황동 테 + 짙은 판 + 바늘"""
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                d = math.hypot(x - cx, y - cy)
                if d <= r:
                    self.px(x, y, COPPER if d > r - 1.6 else (60, 54, 46))
        for i in range(r - 2):
            self.px(cx + i // 2, cy - i // 2, GLASS_HI)
        self.px(cx, cy, COPPER_HI)

    def tube(self, x, y0, y1):
        """빛나는 유리관 (세로)"""
        self.rect(x, y0, x + 6, y1, COPPER_LO)
        self.rect(x + 1, y0 + 2, x + 5, y1 - 2, GLASS)
        self.rect(x + 2, y0 + 3, x + 3, y1 - 3, GLASS_HI)
        self.rect(x - 1, y0, x + 7, y0 + 2, COPPER_HI)
        self.rect(x - 1, y1 - 2, x + 7, y1, COPPER_HI)

    def rivets(self, x0, y0, x1, y1, step=12):
        for x in range(x0, x1, step):
            for y in (y0, y1):
                self.px(x, y, COPPER_LO)
                self.px(x, y - 1, COPPER_HI)

    def arrow(self, x0, y, x1):
        """진행 화살표 파이프 (오른쪽)"""
        self.pipe_h(x0, x1 - 4, y)
        for i in range(5):
            for dy in range(-i, i + 1):
                self.px(x1 - i, y + 2 + dy, COPPER_HI if dy == 0 else COPPER)

    def save(self, path):
        png.write(path, self.img)


# ═════════════ 창별 배치 ═════════════
def deposit_window(extra):
    """DL-7·작물 팔기: 1~4줄 넣는 칸, 5줄 구분 파이프, 6줄 버튼"""
    c = Canvas(6)
    c.base()
    for row in range(4):
        for col in range(9):
            c.cell(row, col)
    y = 17 + 4 * 18                                               # 5줄: 파이프와 톱니
    c.pipe_h(5, c.w - 5, y + 7)
    for x in (30, 88, 146):
        c.gear(x, y + 9, 6)
    for slot in (45, 48, 50, 52) + extra:
        c.cell(5, slot % 9, big=slot == 50)
    c.player_inventory()
    return c


def seed_shop():
    c = Canvas(4)
    c.base()
    for slot in (10, 11, 12, 13, 14, 15, 16, 19, 20, 21, 22, 23, 24, 25):
        c.cell(slot // 9, slot % 9)
    c.cell(3, 0)
    c.cell(3, 4, big=True)
    c.pipe_h(5, c.w - 5, 17 + 3)
    c.gear(150, 17 + 3 * 18 + 9, 6)
    c.gear(60, 17 + 3 * 18 + 9, 5)
    c.player_inventory()
    return c


def stone_shop():
    c = Canvas(4)
    c.base()
    c.cell(0, 4)                                                  # 보유 골드 (제목 띠에 닿지 않게 보통 칸)
    for row in (1, 2, 3):
        c.cell(row, 1)
        for col in (4, 5, 6):
            c.cell(row, col)
        c.pipe_h(7 + 2 * 18, 7 + 4 * 18, 17 + row * 18 + 6)
    c.tube(150, 17 + 18, 17 + 4 * 18 - 1)
    c.gear(24, 17 + 9, 6)
    c.gauge(152, 17 + 9, 7)
    c.player_inventory()
    return c


def cooking():
    c = Canvas(6)
    c.base()
    c.rect(7 + 18 - 3, 17 + 18 - 3, 7 + 4 * 18 + 3, 17 + 4 * 18 + 3, COPPER_LO)   # 재료 3x3 판
    c.rect(7 + 18 - 2, 17 + 18 - 2, 7 + 4 * 18 + 2, 17 + 4 * 18 + 2, DARK)
    for row in (1, 2, 3):
        for col in (1, 2, 3):
            c.cell(row, col)
    c.arrow(7 + 4 * 18 + 4, 17 + 2 * 18 + 6, 7 + 5 * 18 - 2)
    c.cell(2, 5)                                                  # 진행
    c.arrow(7 + 6 * 18 + 1, 17 + 2 * 18 + 6, 7 + 7 * 18 - 4)
    c.cell(2, 7, big=True)                                        # 결과
    c.cell(3, 7)
    c.cell(3, 8)                                                  # 부산물
    c.cell(5, 4)                                                  # 레시피 책
    c.tube(7 + 5 * 18 + 6, 17 + 3 * 18 + 2, 17 + 5 * 18 - 4)
    c.gauge(7 + 5 * 18 + 9, 17 + 18 + 7, 7)
    c.gear(150, 17 + 18 + 7, 7)
    c.pipe_h(7, 7 + 4 * 18, 17 + 5 * 18 + 7)                   # 파이프를 먼저, 톱니를 위에
    c.pipe_h(7 + 5 * 18, c.w - 7, 17 + 5 * 18 + 7)
    c.gear(30, 17 + 5 * 18 + 9, 6)
    c.gear(140, 17 + 5 * 18 + 9, 6)
    c.player_inventory()
    return c


def recipe_book():
    c = Canvas(6)
    c.base()
    for row in range(5):
        for col in range(9):
            c.cell(row, col)
    c.pipe_h(5, 7 + 4 * 18, 17 + 5 * 18 + 7)
    c.pipe_h(7 + 5 * 18, c.w - 5, 17 + 5 * 18 + 7)
    c.cell(5, 4, big=True)
    c.player_inventory()
    return c


WINDOWS = {
    "dl7_bg": lambda: deposit_window((46,)),         # 46 = 오늘의 주문
    "crop_sell_bg": lambda: deposit_window((46,)),   # 46 = 씨앗 사기
    "seed_shop_bg": seed_shop,
    "stone_shop_bg": stone_shop,
    "cooking_bg": cooking,
    "recipe_bg": recipe_book,
}

if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    made = {}
    for name, build in WINDOWS.items():
        c = build()
        c.save(os.path.join(out, name + ".png"))
        made[name] = c
    if len(sys.argv) > 2:                                          # 미리보기: 3배로 두 줄 배치
        k, gap = 3, 12
        cells = list(made.values())
        W = (176 * k + gap) * 3
        H = (222 * k + gap) * 2
        sheet = [[(24, 26, 30, 255)] * W for _ in range(H)]
        for i, c in enumerate(cells):
            crop = [row[:c.w] for row in c.img[:c.h]]
            png.paste(sheet, png.scale(crop, k), (i % 3) * (176 * k + gap), (i // 3) * (222 * k + gap))
        png.write(sys.argv[2], sheet)
    print("ok", len(made))

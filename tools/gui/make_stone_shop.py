"""
강화석 상점 창 배경 (사용자 시안: 나무·황동 상점 판, 등급 카드 3장, 수량 버튼, 총 가격·구매하기).
마인크래프트 6줄 상자 창(176 x 222) 칸 격자에 맞춰 배치하고, 한글 글씨가 또렷하도록 2배 해상도(352 x 444)로 그린다.
(ItemsAdder font_image 에서 높이 222 로 줄여 쓰면 GUI 배율 2 이상에서 2배 해상도 그대로 보인다.)

칸 배치 (줄, 열):
  0~2줄: 등급 카드 3장 (열 0~2 하급 / 3~5 중급 / 6~8 상급). 결정 그림은 배경에 그리고, 카드의 9칸은 투명 아이템(설명창만)이다.
  3줄: 구매 수량 (열 3~4: 1개 / 5~6: 10개 / 7~8: 64개)
  4줄: 총 가격 (열 0~4, 숫자는 게임이 그림) / 구매하기 (열 5~8)
  5줄: 안내 문구 / 닫기 (열 8)
바뀌는 것(보유 골드·총 가격 숫자, 고른 카드·수량의 노란 테두리)은 게임에서 따로 겹쳐 그린다. 미리보기에는 예시 값으로 그린다.

사용: python3 -I tools/gui/make_stone_shop.py <출력 폴더> <강화석 아이콘 폴더> [미리보기 png]
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

S = 2                                   # 그림 배율 (GUI 1칸 = 2픽셀)
W, H = 176, 222
FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"

WOOD_DARK = (44, 30, 22)
PANEL = (58, 40, 29)
PANEL_LINE = (50, 34, 25)
CARD = (70, 49, 35)
CARD_EDGE = (112, 76, 48)
WOOD = (122, 78, 44)
WOOD_HI = (166, 112, 62)
WOOD_LO = (86, 54, 30)
BRASS = (226, 179, 99)
BRASS_LO = (146, 92, 40)
GOLD_TEXT = (255, 214, 102)
CREAM = (246, 232, 206)
GRAY_TEXT = (196, 180, 156)
GLOW = (255, 210, 74)
BUY = (250, 196, 64)
BUY_HI = (255, 226, 130)
BUY_LO = (196, 132, 30)
SLOT = (52, 36, 27)
GRADES = [("하급 강화석", (214, 214, 222), "1,000", "low"),
          ("중급 강화석", (110, 176, 255), "1,000", "mid"),
          ("상급 강화석", (196, 142, 255), "16,000", "high")]
# 결정 덩이 색 (밝은 면, 가운데, 그늘) — 시안: 하급 회색 · 중급 파랑 · 상급 보라
CRYSTAL = [((236, 236, 244), (196, 196, 210), (140, 140, 158)),
           ((150, 210, 255), (74, 146, 240), (40, 88, 190)),
           ((226, 186, 255), (170, 110, 240), (110, 60, 190))]


def font(size, bold=True):
    return ImageFont.truetype(FONT, size, index=6 if bold else 2)


class Gui:
    def __init__(self):
        self.img = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)
        self.d.fontmode = "1"                 # 글씨 가장자리 흐림 없음 (픽셀 느낌)

    def rect(self, x0, y0, x1, y1, fill, outline=None, width=1):
        """GUI 좌표(1칸 단위)로 사각형"""
        self.d.rectangle([x0 * S, y0 * S, x1 * S - 1, y1 * S - 1], fill=fill,
                         outline=outline, width=width * S if outline else 0)

    def bevel(self, x0, y0, x1, y1, fill, hi, lo):
        self.rect(x0, y0, x1, y1, fill)
        self.rect(x0, y0, x1, y0 + 1, hi)
        self.rect(x0, y0, x0 + 1, y1, hi)
        self.rect(x0, y1 - 1, x1, y1, lo)
        self.rect(x1 - 1, y0, x1, y1, lo)

    def text(self, x, y, s, color, size=14, anchor="la", bold=True, shadow=True):
        """x, y 는 GUI 좌표, size 는 그림 픽셀(2배) 글씨 크기"""
        f = font(size, bold)
        if shadow:
            self.d.text((x * S + 2, y * S + 2), s, font=f, fill=(20, 12, 8), anchor=anchor)
        self.d.text((x * S, y * S), s, font=f, fill=color, anchor=anchor)

    def coin(self, x, y, r=4):
        cx, cy = x * S, y * S
        self.d.ellipse([cx - r * S, cy - r * S, cx + r * S - 1, cy + r * S - 1], fill=BRASS_LO)
        self.d.ellipse([cx - r * S + 2, cy - r * S + 2, cx + r * S - 3, cy + r * S - 3], fill=(250, 196, 64))
        self.d.ellipse([cx - 3, cy - 3, cx + 2, cy + 2], fill=BUY_HI)

    def gem(self, x, y, color, r=3):
        cx, cy = x * S, y * S
        self.d.polygon([(cx, cy - r * S), (cx + r * S, cy), (cx, cy + r * S), (cx - r * S, cy)], fill=color)
        self.d.polygon([(cx, cy - r * S), (cx + r * S, cy), (cx, cy)], fill=tuple(min(255, v + 40) for v in color))

    def crystal(self, cx, cy, h, w, cols):
        """결정 하나 (아래가 평평한 육각 기둥 + 뾰족한 끝), GUI 좌표"""
        hi, mid, lo = cols
        X = lambda v: v * S
        top, mid_y, base = cy - h / 2, cy - h / 6, cy + h / 2
        pts = [(cx - w / 2, base), (cx - w / 2, mid_y), (cx, top), (cx + w / 2, mid_y), (cx + w / 2, base)]
        self.d.polygon([(X(a), X(b)) for a, b in pts], fill=mid)
        self.d.polygon([(X(cx - w / 2), X(base)), (X(cx - w / 2), X(mid_y)), (X(cx), X(top)), (X(cx - w / 8), X(base))], fill=hi)
        self.d.polygon([(X(cx + w / 4), X(base)), (X(cx + w / 4), X(mid_y + h / 10)), (X(cx + w / 2), X(mid_y)), (X(cx + w / 2), X(base))], fill=lo)

    def cluster(self, cx, cy, cols, sparkle=False):
        """결정 세 개 덩이 (가운데 큰 것, 양옆 작은 것)"""
        self.crystal(cx - 6, cy + 3, 11, 7, cols)
        self.crystal(cx + 6.5, cy + 4, 9, 6, cols)
        self.crystal(cx, cy, 18, 9, cols)
        if sparkle:
            for sx, sy in ((cx - 11, cy - 7), (cx + 11, cy - 4)):
                for dx, dy in ((0, -2), (0, 2), (-2, 0), (2, 0), (0, 0)):
                    self.rect(sx + dx * 0.5, sy + dy * 0.5, sx + dx * 0.5 + 1, sy + dy * 0.5 + 1, (255, 236, 255))

    def glow(self, x0, y0, x1, y1):
        """고른 카드·버튼 노란 테두리 (게임에서는 겹쳐 그리는 그림)"""
        self.rect(x0 - 1, y0 - 1, x1 + 1, y1 + 1, None, outline=(150, 100, 20))
        self.rect(x0, y0, x1, y1, None, outline=GLOW)


def build(selected_card=0, selected_qty=0, gold="12,450", total="1,000"):
    g = Gui()
    # ── 판·틀 ──
    g.rect(0, 0, W, H, PANEL)
    for y in range(20, H, 6):                                        # 나무 판 결
        g.rect(4, y, W - 4, y + 1, PANEL_LINE)
    for x0, x1 in ((0, 4), (W - 4, W)):                               # 옆 기둥
        g.bevel(x0, 0, x1, H, WOOD, WOOD_HI, WOOD_LO)
    g.bevel(0, H - 4, W, H, WOOD, WOOD_HI, WOOD_LO)                   # 바닥 들보
    # ── 위 간판 (0~17) ──
    g.bevel(0, 0, W, 17, WOOD, WOOD_HI, WOOD_LO)
    g.bevel(3, 1, 92, 16, WOOD_DARK, BRASS_LO, (24, 16, 12))          # 간판 판
    g.gem(10, 8.5, (214, 214, 222), 4)
    g.text(17, 8.5, "강화석 상점", GOLD_TEXT, 22, anchor="lm")
    g.bevel(110, 2, 173, 15, WOOD_DARK, BRASS_LO, (24, 16, 12))       # 보유 골드 판
    g.coin(118, 8.5)
    g.text(170, 8.5, gold, CREAM, 16, anchor="rm")
    # ── 등급 카드 (0~2줄) ──
    for i, (name, color, price, _) in enumerate(GRADES):
        x0, y0 = 7 + i * 54, 17
        g.bevel(x0 + 1, y0 + 1, x0 + 53, y0 + 53, CARD, CARD_EDGE, (40, 27, 20))
        g.gem(x0 + 8, y0 + 7.5, color, 2.5)
        g.text(x0 + 13, y0 + 7.5, name, color, 13, anchor="lm")
        g.rect(x0 + 4, y0 + 13, x0 + 50, y0 + 14, CARD_EDGE)
        g.d.ellipse([(x0 + 11) * S, (y0 + 31) * S, (x0 + 43) * S, (y0 + 39) * S], fill=(48, 33, 24))   # 결정 그림자
        g.cluster(x0 + 27, y0 + 25, CRYSTAL[i], sparkle=i == 2)                                        # 결정 덩이 (가운데 칸은 투명 아이템)
        g.rect(x0 + 4, y0 + 41, x0 + 50, y0 + 42, CARD_EDGE)
        g.coin(x0 + 9, y0 + 47.5, 3)
        g.text(x0 + 14, y0 + 47.5, price + " / 개", CREAM, 13, anchor="lm")
        if i == selected_card:
            g.glow(x0 + 1, y0 + 1, x0 + 53, y0 + 53)
    # ── 구매 수량 (3줄) ──
    y0 = 17 + 3 * 18
    g.bevel(5, y0 + 1, W - 5, y0 + 17, WOOD_DARK, CARD_EDGE, (30, 20, 15))
    g.text(10, y0 + 9, "구매 수량", CREAM, 14, anchor="lm")
    for i, (label, col) in enumerate((("1개", 3), ("10개", 5), ("64개", 7))):
        x0 = 7 + col * 18
        g.bevel(x0 + 1, y0 + 2, x0 + 35, y0 + 16, CARD, CARD_EDGE, (40, 27, 20))
        g.text(x0 + 18, y0 + 9, label, CREAM, 14, anchor="mm")
        if i == selected_qty:
            g.glow(x0 + 1, y0 + 2, x0 + 35, y0 + 16)
    # ── 총 가격 · 구매하기 (4줄) ──
    y0 = 17 + 4 * 18
    g.bevel(5, y0 + 1, 7 + 5 * 18 - 1, y0 + 17, WOOD_DARK, CARD_EDGE, (30, 20, 15))
    g.text(10, y0 + 9, "총 가격", CREAM, 14, anchor="lm")
    g.coin(46, y0 + 9, 3.5)
    g.text(52, y0 + 9, total, GOLD_TEXT, 16, anchor="lm")
    x0 = 7 + 5 * 18
    g.bevel(x0 + 1, y0 + 1, W - 5, y0 + 17, BUY, BUY_HI, BUY_LO)
    g.text((x0 + W - 5) / 2 + 1, y0 + 9, "구매하기", (70, 40, 10), 16, anchor="mm", shadow=False)
    # ── 안내 · 닫기 (5줄) ──
    y0 = 17 + 5 * 18
    g.text(9, y0 + 9, "등급과 수량을 고르고 구매하기를 누르세요", GRAY_TEXT, 11, anchor="lm", bold=False)
    x0 = 7 + 8 * 18
    g.bevel(x0 + 1, y0 + 2, x0 + 17, y0 + 16, (110, 40, 30), (170, 70, 50), (70, 22, 16))
    g.text(x0 + 9, y0 + 9, "X", CREAM, 16, anchor="mm")
    # ── 가방 칸 (게임이 아이템을 그림) ──
    top = 17 + 6 * 18 + 13
    g.bevel(4, top - 13, W - 4, top - 1, WOOD, WOOD_HI, WOOD_LO)   # "인벤토리" 글자가 읽히는 밝은 들보
    for row in range(4):
        y = top + row * 18 + (4 if row == 3 else 0)
        for col in range(9):
            g.bevel(7 + col * 18, y, 7 + col * 18 + 18, y + 18, SLOT, (30, 20, 15), (100, 70, 48))
    return g.img


if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    build().save(os.path.join(out, "stone_shop_bg.png"))
    if len(sys.argv) > 3:                                              # 미리보기: 2배 확대
        img = build()
        img.resize((img.width * 2, img.height * 2), Image.NEAREST).save(sys.argv[3])
    print("ok")

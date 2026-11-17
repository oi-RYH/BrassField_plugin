"""
종자·작물 거래기 창 배경 두 장 (공통 부품은 gui_kit.py). 단순 칸 대신 물건 위에 아이템이 놓인 모습으로 비튼다.

작물 팔기 (6줄, CropSellGui): "도마에 올려서 판다"
  0줄 간판 자리, 간판 양옆에서 옆 기둥까지 파이프 (간판이 기계에 이어진 모습)
  사용자 도마 시안(art/cutting_board.png)을 손잡이까지 전부 줄여 깔고 왼쪽을 조금 늘린다.
        도마 안쪽 면(홈 안)에만 넣는 칸 21개 (1~3줄 1~7열). 4줄은 도마 아랫단
  5줄: 0~2열 [씨앗 사기][가격표][모두 팔기] 한 테 · 3~7열 여백 둔 황동 숫자 창(판매 예정 금액) · 8열 [판매] 버튼 (테 없음)
  바탕: 강화 창처럼 연한 색 장식(T 자 파이프·밸브 손잡이·꺾인 관·회로선·톱니)을 먼저 깔아 빈자리로만 보이게
  아이콘: 판매 버튼은 make_sell_button.py, 나머지는 make_crop_icons.py
씨앗 사기 (6줄, SeedShopGui): "꾸러미에서 사 온다"
  0줄 간판 자리 / 1~3줄 봉투 아이콘(make_seed_icons.py)을 한 칸씩 띄워 5·5·3개 (SEED_SLOTS), 줄마다 나무 선반
  4줄 비움 (연한 바탕 장식) / 5줄 나무 선반: 0열 [작물 팔기] · 8열 보유 골드

간판: art/sign_crop_sell.png · art/sign_seed_shop.png (make_crop_signs.py 로 사용자 시안에서 만든 것).
  간판 양 끝 톱니가 옆 기둥 가까이 닿으므로 따로 이어 주는 파이프(sign_pipes)는 간판 폭이 좁을 때만 그린다.

사용: python3 tools/gui/make_crop_bg.py <enhance_bg.png> <출력 폴더> [미리보기 폴더 <작물 텍스처 폴더> <클라이언트 jar> <골드 아이콘.png> <버튼 아이콘 폴더>]
"""
import math
import os
import random
import sys

from PIL import Image, ImageDraw

from gui_kit import CIRCUIT_GEAR, CIRCUIT_LINK, DARK, PAD_TOP, Preview, Window, cut_black, shrink_art, slot_box

ART = os.path.join(os.path.dirname(os.path.abspath(__file__)), "art")
SIGN_BOTTOM = 31
SELL_ROWS, SEED_ROWS = 6, 6
SEED_ORDER = ["rice", "onion", "tomato", "cabbage", "chinese_cabbage", "corn", "eggplant", "garlic", "grape", "hop",
              "pepper", "pineapple", "pitaya"]                     # 설정(crop-shop) 순서

# 나무 (도마·선반·진열판): 밝은 → 어두운
WOOD = [(214, 160, 100), (198, 142, 84), (181, 125, 70), (160, 107, 58), (134, 86, 45)]
WOOD_EDGE = (98, 60, 30)
BRASS = [(252, 214, 130), (226, 179, 99), (187, 127, 54), (146, 83, 40)]
SCREEN = (24, 18, 12)


def sign(name):
    path = os.path.join(ART, name)
    return path if os.path.exists(path) else None


def wood_fill(img, box, ramp, rnd, radius=2, grain=0.55):
    """나뭇결 판: 가로 결 무늬 + 둥근 모서리 + 짙은 테두리, 윗면 1px 밝게"""
    x0, y0, x1, y1 = box
    p = img.load()
    for y in range(y0, y1):
        for x in range(x0, x1):
            cx = min(x - x0, x1 - 1 - x)
            cy = min(y - y0, y1 - 1 - y)
            if cx < radius and cy < radius and math.hypot(radius - cx - 0.5, radius - cy - 0.5) > radius:
                continue                                          # 둥근 모서리 바깥
            edge = cx == 0 or cy == 0 or (cx < radius and cy < radius and
                                          math.hypot(radius - cx - 0.5, radius - cy - 0.5) > radius - 1)
            if edge:
                p[x, y] = WOOD_EDGE + (255,)
                continue
            g = math.sin(y * grain + 2.2 * math.sin(x * 0.07 + y * 0.3)) + rnd.uniform(-0.35, 0.35)
            i = 1 if g > 0.6 else 2 if g > -0.4 else 3
            if y == y0 + 1:
                i = 0                                             # 윗면 빛
            elif y == y1 - 2:
                i = len(ramp) - 1                                 # 아랫면 그늘
            p[x, y] = ramp[min(i, len(ramp) - 1)] + (255,)


BOARD_ART = os.path.join(ART, "cutting_board.png")             # 사용자 도마 시안 (검은 바탕)
BOARD_BOX = (20, 11, 1764, 781)                                  # 시안 속 도마(행주 포함) 범위
BOARD_FACE = (116, 110, 1524, 690)                               # 도마 안쪽 면(홈 안) 범위 = 작물을 올리는 곳
BOARD_SCALE = 0.0885                                             # 안쪽 면이 7열×3줄 아이템(124x52px)을 덮고, 손잡이까지 양 기둥 사이에
DEPOSIT = (1, 1, 3, 7)                                           # 넣는 칸: 시작 줄·열, 줄 수, 열 수
BOARD_STRETCH = (30, 10)                                         # 줄인 도마의 x=30 에서 나뭇결 띠를 복제해 왼쪽으로 10px 늘림
SIGN_PIPE_Y = 23                                                 # 간판 양옆 파이프 윗줄 y (왼쪽 위 큰 톱니 아래)


def stretch_left(board, at, extra):
    """도마 왼쪽을 늘린다: x=at 의 세로 띠(extra 폭)를 복제해 끼워 넣는다 (가로 나뭇결이라 이음매가 보이지 않는다)"""
    w, h = board.size
    out = Image.new("RGBA", (w + extra, h), (0, 0, 0, 0))
    out.alpha_composite(board.crop((0, 0, at, h)), (0, 0))
    out.alpha_composite(board.crop((at, 0, at + extra, h)), (at, 0))
    out.alpha_composite(board.crop((at, 0, w, h)), (at + extra, 0))
    return out


PIPE_V = [(13, 10, 7), (226, 179, 99), (187, 127, 54), (146, 83, 40), (13, 10, 7)]   # 세로 파이프 왼쪽 → 오른쪽
GAUGE_FACE = (238, 226, 196)


def pipe_v(win, x, y0, y1):
    for i, c in enumerate(PIPE_V):
        win.d.line([(x + i, y0), (x + i, y1 - 1)], fill=c)


def elbow(win, cx, cy, quadrant):
    """둥글게 꺾인 파이프 (굵기 5). (cx, cy) = 꺾임 원 중심, quadrant = 그리는 사분면 'ne' 'nw' 'se' 'sw'.
    단면 색은 바깥 → 안쪽으로 짙은선·밝음·중간·그늘·짙은선. 위·왼쪽을 향한 바깥 면이 밝게 보이도록 사분면마다 뒤집는다."""
    p = win.img.load()
    sx = 1 if "e" in quadrant else -1
    sy = 1 if "s" in quadrant else -1
    for dy in range(0, 8):
        for dx in range(0, 8):
            r = math.hypot(dx + 0.5, dy + 0.5)
            if not 1.5 <= r < 6.5:
                continue
            i = int(r - 1.5)                                      # 0 = 안쪽 테 … 4 = 바깥 테
            col = PIPE_V[i] if quadrant in ("se", "ne") else PIPE_V[4 - i]
            if quadrant in ("nw", "ne"):
                col = PIPE_V[4 - i] if quadrant == "ne" else PIPE_V[i]
            p[cx + sx * dx - (1 if sx < 0 else 0), cy + sy * dy - (1 if sy < 0 else 0)] = col + (255,)


def collar(win, x, y, vertical):
    """파이프 이음쇠 고리 (파이프보다 1px 굵음)"""
    d = win.d
    if vertical:
        d.rectangle([x - 1, y, x + 5, y + 1], fill=DARK)
        d.line([(x, y), (x + 4, y)], fill=BRASS[0])
        d.line([(x, y + 1), (x + 4, y + 1)], fill=BRASS[2])
    else:
        d.rectangle([x, y - 1, x + 1, y + 5], fill=DARK)
        d.line([(x, y), (x, y + 4)], fill=BRASS[0])
        d.line([(x + 1, y), (x + 1, y + 4)], fill=BRASS[2])


def gauge(win, cx, cy):
    """작은 압력계 (지름 7): 황동 테 · 크림색 눈금판 · 바늘"""
    p = win.img.load()
    for dy in range(-4, 5):
        for dx in range(-4, 5):
            r = math.hypot(dx, dy)
            if r > 4.2:
                continue
            col = DARK if r > 3.4 else (BRASS[0] if dx + dy < 0 else BRASS[2]) if r > 2.5 else GAUGE_FACE
            p[cx + dx, cy + dy] = col + (255,)
    for dx, dy in ((0, 0), (1, -1), (2, -1)):                    # 바늘 (오른쪽 위)
        p[cx + dx, cy + dy] = (150, 30, 20, 255)
    win.d.rectangle([cx - 1, cy + 4, cx + 1, cy + 6], fill=DARK)  # 받침 (아래 파이프로)
    win.d.line([(cx, cy + 4), (cx, cy + 6)], fill=BRASS[2])


def sign_pipes(win, sign_path):
    """간판과 옆 기둥을 잇는 굽은 파이프 (간판 뒤로 들어감).
    왼쪽: 기둥 → 톱니 아래로 가로 → 위로 꺾여 올라감(이음쇠) → 다시 꺾여 간판 옆구리로
    오른쪽: 간판 옆구리 → 아래로 휘어 내려감 → 꺾여 기둥으로 (위에 압력계)"""
    if not sign_path:
        return
    sw = Image.open(sign_path).size[0]
    if sw > 140:                                                  # 넓은 간판은 양 끝 톱니가 기둥에 닿아 파이프가 필요 없다
        return
    sx0, sx1 = (176 - sw) // 2, (176 + sw) // 2
    lo, hi = SIGN_PIPE_Y, 8                                       # 아래 가로 파이프 · 위 가로 파이프 윗줄 y
    vx = sx0 - 6                                                  # 왼쪽 세로 파이프 x
    win.pipe_h(6, vx - 1, lo)
    elbow(win, vx - 1, lo - 1, "se")                              # 가로(오른쪽으로) → 위로
    pipe_v(win, vx, hi + 6, lo - 1)
    elbow(win, vx + 6, hi + 6, "nw")                              # 위로 → 오른쪽으로
    win.pipe_h(vx + 6, sx0 + 8, hi)
    collar(win, vx, lo - 8, True)
    rx = sx1 + 1                                                  # 오른쪽 세로 파이프 x
    win.pipe_h(sx1 - 8, rx - 1, hi)
    elbow(win, rx - 1, hi + 6, "ne")                              # 오른쪽으로 → 아래로
    pipe_v(win, rx, hi + 6, lo - 1)
    elbow(win, rx + 6, lo - 1, "sw")                              # 아래로 → 오른쪽으로
    win.pipe_h(rx + 6, 170, lo)
    gauge(win, 163, lo - 6)
    collar(win, 168, lo, False)


FAINT = (60, 53, 43)                                             # 바탕 판보다 조금 밝은 선 (강화 창 회로선 색 정도)
FAINT_HI = (68, 61, 50)


def faint_pipe(win, x0, y, x1, branch=None):
    """연한 가로 파이프 윤곽 (위·아래 선) + 이음쇠 눈금, branch=x 면 그 자리에서 아래로 T 자 갈림"""
    d = win.d
    d.line([(x0, y), (x1, y)], fill=FAINT)
    d.line([(x0, y + 3), (x1, y + 3)], fill=FAINT)
    for x in range(x0 + 6, x1 - 2, 12):
        d.line([(x, y - 1), (x, y + 4)], fill=FAINT_HI)
    if branch:
        d.rectangle([branch, y + 3, branch + 3, y + 3], fill=win.img.getpixel((branch, y + 5))[:3])
        d.line([(branch, y + 3), (branch, y + 9)], fill=FAINT)
        d.line([(branch + 3, y + 3), (branch + 3, y + 9)], fill=FAINT)
        d.line([(branch - 1, y + 9), (branch + 4, y + 9)], fill=FAINT_HI)


def faint_valve(win, cx, cy):
    """연한 밸브 손잡이 (지름 9, 살 4개)"""
    p = win.img.load()
    for dy in range(-4, 5):
        for dx in range(-4, 5):
            r = math.hypot(dx, dy)
            if 3.3 < r < 4.4 or (r < 3.4 and (dx == 0 or dy == 0)):
                p[cx + dx, cy + dy] = (FAINT_HI if r < 1 else FAINT) + (255,)


def faint_bend(win, x, y, w, h):
    """연한 꺾인 관 (ㄱ 자): 가로로 w, 아래로 h"""
    d = win.d
    d.line([(x, y), (x + w, y)], fill=FAINT)
    d.line([(x, y + 3), (x + w - 3, y + 3)], fill=FAINT)
    d.line([(x + w, y), (x + w, y + h)], fill=FAINT)
    d.line([(x + w - 3, y + 3), (x + w - 3, y + h)], fill=FAINT)
    d.line([(x + w - 4, y + h), (x + w + 1, y + h)], fill=FAINT_HI)


def build_sell(enh):
    win = Window(enh, SELL_ROWS, seed=911)
    img, d = win.img, win.d
    # ── 연한 바탕 장식 (도마·버튼보다 먼저: 빈자리로만 살짝 보인다) ──
    faint_pipe(win, 8, 99, 168, branch=60)
    faint_valve(win, 118, 101)
    faint_bend(win, 150, 92, 12, 12)
    win.copy(CIRCUIT_LINK, (6, 88))
    win.copy(CIRCUIT_GEAR, (152, 30))
    # ── 도마: 안쪽 면이 넣는 칸(2~4줄 1~7열) 아이템 자리를 덮게. 손잡이까지 양 기둥 사이 ──
    board = stretch_left(shrink_art(cut_black(Image.open(BOARD_ART)), BOARD_BOX, BOARD_SCALE), *BOARD_STRETCH)
    row0, col0, rows, cols = DEPOSIT
    gx, gy = slot_box(row0, col0)
    face_x = (BOARD_FACE[0] - BOARD_BOX[0]) * BOARD_SCALE + BOARD_STRETCH[1]   # 안쪽 면 오른쪽 끝 기준 (왼쪽으로 늘어남)
    face_y = (BOARD_FACE[1] - BOARD_BOX[1]) * BOARD_SCALE
    face_w = (BOARD_FACE[2] - BOARD_FACE[0]) * BOARD_SCALE
    face_h = (BOARD_FACE[3] - BOARD_FACE[1]) * BOARD_SCALE
    bx = round(gx + 1 + (cols * 18 - 2 - face_w) / 2 - face_x)    # 아이템 자리(칸 안쪽 16px)에 안쪽 면(늘리기 전) 맞춤
    by = round(gy + 1 + (rows * 18 - 2 - face_h) / 2 - face_y)
    img.alpha_composite(board, (bx, by))
    # ── 5줄: 3~7열 여백 둔 황동 숫자 창 · 8열 판매 버튼(테 없음) ──
    _, sy = slot_box(5, 0)
    x0, x1 = slot_box(5, 3)[0] + 4, slot_box(5, 7)[0] + 17
    d.rectangle([x0, sy + 2, x1, sy + 16], fill=DARK)
    d.rectangle([x0 + 1, sy + 3, x1 - 1, sy + 15], fill=BRASS[2])
    d.line([(x0 + 1, sy + 3), (x1 - 1, sy + 3)], fill=BRASS[0])
    d.line([(x0 + 1, sy + 15), (x1 - 1, sy + 15)], fill=BRASS[3])
    d.rectangle([x0 + 2, sy + 4, x1 - 2, sy + 14], fill=SCREEN)
    win.frame_slots(5, 0, cols=3)                                 # 씨앗 사기 · 가격표 · 모두 팔기
    win.corner_gears(bottom_right=False, top_left=False)    # 간판 끝 톱니와 겹치지 않게
    sign_pipes(win, sign("sign_crop_sell.png"))
    return win.finish(sign("sign_crop_sell.png"), SIGN_BOTTOM)


SEED_SLOTS = [(row, col) for row in (1, 2, 3, 4) for col in (1, 4, 7)]   # 한 페이지 3열 4행 = 12칸
SEED_PRICES = {"rice": 10, "onion": 10, "tomato": 15, "cabbage": 10, "chinese_cabbage": 10, "corn": 10, "eggplant": 10,
               "garlic": 10, "grape": 20, "hop": 10, "pepper": 15, "pineapple": 10, "pitaya": 20}   # 미리보기용 (설정값)
COIN5 = [".OOO.", "OLMMO", "OMDMO", "OMMDO", ".OOO."]                          # 가격표 작은 금화
COIN5_PAL = {"O": (92, 58, 10), "L": (255, 220, 110), "M": (232, 170, 40), "D": (176, 112, 20)}
SEED_NAV = {"tab": (5, 0), "prev": (5, 3), "page": (5, 4), "next": (5, 5), "gold": (5, 8)}


def build_seed(enh):
    win = Window(enh, SEED_ROWS, seed=912)
    rnd = random.Random(31)
    img, d = win.img, win.d
    for row in (1, 2, 3, 4):                                      # 봉투 줄마다 나무 선반 (봉투 아랫단이 올라앉음)
        _, y = slot_box(row, 0)
        wood_fill(img, (6, y + 14, 170, y + 19), WOOD, rnd, radius=1, grain=1.4)
    # 맨 아래 줄: 페이지 번호 창 (이전·다음 버튼 사이, 판매 화면 금액 창과 같은 모양)
    px, py = slot_box(*SEED_NAV["page"])
    x0, x1 = px - 1, px + 18
    d.rectangle([x0, py + 2, x1, py + 16], fill=DARK)
    d.rectangle([x0 + 1, py + 3, x1 - 1, py + 15], fill=BRASS[2])
    d.line([(x0 + 1, py + 3), (x1 - 1, py + 3)], fill=BRASS[0])
    d.line([(x0 + 1, py + 15), (x1 - 1, py + 15)], fill=BRASS[3])
    d.rectangle([x0 + 2, py + 4, x1 - 2, py + 14], fill=SCREEN)
    win.corner_gears(bottom_right=False, top_left=False)    # 간판 끝 톱니와 겹치지 않게
    sign_pipes(win, sign("sign_seed_shop.png"))
    return win.finish(sign("sign_seed_shop.png"), SIGN_BOTTOM)


DIGITS = {"0": ["111", "101", "101", "101", "111"], "1": ["010", "110", "010", "010", "111"],
          "2": ["111", "001", "111", "100", "111"], "3": ["111", "001", "111", "001", "111"],
          "4": ["101", "101", "111", "001", "001"], "5": ["111", "100", "111", "001", "111"],
          "6": ["111", "100", "111", "101", "111"], "7": ["111", "001", "010", "010", "010"],
          "8": ["111", "101", "111", "101", "111"], "9": ["111", "101", "111", "001", "111"],
          ",": ["0", "0", "0", "1", "1"], "/": ["001", "001", "010", "100", "100"]}


def price_tag(prev, row, col, price):
    """미리보기용: 봉투 오른쪽 옆 가격표 (봉투 절반 높이 9px). 황동 테 짙은 판 + 작은 금화 + 숫자.
    게임에서는 페이지마다 바뀌므로 제목 글자(글꼴 그림)로 띄운다."""
    x, y = slot_box(row, col)
    text = str(price)
    w = 2 + 5 + 1 + sum(len(DIGITS[ch][0]) + 1 for ch in text) + 1   # 테 2 · 금화 5 · 틈 1 · 숫자 · 테 1
    x0, y0 = x + 18, y + 4 + PAD_TOP
    d = ImageDraw.Draw(prev.img)
    d.rectangle([x0, y0, x0 + w, y0 + 8], fill=DARK)
    d.rectangle([x0 + 1, y0 + 1, x0 + w - 1, y0 + 7], fill=BRASS[2])
    d.line([(x0 + 1, y0 + 1), (x0 + w - 1, y0 + 1)], fill=BRASS[0])
    d.rectangle([x0 + 2, y0 + 2, x0 + w - 2, y0 + 6], fill=SCREEN)
    p = prev.img.load()
    for j, line in enumerate(COIN5):
        for i, c in enumerate(line):
            if c != ".":
                p[x0 + 2 + i, y0 + 2 + j] = COIN5_PAL[c] + (255,)
    cx = x0 + 2 + 5 + 1
    for ch in text:
        for j, line in enumerate(DIGITS[ch]):
            for i, c in enumerate(line):
                if c == "1":
                    p[cx + i, y0 + 2 + j] = (253, 226, 150, 255)
        cx += len(DIGITS[ch][0]) + 1


def screen_digits(prev, text, right, row):
    """미리보기용: 숫자 창에 글자 (게임에서는 강화 창 글자 보드처럼 제목 글자로 띄운다). right = 글자 오른쪽 끝 x"""
    y = slot_box(row, 0)[1] + 7 + PAD_TOP
    p = prev.img.load()
    x = right - sum(len(DIGITS[ch][0]) + 1 for ch in text) + 2
    for ch in text:
        for j, line in enumerate(DIGITS[ch]):
            for i, c in enumerate(line):
                if c == "1":
                    p[x + i, y + j] = (255, 196, 80, 255)
        x += len(DIGITS[ch][0]) + 1


if __name__ == "__main__":
    enh = Image.open(sys.argv[1]).convert("RGBA")
    out_dir = sys.argv[2]
    sell, seed = build_sell(enh), build_seed(enh)
    sell.save(os.path.join(out_dir, "crop_sell_bg.png"))
    seed.save(os.path.join(out_dir, "seed_shop_bg.png"))
    if len(sys.argv) > 3:
        prev_dir, crops_dir, jar, gold, icons = sys.argv[3:8]
        crop = lambda c, s="": Image.open(os.path.join(crops_dir, c, c + s + ".png")).convert("RGBA")
        gold_icon = Image.open(gold).convert("RGBA")
        p = Preview(sell, SELL_ROWS, jar)                         # 작물 몇 개를 올려 둔 모습
        for i, (c, n) in enumerate((("tomato", 32), ("cabbage", 64), ("grape", 20), ("pepper", 7), ("eggplant", 16),
                                    ("corn", 12), ("garlic", 9))):
            p.item(1 + i // 7, 1 + i % 7, crop(c), n)
        p.item(2, 1, crop("tomato", "_golden_star"), 3)
        for col, name in enumerate(("seed_tab", "price_list", "sell_all")):
            p.item(5, col, Image.open(os.path.join(icons, name + ".png")).convert("RGBA"))
        p.item(5, 8, Image.open(os.path.join(icons, "sell_button16.png")).convert("RGBA"))
        screen_digits(p, "5,580", slot_box(5, 7)[0] + 13, 5)
        p.save(os.path.join(prev_dir, "crop_sell_preview.png"))
        board_icon = shrink_art(cut_black(Image.open(BOARD_ART)), BOARD_BOX, 16 / (BOARD_BOX[2] - BOARD_BOX[0]))
        tab = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        tab.alpha_composite(board_icon, (0, (16 - board_icon.height) // 2))
        per_page = len(SEED_SLOTS)
        pages = (len(SEED_ORDER) + per_page - 1) // per_page
        for page in range(pages):
            p = Preview(seed, SEED_ROWS, jar)
            for (row, col), c in zip(SEED_SLOTS, SEED_ORDER[page * per_page:(page + 1) * per_page]):
                p.item(row, col, Image.open(os.path.join(icons, c + "_seeds_icon.png")).convert("RGBA"))
                price_tag(p, row, col, SEED_PRICES[c])
            p.item(*SEED_NAV["tab"], tab)
            if page > 0:
                p.item(*SEED_NAV["prev"], Image.open(os.path.join(icons, "page_prev.png")).convert("RGBA"))
            if page < pages - 1:
                p.item(*SEED_NAV["next"], Image.open(os.path.join(icons, "page_next.png")).convert("RGBA"))
            p.item(*SEED_NAV["gold"], gold_icon)
            text = "%d/%d" % (page + 1, pages)
            px, _ = slot_box(*SEED_NAV["page"])
            screen_digits(p, text, px + 9 + (sum(len(DIGITS[ch][0]) + 1 for ch in text) - 1) // 2, SEED_NAV["page"][0])
            p.save(os.path.join(prev_dir, "seed_shop_preview_%d.png" % (page + 1)))
    print("ok")

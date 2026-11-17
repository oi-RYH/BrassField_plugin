"""
DL-7 납품 창 배경 (6줄, 공통 부품 gui_kit.py). 사용자 시안(art/dl7_concept.png)에서 부품을 잘라 칸 격자에 맞춰 조립한다.
  간판 없음 (상자 윗테가 창 위쪽까지 올라와 간판 자리가 없다)
  화물 상자 (art/dl7_concept2.png) : 칸 선 없이 안이 트인 나무 상자. 상자 안쪽 = 1~4줄 1~5열 (요리 넣는 칸 20개, 칸 자리는
                                   모서리 점만 희미하게). 상자 전체가 왼쪽 기둥과 영수증 사이에 들어오도록 안쪽을 5열(90px) x
                                   상자 전체 높이는 위 들보와 가방 칸 들보 사이에 맞춘다 (맨 아랫줄 요리는 앞테에 조금 걸친다).
                                   상자 바깥 시안 바탕은 윤곽을 따라 지운다. 손잡이는 자리가 없어 뺀다
  DL-7 얼굴                       : 0줄 0열 (마우스를 올리면 오늘의 주문)
  영수증                          : 오른쪽 7~8열 (개수·총 금액은 제목 글자로 띄움)
  납품 버튼                       : 4~5줄 7~8열 2x2 (네 칸 어디를 눌러도 납품). 시안 버튼 판을 위아래로 늘리고
                                   상자 그림(16px)과 간판 글씨체 "납품"(9px)을 크게 다시 얹는다
시안 좌표는 원본(1199x1312) 기준.

사용: python3 tools/gui/make_dl7_bg.py <enhance_bg.png> <출력.png> [미리보기.png <클라이언트 jar>]
"""
import os
import sys
from collections import Counter

from PIL import Image

from gui_kit import PILLAR, Preview, Window, cut_black, cut_outside, shrink_art, slot_box

ART = os.path.join(os.path.dirname(os.path.abspath(__file__)), "art", "dl7_concept.png")
ART_CRATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "art", "dl7_concept2.png")   # 트인 나무 상자 시안
CRATE = (124, 286, 778, 861)             # 상자 테두리까지 (손잡이 제외, 양옆 파이프 조각 제외, 아래 금속 발판 끝까지)
CRATE_SPAN = (7, 125)                    # 상자를 넣는 세로 범위: 위 들보 아래 ~ 가방 칸 들보 위
CRATE_BG = 120                           # 상자 바깥 시안 바탕(밝기 합 이하)만 지운다
OUTLINE = (12, 8, 6)                     # 상자 둘레 검은 테두리 (끊긴 곳을 이어 줌, 시안 테두리처럼 짙게)
OUTLINE_DARK = 80                        # 이보다 어두운 가장자리 칸만 이미 테두리로 본다 (어두운 철제 면은 테두리가 아님)
CRATE_COLS, CRATE_ROWS, CRATE_COL0 = 5, 4, 1   # 상자 안 칸: 5열 x 4줄, 1열부터
CRATE_INSIDE = (190, 400, 720, 745)      # 상자 안쪽 (요리 넣는 칸 6x4)
PAD = 0                                  # 간판이 없어 창 위로 넘치는 부분 없음 (guis.yml y_position 13)
ROWS = 6

# 시안 부품 범위 (x0, y0, x1, y1)
HEAD = (118, 122, 278, 300)              # DL-7 얼굴 (art/dl7_concept2.png, 왼쪽 파이프·등불과 오른쪽 상자 윗테 제외)
RECEIPT = (767, 167, 1107, 590)
BUTTON = (773, 616, 1087, 743)
SIGN_WORD = (575, 48, 673, 100)          # 간판 속 "납품" 글자 (버튼 글자로 다시 씀 — 버튼 속 글자는 획이 가늘어 줄이면 끊긴다)
BUTTON_ICON = (843, 646, 914, 727)       # 버튼 속 상자 그림
BUTTON_CLEAR = (836, 644, 1016, 728)     # 버튼 판에서 그림·글자를 지울 범위
BUTTON_SIZE = 36
BUTTON_SLICE = 5                         # 버튼 판 위·아래 테두리 높이 (가운데만 늘림)
# 영수증 속 글자 자리 (지우고 아이콘·숫자로 바꿈): 제목 · 납품 항목 줄 · 총 금액 줄
RECEIPT_TEXT = [(800, 255, 1075, 310), (800, 350, 1075, 395), (800, 415, 1075, 465)]
PAPER = (242, 206, 160)
RECEIPT_LINES = (372, 440)               # 영수증 개수 줄 · 총 금액 줄 가운데 y (시안)
BOWL = ["..w.w..", ".w.w...", "OOOOOOO", "OBBBBBO", ".OBBBO.", "..OOO.."]   # 영수증 김 나는 그릇 (= 올린 요리 개수)
BOWL_PAL = {"O": (96, 58, 30), "B": (214, 132, 64), "w": (176, 160, 146)}
PAPER_TONES = [(250, 226, 186), (238, 204, 156), (216, 174, 122)]       # 영수증 종이 밝음 · 중간 · 그늘
RECEIPT_RULES = (330, 405, 480)          # 영수증 점선 구분선 y (시안)
# "납품" 버튼 글자: art/dl7_label.txt (한 줄 = 한 픽셀 줄, '1' = 글자 픽셀, '.' = 빈칸). 크림색 + 오른쪽 아래 그림자.
# 픽셀 편집 페이지(납품 글자 편집기)에서 찍은 결과를 이 파일에 붙여 넣으면 된다.
LABEL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "art", "dl7_label.txt")


def load_label():
    with open(LABEL_FILE) as f:
        rows = [line.rstrip("\n") for line in f if line.strip()]
    width = max(len(r) for r in rows)
    return [r.ljust(width, ".") for r in rows]


LABEL_COLOR, LABEL_SHADOW = (253, 226, 150), (60, 30, 15)
COIN5 = [".OOO.", "OLMMO", "OMDMO", "OMMDO", ".OOO."]
COIN5_PAL = {"O": (92, 58, 10), "L": (255, 220, 110), "M": (232, 170, 40), "D": (176, 112, 20)}
BG_DARK = 140                            # 시안 바탕(짙은 갈색): 가장자리에서 이어진 이보다 어두운 칸을 지운다

RECEIPT_TOP = 20
RECEIPT_ICON_X = 6                       # 영수증 왼쪽에서 아이콘까지
RECEIPT_DIGITS_RIGHT = 39                # 영수증 왼쪽에서 숫자 오른쪽 끝까지
HEAD_HEIGHT = 30
RECEIPT_WIDTH = 46



def piece(src, box, w=None, h=None, scale=None, cut=True):
    """시안 부품을 잘라(가장자리와 이어진 짙은 바탕은 지움) 줄인다: scale 또는 폭 w / 높이 h 에 맞춤"""
    bw, bh = box[2] - box[0], box[3] - box[1]
    if scale is None:
        scale = (w / bw) if w else (h / bh)
    crop = src.crop(box)
    if cut:
        crop = cut_black(crop, threshold=BG_DARK)
    return shrink_art(crop, (0, 0, bw, bh), scale)


def clean_paper(receipt):
    """줄인 영수증의 종이 결을 세 가지 종이색으로 정리해 또렷하게 (종이가 아닌 고리·바코드 등은 그대로)"""
    p = receipt.load()
    for y in range(receipt.height):
        for x in range(receipt.width):
            r, g, b, a = p[x, y]
            if a and r > 190 and g > 145 and b > 95:
                lum = r + g + b
                p[x, y] = (PAPER_TONES[0] if lum > 620 else PAPER_TONES[1] if lum > 560 else PAPER_TONES[2]) + (255,)
    return receipt


def close_outline(img):
    """물체 둘레 검은 테두리 잇기: 가장자리 칸이 밝은데 바로 바깥(상하좌우)이 비어 있으면 그 빈칸을 테두리 색으로 채운다.
    가장자리가 이미 어두우면(테두리가 있으면) 그대로 둬서 두 겹이 되지 않게 한다.
    먼저 둘레에 홀로 붙은 밝은 조각(시안의 옆 파이프 부스러기: 상하좌우 이웃이 2칸 이하)을 지운다."""
    p = img.load()
    w, h = img.size
    for _ in range(2):                                               # 부스러기 지우기 (두 번: 2칸짜리 조각까지)
        crumbs = [(x, y) for y in range(h) for x in range(w)
                  if p[x, y][3] and sum(p[x, y][:3]) > 300
                  and sum(1 for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1))
                          if 0 <= x + i < w and 0 <= y + j < h and p[x + i, y + j][3]) <= 2
                  and any(not (0 <= x + i < w and 0 <= y + j < h) or not p[x + i, y + j][3]
                          for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
        for x, y in crumbs:
            p[x, y] = (0, 0, 0, 0)
    fill = []
    for y in range(h):
        for x in range(w):
            if p[x, y][3]:
                continue
            for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + i, y + j
                if 0 <= nx < w and 0 <= ny < h and p[nx, ny][3] and sum(p[nx, ny][:3]) > OUTLINE_DARK:
                    fill.append((x, y))
                    break
    for x, y in fill:
        p[x, y] = OUTLINE + (255,)
    return img


def straighten_receipt(receipt, hanger_rows=12):
    """영수증 종이 양옆을 곧게: 고리 아래 줄들에서 가장 흔한 종이 왼쪽·오른쪽 끝에 맞춰 넘친 칸은 지우고 모자란 칸은 채운다.
    아래 찢긴 끝은 2칸 톱니로 다시 그리고, 종이 밖(시안의 옆 파이프 조각)은 지운다."""
    p = receipt.load()
    w, h = receipt.size
    is_paper = lambda x, y: p[x, y][3] and p[x, y][:3] in PAPER_TONES
    rows = [y for y in range(hanger_rows, h) if any(is_paper(x, y) for x in range(w))]
    lefts = Counter(min(x for x in range(w) if is_paper(x, y)) for y in rows)
    rights = Counter(max(x for x in range(w) if is_paper(x, y)) for y in rows)
    left, right = lefts.most_common(1)[0][0], rights.most_common(1)[0][0]
    bottom = rows[-1] - 2                                            # 찢긴 끝 두 줄 위까지 곧은 종이
    for y in range(hanger_rows, h):
        for x in range(w):
            inside = left <= x <= right
            if y <= bottom:
                if not inside:
                    p[x, y] = (0, 0, 0, 0)
                elif not p[x, y][3] or not is_paper(x, y) and (x in (left, right)):
                    p[x, y] = PAPER_TONES[1] + (255,)
            else:                                                    # 찢긴 끝: 2칸 톱니
                k = (x - left) % 4
                keep = inside and (k in (0, 1) if y == bottom + 1 else k == 0)
                p[x, y] = PAPER_TONES[1] + (255,) if keep else (0, 0, 0, 0)
    return receipt


def word(src, box, h):
    """시안 속 밝은 글자만 떼어 높이 h 로 줄인다"""
    crop = src.crop(box).copy()
    p = crop.load()
    for y in range(crop.height):
        for x in range(crop.width):
            r, g, b, a = p[x, y]
            if not (r > 185 and g > 105):                            # 밝은 글자 + 둘레 주황 테
                p[x, y] = (0, 0, 0, 0)
    return shrink_art(crop, (0, 0, crop.width, crop.height), h / crop.height)


def build(enh):
    src = Image.open(ART).convert("RGBA")
    src_clean = src.copy()                                           # 영수증 글자·버튼 글자를 지운 시안
    from PIL import ImageDraw
    d = ImageDraw.Draw(src_clean)
    for box in RECEIPT_TEXT:
        d.rectangle(box, fill=PAPER)
    btn = src.load()
    d.rectangle(BUTTON_CLEAR, fill=btn[1030, 700])
    win = Window(enh, ROWS, seed=913, pad_top=PAD)
    img = win.img
    # ── 화물 상자: 안쪽 폭 = 6칸, 안쪽 왼쪽 위 = 1줄 0열 칸 ──
    crate_src = Image.open(ART_CRATE).convert("RGBA")
    sx = CRATE_COLS * 18 / (CRATE_INSIDE[2] - CRATE_INSIDE[0])     # 안쪽 폭 = 5칸
    sy = (CRATE_SPAN[1] - CRATE_SPAN[0]) / (CRATE[3] - CRATE[1])     # 상자 전체 높이 = 들보 사이
    cut = cut_outside(crate_src.crop(CRATE), lambda c: c[0] + c[1] + c[2] <= CRATE_BG)
    tall = shrink_art(cut, (0, 0, cut.width, cut.height), sx)       # 가로 배율로 줄인 뒤 세로만 맞춤
    crate = tall.resize((tall.width, CRATE_SPAN[1] - CRATE_SPAN[0]), Image.NEAREST)
    framed = Image.new("RGBA", (crate.width + 2, crate.height + 2), (0, 0, 0, 0))   # 테두리 한 칸 자리
    framed.alpha_composite(crate, (1, 1))
    crate = close_outline(framed)
    gx, gy = slot_box(1, CRATE_COL0)
    cx = gx - round((CRATE_INSIDE[0] - CRATE[0]) * sx) - 1
    cy = CRATE_SPAN[0] - 1
    img.alpha_composite(crate, (cx, cy))
    p = img.load()
    for row in range(CRATE_ROWS):                                    # 칸 자리: 모서리 점만 희미하게
        for col in range(CRATE_COLS):
            x, y = slot_box(1 + row, CRATE_COL0 + col)
            for qx, qy in ((x + 1, y + 1), (x + 16, y + 1), (x + 1, y + 16), (x + 16, y + 16)):
                r, g, b, a = p[qx, qy]
                p[qx, qy] = (int(r * 0.8), int(g * 0.8), int(b * 0.8), a)
    # ── 오른쪽: 영수증 · 납품 버튼 · 도장 ──
    receipt = straighten_receipt(clean_paper(piece(src_clean, RECEIPT, w=RECEIPT_WIDTH)))
    rx = 170 - 1 - receipt.width
    k = RECEIPT_WIDTH / (RECEIPT[2] - RECEIPT[0])
    rp = receipt.load()
    for rule in RECEIPT_RULES:                                         # 점선 구분선 다시 그리기
        y = round((rule - RECEIPT[1]) * k)
        for x in range(4, receipt.width - 4, 2):
            if rp[x, y][3] and rp[x, y][:3] in PAPER_TONES:
                rp[x, y] = PAPER_TONES[2] + (255,)
    img.alpha_composite(receipt, (rx, RECEIPT_TOP))
    for pattern, pal, line in ((BOWL, BOWL_PAL, RECEIPT_LINES[0]), (COIN5, COIN5_PAL, RECEIPT_LINES[1])):
        y = RECEIPT_TOP + round((line - RECEIPT[1]) * k) - len(pattern) // 2
        for j, row in enumerate(pattern):
            for i, c in enumerate(row):
                if c != ".":
                    img.putpixel((rx + RECEIPT_ICON_X + i, y + j), pal[c] + (255,))
    plate = piece(src_clean, BUTTON, w=BUTTON_SIZE)                  # 버튼 판: 위·아래 테두리는 두고 가운데만 늘림
    button = Image.new("RGBA", (BUTTON_SIZE, BUTTON_SIZE), (0, 0, 0, 0))
    t = BUTTON_SLICE
    button.alpha_composite(plate.crop((0, 0, BUTTON_SIZE, t)), (0, 0))
    button.alpha_composite(plate.crop((0, plate.height - t, BUTTON_SIZE, plate.height)), (0, BUTTON_SIZE - t))
    middle = plate.crop((0, t, BUTTON_SIZE, plate.height - t)).resize((BUTTON_SIZE, BUTTON_SIZE - 2 * t), Image.NEAREST)
    button.alpha_composite(middle, (0, t))
    icon = piece(src, BUTTON_ICON, w=16, cut=False)
    button.alpha_composite(icon, ((BUTTON_SIZE - icon.width) // 2, 4))
    if os.environ.get("DL7_PLATE_OUT"):                                # 편집 페이지용: 글자 없는 버튼 판
        button.save(os.environ["DL7_PLATE_OUT"])
    label = load_label()
    lx, ly = (BUTTON_SIZE - len(label[0])) // 2, 4 + icon.height + 1
    bp = button.load()
    for dx, dy, col in ((1, 1, LABEL_SHADOW), (0, 0, LABEL_COLOR)):    # 그림자 먼저, 글자 나중
        for j, row in enumerate(label):
            for i, c in enumerate(row):
                if c == "1":
                    bp[lx + i + dx, ly + j + dy] = col + (255,)
    px, py = slot_box(4, 7)
    img.alpha_composite(button, (px, py))
    # ── DL-7 얼굴 (0줄 0열) ──
    head_src = cut_outside(crate_src.crop(HEAD), lambda c: c[0] + c[1] + c[2] <= CRATE_BG)
    head = shrink_art(head_src, (0, 0, head_src.width, head_src.height), HEAD_HEIGHT / head_src.height)
    win.corner_gears(bottom_right=False, top_left=False)             # 왼쪽 위는 얼굴 자리라 톱니 대신 볼트 판
    hx, hy = slot_box(0, 0)
    img.alpha_composite(head, (max(PILLAR, hx + (18 - head.width) // 2), hy + 18 - head.height + 4))   # 기둥 위로 겹치지 않게
    return win.finish()


if __name__ == "__main__":
    out = build(Image.open(sys.argv[1]).convert("RGBA"))
    out.save(sys.argv[2])
    if len(sys.argv) > 3:                                          # 미리보기: 영수증 숫자 예시 (게임에서는 제목 글자)
        p = Preview(out, ROWS, sys.argv[4], pad_top=PAD)
        k = RECEIPT_WIDTH / (RECEIPT[2] - RECEIPT[0])
        rx = 170 - 1 - RECEIPT_WIDTH
        digits = {"0": ["111", "101", "101", "101", "111"], "1": ["010", "110", "010", "010", "111"],
                  "2": ["111", "001", "111", "100", "111"], "3": ["111", "001", "111", "001", "111"],
                  "4": ["101", "101", "111", "001", "001"], "5": ["111", "100", "111", "001", "111"],
                  "6": ["111", "100", "111", "101", "111"], "7": ["111", "001", "010", "010", "010"],
                  "8": ["111", "101", "111", "101", "111"], "9": ["111", "101", "111", "001", "111"],
                  ",": ["0", "0", "0", "1", "1"]}
        px = p.img.load()
        for text, line in (("12", RECEIPT_LINES[0]), ("4,860", RECEIPT_LINES[1])):
            y = RECEIPT_TOP + round((line - RECEIPT[1]) * k) - 2 + PAD
            x = rx + RECEIPT_DIGITS_RIGHT - sum(len(digits[c][0]) + 1 for c in text) + 2
            for c in text:
                for j, row in enumerate(digits[c]):
                    for i, v in enumerate(row):
                        if v == "1":
                            px[x + i, y + j] = (70, 40, 20, 255)
                x += len(digits[c][0]) + 1
        p.save(sys.argv[3])
    print("ok")

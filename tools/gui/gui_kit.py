"""
상자 창 배경 공통 부품: 강화 창 배경(enhance_bg.png)의 부품을 잘라 여러 줄 상자 창 배경을 조립한다.
같은 세트로 보이도록 새로 그리지 않고 강화 창 그림을 그대로 쓴다.

부품 (강화 창 그림 좌표):
  옆 기둥(7px: 회백색 금속 + 안쪽 밝은 회색 줄 + 구리 고리, 18px 주기) · 위 구리 들보 · 왼쪽 위 톱니 · 오른쪽 위 볼트 · 오른쪽 아래 톱니
  칸 황동 테 (칸 바깥 2px, 9분할로 늘려 여러 칸을 한 테로 묶을 수 있다) · 유리관 · 작은 톱니
  아래 가방 칸 부분 전체 (창 칸 끝 y=71 부터 끝까지)
  바탕 판: 잔무늬 + 강화 창처럼 어둡고 밝은 작은 점, 희미한 회로선 두 가지(마디→톱니, 마디-꺾인 선-마디)
간판: 창 위 가운데에 걸고 창 위로 넘치는 만큼 그림 맨 위에 PAD_TOP 여백을 둔다
  (ItemsAdder guis.yml 의 y_position 은 enhance_bg 기준 13 에 PAD_TOP 을 더한다).
  위 구리 들보는 간판 뒤로 지나가고, 간판 아래·오른쪽으로 바탕 판에 그림자를 드리운다.
"""
import io
import random
import zipfile
from collections import deque

from PIL import Image, ImageDraw, ImageFont

W = 176
PILLAR = 7                             # 옆 기둥 폭 (안쪽 끝 한 줄은 밝은 회색 176,155,117)
SEAM_ROWS = 4                          # 가방 칸 부분 맨 위에 딸려 오는 강화 창 장비 칸 테·오른쪽 아래 톱니 조각 줄 수
ENH_ROWS_END = 17 + 3 * 18             # 강화 창(3줄) 창 칸이 끝나는 y
PANEL = [(42, 35, 28), (43, 36, 29), (44, 37, 30), (45, 38, 31), (46, 39, 32)]
SPECKS = [((39, 31, 24), 0.015), ((58, 53, 45), 0.01)]   # 강화 창 바탕의 작은 점 (색, 비율)
DARK = (13, 10, 7)
DIVIDER = (50, 45, 37)                 # 여러 칸 묶음 안의 칸 구분선
PIPE = [(13, 10, 7), (226, 179, 99), (187, 127, 54), (146, 83, 40), (13, 10, 7)]   # 가로 파이프 위→아래
PAD_TOP = 8
SHADOW = 0.55                          # 간판 그림자: 바탕 판 밝기 배율

# 강화 창에서 잘라 쓰는 장식 (그림 좌표 상자)
GEAR_SMALL = (54, 36, 70, 52)          # 파이프 가운데 작은 톱니 (16x16)
TUBE = (6, 22, 22, 70)                 # 왼쪽 유리관
CIRCUIT_GEAR = (101, 10, 122, 36)      # 회로선: 마디 → 희미한 톱니
CIRCUIT_LINK = (57, 55, 78, 68)        # 회로선: 마디 - 꺾인 선 - 마디


def cut_black(img, threshold=40):
    """검은 바탕 그림(시안)에서 가장자리와 이어진 검은 바탕만 투명하게 (안쪽 짙은 색은 남긴다)"""
    img = img.convert("RGBA")
    w, h = img.size
    p = img.load()
    seen = bytearray(w * h)
    q = deque([(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)])
    while q:
        x, y = q.popleft()
        if not (0 <= x < w and 0 <= y < h) or seen[y * w + x]:
            continue
        r, g, b, a = p[x, y]
        if a and r + g + b > threshold:
            continue
        seen[y * w + x] = 1
        p[x, y] = (0, 0, 0, 0)
        q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return img


def cut_outside(img, is_bg, step=6, close=5, keep=3):
    """시안 그림에서 물체 바깥 바탕만 투명하게. 안쪽에 바탕과 비슷한 어두운 곳이 있어도 남긴다:
    저해상도(step 배)로 물체 칸을 잡아 close 만큼 틈을 메우고, 가장자리와 이어진 빈 곳만 바깥으로 본다.
    메운 뒤 keep 만큼만 되돌려 깎아, 물체 바로 바깥의 짙은 외곽선은 남긴다 (keep=close 면 메운 만큼 다 깎음)."""
    from PIL import ImageFilter
    img = img.convert("RGBA")
    w, h = img.size
    px = img.load()
    lw, lh = w // step + 1, h // step + 1
    low = Image.new("L", (lw, lh), 0)
    lp = low.load()
    for y in range(0, h, step):
        for x in range(0, w, step):
            if not is_bg(px[x, y]):
                lp[x // step, y // step] = 255
    low = low.filter(ImageFilter.MaxFilter(close))
    lp = low.load()
    outside = bytearray(lw * lh)
    q = deque([(x, 0) for x in range(lw)] + [(x, lh - 1) for x in range(lw)]
              + [(0, y) for y in range(lh)] + [(lw - 1, y) for y in range(lh)])
    while q:
        x, y = q.popleft()
        if not (0 <= x < lw and 0 <= y < lh) or outside[y * lw + x] or lp[x, y]:
            continue
        outside[y * lw + x] = 1
        q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    inside = Image.new("L", (lw, lh), 0)
    ip = inside.load()
    for y in range(lh):
        for x in range(lw):
            if not outside[y * lw + x]:
                ip[x, y] = 255
    if keep > 1:
        inside = inside.filter(ImageFilter.MinFilter(keep))
    inside = inside.resize((w, h), Image.NEAREST)
    ins = inside.load()
    for y in range(h):
        for x in range(w):
            if not ins[x, y] and is_bg(px[x, y]):
                px[x, y] = (0, 0, 0, 0)
    return img


def shrink_art(img, box, scale, fill=0.5):
    """시안 그림의 box 범위를 scale 배로 줄인다 (칸마다 가운데 70% 의 불투명 픽셀 밝기 중앙값, fill 비율 이상 차지 않으면 투명.
    가는 선이 많은 그림은 fill 을 낮춰 선이 끊기지 않게 한다)"""
    x0, y0, x1, y1 = box
    c = 1 / scale
    tw, th = round((x1 - x0) * scale), round((y1 - y0) * scale)
    sp = img.load()
    out = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    for gy in range(th):
        for gx in range(tw):
            pts = [sp[min(x1 - 1, int(x0 + (gx + 0.15 + 0.7 * i / 4) * c)), min(y1 - 1, int(y0 + (gy + 0.15 + 0.7 * j / 4) * c))]
                   for i in range(5) for j in range(5)]
            solid = sorted((q for q in pts if q[3] > 128), key=lambda q: sum(q[:3]))
            if len(solid) > len(pts) * fill:
                out.putpixel((gx, gy), solid[len(solid) // 2][:3] + (255,))
    return out


def slot_box(row, col):
    return 7 + col * 18, 17 + row * 18


class Window:
    """rows 줄 상자 창 배경. 좌표는 창 기준(간판 여백 PAD_TOP 은 finish 에서 붙인다)."""

    def __init__(self, enh, rows, seed=910, enh_seam=False, pad_top=PAD_TOP):
        """enh_seam: 아래 가방 칸 부분을 강화 창 창칸 끝(y=71)부터 그대로 가져온다. 맨 위 네 줄에 강화 창 장비 칸 테
        끝자락과 오른쪽 아래 톱니 아랫부분이 딸려 오므로, 그 자리를 다른 테로 덮는 창(강화석 상점)만 True.
        기본은 그 네 줄(SEAM_ROWS)을 바탕 판으로 둔다.
        pad_top: 창 위로 넘치는 간판 자리 (guis.yml y_position = 13 + pad_top)"""
        self.pad = pad_top
        self.enh = enh
        self.rows = rows
        self.h = 114 + rows * 18
        self.top = 17 + rows * 18                 # 창 칸이 끝나는 y
        self.img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)
        rnd = random.Random(seed)
        for y in range(self.h):                   # 바탕 판 (+ 작은 점)
            for x in range(W):
                col, r = rnd.choice(PANEL), rnd.random()
                for speck, share in SPECKS:
                    if r < share:
                        col = speck
                        break
                    r -= share
                self.img.putpixel((x, y), col + (255,))
        for y in range(0, self.top, 18):          # 옆 기둥 (18px 주기로 이어 붙임)
            h = min(18, self.top - y)
            src_y = 18 + (y % 18)
            self.copy((W - PILLAR, src_y, W, src_y + h), (0, y), flip=True)    # 왼쪽 기둥 y 18~19 에 큰 톱니 꼬리가
            self.copy((W - PILLAR, src_y, W, src_y + h), (W - PILLAR, y))      # 섞여 있어 깨끗한 오른쪽을 뒤집어 쓴다
        self.copy((W - PILLAR, 0, W, 18), (0, 0), flip=True)          # 왼쪽 위 기둥: 강화 창 왼쪽 위는 큰 톱니 조각이 섞여
        self.copy((W - PILLAR, 0, W, 18), (W - PILLAR, 0))              # 있어 오른쪽 위 기둥을 뒤집어 쓴다
        for x in range(6, 170, 30):               # 위 구리 들보
            self.copy((22, 0, 22 + min(30, 170 - x), 7), (x, 0))
        self.copy((164, 0, 176, 8), (164, 0))     # 오른쪽 위 볼트
        seam = None if enh_seam else self.img.crop((PILLAR, self.top, W - PILLAR, self.top + SEAM_ROWS))
        self.copy((0, ENH_ROWS_END, 176, 168), (0, self.top))   # 아래 가방 칸 부분 그대로
        if seam:
            self.img.paste(seam, (PILLAR, self.top))

    def copy(self, box, to, flip=False):
        piece = self.enh.crop(box)
        if flip:
            piece = piece.transpose(Image.FLIP_LEFT_RIGHT)
        self.img.alpha_composite(piece, to)

    def frame(self, x0, y0, x1, y1):
        """칸 테두리 (x0,y0)-(x1,y1) 바깥에 강화 창 황동 테. 9분할: 모서리 3px, 변은 늘림. 여러 칸이면 칸 사이 구분선"""
        fx0, fy0, fx1, fy1 = 23, 15, 45, 37       # 강화 창 장비 칸 테 (칸 25..43 / 17..35)
        X0, Y0, X1, Y1 = x0 - 2, y0 - 2, x1 + 2, y1 + 2
        c = 3
        for (sx0, sx1, dx0, dx1) in ((fx0, fx0 + c, X0, X0 + c), (fx0 + c, fx1 - c, X0 + c, X1 - c),
                                     (fx1 - c, fx1, X1 - c, X1)):
            for (sy0, sy1, dy0, dy1) in ((fy0, fy0 + c, Y0, Y0 + c), (fy0 + c, fy1 - c, Y0 + c, Y1 - c),
                                         (fy1 - c, fy1, Y1 - c, Y1)):
                piece = self.enh.crop((sx0, sy0, sx1, sy1)).resize((dx1 - dx0, dy1 - dy0), Image.NEAREST)
                self.img.alpha_composite(piece, (dx0, dy0))
        for x in range(x0 + 18, x1 - 1, 18):
            self.d.line([(x, y0 + 1), (x, y1 - 2)], fill=DIVIDER)
        for y in range(y0 + 18, y1 - 1, 18):
            self.d.line([(x0 + 1, y), (x1 - 2, y)], fill=DIVIDER)

    def frame_slots(self, row, col, rows=1, cols=1):
        """row·col 칸부터 rows x cols 칸을 한 테로 묶는다"""
        x, y = slot_box(row, col)
        self.frame(x, y, x + 18 * cols, y + 18 * rows)

    def pipe_h(self, x0, x1, y):
        for i, c in enumerate(PIPE):
            self.d.line([(x0, y + i), (x1 - 1, y + i)], fill=c)

    def gear_small(self, x, y):
        self.copy(GEAR_SMALL, (x, y))

    def corner_gears(self, bottom_right=True, top_left=True):
        """왼쪽 위 큰 톱니 · 오른쪽 아래(창 칸 끝) 톱니 — 강화 창과 같은 자리
        (오른쪽 아래 칸을 쓰면 bottom_right=False, 간판 끝 톱니와 겹치면 top_left=False)"""
        if bottom_right:
            self.copy((158, ENH_ROWS_END - 10, 176, ENH_ROWS_END + 6), (158, self.top - 10))
        if top_left:
            self.copy((0, 0, 22, 22), (0, 0))
        else:
            self.copy((164, 0, 176, 8), (0, 0), flip=True)             # 톱니 대신 오른쪽 위와 같은 볼트 판

    def finish(self, sign_path=None, sign_bottom=None):
        """창을 PAD_TOP 만큼 내려 놓고, 간판(있으면)을 위 가운데에 단다. 간판 아래 끝 y = sign_bottom(창 기준)"""
        pad = self.pad
        out = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        out.alpha_composite(self.img.crop((0, 0, 256, 256 - pad)), (0, pad))
        if not sign_path:
            return out
        sign = Image.open(sign_path).convert("RGBA")
        sw, sh = sign.size
        sx, sy = (W - sw) // 2, pad + sign_bottom - sh
        a = sign.split()[3].load()
        op = out.load()
        for y in range(sh):                       # 그림자: 오른쪽 1px · 아래 2px 로 밀린 간판 모양
            for x in range(sw):
                if not a[x, y]:
                    continue
                for tx, ty in ((x + 1, y + 2), (x + 1, y + 1)):
                    if tx < sw and ty < sh and a[tx, ty]:
                        continue
                    X, Y = sx + tx, sy + ty
                    if Y >= pad and 0 <= X < W:
                        r, g, b, al = op[X, Y]
                        if al:
                            op[X, Y] = (int(r * SHADOW), int(g * SHADOW), int(b * SHADOW), al)
        out.alpha_composite(sign, (sx, sy))
        return out


class Preview:
    """배경 위에 아이템을 올려 3배로 키운 미리보기 (창 바깥은 게임 화면 회색)"""

    def __init__(self, bg, rows, jar_path, pad_top=PAD_TOP):
        self.pad = pad_top
        self.h = 114 + rows * 18 + pad_top
        self.img = bg.crop((0, 0, W, self.h)).copy()
        self.jar = zipfile.ZipFile(jar_path)
        self.labels = []

    def vanilla(self, name):
        return Image.open(io.BytesIO(self.jar.read("assets/minecraft/textures/item/%s.png" % name))).convert("RGBA")

    def item(self, row, col, icon, count=None):
        """창 칸(row, col)에 아이콘. 플레이어 가방 칸이면 row 를 창 줄 수 이상으로 (가방 칸은 13px 아래)"""
        x, y = slot_box(row, col)
        icon = icon.resize((16, 16), Image.NEAREST) if icon.size != (16, 16) else icon
        self.img.alpha_composite(icon, (x + 1, y + 1 + self.pad))
        if count:
            self.labels.append((x + 17, y + 17 + self.pad, str(count)))

    def save(self, path):
        bg = Image.new("RGBA", self.img.size, (110, 110, 110, 255))
        bg.alpha_composite(self.img)
        out = bg.resize((W * 3, self.h * 3), Image.NEAREST)
        d = ImageDraw.Draw(out)
        f = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", 24, index=2)
        for x, y, text in self.labels:
            d.text((x * 3, y * 3), text, font=f, fill=(255, 255, 255), anchor="rd")
        out.save(path)

"""
장신구 장착 창(3줄 상자 창) 배경 rustport:accessory_bg_{common,rare,epic,legendary}.
장착한 장신구 중 가장 높은 등급의 그림을 쓴다 (아무것도 없으면 common). 그림 원본: art/accessory_bg_<등급>.png
(별자리 원판 · 깃발 · 선반의 공방 그림).

창 테두리(황동 기둥 · 위 들보 · 모서리 톱니)와 아래 가방 · 단축바는 다른 BrassField 창과 같은 황동 창(gui_kit.Window) 그대로 두고,
테 안쪽 장신구 부분(ART_BOX)만 원본의 선반 아래 끝 위쪽 그림으로 채운다. 그 위에 사람 실루엣과 칸을 그린다:
  장신구 5칸 (강화 창 황동 테): 귀걸이 (0,2) · (0,6) / 목걸이 (1,4) 별자리 원판 가운데 / 반지 (2,2) · (2,6)
  세트 효과 (1,0) 왕관 · 종합 효과 (1,8) 크리스탈 — 아이콘 아이템(rustport:accessory_set · accessory_total)이 테까지 그려 배경에는 칸 없음
칸 번호는 com.brassfield.accessory.AccessoryGui 와 맞춘다.

사용: python3 tools/gui/make_accessory_gui.py <출력 폴더> [미리보기 png] [아이콘 폴더]
"""
import os
import sys

import math

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gui_kit as gk  # noqa: E402
import accessory_bg_unify as unify  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 176, 168
ART_BOX = (gk.PILLAR, 7, W - gk.PILLAR, 80)   # 그림이 들어가는 창 안쪽 (황동 기둥 · 위 들보 안, 가방 칸 테 바로 위까지)
GRADES = ["common", "rare", "epic", "legendary"]
SHELF = {"common": 599 / 1225, "rare": 376 / 706, "epic": 376 / 706, "legendary": 376 / 706}   # 원본에서 선반 아래 끝 비율
ART_CROP = (0.035, None, 0.965)    # 원본 바깥 기둥을 잘라 낸다 (왼쪽 x, -, 오른쪽 x 비율). 위는 같은 배율로 맞춰 자른다
WORK = 4                           # 원판을 지우고 다시 그리는 작업 배율
COMPASS_C = (88, 32)               # 원판 가운데 (창 좌표, 사람 머리 바로 아래)
COMPASS_R = 31                     # 바깥 호 반지름 (창 픽셀)
COMPASS_COLOR = {"common": (176, 116, 62), "rare": (80, 140, 230), "epic": (186, 96, 226), "legendary": (255, 196, 92)}
BODY = (66, 58, 49, 255)           # 사람 실루엣
BODY_EDGE = (30, 25, 20, 255)
BODY_HI = (84, 74, 62, 255)
SLOTS = {"earring_l": (0, 2), "earring_r": (0, 6), "necklace": (1, 4), "ring_l": (2, 2), "ring_r": (2, 6)}
# 효과 단추 (아이콘에 테가 있어 배경에는 칸을 그리지 않는다): 왼쪽 기둥 = 세트 효과(왕관), 오른쪽 기둥 = 종합 효과(크리스탈)
SET_SLOT, TOTAL_SLOT = (1, 0), (1, 8)


def work_art(grade):
    """등급 원본 → 창 안쪽 ART_BOX 의 WORK 배 크기. 가로 · 세로 같은 배율, 선반 아래 끝을 ART_BOX 아래에 맞춘다
    (원본마다 세로 길이 · 선반 높이가 달라 가로 · 세로를 따로 늘리면 소품 크기 · 높이가 등급마다 달라진다)"""
    src = Image.open(os.path.join(HERE, "art", "accessory_bg_%s.png" % grade)).convert("RGB")
    w, h = src.size
    x0, y0, x1, y1 = ART_BOX
    left, right = round(w * ART_CROP[0]), round(w * ART_CROP[2])
    crop_h = round((right - left) * (y1 - y0) / (x1 - x0))
    bottom = round(h * SHELF[grade])
    return src.crop((left, bottom - crop_h, right, bottom)).resize(((x1 - x0) * WORK, (y1 - y0) * WORK), Image.LANCZOS)


def art_top(grade):
    """창 안쪽 그림: 일반 그림을 네 등급 공통 바탕으로(accessory_bg_unify) 등급 색 · 빛만 바꾸고,
    원판은 지운 뒤 같은 모양(compass)을 등급 색으로 다시 그려 WORK 배 크기에서 줄인다"""
    x0, y0, x1, y1 = ART_BOX
    cx, cy, r = (COMPASS_C[0] - x0) * WORK, (COMPASS_C[1] - y0) * WORK, COMPASS_R * WORK
    common = erase_compass(work_art("common"), cx, cy, r)
    raw = work_art(grade)
    work = unify.unify(common, erase_compass(raw.copy(), cx, cy, r), raw, grade).convert("RGBA")
    compass(work, cx, cy, r, COMPASS_COLOR[grade], grade == "legendary")
    return work.resize((x1 - x0, y1 - y0), Image.LANCZOS)


def erase_compass(img, cx, cy, r):
    """원판 둘레(반지름 1.2r)에서 주변보다 밝은 선 · 별을 주변 중앙값으로 덮어 지운다 (벽돌 · 빛 번짐은 남는다)"""
    med = img.filter(ImageFilter.MedianFilter(21))
    px, mp = img.load(), med.load()
    w, h = img.size
    lim = (1.2 * r) ** 2
    for y in range(h):
        for x in range(w):
            if (x - cx) ** 2 + (y - cy) ** 2 > lim:
                continue
            a, b = px[x, y], mp[x, y]
            if sum(a) > sum(b) + 30 or max(a) - min(a) > max(b) - min(b) + 40:
                px[x, y] = b
    return img


def compass(img, cx, cy, r, color, glow):
    """원본(일반 그림) 원판을 본뜬 별자리 원판: 바깥 이중 호 · 가운데 고리 · 안 고리 · 동서남북 마름모 · 대각 화살표 · 8갈래 별 · 점"""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    c = color + (230,)
    faint = color + (120,)
    lw = max(2, round(r / 40))

    def ring(rad, col, width, gaps=0.0):
        """gaps: 동서남북 마름모 자리에서 끊는 각도(도)"""
        box = (cx - rad, cy - rad, cx + rad, cy + rad)
        if not gaps:
            d.ellipse(box, outline=col, width=width)
            return
        for k in range(4):
            start = k * 90 + gaps
            d.arc(box, start, start + 90 - 2 * gaps, fill=col, width=width)

    def pt(angle, rad):
        a = math.radians(angle)
        return cx + rad * math.cos(a), cy + rad * math.sin(a)

    ring(1.08 * r, faint, lw, 14)            # 가장 바깥 희미한 호
    ring(1.0 * r, c, lw + 1, 9)              # 바깥 호 (마름모 자리 끊김)
    ring(0.82 * r, c, lw)                    # 둘째 고리
    ring(0.68 * r, faint, lw, 20)            # 셋째 고리 (희미, 끊김)
    ring(0.45 * r, c, lw)                    # 안 고리
    for k in range(4):                       # 동서남북 속 빈 마름모 + 바깥 가시
        a = k * 90
        tip_o, tip_i, mid = pt(a, 1.16 * r), pt(a, 0.86 * r), 1.01 * r
        side1, side2 = pt(a + 4.5, mid), pt(a - 4.5, mid)
        d.polygon([tip_o, side1, tip_i, side2], outline=c, width=lw)
        d.line([pt(a, 1.16 * r), pt(a, 1.24 * r)], fill=faint, width=lw)
        d.line([pt(a, 0.5 * r), pt(a, 0.6 * r)], fill=c, width=lw)       # 안쪽 눈금
    for k in range(4):                       # 대각 화살표 (바깥쪽을 가리킴)
        a = 45 + k * 90
        d.line([pt(a, 0.58 * r), pt(a, 0.86 * r)], fill=c, width=lw)
        head = pt(a, 0.9 * r)
        d.polygon([head, pt(a + 4, 0.8 * r), pt(a - 4, 0.8 * r)], fill=c)
    for k in range(16):                      # 고리 위 작은 점
        a = 11.25 + k * 22.5
        x, y = pt(a, 0.75 * r)
        d.ellipse((x - lw, y - lw, x + lw, y + lw), fill=faint)
    star = []                                # 8갈래 별 (긴 동서남북 · 짧은 대각)
    for k in range(16):
        a = k * 22.5 - 90
        rad = 0.34 * r if k % 4 == 0 else 0.16 * r if k % 2 == 0 else 0.06 * r
        star.append(pt(a, rad))
    if glow:                                 # 전설: 별 둘레 빛
        g = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(g).ellipse((cx - 0.4 * r, cy - 0.4 * r, cx + 0.4 * r, cy + 0.4 * r), fill=color + (110,))
        img.alpha_composite(g.filter(ImageFilter.GaussianBlur(r * 0.15)))
    d.polygon(star, fill=tuple(min(255, v + 40) for v in color) + (255,))
    img.alpha_composite(layer)


def gear_only(piece):
    """강화 창에서 잘라 온 톱니 조각에서 바탕 판 픽셀을 지워 톱니(황동 + 바로 옆 검은 테)만 남긴다"""
    piece = piece.copy()
    px = piece.load()
    w, h = piece.size

    def brass(x, y):
        r, g, b, a = px[x, y]
        return a and r - b > 35 and r > 80
    keep = [[brass(x, y) for x in range(w)] for y in range(h)]
    for y in range(h):
        for x in range(w):
            if keep[y][x]:
                continue
            r, g, b, a = px[x, y]
            near = any(0 <= x + dx < w and 0 <= y + dy < h and keep[y + dy][x + dx]
                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if not (near and r + g + b < 60):
                px[x, y] = (0, 0, 0, 0)
    return piece


def gears(win, enh):
    """왼쪽 위 큰 톱니 · 오른쪽 아래(선반 끝) 톱니 — gui_kit.corner_gears 와 같은 자리, 바탕 없이"""
    win.img.alpha_composite(gear_only(enh.crop((0, 0, 22, 22))), (0, 0))
    e = gk.ENH_ROWS_END
    win.img.alpha_composite(gear_only(enh.crop((158, e - 10, 176, e + 6))), (158, win.top - 10))


def center(row, col):
    x, y = gk.slot_box(row, col)
    return x + 9, y + 9


def silhouette(d):
    """가운데 사람: 머리 (0,4) · 몸통은 선반까지 · 두 팔은 반지 칸 쪽으로, 귀에서 귀걸이 칸까지 황동 줄"""
    hx, hy = center(0, 4)
    for g, col in ((1, BODY_EDGE), (0, BODY)):
        d.ellipse((hx - 7 - g, hy - 8 - g, hx + 7 + g, hy + 6 + g), fill=col)               # 머리
        d.rectangle((hx - 3 - g, hy + 5 - g, hx + 3 + g, hy + 10 + g), fill=col)            # 목
        d.polygon([(hx - 14 - g, hy + 11 - g), (hx + 14 + g, hy + 11 - g),
                   (hx + 11 + g, hy + 49 + g), (hx - 11 - g, hy + 49 + g)], fill=col)       # 몸통 (선반 윗면까지)
        for s in (-1, 1):                                                                    # 어깨 → 손
            rx, ry = center(2, 4 + 2 * s)
            d.line([(hx + s * 12, hy + 14), (rx - s * 4, ry - 6)], fill=col, width=7 + 2 * g)
    for s in (-1, 1):                                                                        # 귀 → 귀걸이 칸
        ex, ey = center(0, 4 + 2 * s)
        d.line([(hx + s * 8, hy), (ex - s * 11, ey)], fill=(13, 10, 7, 255), width=3)
        d.line([(hx + s * 8, hy), (ex - s * 11, ey)], fill=(187, 127, 54, 255), width=1)
    d.line([(hx - 5, hy - 6), (hx - 1, hy - 7)], fill=BODY_HI)
    d.line([(hx - 12, hy + 12), (hx + 12, hy + 12)], fill=BODY_HI)


def sunken(img, x, y):
    """그림 위에 어둡게 파인 칸 (18 x 18 상자): 바탕 어둡게 + 위 · 왼쪽 그늘 + 아래 · 오른쪽 빛"""
    box = img.crop((x, y, x + 18, y + 18))
    box.alpha_composite(Image.new("RGBA", box.size, (10, 7, 5, 150)))
    d = ImageDraw.Draw(box)
    d.line((0, 0, 17, 0), fill=(6, 4, 3, 255))
    d.line((0, 0, 0, 17), fill=(6, 4, 3, 255))
    d.line((1, 17, 17, 17), fill=(120, 92, 60, 200))
    d.line((17, 1, 17, 17), fill=(120, 92, 60, 200))
    img.alpha_composite(box, (x, y))


def build(grade):
    enh = Image.open(os.path.join(HERE, "art", "enhance_bg_3row.png")).convert("RGBA")
    win = gk.Window(enh, 3, pad_top=0)             # 황동 테(기둥 · 들보) · 아래 가방 부분은 그대로
    win.img.paste(art_top(grade), ART_BOX[:2])
    win.d = ImageDraw.Draw(win.img)
    silhouette(win.d)
    gears(win, enh)
    for row, col in SLOTS.values():
        x, y = gk.slot_box(row, col)
        sunken(win.img, x, y)
        win.frame_slots(row, col)
    return win.img


def preview(bgs, path, icons=None):
    names = {"earring_l": "combat_earring_a_epic_2", "earring_r": "combat_earring_b_rare_1",
             "necklace": "combat_necklace_legendary_3", "ring_l": "combat_ring_a_common_0"}
    buttons = {SET_SLOT: "accessory_set", TOTAL_SLOT: "accessory_total"}
    sheet = Image.new("RGBA", (len(bgs) * (W * 3 + 12) + 12, H * 3 + 24), (60, 60, 60, 255))
    for i, bg in enumerate(bgs):
        shot = Image.new("RGBA", (W, H), (110, 110, 110, 255))
        shot.alpha_composite(bg.crop((0, 0, W, H)))
        big = shot.resize((W * 3, H * 3), Image.NEAREST)
        for (row, col), name in buttons.items():
            x, y = gk.slot_box(row, col)
            big.alpha_composite(Image.open(os.path.join(HERE, "art", name + ".png")).convert("RGBA").resize((48, 48), Image.NEAREST),
                                ((x + 1) * 3, (y + 1) * 3))
        if icons:
            for key, name in names.items():
                p = os.path.join(icons, name + ".png")
                if os.path.exists(p):
                    x, y = gk.slot_box(*SLOTS[key])
                    big.alpha_composite(Image.open(p).convert("RGBA").resize((48, 48), Image.NEAREST), ((x + 1) * 3, (y + 1) * 3))
        sheet.alpha_composite(big, (12 + i * (W * 3 + 12), 12))
    sheet.save(path)


if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    made = []
    for grade in GRADES:
        bg = build(grade)
        bg.save(os.path.join(out, "accessory_bg_%s.png" % grade))
        made.append(bg)
    if len(sys.argv) > 2:
        preview(made, sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)

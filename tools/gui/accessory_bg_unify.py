"""
장신구 창 등급 배경 통일: 일반(common) 그림 하나를 네 등급 공통 바탕으로 쓰고, 등급마다 색 · 장식만 바꾼다.
(등급 원본마다 깃발 · 크리스탈 · 천체기 · 책 위치와 크기가 조금씩 달라서, 소품은 일반 그림 것으로 통일)

작업은 make_accessory_gui 의 4배 작업 크기(창 안쪽 162 x 73 의 4배)에서 한다. 좌표 = 작업 좌표.
  1. 벽 색감: 어둡고 채도 낮은 벽돌 · 기둥을 등급 색으로 물들인다 (레어 남색 · 영웅 보라 · 전설 금빛)
  2. 크리스탈 색 바꾸기 (일반 그림의 유리관 자리 상자 안, 남보라 색만). 깃발은 등급 원본 깃발(천 · 테 · 문양)을 일반 그림 깃발 자리 크기로 옮긴다
  3. 빛: 등급 원본의 넓은 빛(크게 흐린 그림)이 일반 그림보다 밝은 만큼 더한다 (선반 빛 · 전설 광채)
  4. 등급 장식: 원본에서 주변보다 밝고 채도 높은 가는 선(영웅 보라 기운 · 전설 금빛 균열)을 소품 자리 밖에서만 옮겨 오고,
     (커튼 · 왕관은 원본마다 자리가 달라 옮기면 조각이 지저분하게 붙어 넣지 않는다 — curtains · crown 함수는 남겨 둠)
"""
import colorsys

from PIL import Image, ImageChops, ImageFilter

TONE = {"rare": (0.5, 0.74, 1.45), "epic": (1.05, 0.72, 1.3), "legendary": (1.32, 1.04, 0.62)}
CRYSTAL_HUE = {"rare": 0.58, "epic": 0.8, "legendary": 0.11}
# 일반 그림(작업 좌표) 소품 자리
BANNERS = [(20, 0, 85, 110), (562, 0, 625, 110)]
# 깃발 (작업 좌표 x0, y0, x1, 끝 y): 일반 그림 자리 · 등급 원본 자리. 등급 깃발(천 색 · 테 · 문양)을 통째로 일반 그림 자리 크기로 옮긴다
BANNER_AT = [(28, 0, 79, 106), (571, 0, 621, 106)]
BANNER_SRC = {"rare": [(38, 0, 91, 94), (556, 0, 611, 94)],
              "epic": [(45, 0, 103, 93), (548, 0, 606, 93)],
              "legendary": [(45, 0, 109, 101), (538, 0, 602, 105)]}
TIP = 0.74                                          # 깃발 V 끝이 시작하는 높이 비율
CRYSTAL = (520, 170, 580, 245)
# 등급 원본(작업 좌표)에서 장식을 옮기지 않을 소품 자리 (깃발 · 천체기 · 책 · 촛불 · 유리관 · 물약)
PROPS = [(30, 0, 115, 115), (530, 0, 620, 115), (40, 100, 150, 215), (0, 170, 180, 292), (510, 150, 648, 292)]
SIDE = 70                                          # 커튼을 옮겨 오는 양옆 띠 폭
CROWN = (230, 0, 420, 50)


def _hsv(px):
    r, g, b = px[:3]
    return colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)


def _rgb(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return round(r * 255), round(g * 255), round(b * 255)


def _inside(x, y, boxes):
    return any(x0 <= x < x1 and y0 <= y < y1 for x0, y0, x1, y1 in boxes)


def tint_walls(img, grade):
    tone = TONE.get(grade)
    if not tone:
        return img
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y][:3]
            hh, s, v = _hsv((r, g, b))
            a = max(0.0, min(1.0, (1 - v * 1.6))) * (1 - min(1.0, s * 1.5)) * 0.9
            if a <= 0:
                continue
            lum = (r + g + b) / 3
            t = [min(255, lum * k) for k in tone]
            px[x, y] = tuple(round(c * (1 - a) + tc * a) for c, tc in zip((r, g, b), t)) + px[x, y][3:]
    return img


def recolor(img, boxes, hue_lo, hue_hi, new_hue, min_s=0.2, boost=1.0):
    px = img.load()
    for x0, y0, x1, y1 in boxes:
        for y in range(y0, y1):
            for x in range(x0, x1):
                h, s, v = _hsv(px[x, y])
                if s >= min_s and hue_lo <= h <= hue_hi:
                    px[x, y] = _rgb(new_hue, s, min(1.0, v * boost)) + px[x, y][3:]
    return img


def add_light(base, grade_img, radius=22, gain=1.0):
    lb = base.filter(ImageFilter.GaussianBlur(radius))
    lg = grade_img.filter(ImageFilter.GaussianBlur(radius))
    glow = ImageChops.subtract(lg, lb)
    if gain != 1.0:
        glow = glow.point(lambda v: min(255, round(v * gain)))
    return ImageChops.add(base, glow)


VEIN_THRESHOLD = {"epic": 16, "legendary": 22}
LIGHT_GAIN = {"legendary": 2.0}                    # 원본 빛을 더하는 세기 (기본 1.1)
WARM = {"legendary": (1.28, 1.14, 0.86)}           # 마지막 전체 밝기 · 색 (전설: 밝은 금빛)
SATURATION = {"common": 0.75}                      # 일반: 채도를 조금 빼 차분하게 (등급이 오를수록 화려해 보이도록)


def veins(base, grade_img, keep_props=PROPS, threshold=38):
    """원본에서 주변(중앙값)보다 밝고 채도 높은 가는 선만 소품 자리 밖에서 옮긴다"""
    med = grade_img.filter(ImageFilter.MedianFilter(9))
    gp, mp, bp = grade_img.load(), med.load(), base.load()
    w, h = base.size
    for y in range(h):
        for x in range(w):
            if _inside(x, y, keep_props):
                continue
            a, m = gp[x, y], mp[x, y]
            if sum(a[:3]) > sum(m[:3]) + threshold * 3 and _hsv(a)[1] > 0.35:
                bp[x, y] = a[:3] + bp[x, y][3:]
    return base


def curtains(base, grade_img, grade):
    """양옆 띠에서 커튼 색(영웅: 짙은 보라 천, 전설: 금빛 천) 픽셀만 옮긴다 (깃발 자리는 빼고)"""
    gp, bp = grade_img.load(), base.load()
    w, h = base.size
    for y in range(0, h - 40):
        for x in list(range(0, SIDE)) + list(range(w - SIDE, w)):
            if _inside(x, y, BANNERS):
                continue
            hh, s, v = _hsv(gp[x, y])
            if grade == "epic" and 0.72 <= hh <= 0.92 and s > 0.3 and 0.12 < v < 0.6:
                bp[x, y] = gp[x, y][:3] + bp[x, y][3:]
            elif grade == "legendary" and 0.06 <= hh <= 0.16 and s > 0.45 and v > 0.45:
                bp[x, y] = gp[x, y][:3] + bp[x, y][3:]
    return base


def crown(base, raw_grade):
    """전설 원판 위 왕관 · 날개: 원판을 지우기 전 원본에서 밝은 금빛 픽셀만"""
    gp, bp = raw_grade.load(), base.load()
    x0, y0, x1, y1 = CROWN
    for y in range(y0, y1):
        for x in range(x0, x1):
            h, s, v = _hsv(gp[x, y])
            if 0.06 <= h <= 0.17 and s > 0.35 and v > 0.55:
                bp[x, y] = gp[x, y][:3] + bp[x, y][3:]
    return base


def banners(base, grade_img, grade):
    """등급 원본 깃발을 일반 그림 깃발 자리 크기로 줄여 깃발 모양(사각 + V 끝) 안만 덮는다"""
    from PIL import ImageDraw
    for (sx0, sy0, sx1, sy1), (dx0, dy0, dx1, dy1) in zip(BANNER_SRC[grade], BANNER_AT):
        w, h = dx1 - dx0, dy1 - dy0
        piece = grade_img.crop((sx0, sy0, sx1, sy1)).resize((w, h), Image.LANCZOS)
        mask = Image.new("L", (w, h), 0)
        ImageDraw.Draw(mask).polygon([(0, 0), (w - 1, 0), (w - 1, h * TIP), (w / 2, h - 1), (0, h * TIP)], fill=255)
        base.paste(piece, (dx0, dy0), mask)
    return base


def unify(common, grade_img, raw_grade, grade):
    """common: 일반 그림(원판 지움), grade_img: 그 등급 원본(원판 지움), raw_grade: 원판 지우기 전 원본 — 모두 작업 크기 RGB"""
    out = common.copy()
    if grade == "common":
        from PIL import ImageEnhance
        return ImageEnhance.Color(out).enhance(SATURATION["common"])
    out = tint_walls(out, grade)
    recolor(out, [CRYSTAL], 0.55, 0.85, CRYSTAL_HUE[grade], min_s=0.15, boost=1.1)
    out = add_light(out, grade_img, gain=LIGHT_GAIN.get(grade, 1.1))
    if grade in VEIN_THRESHOLD:
        out = veins(out, grade_img, threshold=VEIN_THRESHOLD[grade])
    if grade in WARM:
        k = WARM[grade]
        r, g, b = out.split()[:3]
        out = Image.merge("RGB", [ch.point(lambda v, f=f: min(255, round(v * f))) for ch, f in zip((r, g, b), k)])
    return banners(out, raw_grade, grade)

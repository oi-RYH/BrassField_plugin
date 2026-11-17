"""
씨앗 봉투 아이템 아이콘 16x16: 사용자 시안(art/seed_packets.png, 봉투 13개)을 그대로 줄이고,
작물이 칠해진 칸만 명도·채도 대비를 살짝 올려 종이에 묻히지 않게 한다 (형태·봉투는 그대로).
  1) 시안에서 봉투마다 바탕을 지우고 정사각형으로 잘라 16x16 으로 줄인다 (gui_kit.shrink_art)
  2) 작물 칸 찾기: 시안 봉투 몸통에서 종이색(크라프트·크림)과 확실히 다른 곳 = 작물. 작물 안쪽의 종이 비슷한 색(양파 단면 등)은
     둘레를 메워 포함한다. 16x16 칸마다 그 비율이 40% 이상이면 작물 칸.
  3) 작물 칸만: 채도 x SAT, 명도는 작물 칸 평균을 기준으로 차이를 x CONTRAST.

사용: python3 tools/gui/make_seed_icons.py <출력 폴더> [미리보기.png]   (파일 이름: <작물>_seeds_icon.png)
"""
import colorsys
import os
import sys
from collections import deque

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from gui_kit import shrink_art

ART = os.path.join(os.path.dirname(os.path.abspath(__file__)), "art", "seed_packets.png")
NAMES = ["rice", "onion", "tomato", "cabbage", "chinese_cabbage", "corn", "eggplant", "garlic", "grape", "hop",
         "pepper", "pineapple", "pitaya"]                          # 시안 순서 (왼쪽 위부터)
KOREAN = ["쌀", "양파", "토마토", "양배추", "배추", "옥수수", "가지", "마늘", "포도", "홉", "고추", "파인애플", "용과"]
PAPER = [(236, 188, 124), (250, 220, 166)]                         # 시안 봉투 종이색
PAPER_DIST = 34
BODY = (0.12, 0.30, 0.88, 0.86)                                    # 봉투 안 작물이 있는 몸통 범위 (비율)
SAT, CONTRAST = 1.18, 1.3


def find_packets(src):
    """바탕색과 다른 부분을 줄·칸 단위로 묶어 봉투 13개 범위를 찾는다 (아래 이름 글자 줄은 높이로 거른다)"""
    px = src.load()
    w, h = src.size
    bg = px[5, 5][:3]
    fg = lambda p: sum(abs(a - b) for a, b in zip(p[:3], bg)) > 45
    rows = [y for y in range(h) if sum(1 for x in range(0, w, 3) if fg(px[x, y])) > 20]
    bands, s, pv = [], rows[0], rows[0]
    for y in rows[1:] + [10 ** 6]:
        if y - pv > 3:
            if pv - s > 100:                                       # 봉투 줄 (이름 글자 줄은 낮다)
                bands.append((s, pv + 1))
            s = y
        pv = y
    boxes = []
    for y0, y1 in bands:
        cols = [x for x in range(w) if sum(1 for y in range(y0, y1, 3) if fg(px[x, y])) > 5]
        s, pv = cols[0], cols[0]
        for x in cols[1:] + [10 ** 6]:
            if x - pv > 5:
                boxes.append((s, y0, pv + 1, y1))
                s = x
            pv = x
    return boxes, bg


def cut(src, box, bg):
    """봉투를 정사각형으로 자르고 가장자리와 이어진 바탕만 투명하게"""
    x0, y0, x1, y1 = box
    side = max(x1 - x0, y1 - y0) + 4
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    c = src.crop((int(cx - side / 2), int(cy - side / 2), int(cx + side / 2), int(cy + side / 2))).copy()
    p = c.load()
    w, h = c.size
    seen = set()
    q = deque([(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)])
    while q:
        x, y = q.popleft()
        if (x, y) in seen or not (0 <= x < w and 0 <= y < h):
            continue
        if sum(abs(a - b) for a, b in zip(p[x, y][:3], bg)) > 45:
            continue
        seen.add((x, y))
        p[x, y] = (0, 0, 0, 0)
        q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return c


def crop_mask(packet):
    """시안 크기 봉투에서 작물 영역 (L 이미지, 255 = 작물)"""
    w, h = packet.size
    p = packet.load()
    m = Image.new("L", (w, h), 0)
    mp = m.load()
    bx0, by0, bx1, by1 = int(w * BODY[0]), int(h * BODY[1]), int(w * BODY[2]), int(h * BODY[3])
    for y in range(by0, by1):
        for x in range(bx0, bx1):
            c = p[x, y]
            if c[3] and min(sum(abs(a - b) for a, b in zip(c[:3], q)) for q in PAPER) > PAPER_DIST:
                mp[x, y] = 255
    return m.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MinFilter(9))   # 작물 안쪽 메우기


def enhance(icon, mask, scale):
    """16x16 아이콘의 작물 칸만 채도·명도 대비를 올린다"""
    w, h = icon.size
    p = icon.load()
    mp = mask.load()
    c = 1 / scale
    cells = []
    for y in range(h):
        for x in range(w):
            if not p[x, y][3]:
                continue
            hits = sum(1 for i in range(4) for j in range(4)
                       if mp[min(mask.width - 1, int((x + 0.125 + i / 4) * c)), min(mask.height - 1, int((y + 0.125 + j / 4) * c))])
            if hits >= 7:                                          # 40% 이상
                cells.append((x, y))
    if not cells:
        return icon
    hsv = {xy: colorsys.rgb_to_hsv(*[v / 255 for v in p[xy][:3]]) for xy in cells}
    mean_v = sum(v for _, _, v in hsv.values()) / len(hsv)
    for xy, (hh, ss, vv) in hsv.items():
        ss = min(1.0, ss * SAT)
        vv = max(0.0, min(1.0, mean_v + (vv - mean_v) * CONTRAST))
        r, g, b = colorsys.hsv_to_rgb(hh, ss, vv)
        p[xy] = (round(r * 255), round(g * 255), round(b * 255), 255)
    return icon


def build():
    src = Image.open(ART).convert("RGBA")
    boxes, bg = find_packets(src)
    assert len(boxes) == len(NAMES), len(boxes)
    plain, out = {}, {}
    for name, box in zip(NAMES, boxes):
        packet = cut(src, box, bg)
        scale = 16 / packet.width
        icon = shrink_art(packet, (0, 0, packet.width, packet.height), scale)
        plain[name] = icon.copy()
        out[name] = enhance(icon, crop_mask(packet), scale)
    return plain, out


if __name__ == "__main__":
    plain, out = build()
    for name, icon in out.items():
        icon.save(os.path.join(sys.argv[1], name + "_seeds_icon.png"))
    if len(sys.argv) > 2:                                          # 미리보기: 축소본 / 대비 조절 / 실제 크기
        f = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", 18, index=6)
        k, cell = 8, 16 * 8 + 14
        sheet = Image.new("RGBA", (len(NAMES) * cell + 10, 2 * (cell + 30) + 90), (40, 40, 40, 255))
        d = ImageDraw.Draw(sheet)
        for j, (label, icons) in enumerate((("축소본 16×16", plain), ("작물 대비 조절 16×16", out))):
            y = 30 + j * (cell + 30)
            d.text((10, y - 26), label, font=f, fill=(230, 220, 200))
            for i, n in enumerate(NAMES):
                g = Image.new("RGBA", (16, 16), (139, 139, 139, 255))
                g.alpha_composite(icons[n])
                sheet.alpha_composite(g.resize((16 * k, 16 * k), Image.NEAREST), (10 + i * cell, y))
        y = 30 + 2 * (cell + 30)
        d.text((10, y - 26), "실제 크기(2배)", font=f, fill=(230, 220, 200))
        for i, n in enumerate(NAMES):
            g = Image.new("RGBA", (18, 18), (139, 139, 139, 255))
            g.alpha_composite(out[n], (1, 1))
            sheet.alpha_composite(g.resize((36, 36), Image.NEAREST), (10 + i * cell, y))
            d.text((52 + i * cell, y + 6), KOREAN[i], font=f, fill=(230, 220, 200))
        sheet.save(sys.argv[2])
    print("ok")

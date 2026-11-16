"""
강화석 상점 간판: 사용자 시안(art/sign_stone_shop.png, 흰 바탕 위 갈색 띠 위의 간판)에서 간판만 떼어 폭 N 픽셀로 줄인다.
1) 흰색·띠 갈색(51,31,26 근처)을 배경으로 보고, 테두리 틈을 메운 저해상도 마스크로 바깥만 지운다
   (간판 안쪽 바탕이 띠 색과 비슷해서, 바깥에서 이어진 부분만 지워야 안쪽이 남는다).
2) 간판 범위를 잘라 칸마다 가운데 70% 의 불투명 픽셀 밝기 중앙값으로 줄인다. 절반 넘게 비면 투명.

사용: python3 tools/gui/make_sign.py <시안.png> <출력.png> [폭=120]
"""
import sys
from collections import deque

from PIL import Image, ImageFilter

BAND = (51, 31, 26)
S = 6                                    # 마스크 저해상도 배율


def is_bg(p):
    return sum(abs(a - b) for a, b in zip(p, BAND)) < 30 or min(p) > 225


def cut(src):
    w, h = src.size
    px = src.load()
    lw, lh = w // S + 1, h // S + 1
    low = Image.new("L", (lw, lh), 0)
    lp = low.load()
    for y in range(0, h, S):
        for x in range(0, w, S):
            if not is_bg(px[x, y]):
                lp[x // S, y // S] = 255
    low = low.filter(ImageFilter.MaxFilter(5))           # 테두리 틈 메우기
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
    inside = inside.filter(ImageFilter.MinFilter(5)).resize((w, h), Image.NEAREST)   # 메운 만큼 다시 깎기
    ins = inside.load()
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    op = out.load()
    for y in range(h):
        for x in range(w):
            p = px[x, y]
            if (ins[x, y] and min(p) <= 225) or not is_bg(p):
                op[x, y] = p + (255,)
    a = out.split()[3].load()                            # 간판 범위 (가장자리 실선 같은 부스러기 제외)
    cols = [x for x in range(w) if sum(1 for y in range(0, h, 2) if a[x, y]) > 40]
    rows = [y for y in range(h) if sum(1 for x in range(0, w, 2) if a[x, y]) > 40]
    return out.crop((cols[0], rows[0], cols[-1] + 1, rows[-1] + 1))


def shrink(sign, tw):
    sw, sh = sign.size
    sp = sign.load()
    c = sw / tw
    th = round(sh / c)
    out = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    for gy in range(th):
        for gx in range(tw):
            pts = [sp[min(sw - 1, int((gx + 0.15 + 0.7 * i / 4) * c)), min(sh - 1, int((gy + 0.15 + 0.7 * j / 4) * c))]
                   for i in range(5) for j in range(5)]
            solid = sorted((p for p in pts if p[3]), key=lambda p: sum(p[:3]))
            if len(solid) * 2 > len(pts):
                out.putpixel((gx, gy), solid[len(solid) // 2])
    return out


if __name__ == "__main__":
    width = int(sys.argv[3]) if len(sys.argv) > 3 else 120
    out = shrink(cut(Image.open(sys.argv[1]).convert("RGB")), width)
    out.save(sys.argv[2])
    print(out.size)

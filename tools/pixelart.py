"""
픽셀아트 공용 도구: 명암 단계 색, 구 명암, 잎·줄기 선, 색 외곽선. (작물·요리 그림 공용)

- 색은 단색 대신 어둠→밝음 단계(ramp)로, 빛은 왼쪽 위에서.
- 외곽선은 검정 대신 이웃 색을 어둡게 한 색.
"""
import math

T = (0, 0, 0, 0)
LIGHT = (-0.55, -0.65, 0.52)   # 빛 방향 (왼쪽 위 앞)


def rgb(r, g, b, a=255):
    return (r, g, b, a)


def mix(c1, c2, k):
    return tuple(int(round(c1[i] + (c2[i] - c1[i]) * k)) for i in range(3)) + (255,)


def ramp_color(ramp, v):
    """0(어둠)~1(밝음) → 색 (단계 사이는 계단식: 픽셀아트 느낌 유지)"""
    v = max(0.0, min(0.999, v))
    return ramp[int(v * len(ramp))]


def blank(size=16):
    return [[T] * size for _ in range(size)]


def outline(img, factor=0.42):
    """투명 칸 중 불투명 칸과 맞닿은 곳을, 그 이웃 색을 어둡게 한 색으로 칠한다 (검정 외곽선 대신)"""
    h, w = len(img), len(img[0])
    out = [row[:] for row in img]
    for y in range(h):
        for x in range(w):
            if img[y][x][3]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and img[ny][nx][3]:
                    c = img[ny][nx]
                    out[y][x] = (int(c[0] * factor), int(c[1] * factor), int(c[2] * factor), 255)
                    break
    return out


def sphere(img, cx, cy, rx, ry, ramp, taper=0.0, stripes=0, stripe_dark=0.18):
    """구 명암 타원. taper>0 이면 위로 갈수록 좁아짐(양파 모양). stripes: 세로 껍질 결 수"""
    lx, ly, lz = LIGHT
    for y in range(len(img)):
        for x in range(len(img[0])):
            fy = (y + 0.5 - cy) / ry
            width = rx * (1 - taper * max(0.0, -fy) ** 1.6)
            if width <= 0:
                continue
            fx = (x + 0.5 - cx) / width
            d = fx * fx + fy * fy
            if d > 1:
                continue
            nz = math.sqrt(1 - d)
            v = 0.5 + 0.5 * (fx * lx + fy * ly + nz * lz)
            v = max(0.0, min(1.0, v * 1.05))
            if stripes and abs(math.sin(math.asin(max(-1, min(1, fx))) * stripes)) < 0.22 and d < 0.92:
                v -= stripe_dark
            img[y][x] = ramp_color(ramp, v)


def thick_line(img, pts, ramp, width=1, base_dark=0.15, tip_light=0.85, side_light=True):
    """잎·줄기: 점 목록을 잇고, 뿌리(첫 점) 쪽 어둡고 끝으로 갈수록 밝게. width=2면 왼쪽 줄을 밝게(통 잎 느낌)"""
    total = len(pts) - 1
    for i in range(total):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        steps = max(abs(x1 - x0), abs(y1 - y0), 1) * 2
        for s in range(steps + 1):
            t = (i + s / steps) / total
            x = x0 + (x1 - x0) * s / steps
            y = y0 + (y1 - y0) * s / steps
            v = base_dark + (tip_light - base_dark) * t
            for k in range(width):
                px, py = int(round(x)) + k, int(round(y))
                if 0 <= px < len(img[0]) and 0 <= py < len(img):
                    shade = v + (0.12 if (side_light and width > 1 and k == 0) else 0) - (0.08 if k == width - 1 and width > 1 else 0)
                    img[py][px] = ramp_color(ramp, shade)




def ellipse(img, cx, cy, rx, ry, color_fn):
    """타원 안을 color_fn(fx, fy)로 칠한다. fx, fy는 중심 기준 -1~1"""
    for y in range(len(img)):
        for x in range(len(img[0])):
            fx = (x + 0.5 - cx) / rx
            fy = (y + 0.5 - cy) / ry
            if fx * fx + fy * fy <= 1:
                c = color_fn(fx, fy)
                if c is not None:
                    img[y][x] = c


def put(img, x, y, color):
    if 0 <= x < len(img[0]) and 0 <= y < len(img):
        img[y][x] = color

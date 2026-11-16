"""
강화석 아이템 아이콘 24x24 (시안 art/stones_concept4.png 를 바탕으로 다시 그린 픽셀 그림).
  생김새는 가운데 기준 대칭 — 부품 영역을 (|dx|, |dy|) 의 함수로만 정한다.
  빛·그림자는 대칭이 아니다 — 왼쪽 위 광원. 픽셀 그림처럼 면마다 정해진 단계로 칠한다:
    바깥을 향한 면은 왼쪽 위가 가장 밝고 오른쪽 아래가 가장 어둡다, 안쪽을 향한 면(고리 안쪽)은 반대.
    보석은 둥근 면 + 왼쪽 위 작은 반사광 + 오른쪽 아래 안쪽 굴절광 + 가운데 별빛.
  하급은 둥근 모양. 보석은 깎은 보석(윗면 + 둘레 8면 + 반사광·굴절광)으로 칠한다.
  중급 구슬은 시안처럼 매끈한 구슬(붉은 둘레·환한 가운데·흰 반사광).
  상급의 리본(아래)은 시안대로 둔 장식이라 대칭에서 뺀다.
  색은 시안에서 뽑은 색만 쓴다. 크기(외곽선 포함): 하급 16 · 중급 20 · 상급 24

사용: python3 tools/hud/draw_stones24.py <출력 폴더>
"""
import math
import os
import sys

from PIL import Image

N = 24
C = (N - 1) / 2
O = (48, 26, 14)
M = [None, (131, 37, 2), (167, 75, 4), (201, 96, 12), (224, 121, 19), (242, 146, 26), (251, 176, 33),
     (251, 202, 88), (253, 230, 158)]                   # 황동 1(어두움) ~ 8(밝음)
STONE = [(59, 44, 41), (73, 57, 53), (99, 76, 68), (121, 97, 90)]
DOT = (97, 48, 33)
GLOW = (253, 230, 158)
STAR = (249, 179, 52)
ORANGE = [(217, 28, 1), (227, 78, 4), (245, 126, 11), (252, 152, 13)]
RED = [(143, 2, 2), (206, 5, 4), (242, 33, 11)]
RED_SPEC = (219, 85, 13)


def face(dx, dy):
    """바깥을 향한 면의 밝기 단계: 왼쪽 위 3, 오른쪽 위·왼쪽 아래 2, 오른쪽 아래 1"""
    return 3 if dx < 0 and dy < 0 else (1 if dx > 0 and dy > 0 else 2)


def metal(dx, dy, inner=False):
    """둥근 황동 테: 바깥 면은 왼쪽 위로 갈수록 밝고(7→3), 안쪽 면은 반대"""
    lit = -(dx + dy) / ((math.hypot(dx, dy) or 1) * 1.414)
    if inner:
        lit = -lit
    return M[7] if lit > 0.6 else M[6] if lit > 0.2 else M[5] if lit > -0.2 else M[4] if lit > -0.6 else M[3]


def orb(body, dx, dy, r, spec, star=0, arm=STAR):
    """둥근 보석. body 어두운→밝은"""
    if star and abs(dx) < 1 and abs(dy) < 1:
        return GLOW
    if star and ((abs(dx) < 1 and abs(dy) < star) or (abs(dy) < 1 and abs(dx) < star)):
        return arm
    if spec and -r * 0.75 < dx < -r * 0.2 and -r * 0.75 < dy < -r * 0.2 and abs(dx - dy) < 1.2:
        return spec                                      # 왼쪽 위 반사광 (짧은 사선)
    d = math.hypot(dx, dy)
    lit = -(dx + dy) / (r * 1.41)                         # 왼쪽 위일수록 +
    if d > r * 0.55 and lit < -0.45:
        return body[-2]                                  # 오른쪽 아래 안쪽 굴절광
    v = 0.55 * lit + 0.6 * (1 - d / r) + 0.25
    return body[int(min(0.999, max(0.0, v)) * len(body))]


def cut_gem(body, dx, dy, r, spec, sparkle=GLOW, star=0, arm=STAR):
    """깎은 보석: 가운데 윗면(평평, 밝음) + 둘레 8면(면마다 빛 받는 정도가 다름)
    + 왼쪽 위 반사광 + 오른쪽 아래 안쪽 굴절광 + 가장자리 어두움. body 어두운→밝은"""
    if star and abs(dx) < 1 and abs(dy) < 1:
        return GLOW
    if star and ((abs(dx) < 1 and abs(dy) < star) or (abs(dy) < 1 and abs(dx) < star)):
        return arm
    d = math.hypot(dx, dy)
    k = len(body) - 1
    if d <= r * 0.45:                                    # 윗면
        if spec and dx < 0 and dy < 0 and d > r * 0.15:
            return spec                                  # 윗면 왼쪽 위 반사광
        return body[k] if dx + dy < 0 else body[k - 1]
    ang = math.atan2(dy, dx)
    sector = round(ang / (math.pi / 4)) * (math.pi / 4)  # 8면
    lit = -(math.cos(sector) + math.sin(sector)) / 1.414  # 면이 왼쪽 위를 볼수록 +
    if lit < -0.5 and d < r * 0.85:
        return body[k - 1]                               # 오른쪽 아래 안쪽 굴절광
    if sparkle and lit > 0.9 and r * 0.6 < d < r * 0.8:
        return sparkle                                   # 둘레 면의 반짝임 한 점
    i = 1 + round((lit + 1) / 2 * (k - 2))
    if d > r * 0.85:
        i -= 1                                           # 가장자리
    return body[max(0, min(k, i))]


def glossy(body, dx, dy, r):
    """매끈한 구슬 (시안 중급): 둘레는 붉고 어둡게(오른쪽 아래 둘레는 굴절광으로 밝게),
    안쪽은 가운데 조금 아래가 가장 환하고, 왼쪽 위에 또렷한 흰 반사광. body 어두운→밝은"""
    if abs(dx + r * 0.42) < 0.6 and abs(dy + r * 0.42) < 0.6:
        return GLOW                                      # 반사광 가운데
    if abs(dx + r * 0.42) < 1.6 and abs(dy + r * 0.42) < 1.6 and abs(dx - dy) < 1.1 and dx + dy < -r * 0.6:
        return (251, 217, 135)                           # 반사광 둘레
    d = math.hypot(dx, dy)
    k = len(body) - 1
    if d > r * 0.8:                                      # 둘레
        if dx + dy > r * 0.5:
            return body[3]                               # 오른쪽 아래 굴절광
        return body[1] if dy < 0 or dx < -r * 0.5 else body[2]
    g = 1 - math.hypot(dx, dy - r * 0.25) / r
    return body[max(2, min(k, 2 + round(g * 4)))]


def rock(dx, dy, x, y):
    """둥근 돌 고리: 각도에 따른 밝기 + 군데군데 한 단계 어두운 결"""
    lit = -(dx + dy) / ((math.hypot(dx, dy) or 1) * 1.414)
    i = 3 if lit > 0.5 else 2 if lit > -0.1 else 1 if lit > -0.6 else 0
    if (x * 5 + y * 3) % 7 == 0:
        i = max(0, i - 1)
    return STONE[i]


# ── 하급: 둥근 회색 돌 고리 + 네 끝 2x2 징 + 황동 테 두른 둥근 붉은 보석 ──
def low(a, b, dx, dy):
    lo, hi, d = min(a, b), max(a, b), math.hypot(a, b)
    if lo < 1 and 5 < hi < 6:                             # 징 (2x1, 돌 고리 바깥선에 맞춤)
        f = face(dx, dy)
        return M[7] if f == 3 else (M[5] if f == 2 else M[3])
    if d <= 2.6:                                         # 둥근 보석
        return cut_gem([(143, 2, 2), (203, 21, 2), (217, 101, 9), (245, 136, 13)], dx, dy, 2.6, None,
                       sparkle=None, star=1.6)
    if d <= 3.6:
        return metal(dx, dy)                             # 황동 테
    if d <= 4.6:
        return O
    if d <= 5.6:
        if lo < 2 and hi > 4.6:
            return O                                     # 징과 돌 사이 틈
        x, y = int(dx + C), int(dy + C)
        return rock(dx, dy, x, y)
    return None


# ── 중급: 주황 구슬 + 황동 고리 + 네 방향 4x3 징(홈) + 대각선 잎 장식 ──
def mid(a, b, dx, dy):
    lo, hi, d = min(a, b), max(a, b), math.hypot(a, b)
    if lo < 2 and 6 < hi < 9:
        on_x = a > b
        ex = dx - (math.copysign(7.5, dx) if on_x else 0)
        ey = dy - (0 if on_x else math.copysign(7.5, dy))
        if abs(ex) < 1 and abs(ey) < 1 and (abs(ey) < 0.6 if not on_x else abs(ex) < 0.6):
            return DOT if (ex + ey) < 0 else M[1]        # 홈
        if abs(ex) < 1 and abs(ey) < 1:
            return DOT if (ex + ey) < 0 else M[1]
        hw, hh = (1.5, 2) if on_x else (2, 1.5)
        if (abs(ex) > hw - 1 and ex < 0) or (abs(ey) > hh - 1 and ey < 0):
            return M[7]
        if (abs(ex) > hw - 1 and ex > 0) or (abs(ey) > hh - 1 and ey > 0):
            return M[3]
        return M[5]
    if d <= 3.6:
        return glossy([(131, 37, 2), (217, 28, 1), (227, 78, 4), (245, 126, 11), (252, 152, 13), (249, 179, 52)],
                      dx, dy, 3.6)
    if d <= 4.6:
        return O
    if d <= 6.6:
        if lo < 2.2 and hi > 6:
            return O                                     # 징과 고리 사이 틈
        return metal(dx, dy, inner=d < 5.6)
    if abs(a - b) <= 2 and d <= 8.7:
        if abs(a - b) <= 1 and d < 7.2 or (abs(a - b) == 1 and d < 7.2):
            return O                                     # 잎과 고리 사이 틈
        f = face(dx, dy)
        tip = d > 8
        return M[{3: 8 if tip else 6, 2: 5, 1: 2 if tip else 3}[f]]
    return None


# ── 상급: 붉은 구슬(별빛) + 황동 고리 + 네 방향 마름모 받침(붉은 보석) ──
def high(a, b, dx, dy):
    lo, hi, d = min(a, b), max(a, b), math.hypot(a, b)
    s = lo + abs(hi - 7)
    if s <= 3:                                           # 네 방향 마름모 받침 (구슬·고리 앞에 겹침)
        on_x = a > b
        ex = dx - (math.copysign(7, dx) if on_x else 0)
        ey = dy - (0 if on_x else math.copysign(7, dy))
        if s <= 1:                                       # 붉은 보석 (2x2: 반사광·굴절광)
            return RED_SPEC if ex < 0 and ey < 0 else (RED[2] if ex > 0 and ey > 0 else RED[1])
        if s <= 2:
            return M[{3: 8, 2: 6, 1: 4}[face(ex, ey)]]
        return M[{3: 6, 2: 4, 1: 2}[face(ex, ey)]]       # 받침 바깥 비탈
    if s <= 4 and d <= 7.0:
        return O                                         # 받침 둘레 외곽선 (뒤의 구슬·고리와 떼어 놓음)
    if d <= 4.8:
        return cut_gem([(143, 2, 2), (166, 36, 10), (206, 5, 4), (242, 33, 11)], dx, dy, 4.8,
                       spec=RED_SPEC, sparkle=RED_SPEC, star=2, arm=M[6])
    if d <= 5.6:
        return O
    if d <= 7.0:
        if abs(a - b) < 1:
            return M[8] if dx < 0 and dy < 0 else (M[6] if dx * dy < 0 else M[4])   # 대각선 리벳
        return metal(dx, dy, inner=d < 6.2)
    if abs(a - b) < 1 and d < 8:
        return M[7] if dx < 0 and dy < 0 else (M[5] if dx * dy < 0 else M[3])      # 대각선 황동 구슬
    return None


def ribbon(dx, dy):
    """양쪽 아래 리본: 안쪽 면 밝고 바깥 접힌 면 어둡게, 가운데 접힌 주름, 끝은 V 로 갈라짐"""
    a = abs(dx)
    if 5 < a < 8 and 5 < dy < 10.6 and not (dy > 9 and abs(a - 6.5) < 0.6):
        k = 2 if a < 6 else (1 if a < 7 else 0)
        if abs(dy - 7.5) < 0.6:
            k = max(0, k - 1)                            # 주름 그림자
        elif abs(dy - 8.5) < 0.6 and a < 7:
            k = min(2, k + 1)                            # 주름 아래 밝은 면
        return RED[k]
    return None


def render(kind):
    f = {"low": low, "mid": mid, "high": high}[kind]
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    body = set()
    for y in range(N):
        for x in range(N):
            dx, dy = x - C, y - C
            col = f(abs(dx), abs(dy), dx, dy)
            if not col and kind == "high":
                col = ribbon(dx, dy)
            if col:
                img.putpixel((x, y), col + (255,))
                body.add((x, y))
    for y in range(N):                                   # 바깥 외곽선
        for x in range(N):
            if (x, y) not in body and any(
                    (x + i, y + j) in body for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                img.putpixel((x, y), O + (255,))
    return img


if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for kind in ("low", "mid", "high"):
        im = render(kind)
        print(kind, im.getbbox())
        im.save(os.path.join(out, "stone_icon_%s.png" % kind))

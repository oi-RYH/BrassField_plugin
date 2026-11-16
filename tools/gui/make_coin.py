"""
골드 아이템 아이콘 16x16: HUD 사이드바 골드 동전(textures/font/hud/coin.png, 9x9)을 같은 색·같은 구조로 크게 다시 그린다.
  짙은 갈색 외곽선 → 테두리(오른쪽 아래는 그늘) → 밝게 솟은 고리(오른쪽 아래는 한 단계 어둡게)
  → 고리 안쪽 벽(왼쪽 위는 그늘, 오른쪽 아래는 빛) → 동전 면 → 가운데 움푹한 점, 면 왼쪽 위에 반사광. 빛은 왼쪽 위.

사용: python3 tools/gui/make_coin.py <출력.png>
"""
import math
import sys

from PIL import Image

OUT = (0x5c, 0x3a, 0x0a)
DARK = (0xb0, 0x70, 0x14)
MID = (0xe8, 0xaa, 0x28)
LIGHT = (0xff, 0xdc, 0x6e)
SHINE = (0xff, 0xfa, 0xd2)
C = 7.5


def color(dx, dy):
    d = math.hypot(dx, dy)
    lit = -(dx + dy)                                     # 왼쪽 위일수록 +
    if d > 7.3:
        return None
    if d > 6.4:
        return OUT
    if d > 5.3:                                          # 테두리
        return DARK if lit < -2.5 else MID
    if d > 4.1:                                          # 솟은 고리
        return MID if lit < -2.5 else LIGHT
    if -3 < dx < -1 and -3 < dy < -1 and abs(dx - dy) < 1.1:
        return SHINE                                     # 반사광
    if d > 3.2 and abs(lit) > 2.2:                       # 고리 안쪽 벽
        return DARK if lit > 0 else LIGHT
    if abs(dx) < 1 and abs(dy) < 1:                      # 가운데 움푹한 점
        return DARK if lit > -0.5 else OUT
    return MID


def draw():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y in range(16):
        for x in range(16):
            c = color(x - C, y - C)
            if c:
                img.putpixel((x, y), c + (255,))
    return img


if __name__ == "__main__":
    draw().save(sys.argv[1])
    print("ok")

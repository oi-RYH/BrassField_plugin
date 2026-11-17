"""
판매 버튼 아이템 아이콘 16x16: 사용자 시안(art/sell_button.png, 금색 네모 단추)을 같은 색으로 16px 에 맞게 다시 그리고,
가운데에 서버 화폐 골드 동전을 넣는다. 사이드바 골드 아이콘(textures/font/hud/coin.png, 9x9)과 같은 색·구조를
10x10 으로 그려 16px 단추 정가운데(3~12)에 맞춘다 (9px 동전은 정가운데에 올 수 없다).
  둥근 네모 단추(모서리 3px 깎음): 짙은 갈색 외곽선 · 왼쪽 위 밝은 테 · 오른쪽 아래 어두운 테 · 위 절반 밝고 아래 절반 조금 어두운 면

사용: python3 tools/gui/make_sell_button.py <출력.png>
"""
import sys

from PIL import Image

O = (92, 42, 10)
SHINE = (255, 250, 222)
RIM_HI = (255, 230, 150)
FACE_HI = (253, 206, 88)
FACE_LO = (247, 182, 56)
RIM_LO = (222, 140, 30)
CUT = 3                                                    # 모서리 깎는 정도

# 골드 동전 10x10 (사이드바 coin.png 색): O 외곽선, D 그늘, M 면, L 솟은 고리, S 반사광
COIN_PAL = {"O": (0x5c, 0x3a, 0x0a), "D": (0xb0, 0x70, 0x14), "M": (0xe8, 0xaa, 0x28),
            "L": (0xff, 0xdc, 0x6e), "S": (0xff, 0xfa, 0xd2)}
COIN = [
    "..OOOOOO..",
    ".ODMMMMDO.",
    "ODMLLLLMDO",
    "OMLSMMMLMO",
    "OMLMDDMLMO",
    "OMLMDDMLMO",
    "OMLMMMMLMO",
    "ODMLLLLMDO",
    ".ODDMMDDO.",
    "..OOOOOO..",
]


def draw():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = img.load()
    for y in range(16):
        for x in range(16):
            corner = min(x, 15 - x) + min(y, 15 - y)
            if corner < CUT:
                continue                                    # 깎은 모서리 바깥
            edge = x in (0, 15) or y in (0, 15) or corner == CUT
            if edge:
                col = O
            elif x == 1 or y == 1 or (corner == CUT + 1 and (x < 8 and y < 8)):
                col = SHINE if (x + y) < 7 else RIM_HI      # 왼쪽 위 밝은 테 (모서리는 더 밝게)
            elif x == 14 or y == 14 or corner == CUT + 1:
                col = RIM_LO                                # 오른쪽 아래 어두운 테
            else:
                col = FACE_HI if y < 8 else FACE_LO
            p[x, y] = col + (255,)
    for j, row in enumerate(COIN):
        for i, c in enumerate(row):
            if c != ".":
                p[3 + i, 3 + j] = COIN_PAL[c] + (255,)
    return img


if __name__ == "__main__":
    draw().save(sys.argv[1])
    print("ok")

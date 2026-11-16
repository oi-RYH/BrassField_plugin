"""
강화석 상점 창 배경: 강화 창 배경(enhance_bg.png)의 부품을 잘라 지금 상점 배치(4줄 상자 창)에 맞게 조립한다.
같은 세트로 보이도록 새로 그리지 않고 강화 창 그림을 그대로 쓴다.

부품 (강화 창 그림 좌표):
  옆 기둥(회백색 금속 + 구리 고리, 18px 주기) · 위 구리 들보 · 왼쪽 위 톱니 · 오른쪽 위 볼트
  칸 황동 테 (칸 바깥 2px, 9분할로 늘려 여러 칸을 한 테로 묶을 수 있다) · 유리관 · 작은 톱니
  아래 가방 칸 부분 전체 (창 칸 끝 y=71 부터 끝까지)

상점 배치 (StoneShopGui): 2줄 8열 보유 골드 / 1~3줄 1열 강화석 아이콘, 4·5·6열 1개·10개·64개 구매 버튼(숫자 아이템).
제목은 간판 그림(art/sign_stone_shop_120.png, make_sign.py 로 만든 폭 120 간판)을 위 가운데에 단다. 게임 제목 글자는 쓰지 않는다.
  간판 아래 끝은 구매 버튼 테 바로 위(y=31), 윗부분은 창 위로 7px 넘친다 → 그림 맨 위에 PAD_TOP 만큼 여백을 두고
  창을 그만큼 아래에 그린다 (ItemsAdder guis.yml 의 y_position 도 PAD_TOP 만큼 올린다).
  어우러지게: 위 구리 들보는 간판 뒤로 지나가고, 간판 아래·오른쪽으로 바탕 판에 그림자를 드리운다.
바탕 판 무늬: 강화 창 바탕처럼 어둡고 밝은 작은 점을 드문드문 뿌리고,
  희미한 회로선 두 가지(마디→톱니, 마디-꺾인 선-마디)를 빈자리에 옮겨 붙인다.

사용: python3 tools/gui/make_shop_bg.py <enhance_bg.png> <출력.png> [미리보기.png <아이템 텍스처 폴더> <클라이언트 jar> [숫자 아이템 폴더]]
"""
import io
import os
import random
import sys
import zipfile

from PIL import Image, ImageDraw, ImageFont

ROWS = 4
W, H = 176, 114 + ROWS * 18
ENH_ROWS_END = 17 + 3 * 18             # 강화 창(3줄) 창 칸이 끝나는 y
TOP = 17 + ROWS * 18                    # 이 창의 창 칸이 끝나는 y

PANEL = [(42, 35, 28), (43, 36, 29), (44, 37, 30), (45, 38, 31), (46, 39, 32)]
SPECKS = [((39, 31, 24), 0.015), ((58, 53, 45), 0.01)]   # 강화 창 바탕의 작은 점 (색, 비율)
DARK = (13, 10, 7)
FRAME_IN = (68, 62, 50)
PIPE = [(13, 10, 7), (226, 179, 99), (187, 127, 54), (146, 83, 40), (13, 10, 7)]   # 가로 파이프 위→아래


SIGN_IMAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "art", "sign_stone_shop_120.png")
SIGN_BOTTOM = 31                          # 간판 아래 끝 y (구매 버튼 테 y=33 위)
PAD_TOP = 8                               # 창 위로 넘치는 간판 자리 (그림 맨 위 여백)
SHADOW = 0.55                             # 그림자: 바탕 판 밝기 배율


def slot_box(row, col):
    return 7 + col * 18, 17 + row * 18


def build(enh):
    rnd = random.Random(910)
    img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for y in range(H):                                            # 바탕 판 (+ 작은 점)
        for x in range(W):
            col, r = rnd.choice(PANEL), rnd.random()
            for speck, share in SPECKS:
                if r < share:
                    col = speck
                    break
                r -= share
            img.putpixel((x, y), col + (255,))

    def copy(box, to):
        img.alpha_composite(enh.crop(box), to)

    for y in range(0, TOP, 18):                                   # 옆 기둥 (18px 주기로 이어 붙임)
        h = min(18, TOP - y)
        src_y = 18 + (y % 18)
        copy((0, src_y, 6, src_y + h), (0, y))
        copy((170, src_y, 176, src_y + h), (170, y))
    copy((0, 0, 6, 18), (0, 0))
    copy((170, 0, 176, 18), (170, 0))
    for x in range(6, 170, 30):                                   # 위 구리 들보
        copy((22, 0, 22 + min(30, 170 - x), 7), (x, 0))
    copy((164, 0, 176, 8), (164, 0))                              # 오른쪽 위 볼트
    copy((0, ENH_ROWS_END, 176, 168), (0, TOP))                   # 아래 가방 칸 부분 그대로

    def frame(x0, y0, x1, y1):
        """칸 테두리 (x0,y0)-(x1,y1) 바깥에 강화 창 황동 테. 9분할: 모서리 3px, 변은 늘림"""
        fx0, fy0, fx1, fy1 = 23, 15, 45, 37                       # 강화 창 장비 칸 테 (칸 25..43 / 17..35)
        X0, Y0, X1, Y1 = x0 - 2, y0 - 2, x1 + 2, y1 + 2
        c = 3
        for (sx0, sx1, dx0, dx1) in ((fx0, fx0 + c, X0, X0 + c), (fx0 + c, fx1 - c, X0 + c, X1 - c), (fx1 - c, fx1, X1 - c, X1)):
            for (sy0, sy1, dy0, dy1) in ((fy0, fy0 + c, Y0, Y0 + c), (fy0 + c, fy1 - c, Y0 + c, Y1 - c), (fy1 - c, fy1, Y1 - c, Y1)):
                piece = enh.crop((sx0, sy0, sx1, sy1)).resize((dx1 - dx0, dy1 - dy0), Image.NEAREST)
                img.alpha_composite(piece, (dx0, dy0))
        for x in range(x0 + 18, x1 - 1, 18):                     # 여러 칸 묶음: 칸 사이 구분선
            d.line([(x, y0 + 1), (x, y1 - 2)], fill=(50, 45, 37))

    def pipe_h(x0, x1, y):
        for i, c in enumerate(PIPE):
            d.line([(x0, y + i), (x1 - 1, y + i)], fill=c)

    # ── 강화석 아이콘 (1~3줄 1열) · 구매 버튼 (1~3줄 4~6열): 각각 하나의 테로 묶는다 ──
    ix, iy = slot_box(1, 1)
    bx, by = slot_box(1, 4)
    for row in (1, 2, 3):                                         # 아이콘 → 버튼 파이프와 가운데 톱니
        y = slot_box(row, 1)[1]
        pipe_h(ix + 20, bx - 2, y + 7)
        copy((54, 36, 70, 52), (ix + 27, y + 1))
    frame(ix, iy, ix + 18, iy + 54)
    for y in (iy + 18, iy + 36):                                  # 아이콘 칸 사이 가로 구분선
        d.line([(ix + 1, y), (ix + 16, y)], fill=(50, 45, 37))
    frame(bx, by, bx + 54, by + 54)
    for y in (by + 18, by + 36):
        d.line([(bx + 1, y), (bx + 52, y)], fill=(50, 45, 37))
    # ── 보유 골드 (2줄 8열): 버튼 묶음 가운데 줄에서 파이프로 이어진 칸 ──
    gx, gy = slot_box(2, 8)
    copy((6, 22, 22, 70), (6, 26))                                # 왼쪽 유리관 (강화 창 왼쪽 관)
    pipe_h(bx + 56, gx - 2, gy + 7)
    frame(gx, gy, gx + 18, gy + 18)
    # ── 바탕 판 무늬 (강화 창의 희미한 회로선): 간판 오른쪽 빈자리, 버튼 묶음 오른쪽 아래 빈자리 ──
    copy((101, 10, 122, 36), (148, 16))                           # 마디 → 희미한 톱니
    copy((57, 55, 78, 68), (137, 74))                             # 마디 - 꺾인 선 - 마디
    # ── 장식: 오른쪽 아래 톱니 ──
    copy((158, ENH_ROWS_END - 10, 176, ENH_ROWS_END + 6), (158, TOP - 10))   # 오른쪽 아래 톱니 (강화 창과 같은 자리, 온전하게)
    copy((0, 0, 22, 22), (0, 0))                                  # 왼쪽 위 큰 톱니
    return hang_sign(img)


def hang_sign(gui):
    """창 그림을 PAD_TOP 만큼 내려 놓고, 위 가운데에 간판과 그림자를 단다"""
    sign = Image.open(SIGN_IMAGE).convert("RGBA")
    sw, sh = sign.size
    sx, sy = (W - sw) // 2, PAD_TOP + SIGN_BOTTOM - sh
    out = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    out.alpha_composite(gui.crop((0, 0, 256, 256 - PAD_TOP)), (0, PAD_TOP))
    a = sign.split()[3].load()
    op = out.load()
    for y in range(sh):                                           # 그림자: 오른쪽 1px · 아래 2px 로 밀린 간판 모양
        for x in range(sw):
            if not a[x, y]:
                continue
            for tx, ty in ((x + 1, y + 2), (x + 1, y + 1)):
                if tx < sw and ty < sh and a[tx, ty]:
                    continue
                X, Y = sx + tx, sy + ty
                if Y >= PAD_TOP and 0 <= X < W:
                    r, g, b, al = op[X, Y]
                    if al:
                        op[X, Y] = (int(r * SHADOW), int(g * SHADOW), int(b * SHADOW), al)
    out.alpha_composite(sign, (sx, sy))
    return out


if __name__ == "__main__":
    enh = Image.open(sys.argv[1]).convert("RGBA")
    out = build(enh)
    out.save(sys.argv[2])
    if len(sys.argv) > 3:                                         # 미리보기: 아이템을 올려 3배 확대
        prev = out.crop((0, 0, W, H + PAD_TOP)).copy()
        items, jar = sys.argv[4], zipfile.ZipFile(sys.argv[5])
        vanilla = lambda n: Image.open(io.BytesIO(jar.read("assets/minecraft/textures/item/%s.png" % n))).convert("RGBA")
        gx, gy = slot_box(2, 8)
        prev.alpha_composite(vanilla("gold_ingot"), (gx + 1, gy + 1 + PAD_TOP))
        numbers = sys.argv[6] if len(sys.argv) > 6 else None
        for row, key in ((1, "low"), (2, "mid"), (3, "high")):
            ix, iy = slot_box(row, 1)
            icon = Image.open("%s/stone_icon_%s.png" % (items, key)).convert("RGBA").resize((16, 16), Image.NEAREST)
            prev.alpha_composite(icon, (ix + 1, iy + 1 + PAD_TOP))
            for i, n in enumerate(("1", "10", "64")):
                bx, by = slot_box(row, 4 + i)
                if numbers:
                    prev.alpha_composite(Image.open("%s/number_%s.png" % (numbers, n)).convert("RGBA"),
                                         (bx + 1, by + 1 + PAD_TOP))
                else:
                    prev.alpha_composite(vanilla("gold_nugget"), (bx + 1, by + 1 + PAD_TOP))
        bg = Image.new("RGBA", prev.size, (110, 110, 110, 255))   # 창 바깥(게임 화면) 회색
        bg.alpha_composite(prev)
        prev = bg.resize((W * 3, (H + PAD_TOP) * 3), Image.NEAREST)
        dd = ImageDraw.Draw(prev)
        f = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", 24, index=2)
        for row in (1, 2, 3):
            for i, n in enumerate(("", "10", "64")):
                if n and not numbers:
                    bx, by = slot_box(row, 4 + i)
                    dd.text(((bx + 17) * 3, (by + 17 + PAD_TOP) * 3), n, font=f, fill=(255, 255, 255), anchor="rd")
        prev.save(sys.argv[3])
    print("ok")

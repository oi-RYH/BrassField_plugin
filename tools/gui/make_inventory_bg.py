"""
서바이벌 인벤토리(E 키 창) 배경 — minecraft:textures/gui/container/inventory.png 덮어쓰기.
칸 위치는 바닐라 그대로 두고(서버가 칸을 바꿀 수 없다) 그림만 강화 창과 같은 황동 · 스팀펑크로 바꾼다.

바닐라 배치 (창 기준 픽셀, 칸 상자 = 테두리 포함 18px):
  방어구 4칸 (7,7)~(25,79) 세로 · 플레이어 모습 창 (25,7)~(76,79) · 보조손 (76,61)
  조합 2x2 (97,17) · 화살표 · 결과 (153,27) · 레시피 책 단추 (104,61, 게임이 그림)
  "제작" 글자는 contents/rustport/configs/lang_overwrite.yml 에서 container.crafting 을 지워 없앤다.
  가방 3줄 (7,83) · 단축바 (7,141) · 창 높이 166
아래 가방 · 단축바 부분은 강화 창 그림(3줄 상자 창, 가방 칸이 1px 아래)을 1px 올려 그대로 쓴다.

사용: python3 tools/gui/make_inventory_bg.py <출력 png> [미리보기 png]
"""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gui_kit as gk  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
H = 166
TOP_END = 80                     # 위 부분(방어구 · 모습 창 · 조합)이 끝나는 y, 여기부터 강화 창 가방 부분(+1)

DK = (13, 10, 7, 255)
BRASS = (187, 127, 54, 255)
BRASS_HI = (226, 179, 99, 255)
BRASS_LO = (146, 83, 40, 255)
WIN_TOP = (34, 30, 26)           # 모습 창 안 (위 → 아래로 조금 밝게)
WIN_BOT = (52, 45, 37)


def build():
    enh = Image.open(os.path.join(HERE, "art", "enhance_bg_3row.png")).convert("RGBA")
    win = gk.Window(enh, 4, pad_top=0)            # 바탕 판 · 옆 기둥 · 위 들보 (4줄이면 기둥이 y 89 까지 이어진다)
    win.corner_gears(bottom_right=False, top_left=False)
    img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    img.alpha_composite(win.img.crop((0, 0, 176, TOP_END)), (0, 0))
    img.alpha_composite(enh.crop((0, TOP_END + 1, 176, H + 1)), (0, TOP_END))   # 가방 · 단축바 (1px 올림)
    win.img, win.d = img, ImageDraw.Draw(img)
    d = win.d

    # 방어구 4칸 · 보조손 · 조합 2x2 · 결과
    win.frame(7, 7, 25, 79)
    win.frame(76, 61, 94, 79)
    win.frame(97, 17, 133, 53)
    win.frame(153, 27, 171, 45)

    # 플레이어 모습 창: 검은 테 + 황동 1px 테 + 어두운 유리
    x0, y0, x1, y1 = 28, 6, 73, 79
    d.rectangle((x0, y0, x1, y1), fill=DK)
    d.rectangle((x0 + 1, y0 + 1, x1 - 1, y1 - 1), fill=BRASS)
    d.line((x0 + 1, y0 + 1, x1 - 1, y0 + 1), fill=BRASS_HI)
    d.line((x0 + 1, y1 - 1, x1 - 1, y1 - 1), fill=BRASS_LO)
    d.rectangle((x0 + 2, y0 + 2, x1 - 2, y1 - 2), fill=DK)
    for y in range(y0 + 3, y1 - 2):
        t = (y - y0 - 3) / (y1 - y0 - 6)
        c = tuple(round(a + (b - a) * t) for a, b in zip(WIN_TOP, WIN_BOT)) + (255,)
        d.line((x0 + 3, y, x1 - 3, y), fill=c)
    for x in (x0 + 4, x1 - 4):                    # 유리 안 모서리 리벳
        for y in (y0 + 4, y1 - 4):
            d.point((x, y), fill=BRASS_LO)

    # 조합 → 결과: 황동 관 + 화살촉
    win.pipe_h(136, 146, 33)
    for i in range(5):
        d.line((146 + i, 31 + i, 146 + i, 41 - i), fill=BRASS_HI if i == 0 else BRASS)
        d.point((146 + i, 31 + i), fill=DK)
        d.point((146 + i, 41 - i), fill=DK)

    # 빈 자리 장식: 결과 칸 아래 작은 톱니 · 회로선
    win.gear_small(150, 52)
    win.copy(gk.CIRCUIT_LINK, (128, 64))
    return img


def preview(bg, jar, path):
    import io
    import zipfile
    z = zipfile.ZipFile(jar)

    def tex(p):
        return Image.open(io.BytesIO(z.read(p))).convert("RGBA")
    shot = Image.new("RGBA", (176, H), (110, 110, 110, 255))
    shot.alpha_composite(bg.crop((0, 0, 176, H)))
    shot.alpha_composite(tex("assets/minecraft/textures/gui/sprites/recipe_book/button.png"), (104, 61))
    items = {}                                   # 빈 창 그대로 (아이템 없이)
    for (x, y), name in items.items():
        for p in ("assets/minecraft/textures/item/%s.png" % name, "assets/minecraft/textures/block/%s.png" % name):
            if p in z.namelist():
                shot.alpha_composite(tex(p).resize((16, 16), Image.NEAREST), (x, y))
                break
    big = shot.resize((176 * 4, H * 4), Image.NEAREST)
    van = tex("assets/minecraft/textures/gui/container/inventory.png").crop((0, 0, 176, H)).resize((176 * 4, H * 4), Image.NEAREST)
    out = Image.new("RGBA", (176 * 8 + 24, H * 4), (60, 60, 60, 255))
    out.alpha_composite(van, (0, 0))
    out.alpha_composite(big, (176 * 4 + 24, 0))
    out.save(path)


if __name__ == "__main__":
    bg = build()
    bg.save(sys.argv[1])
    if len(sys.argv) > 2:
        preview(bg, os.path.expanduser("~/Library/Application Support/minecraft/versions/26.1.2/26.1.2.jar"), sys.argv[2])

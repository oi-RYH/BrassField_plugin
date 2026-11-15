"""
요리 아이템 그림 (3판): 16x16 손 픽셀 그리드. Farmer's Delight·바닐라 아이템 느낌을 참고했다
(작고 굵은 실루엣, 그릇 위로 수북이 쌓인 내용물, 픽셀 단위로 거친 색, 짙은 색 외곽선). 그림 자체는 직접 그렸다.

- 각 그림은 글자 그리드(16줄 x 16칸)와 글자→색 팔레트. '.'은 투명.
- 외곽선은 그리드에 그리지 않고, 마지막에 이웃 색을 짙게 만든 색으로 둘러준다 (food_kit.dark_outline).
- layers: [(그리드, (x, y))] 를 순서대로 덮어 그려 그릇·판 같은 공용 부품을 재사용한다.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from food_kit import dark_outline, rgb, blank, png  # noqa: E402

# ── 공용 팔레트 ──
WOOD = {"h": rgb(196, 146, 88), "l": rgb(158, 108, 58), "m": rgb(122, 80, 40), "d": rgb(88, 54, 26), "k": rgb(60, 34, 16)}
BOARD = {"n": rgb(206, 158, 96), "N": rgb(170, 122, 66), "M": rgb(116, 76, 38)}


def compose(*layers, palette):
    """layers: (줄 목록, (x, y)) 를 아래부터 덮어 그린 16x16 그림 (외곽선 포함)"""
    img = blank(16)
    for rows, (ox, oy) in layers:
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch == "." or not (0 <= ox + i < 16 and 0 <= oy + j < 16):
                    continue
                img[oy + j][ox + i] = palette[ch]
    return dark_outline(img)


def check(name, rows, width=None):
    for r in rows:
        assert width is None or len(r) == width, "%s: 줄 길이 %d (%r)" % (name, len(r), r)


# ═════════════ 공용 부품 ═════════════
# 나무 그릇 앞면 (14칸, 5줄) — 내용물 아래에 덮어 그린다. 위쪽 줄이 테(밝음)
BOWL = [
    "hhllllllllmmdd",
    "llmmmmdmmmmddd",
    ".lmmmmmmmmddd.",
    "..mmdmmmmmdd..",
    "....dmmmdd....",
]

# ═════════════ 햄버거 ═════════════
HAMBURGER = [
    "................",
    "................",
    "......bCCb......",
    "....bcCCCcbb....",
    "...bcCsCcbbsb...",
    "..bcCcbbbbsbbB..",
    "..bcsbbbbbbbBB..",
    "..BbbbbsbbbbBB..",
    ".GyGgGyGGgyGgGg.",
    ".gRRrRRRrRRRrRg.",
    ".PqPPpPqPPPpPPp.",
    ".pppPpppPpppppp.",
    "..cCCcccccccbb..",
    "..Bbbbbbbbbbbb..",
    "................",
    "................",
]
HAMBURGER_P = {
    "C": rgb(248, 200, 124), "c": rgb(228, 160, 76), "b": rgb(198, 122, 48), "B": rgb(150, 86, 32), "s": rgb(252, 240, 204),
    "y": rgb(176, 218, 92), "G": rgb(110, 178, 56), "g": rgb(52, 112, 32),
    "R": rgb(218, 54, 38), "r": rgb(152, 26, 22),
    "q": rgb(150, 92, 52), "P": rgb(112, 62, 34), "p": rgb(74, 38, 20),
}

# ═════════════ 치킨 수프 ═════════════
CHICKEN_SOUP = [
    "................",
    "................",
    "................",
    "................",
    ".......aW.......",
    ".....wWyae......",
    "...yzwWyaWwey...",
    "..hzyYwWyzaYyh..",
    ".hyaYzyeywWzyYd.",
]
CHICKEN_SOUP_P = dict(WOOD, **{
    "z": rgb(244, 210, 116), "y": rgb(218, 166, 62), "Y": rgb(176, 118, 38),
    "w": rgb(240, 226, 196), "W": rgb(198, 172, 130), "a": rgb(236, 122, 32), "e": rgb(76, 146, 44),
})

# ═════════════ 연어 초밥 (나무 판 위 두 점) ═════════════
NIGIRI = [
    "..SSfSs..",
    ".SfSsfSs.",
    "SfsSfsfSt",
    "tsftsftst",
    "iiiiiIIIj",
    ".iiIIIjj.",
]
GETA = [
    "................",
    ".nnNnnnnnnNnnnn.",
    ".MMMMMMMMMMMMMM.",
    "..M..........M..",
]
SUSHI_P = dict(BOARD, **{
    "S": rgb(255, 160, 108), "s": rgb(238, 114, 66), "t": rgb(196, 74, 40), "f": rgb(255, 224, 200),
    "i": rgb(248, 246, 238), "I": rgb(210, 206, 194), "j": rgb(166, 160, 148),
})


def hamburger():
    check("hamburger", HAMBURGER, 16)
    return compose((HAMBURGER, (0, 0)), palette=HAMBURGER_P)


def chicken_soup():
    check("chicken_soup", CHICKEN_SOUP, 16)
    check("bowl", BOWL, 14)
    return compose((CHICKEN_SOUP, (0, 0)), (BOWL, (1, 9)), palette=CHICKEN_SOUP_P)


def salmon_sushi():
    check("nigiri", NIGIRI, 9)
    check("geta", GETA, 16)
    return compose((GETA, (0, 10)), (NIGIRI, (0, 4)), (NIGIRI, (7, 6)), palette=SUSHI_P)


# 도자기 접시 (14칸, 5줄) — 음식보다 먼저 그린다
PLATE = [
    "..XWWWWWWWWX..",
    ".XWwwwwwwwwWX.",
    "XWwwwwwwwwwwWX",
    ".XYYYYYYYYYYX.",
    "..ZZZZZZZZZZ..",
]
PLATE_P = {"W": rgb(244, 246, 250), "w": rgb(226, 230, 238), "X": rgb(196, 202, 212), "Y": rgb(164, 170, 184), "Z": rgb(124, 130, 146)}


def bowl_dish(name, rows, palette):
    """그릇 요리: 위 9줄(내용물) + 나무 그릇"""
    check(name, rows, 16)
    check("bowl", BOWL, 14)
    return compose((rows, (0, 0)), (BOWL, (1, 9)), palette=dict(WOOD, **palette))


def plate_dish(name, *layers, palette):
    """접시 요리: 접시를 먼저 깔고 (줄 목록, 위치) 들을 덮어 그린다"""
    for rows, _ in layers:
        check(name, rows)
    return compose((PLATE, (1, 10)), *layers, palette=dict(PLATE_P, **palette))


def single(name, rows, palette):
    check(name, rows, 16)
    return compose((rows, (0, 0)), palette=palette)


TOP = ["................"] * 3   # 그릇 요리 위 빈 줄

# ═════════════ 익힌 밥 ═════════════
RICE_P = {"W": rgb(255, 255, 250), "i": rgb(240, 238, 228), "I": rgb(208, 204, 192), "j": rgb(170, 164, 150)}
COOKED_RICE = TOP + [
    "................",
    "......iIi.......",
    "....iiWiiIi.....",
    "...iWiiIiiWij...",
    "..iiIiWiiiIiij..",
    ".hiWiiIiiWiIijd.",
]

# ═════════════ 볶음밥 / 버섯볶음밥 ═════════════
FRIED_RICE_P = {"W": rgb(252, 226, 150), "i": rgb(236, 196, 100), "I": rgb(204, 160, 70), "j": rgb(160, 116, 44),
                "a": rgb(238, 120, 30), "g": rgb(96, 168, 48), "e": rgb(252, 234, 120)}
FRIED_RICE = TOP + [
    "................",
    "......aWi.......",
    "....iigeiIa.....",
    "...iWaiIegWij...",
    "..igIeWaiIgiij..",
    ".hiWgiIeaWiIgjd.",
]
MUSHROOM_RICE_P = {"W": rgb(252, 236, 198), "i": rgb(236, 210, 158), "I": rgb(204, 170, 116), "j": rgb(164, 126, 76),
                   "u": rgb(132, 82, 50), "U": rgb(190, 142, 100), "t": rgb(240, 220, 156)}
MUSHROOM_RICE = TOP + [
    "................",
    "......uWi.......",
    "....iiUuiIt.....",
    "...iWitIiuUij...",
    "..itIiWuiUIiij..",
    ".hiWuiIitWiIijd.",
]

# ═════════════ 야채 수프 ═════════════
VEGETABLE_SOUP_P = {"z": rgb(244, 146, 84), "y": rgb(216, 94, 46), "Y": rgb(160, 54, 30),
                    "w": rgb(240, 218, 156), "W": rgb(198, 170, 110), "a": rgb(246, 156, 34), "e": rgb(76, 146, 44),
                    "c": rgb(158, 206, 96)}
VEGETABLE_SOUP = TOP + [
    "................",
    ".......cW.......",
    ".....wWyce......",
    "...yzcWyaWwey...",
    "..hzyYwcyzaYyh..",
    ".hyaYzyeycWzyYd.",
]

# ═════════════ 양배추 쌈 (접시 위 두 줄 말이) ═════════════
WRAP = [
    ".GyyGGyGgq",
    "GyGGyGGGgP",
    "gGGgGGgGgp",
    ".gggggggg.",
]
WRAP_P = {"y": rgb(184, 226, 120), "G": rgb(120, 182, 64), "g": rgb(62, 120, 40),
          "q": rgb(178, 118, 70), "P": rgb(132, 78, 42), "p": rgb(90, 50, 26)}

# ═════════════ 김밥 (접시 위 세 조각) ═════════════
KIMBAP = [
    ".kKk.",
    "kiecK",
    "Kagik",
    "kiiik",
    ".kkk.",
]
KIMBAP_P = {"k": rgb(30, 40, 30), "K": rgb(62, 80, 54), "i": rgb(246, 244, 236),
            "e": rgb(252, 222, 90), "a": rgb(240, 124, 34), "g": rgb(70, 150, 50), "c": rgb(236, 120, 130)}

# ═════════════ 만두 (접시 위 세 개) ═════════════
DUMPLING = [
    "..DfD..",
    ".fDFDf.",
    "fFFfFFd",
    "FFFFFfd",
    ".ssssd.",
]
DUMPLING_P = {"F": rgb(248, 236, 206), "f": rgb(228, 208, 166), "d": rgb(196, 168, 120), "D": rgb(166, 136, 92),
              "s": rgb(198, 136, 62)}

# ═════════════ 미트볼 파스타 ═════════════
MEATBALL_PASTA = [
    "................",
    ".....qPP.qP.....",
    "....PpQPRqPp....",
    "...nRRpRrRRvRn..",
    "..nNRrRnRRrNnn..",
    "..NnnNnnNnnNnN..",
    "..nNnnnNnnnNnn..",
]
MEATBALL_PASTA_P = {"Q": rgb(194, 128, 80), "q": rgb(160, 96, 56), "P": rgb(122, 66, 38), "p": rgb(82, 42, 24),
                    "R": rgb(212, 52, 34), "r": rgb(150, 28, 20), "n": rgb(244, 210, 116), "N": rgb(204, 162, 68),
                    "v": rgb(76, 156, 52)}

# ═════════════ 라타투이 ═════════════
RATATOUILLE = [
    "................",
    "....AaBbCcAa....",
    "...aAbBcCaAbB...",
    "..sbBcCaAbBcCs..",
    "..saAbBcCaAbBs..",
    "...ssssvsssss...",
]
RATATOUILLE_P = {"A": rgb(236, 84, 58), "a": rgb(178, 40, 30), "B": rgb(150, 90, 166), "b": rgb(96, 46, 110),
                 "C": rgb(250, 168, 70), "c": rgb(214, 116, 30), "s": rgb(176, 50, 32), "v": rgb(80, 160, 56)}

# ═════════════ 꿀 쿠키 ═════════════
HONEY_COOKIE = [
    "................",
    "................",
    "................",
    "......ccCc......",
    "....cCCcCCcc....",
    "...cCHHHcccbc...",
    "..cCHhHHHcbcbb..",
    "..cCHHhHHHcbcb..",
    "..ccbHHHhHcccb..",
    "..cccbcHHccbcb..",
    "..bccccbHcccbb..",
    "...bbccHcbcbb...",
    "....bbbbbbbb....",
    "......BBBB......",
    "................",
    "................",
]
HONEY_COOKIE_P = {"H": rgb(252, 194, 56), "h": rgb(255, 238, 150), "C": rgb(234, 182, 106), "c": rgb(206, 146, 72),
                  "b": rgb(162, 102, 46), "B": rgb(120, 72, 30)}

# ═════════════ 중간 재료 ═════════════
DOUGH = [
    "................",
    "................",
    "................",
    "................",
    "................",
    ".....fFFFf......",
    "...fFFWFFFfd....",
    "..fFWWFFFFffd...",
    "..FFWFFFFfffdd..",
    "..fFFFFFffffdd..",
    "..dfffffffdddD..",
    "...dddffdddDD...",
    "....DDDDDDDD....",
    "................",
    "................",
    "................",
]
DOUGH_P = {"W": rgb(255, 255, 250), "F": rgb(244, 228, 192), "f": rgb(224, 202, 156), "d": rgb(190, 162, 116),
           "D": rgb(150, 124, 84)}
NOODLES = [
    "................",
    "................",
    "................",
    "................",
    "................",
    ".....nNnnN......",
    "...nNnLnNnnN....",
    "..nNLnNnLnNnn...",
    "..NnNnLnNnLnNn..",
    "..nLnNnNnNnLnN..",
    "..NnNnLnNnNnNM..",
    "...MNnNnNnNMM...",
    "....MMMMMMMM....",
    "................",
    "................",
    "................",
]
NOODLES_P = {"L": rgb(255, 240, 180), "n": rgb(242, 208, 112), "N": rgb(206, 164, 66), "M": rgb(160, 118, 40)}
TOMATO_SAUCE = [
    "................",
    "................",
    "....bOOOOOb.....",
    "....oBBBBBo.....",
    "....gRRRRRrg....",
    "...gGRRRRRrrg...",
    "...gGRRRRRrrg...",
    "...gHRRRRRrrg...",
    "...gLLLsLLLLg...",
    "...gLLssLLLLg...",
    "...gGRRRRRrrg...",
    "...gGRRRRrrrg...",
    "....gRRRRrrg....",
    "....gggggggg....",
    "................",
    "................",
]
TOMATO_SAUCE_P = {"O": rgb(252, 216, 140), "B": rgb(220, 168, 86), "b": rgb(170, 116, 46), "o": rgb(128, 82, 30),
                  "g": rgb(150, 178, 184), "G": rgb(222, 240, 242), "H": rgb(255, 255, 255),
                  "R": rgb(208, 52, 34), "r": rgb(150, 30, 20), "L": rgb(238, 224, 192), "s": rgb(212, 62, 40)}
PATTY = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    ".....pPPPPp.....",
    "...pPQPPfPPp....",
    "..pPQfPPPPfPp...",
    "..pPPPPfPPPPpr..",
    "..rpPPPPPPPprr..",
    "...rrppppprrr...",
    "....RRRRRRRR....",
    "................",
    "................",
    "................",
]
PATTY_P = {"Q": rgb(250, 170, 160), "P": rgb(212, 86, 88), "p": rgb(170, 52, 58), "f": rgb(252, 216, 208),
           "r": rgb(130, 34, 40), "R": rgb(100, 24, 30)}


SPRITES = {
    "cooked_rice": lambda: bowl_dish("cooked_rice", COOKED_RICE, RICE_P),
    "salmon_sushi": salmon_sushi,
    "cabbage_wrap": lambda: plate_dish("cabbage_wrap", (WRAP, (2, 6)), (WRAP, (4, 9)), palette=WRAP_P),
    "honey_cookie": lambda: single("honey_cookie", HONEY_COOKIE, HONEY_COOKIE_P),
    "kimbap": lambda: plate_dish("kimbap", (KIMBAP, (5, 5)), (KIMBAP, (2, 8)), (KIMBAP, (9, 8)), palette=KIMBAP_P),
    "mushroom_fried_rice": lambda: bowl_dish("mushroom_fried_rice", MUSHROOM_RICE, MUSHROOM_RICE_P),
    "meatball_pasta": lambda: plate_dish("meatball_pasta", (MEATBALL_PASTA, (0, 3)), palette=MEATBALL_PASTA_P),
    "ratatouille": lambda: plate_dish("ratatouille", (RATATOUILLE, (0, 4)), palette=RATATOUILLE_P),
    "chicken_soup": chicken_soup,
    "fried_rice": lambda: bowl_dish("fried_rice", FRIED_RICE, FRIED_RICE_P),
    "dumplings": lambda: plate_dish("dumplings", (DUMPLING, (4, 5)), (DUMPLING, (1, 8)), (DUMPLING, (8, 8)), palette=DUMPLING_P),
    "vegetable_soup": lambda: bowl_dish("vegetable_soup", VEGETABLE_SOUP, VEGETABLE_SOUP_P),
    "hamburger": hamburger,
    "dough": lambda: single("dough", DOUGH, DOUGH_P),
    "noodles": lambda: single("noodles", NOODLES, NOODLES_P),
    "tomato_sauce": lambda: single("tomato_sauce", TOMATO_SAUCE, TOMATO_SAUCE_P),
    "patty": lambda: single("patty", PATTY, PATTY_P),
}

if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    imgs = []
    for name, draw in SPRITES.items():
        img = draw()
        png.write(os.path.join(out, name + ".png"), img)
        imgs.append(img)
    if os.environ.get("PREVIEW"):
        sheet = png.blank(18 * 9, 18 * 2)
        for i, img in enumerate(imgs):
            png.paste(sheet, img, (i % 9) * 18, (i // 9) * 18 + 1)
        png.write(os.environ["PREVIEW"], png.scale(sheet, 6))
    print("ok: %d" % len(imgs))

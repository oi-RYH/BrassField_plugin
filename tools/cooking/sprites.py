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


# ═════════════════════════ 두 번째 세트: 1단계 재료·음식, 새 2단계 요리, 절구 ═════════════════════════
BLANK_ROWS = ["................"]

# ── 가루 자루 (밀가루·옥수수가루): 열린 삼베 자루 위로 가루가 봉긋 ──
SACK = BLANK_ROWS * 3 + [
    "......PPPP......",
    ".....PPpPPP.....",
    "....sPPPPpPs....",
    "...ssSssssSss...",
    "..bbBbbbbbBbbb..",
    "..bBbbbmbbbbbb..",
    "..bbbbmmmbbbBb..",
    "..bBbbbmbbbbbb..",
    "..bbbbBbbbbbbb..",
    "...bbbbbbbbbb...",
    "....BBBBBBBB....",
    "................",
    "................",
]
SACK_P = {"b": rgb(206, 178, 126), "B": rgb(172, 142, 94), "s": rgb(228, 204, 154), "S": rgb(192, 162, 112),
          "m": rgb(150, 112, 60)}
FLOUR_P = dict(SACK_P, P=rgb(250, 248, 240), p=rgb(222, 218, 206))
CORNMEAL_P = dict(SACK_P, P=rgb(250, 214, 100), p=rgb(222, 176, 60))

# ── 주스 병: 코르크, 유리 테두리와 반사, 과일 그림 라벨 ──
JUICE = BLANK_ROWS + [
    "......cccc......",
    "......cCCc......",
    "......gwgg......",
    "......gwLg......",
    ".....gwLLgg.....",
    "....gwLLLLgg....",
    "....gwLLLLlg....",
    "....gPPFFPPg....",
    "....gPFFFFPg....",
    "....gLLLLLlg....",
    "....gLLLLLlg....",
    "....gllllllg....",
    ".....gggggg.....",
    "................",
    "................",
]
JUICE_BASE = {"c": rgb(176, 130, 80), "C": rgb(206, 160, 104), "g": rgb(180, 210, 216), "w": rgb(236, 248, 250),
              "P": rgb(240, 230, 206)}
APPLE_JUICE_P = dict(JUICE_BASE, L=rgb(240, 196, 70), l=rgb(212, 158, 44), F=rgb(206, 44, 36))
GRAPE_JUICE_P = dict(JUICE_BASE, L=rgb(132, 52, 122), l=rgb(98, 34, 92), F=rgb(110, 60, 150))
PINEAPPLE_JUICE_P = dict(JUICE_BASE, L=rgb(252, 222, 92), l=rgb(226, 188, 54), F=rgb(96, 160, 56))
PITAYA_JUICE_P = dict(JUICE_BASE, L=rgb(232, 72, 142), l=rgb(196, 46, 112), F=rgb(244, 244, 236))

# ── 파이 껍질 / 애플파이 (파이 틀) ──
PIE_CRUST = [
    "....cCcCcCcC....",
    "..cCddddddddCc..",
    ".cCddddddddddCc.",
    ".Cddddddddddddc.",
    "..CcCcCcCcCcCc..",
    "..tttttttttttt..",
    "...TTTTTTTTTT...",
]
APPLE_PIE = [
    "....cCcCcCcC....",
    "..cCLLLLLLLLCc..",
    ".cCLaLaLaLaLLCc.",
    ".CLLLLLLLLLLLLc.",
    ".cCLaLaLaLaLLCc.",
    "..CcCcCcCcCcCc..",
    "..tttttttttttt..",
    "...TTTTTTTTTT...",
]
PIE_P = {"c": rgb(232, 182, 106), "C": rgb(198, 138, 66), "d": rgb(244, 220, 172), "L": rgb(244, 200, 124),
         "a": rgb(170, 70, 40), "t": rgb(176, 180, 190), "T": rgb(132, 136, 148)}

# ── 식빵: 둥근 윗껍질과 칼집 ──
BREAD_LOAF = BLANK_ROWS * 5 + [
    "....bbbbbbbb....",
    "...bCCCCCCCCb...",
    "..bCCwCCCwCCCb..",
    "..bCwCCCwCCCwb..",
    "..bbbbbbbbbbbb..",
    "..BbbbbbbbbbbB..",
    "..BbbBbbbBbbbB..",
    "..BBBBBBBBBBBB..",
    "................",
    "................",
    "................",
]
BREAD_P = {"C": rgb(236, 182, 106), "w": rgb(252, 226, 164), "b": rgb(206, 140, 66), "B": rgb(166, 102, 44)}

# ── 치즈: 구멍 난 쐐기 ──
CHEESE = BLANK_ROWS * 5 + [
    ".........yyy....",
    ".......yyyyyY...",
    ".....yyyyyyYY...",
    "...yyyyyyyYYY...",
    "..ffffffffffFF..",
    "..ffhfffhfffFF..",
    "..fffffhffffFF..",
    "..fhffffffhfFF..",
    "..ffffffffffFF..",
    "................",
    "................",
]
CHEESE_P = {"y": rgb(252, 228, 124), "Y": rgb(236, 200, 92), "f": rgb(244, 202, 76), "F": rgb(214, 166, 52),
            "h": rgb(194, 144, 40)}

# ── 그릇 요리: 요구르트(꿀), 김치, 소고기 스튜, 옥수수 수프, 김치볶음밥 ──
YOGURT = TOP + [
    "................",
    "................",
    "......wwWw......",
    "....wwWwwwwe....",
    "..lwwqqwwwwwel..",
    ".lwWwwwqqwwwwem.",
]
YOGURT_P = {"w": rgb(248, 246, 238), "W": rgb(255, 255, 252), "e": rgb(220, 216, 204), "q": rgb(244, 178, 52)}
KIMCHI = TOP + [
    "................",
    ".......Rr.......",
    ".....rRgRr......",
    "...rRgrRgRrcRr..",
    "..rRgRrcrgRRrr..",
    ".lrRgRrcrgRRrml.",
]
KIMCHI_P = {"r": rgb(214, 70, 44), "R": rgb(170, 40, 28), "g": rgb(236, 220, 170), "c": rgb(120, 24, 18)}
BEEF_STEW_P = {"z": rgb(176, 100, 52), "y": rgb(140, 72, 36), "Y": rgb(104, 52, 26), "w": rgb(236, 214, 150),
               "W": rgb(196, 170, 110), "a": rgb(238, 120, 30), "e": rgb(76, 146, 44)}
CORN_SOUP_P = {"z": rgb(252, 232, 150), "y": rgb(242, 210, 100), "Y": rgb(214, 172, 62), "w": rgb(255, 242, 120),
               "W": rgb(236, 200, 70), "a": rgb(96, 168, 48), "e": rgb(76, 146, 44)}
KIMCHI_FRIED_RICE = TOP + [
    "................",
    ".....eeeee......",
    "....ieeyyeei....",
    "...iWiieeiiWij..",
    "..igIiWgiIgiij..",
    ".hiWgiIigWiIgjd.",
]
KIMCHI_FRIED_RICE_P = {"i": rgb(226, 112, 62), "I": rgb(190, 80, 40), "W": rgb(244, 152, 92), "j": rgb(150, 60, 30),
                       "g": rgb(96, 168, 48), "e": rgb(250, 248, 240), "y": rgb(252, 196, 40)}

# ── 고기: 훈제 소고기(그을린 겉과 분홍 단면), 베이컨 두 줄, 훈제 연어 ──
SMOKED_BEEF = BLANK_ROWS * 5 + [
    ".....bbbbb......",
    "...bbBBBBBbb....",
    "..bBBpPPpBBBb...",
    ".bBBpPPPPpBBBb..",
    ".bBpPPfPPPpBBb..",
    ".bBBpPPPPpBBBb..",
    "..bBBBpppBBBb...",
    "...bbBBBBBbb....",
    ".....bbbbb......",
    "................",
    "................",
]
SMOKED_BEEF_P = {"b": rgb(70, 36, 20), "B": rgb(110, 58, 32), "p": rgb(170, 70, 60), "P": rgb(206, 104, 96),
                 "f": rgb(240, 200, 180)}
BACON = BLANK_ROWS * 4 + [
    "...rrRRffrrRRf..",
    "..rrRRffrrRRff..",
    "..rRRffrrRRffr..",
    "...RRffrrRRff...",
    "................",
    "..ffrrRRffrrRR..",
    ".ffrrRRffrrRRf..",
    ".frrRRffrrRRff..",
    "..rRRffrrRRff...",
    "................",
    "................",
    "................",
]
BACON_P = {"r": rgb(206, 82, 70), "R": rgb(156, 48, 40), "f": rgb(246, 214, 196)}
SMOKED_SALMON = BLANK_ROWS * 5 + [
    "....ddddddd.....",
    "...dOOOwOOOd....",
    "..dOOwOOOwOOd...",
    ".dOwOOOwOOOwOd..",
    ".dOOOwOOOwOOOd..",
    "..dOOOwOOOwOd...",
    "...ddOOOwOOdd...",
    ".....ddddd......",
    "................",
    "................",
    "................",
]
SMOKED_SALMON_P = {"O": rgb(232, 118, 70), "w": rgb(250, 192, 152), "d": rgb(170, 66, 36)}

# ── 접시 요리: 베이컨 에그 ──
EGG = [
    ".eeeee..",
    "eeeyyee.",
    "eeyYyeee",
    "eeeyyeee",
    ".eeeeee.",
]
BACON_STRIP = ["rRfrRf", "RfrRfr"]
BACON_EGGS_P = {"e": rgb(250, 248, 240), "y": rgb(252, 200, 50), "Y": rgb(236, 160, 20),
                "r": rgb(206, 82, 70), "R": rgb(156, 48, 40), "f": rgb(246, 214, 196)}

# ── 피자 ──
PIZZA = [
    "....CCCCCCCC....",
    "..CcyyyyyyyycC..",
    ".CcyypyyyyRyycC.",
    ".CyyyyyRyypyyyC.",
    ".CyRyypyyygyyyC.",
    ".CcyyyyypyyyycC.",
    "..CcyyyyyyyycC..",
    "...CCCCCCCCCC...",
    "....BBBBBBBB....",
]
PIZZA_P = {"C": rgb(222, 160, 84), "c": rgb(240, 192, 112), "y": rgb(252, 222, 112), "p": rgb(176, 44, 34),
           "R": rgb(214, 60, 40), "g": rgb(70, 150, 50), "B": rgb(178, 118, 58)}

# ── 절구: 돌 그릇과 나무 공이 ──
MORTAR = [
    "................",
    "...........ww...",
    "..........wW....",
    ".........wW.....",
    "........wW......",
    ".......wW.......",
    "...ssSSSWSSss...",
    "..sLddddWdddLs..",
    "..sLLLLLLLLLLs..",
    "..sssssssssssS..",
    "..ssSsssssssSS..",
    "...ssssssssSS...",
    "....SSSSSSSS....",
    ".....SSSSSS.....",
    "................",
    "................",
]
MORTAR_P = {"s": rgb(152, 152, 156), "S": rgb(116, 116, 122), "L": rgb(198, 198, 202), "d": rgb(70, 70, 74),
            "w": rgb(192, 142, 86), "W": rgb(150, 104, 56)}


def pad(rows, top):
    """16x16 그림으로: 위에 빈 줄 top 개, 아래도 채움"""
    return BLANK_ROWS * top + rows + BLANK_ROWS * (16 - top - len(rows))




# ── 2판: 포대(밧줄로 묶은 삼베 자루 + 앞에 작물 그림), 조각 빠진 애플파이, 조각 빠진 피자 ──
import math as _math


def sack_icon(crop):
    """삼베 포대: 묶은 입구 위로 주름진 자락, 밧줄, 아래로 퍼진 몸통(엮은 결·꿰맨 바닥), 앞면 가운데 작물 그림"""
    img = blank(16)
    B0, B1, B2, B3 = rgb(222, 196, 146), rgb(204, 176, 124), rgb(176, 146, 98), rgb(140, 112, 72)
    rope = [rgb(150, 104, 56), rgb(112, 74, 38)]
    half = {1: 1.6, 2: 2.6, 3: 1.8, 4: 2.2, 5: 3.4, 6: 4.4, 7: 5.2, 8: 5.8, 9: 6.2, 10: 6.4, 11: 6.5, 12: 6.4, 13: 6.0, 14: 5.2}
    for y, h in half.items():
        for x in range(16):
            d = x + 0.5 - 8
            if abs(d) > h:
                continue
            if y == 3:
                img[y][x] = rope[(x + y) % 2]                                      # 밧줄
                continue
            t = d / max(h, 0.1)                                                     # -1 왼쪽 ~ 1 오른쪽
            c = B0 if t < -0.55 else (B1 if t < 0.35 else B2)
            if (x + y) % 2 == 0 and c != B0:
                c = B2 if c == B1 else B3                                           # 엮은 결
            if y <= 2 and x % 2 == 0:
                c = B2                                                              # 주름진 자락
            if y == 14:
                c = B3 if x % 2 else B2                                             # 꿰맨 바닥
            img[y][x] = c
    for (x, y), c in crop.items():
        img[y][x] = c
    return dark_outline(img)


_G1, _G2, _ST = rgb(252, 200, 56), rgb(206, 140, 30), rgb(112, 86, 32)
WHEAT_ART = {(8, 5): _G1, (7, 6): _G1, (9, 6): _G2, (8, 7): _G1, (7, 8): _G1, (9, 8): _G2, (8, 9): _G1, (6, 7): _G2,
             (10, 7): _G2, (6, 9): _G2, (10, 9): _G2, (8, 10): _ST, (8, 11): _ST, (8, 12): _ST, (7, 12): _ST}
CORN_ART = {(8, 6): rgb(252, 214, 80), (7, 7): rgb(252, 214, 80), (8, 7): rgb(236, 184, 50), (7, 8): rgb(236, 184, 50),
            (8, 8): rgb(252, 214, 80), (7, 9): rgb(252, 214, 80), (8, 9): rgb(236, 184, 50), (7, 10): rgb(236, 184, 50),
            (8, 10): rgb(252, 214, 80), (6, 9): rgb(96, 160, 56), (6, 10): rgb(96, 160, 56), (9, 9): rgb(80, 140, 46),
            (9, 10): rgb(80, 140, 46), (6, 11): rgb(80, 140, 46), (9, 11): rgb(96, 160, 56), (7, 11): rgb(96, 160, 56),
            (8, 11): rgb(80, 140, 46)}

APPLE_PIE2 = [
    "................",
    "................",
    "................",
    ".....cCcCcC.....",
    "...cCLLLLLLCc...",
    "..cLaaLaaLaaLc..",
    ".cLLLLLLLLLLLc..",
    ".cLaaLaaLffffc..",
    ".cLaaLaaLfFFFc..",
    ".CcCcCcCcfFfFc..",
    ".dddddddddkkkd..",
    "..ddddddddkkd...",
    "..tttttttttttt..",
    "...TTTTTTTTTT...",
    "................",
    "................",
]
APPLE_PIE2_P = {"c": rgb(236, 186, 108), "C": rgb(196, 134, 62), "L": rgb(244, 204, 128), "a": rgb(160, 64, 36),
                "f": rgb(240, 214, 120), "F": rgb(208, 150, 64), "d": rgb(214, 156, 82), "k": rgb(184, 124, 58),
                "t": rgb(176, 180, 190), "T": rgb(132, 136, 148)}


def pizza_icon():
    """피자 (위에서 본 둥근 판, 오른쪽 아래 한 조각이 빠짐): 두꺼운 테두리 빵, 토마토 소스 띠, 녹은 치즈,
    큰 페퍼로니, 바질, 조각 칼선"""
    img = blank(16)
    cx = cy = 7.5
    crust = [rgb(232, 170, 86), rgb(198, 132, 58)]
    for y in range(16):
        for x in range(16):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            r = _math.hypot(dx, dy)
            if r > 7.3:
                continue
            ang = _math.degrees(_math.atan2(dy, dx))
            if 5 <= ang <= 60:                                                     # 빠진 조각
                continue
            if r > 5.8:
                c = crust[0] if dy < 0 else crust[1]                               # 테두리 빵
            elif r > 5.0:
                c = rgb(204, 56, 36)                                               # 소스
            else:
                c = rgb(252, 216, 98) if (x * 3 + y) % 5 else rgb(240, 188, 70)    # 치즈
                if abs(ang - 150) < 4 or abs(ang + 90) < 4 or abs(ang + 30) < 4:
                    c = rgb(222, 170, 70)                                          # 조각 칼선
            img[y][x] = c
    for px, py in ((4, 4), (8, 3), (3, 8), (9, 7), (6, 10)):                       # 페퍼로니 (2x2 + 반짝)
        for ddx, ddy in ((0, 0), (1, 0), (0, 1), (1, 1)):
            img[py + ddy][px + ddx] = rgb(170, 40, 30)
        img[py][px] = rgb(214, 82, 64)
    for bx, by in ((6, 6), (11, 4)):
        img[by][bx] = rgb(70, 150, 50)
        img[by][bx + 1] = rgb(50, 120, 40)
    # 빠진 조각 자리 그늘 (판 아래)
    return dark_outline(img)


SPRITES = {
    "flour": lambda: sack_icon(WHEAT_ART),
    "cornmeal": lambda: sack_icon(CORN_ART),
    "pie_crust": lambda: single("pie_crust", pad(PIE_CRUST, 6), PIE_P),
    "bread_loaf": lambda: single("bread_loaf", BREAD_LOAF, BREAD_P),
    "apple_juice": lambda: single("apple_juice", JUICE, APPLE_JUICE_P),
    "grape_juice": lambda: single("grape_juice", JUICE, GRAPE_JUICE_P),
    "pineapple_juice": lambda: single("pineapple_juice", JUICE, PINEAPPLE_JUICE_P),
    "pitaya_juice": lambda: single("pitaya_juice", JUICE, PITAYA_JUICE_P),
    "cheese": lambda: single("cheese", CHEESE, CHEESE_P),
    "yogurt": lambda: bowl_dish("yogurt", YOGURT, YOGURT_P),
    "kimchi": lambda: bowl_dish("kimchi", KIMCHI, KIMCHI_P),
    "smoked_beef": lambda: single("smoked_beef", SMOKED_BEEF, SMOKED_BEEF_P),
    "bacon": lambda: single("bacon", BACON, BACON_P),
    "smoked_salmon": lambda: single("smoked_salmon", SMOKED_SALMON, SMOKED_SALMON_P),
    "beef_stew": lambda: bowl_dish("beef_stew", CHICKEN_SOUP, BEEF_STEW_P),
    "corn_soup": lambda: bowl_dish("corn_soup", CHICKEN_SOUP, CORN_SOUP_P),
    "bacon_and_eggs": lambda: plate_dish("bacon_and_eggs", (EGG, (2, 6)), (BACON_STRIP, (8, 8)), (BACON_STRIP, (7, 10)),
                                         palette=BACON_EGGS_P),
    "kimchi_fried_rice": lambda: bowl_dish("kimchi_fried_rice", KIMCHI_FRIED_RICE, KIMCHI_FRIED_RICE_P),
    "apple_pie": lambda: single("apple_pie", APPLE_PIE2, APPLE_PIE2_P),
    "pizza": pizza_icon,
    "mortar": lambda: single("mortar", MORTAR, MORTAR_P),
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

# 두 번째 세트 아이콘은 현실 모습을 참고한 귀여운 그림(icons2.py)으로 바꾼다
from icons2 import SET2  # noqa: E402
SPRITES.update(SET2)

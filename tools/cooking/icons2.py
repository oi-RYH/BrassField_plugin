"""
두 번째 요리 세트 아이콘 (16x16) — 현실에서 담아 먹는 모습을 참고해 아기자기·따뜻·귀엽게·맛있어 보이게 그린다.
(마인크래프트 3D 모델 모양은 따르지 않는다. 3D 손 모델은 make_food.py 가 따로 만든다)

- 글자 그리드(16줄 x 16칸) + 팔레트, 외곽선은 food_kit.dark_outline (이웃 색을 짙게 만든 따뜻한 테).
- 반짝이는 하이라이트(w), 김(v), 고명으로 맛있어 보이게.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from food_kit import dark_outline, rgb, blank  # noqa: E402

E = "................"


def grid(rows, palette, *overlays):
    """rows(16줄) 위에 overlays [(줄 목록, (x, y), 팔레트)] 를 덮어 그린 뒤 외곽선"""
    assert len(rows) == 16 and all(len(r) == 16 for r in rows), [len(r) for r in rows]
    img = blank(16)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                img[y][x] = palette[ch]
    for over, (ox, oy), pal in overlays:
        for j, row in enumerate(over):
            for i, ch in enumerate(row):
                if ch != "." and 0 <= ox + i < 16 and 0 <= oy + j < 16:
                    img[oy + j][ox + i] = pal[ch]
    return dark_outline(img)


def steam(img, cols=(6, 9), top=0):
    """반투명 김 두 가닥 (외곽선 뒤에 그려 테가 생기지 않게)"""
    for k, x0 in enumerate(cols):
        for i in range(3):
            x = x0 + (1 if (i + k) % 2 else 0)
            y = top + 2 - i
            if 0 <= y < 16 and img[y][x][3] == 0:
                img[y][x] = rgb(255, 255, 255, 150 - i * 30)
    return img


# ═════════════ 밀가루·옥수수가루: 종이 포대 위로 가루가 봉긋, 라벨에 작물 ═════════════
BAG = [
    E,
    E,
    ".....wWWWw......",
    "....wWWWWWw.....",
    "....pPPPPPPk....",
    "....pppppppk....",
    "....pLLLLLLk....",
    "....pLL1LLLk....",
    "....pL121LLk....",
    "....pLL21LLk....",
    "....pLL2LLLk....",
    "....pLLLLLLk....",
    "....pppppppk....",
    "....kkkkkkkk....",
    E, E,
]
BAG_P = {"p": rgb(220, 176, 116), "P": rgb(194, 150, 94), "k": rgb(176, 130, 78), "L": rgb(252, 244, 220)}
FLOUR_P = dict(BAG_P, w=rgb(246, 244, 236), W=rgb(255, 255, 255), **{"1": rgb(244, 186, 52), "2": rgb(176, 132, 52)})
CORNMEAL_P = dict(BAG_P, w=rgb(250, 212, 96), W=rgb(255, 236, 150), **{"1": rgb(252, 208, 56), "2": rgb(96, 164, 56)})

# ═════════════ 파이 껍질: 주름진 황금 테의 빈 파이 껍질 (파이 틀) ═════════════
PIE_SHELL = [
    E, E, E, E,
    ".....cCcCcC.....",
    "...cCddddddCc...",
    "..cdDddddddDdc..",
    "..cddddddddddc..",
    "..CcCcCcCcCcCC..",
    "..tttttttttttt..",
    "...TTTTTTTTTT...",
    E, E, E, E, E,
]
PIE_SHELL_P = {"c": rgb(240, 192, 110), "C": rgb(206, 146, 70), "d": rgb(248, 226, 180), "D": rgb(232, 204, 150),
               "t": rgb(190, 196, 206), "T": rgb(146, 152, 166)}

# ═════════════ 식빵: 봉긋한 두 봉우리 식빵 + 앞에 잘라 둔 한 조각 ═════════════
LOAF = [
    E, E, E,
    "....bbbb.bbbb...",
    "...bCwCCbCwCCb..",
    "...bCCCCCCCCCb..",
    "...bSSSSSSSSSb..",
    "...bSSSSSSSSSb..",
    "...bSSSSSSSSSb..",
    "...bSSSSSSSSSb..",
    "...bSSSSSSSSSb..",
    "...bbbbbbbbbbb..",
    E, E, E, E,
]
SLICE = [
    ".bbbb.",
    "bFFFFb",
    "bFfFFb",
    "bFFFfb",
    "bFFFFb",
    "bFfFFb",
    "bbbbbb",
]
LOAF_P = {"b": rgb(176, 104, 40), "C": rgb(232, 158, 66), "w": rgb(252, 208, 132), "S": rgb(218, 142, 58),
          "F": rgb(254, 246, 226), "f": rgb(236, 220, 186)}

# ═════════════ 주스: 빨대 꽂힌 유리잔, 가장자리에 과일 조각 ═════════════
GLASS = [
    E,
    "...........sS...",
    "..........sS....",
    ".........sS.....",
    "....gggGsSgg....",
    "....gwJJJJJg....",
    "....gwjjjjjg....",
    "....gwjjjjjg....",
    "....gjjjjjjg....",
    "....gjjjjjjg....",
    "....gjjjjjjg....",
    "....gjjjjjjg....",
    "....gggggggg....",
    ".....GGGGGG.....",
    E, E,
]
GLASS_BASE = {"g": rgb(196, 222, 228), "G": rgb(160, 190, 198), "w": rgb(250, 254, 255),
              "s": rgb(250, 250, 250), "S": rgb(226, 74, 86)}
APPLE_SLICE = ([".rr.", "rCCr", "rCcr", ".rr."], {"r": rgb(214, 40, 40), "C": rgb(252, 240, 200), "c": rgb(110, 70, 40)})
GRAPES = ([".g..", "pPp.", "PpPp", ".pP.", "..p."], {"g": rgb(96, 160, 56), "p": rgb(140, 60, 160), "P": rgb(100, 36, 120)})
PINE_WEDGE = (["g.g.", ".gg.", "yYy.", "YyyY"], {"g": rgb(96, 164, 56), "y": rgb(252, 220, 80), "Y": rgb(226, 176, 40)})
PITAYA_SLICE = ([".mm.", "mWkm", "mkWm", ".mm."], {"m": rgb(232, 60, 140), "W": rgb(252, 250, 246), "k": rgb(40, 30, 40)})


def juice(liquid, light, garnish):
    pal = dict(GLASS_BASE, J=light, j=liquid)
    art, gpal = garnish
    return grid(GLASS, pal, (art, (2, 2), gpal))


# ═════════════ 치즈: 반짝이는 구멍 치즈 쐐기 ═════════════
CHEESE = [
    E, E, E, E, E,
    ".........yyy....",
    ".......ywyyyY...",
    ".....yywyyyYY...",
    "...yyyyyyyYYY...",
    "..ffffffffffFF..",
    "..ffhfffhfffFF..",
    "..fffffhffffFF..",
    "..fhffffffhfFF..",
    "..ffffffffffFF..",
    E, E,
]
CHEESE_P = {"y": rgb(255, 230, 120), "w": rgb(255, 250, 210), "Y": rgb(242, 204, 90), "f": rgb(250, 206, 74),
            "F": rgb(222, 170, 50), "h": rgb(206, 150, 40)}

# ═════════════ 요구르트: 분홍 컵에 흰 요구르트, 꿀과 블루베리·딸기 ═════════════
YOGURT = [
    E, E,
    "......b.r.......",
    ".....wWbwrw.....",
    "....wwWwhhww....",
    "....cCCChCCc....",
    "....cBBBBBBc....",
    "....cCCCCCCc....",
    "....cCwCCCCc....",
    "....cCwCCCCc....",
    "....cCCCCCCc....",
    ".....cccccc.....",
    E, E, E, E,
]
YOGURT_P = {"w": rgb(250, 248, 242), "W": rgb(255, 255, 255), "b": rgb(90, 100, 210), "r": rgb(226, 44, 64),
            "h": rgb(246, 180, 52), "c": rgb(228, 164, 168), "C": rgb(252, 208, 210), "B": rgb(255, 244, 244)}

# ═════════════ 김치: 흰 사기 그릇(파란 띠)에 소복한 김치와 깨 ═════════════
KIMCHI = [
    E, E, E, E,
    "......rRr.......",
    "....rRgRsRr.....",
    "...rRgRrrgRsr...",
    "..rsRgRrRgRRrr..",
    "..eeeeeeeeeeee..",
    "..EbbbbbbbbbbE..",
    "..eeeeeeeeeeee..",
    "...eeeeeeeeee...",
    "....EEEEEEEE....",
    E, E, E,
]
KIMCHI_P = {"r": rgb(230, 70, 44), "R": rgb(180, 38, 26), "g": rgb(244, 230, 180), "s": rgb(255, 250, 230),
            "e": rgb(248, 248, 252), "E": rgb(204, 210, 224), "b": rgb(92, 124, 206)}

# ═════════════ 훈제 소고기: 그릴 자국 난 두툼한 고기 + 피어오르는 연기 ═════════════
SMOKED_BEEF = [
    E, E, E, E,
    "......ffff......",
    "....ffMMMMff....",
    "...fMMwMMMMMf...",
    "..fMMgMMgMMgMf..",
    "..fMgMMgMMgMMf..",
    "..fMMgMMgMMMMf..",
    "...fMMMMMMMMf...",
    "....ffMMMMff....",
    "......ffff......",
    E, E, E,
]
SPRIG = (["..g", ".gG", "gG."], {"g": rgb(110, 186, 70), "G": rgb(70, 140, 50)})
SMOKED_BEEF_P = {"M": rgb(156, 74, 40), "w": rgb(204, 120, 78), "g": rgb(84, 38, 20), "f": rgb(240, 206, 172)}


# ═════════════ 베이컨: 바삭하게 구워 물결치는 두 줄 + 반짝임 ═════════════
BACON = [
    E, E, E, E,
    "...rrRRffrrRRf..",
    "..rwRRffrwRRff..",
    "..rRRffrrRRffr..",
    "...RRffrrRRff...",
    E,
    "..ffrrRRffrrRR..",
    ".ffrwRRffrwRRf..",
    ".frrRRffrrRRff..",
    "..rRRffrrRRff...",
    E, E, E,
]
BACON_P = {"r": rgb(214, 86, 70), "R": rgb(164, 50, 40), "f": rgb(250, 222, 200), "w": rgb(255, 196, 180)}

# ═════════════ 훈제 연어: 부채꼴로 펼친 조각 + 레몬·딜 ═════════════
SALMON = [
    E, E, E,
    "..........ll....",
    ".........lYl....",
    "...OOwO..lll....",
    "..OOwOOOwOd.....",
    ".OOwOOOwOOOd....",
    ".OwOOOwOOOwOd...",
    "..OOOwOOOwOOd...",
    "...ddOOOwOOdd.g.",
    ".....ddddd...gg.",
    "............g...",
    E, E, E,
]
SALMON_P = {"O": rgb(246, 132, 80), "w": rgb(255, 204, 168), "d": rgb(200, 84, 48), "l": rgb(252, 230, 80),
            "Y": rgb(255, 250, 200), "g": rgb(90, 160, 60)}

# ═════════════ 그릇 요리 (스튜·수프): 흰 사기 그릇 + 김 ═════════════
SOUP = [
    E, E, E, E,
    E,
    ".......aW.......",
    ".....wWyae......",
    "...yzwWyaWwey...",
    "..eeeeeeeeeeee..",
    "..EzyYwWyzaYyE..",
    "..eeeeeeeeeeee..",
    "...eeeeeeeeee...",
    "....EEEEEEEE....",
    E, E, E,
]
BOWL_E = {"e": rgb(248, 246, 240), "E": rgb(214, 206, 196)}
BEEF_STEW_P = dict(BOWL_E, z=rgb(180, 102, 52), y=rgb(144, 74, 36), Y=rgb(110, 54, 26), w=rgb(240, 216, 150),
                   W=rgb(200, 172, 110), a=rgb(240, 124, 32), **{})
BEEF_STEW_P["e"], BEEF_STEW_P["E"] = BOWL_E["e"], BOWL_E["E"]
CORN_SOUP_P = dict(BOWL_E, z=rgb(254, 236, 156), y=rgb(246, 214, 106), Y=rgb(222, 178, 64), w=rgb(255, 244, 120),
                   W=rgb(240, 204, 70), a=rgb(96, 168, 48))

# ═════════════ 베이컨 에그: 접시 위 반숙 달걀프라이와 베이컨 두 줄 ═════════════
BACON_EGGS = [
    E, E, E, E, E,
    "...eeeee........",
    "..eeeyyee.rRfrR.",
    "..eeyYwyee.RfrRf",
    "..eeeyyeee.rRfr.",
    "...eeeeee..RfrR.",
    "..XWWWWWWWWWWX..",
    ".XWwwwwwwwwwwWX.",
    "..XYYYYYYYYYYX..",
    "...ZZZZZZZZZZ...",
    E, E,
]
BACON_EGGS_P = {"e": rgb(252, 250, 244), "y": rgb(252, 196, 40), "Y": rgb(240, 160, 20), "w": rgb(255, 236, 160),
                "r": rgb(214, 86, 70), "R": rgb(164, 50, 40), "f": rgb(250, 222, 200),
                "W": rgb(246, 248, 252), "X": rgb(200, 206, 216), "Y_": rgb(0, 0, 0), "Z": rgb(130, 136, 150)}
BACON_EGGS_P["Y"] = rgb(240, 160, 20)

# ═════════════ 김치볶음밥: 흰 그릇에 붉은 볶음밥, 위에 달걀프라이·파·깨 ═════════════
KFR = [
    E, E, E,
    "......eeee......",
    ".....eeyyee.....",
    "....ieyYwyei....",
    "...iWieeeeiWg...",
    "..igIiWsiIgiI...",
    "..oooooooooooo..",
    "..OboooooooobO..",
    "..oooooooooooo..",
    "...oooooooooo...",
    "....OOOOOOOO....",
    E, E, E,
]
KFR_P = {"i": rgb(230, 112, 60), "I": rgb(194, 80, 40), "W": rgb(248, 156, 96), "g": rgb(96, 172, 56),
         "s": rgb(255, 250, 230), "e": rgb(252, 250, 244), "y": rgb(252, 196, 40), "Y": rgb(240, 160, 20),
         "w": rgb(255, 236, 160), "o": rgb(248, 246, 240), "O": rgb(214, 206, 196), "b": rgb(230, 112, 60)}

# ═════════════ 애플파이: 접시 위 한 조각 (격자 윗면, 사과 속), 김 ═════════════
PIE_SLICE = [
    E, E, E, E,
    "...........cc...",
    ".........ccLLc..",
    ".......ccLaLLLc.",
    ".....ccLLLLaLLc.",
    "...ccLaLLLLLLLc.",
    "..ffffffffffffc.",
    "..fafffaffaffFc.",
    "..kkkkkkkkkkkkc.",
    ".XWWWWWWWWWWWWX.",
    "..XYYYYYYYYYYX..",
    E, E,
]
PIE_SLICE_P = {"c": rgb(214, 148, 70), "L": rgb(246, 204, 126), "a": rgb(196, 112, 50), "f": rgb(250, 220, 120),
               "F": rgb(226, 182, 80), "k": rgb(222, 166, 92), "W": rgb(246, 248, 252), "X": rgb(200, 206, 216),
               "Y": rgb(164, 170, 184)}


# ═════════════ 피자: 치즈가 늘어지는 한 조각 (위가 테두리 빵, 아래가 뾰족) ═════════════
def pizza_slice():
    img = blank(16)
    crust_hi, crust, cheese, cheese_hi, cheese_lo = (rgb(246, 196, 112), rgb(212, 146, 70), rgb(254, 214, 92),
                                                       rgb(255, 238, 160), rgb(240, 180, 60))
    top, bottom = 2, 13
    for y in range(top, bottom + 1):
        t = (y - top) / (bottom - top)
        half = 6.0 * (1 - t) + 0.4
        for x in range(16):
            d = x + 0.5 - 8
            if abs(d) > half:
                continue
            if y <= top + 1:
                img[y][x] = crust_hi if y == top else crust                       # 테두리 빵
            else:
                img[y][x] = cheese_hi if (d < -half + 1.2 and y < 8) else (cheese_lo if d > half - 1 else cheese)
    for px, py in ((5, 5), (9, 4), (7, 8), (10, 7)):                              # 페퍼로니
        for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
            if img[py + dy][px + dx][3]:
                img[py + dy][px + dx] = rgb(186, 44, 34)
        img[py][px] = rgb(232, 96, 76)
    img[6][8] = rgb(70, 152, 50)                                                  # 바질
    img[10][7] = rgb(70, 152, 50)
    img = dark_outline(img)
    for x, y0, n in ((6, 9, 2), (9, 8, 3)):                                       # 늘어지는 치즈
        for i in range(n):
            if y0 + i < 16 and img[y0 + i][x][3] == 0 or (y0 + i < 16 and i > 0):
                pass
        img[min(15, 13 + (x % 2))][x] = cheese_lo
    return img


# ═════════════ 절구: 돌 절구에 초록 허브, 나무 공이 ═════════════
MORTAR = [
    E,
    "...........ww...",
    "..........wW....",
    ".........wW.....",
    "........wW......",
    "....gG.wW.g.....",
    "...ssgSSWSGss...",
    "..sLddddWdddLs..",
    "..sLLLLLLLLLLs..",
    "..swsssssssssS..",
    "..ssSsssssssSS..",
    "...ssssssssSS...",
    "....SSSSSSSS....",
    ".....SSSSSS.....",
    E, E,
]
MORTAR_P = {"s": rgb(164, 162, 166), "S": rgb(124, 122, 128), "L": rgb(206, 204, 208), "d": rgb(76, 74, 78),
            "w": rgb(200, 150, 92), "W": rgb(156, 108, 58), "g": rgb(110, 186, 70), "G": rgb(70, 140, 50)}


def bowl_steam(rows, pal):
    return steam(grid(rows, pal), cols=(6, 9), top=1)


SET2 = {
    "flour": lambda: grid(BAG, FLOUR_P),
    "cornmeal": lambda: grid(BAG, CORNMEAL_P),
    "pie_crust": lambda: grid(PIE_SHELL, PIE_SHELL_P),
    "bread_loaf": lambda: grid(LOAF, LOAF_P, (SLICE, (1, 7), LOAF_P)),
    "apple_juice": lambda: juice(rgb(244, 196, 64), rgb(255, 226, 120), APPLE_SLICE),
    "grape_juice": lambda: juice(rgb(140, 50, 130), rgb(184, 90, 170), GRAPES),
    "pineapple_juice": lambda: juice(rgb(252, 216, 80), rgb(255, 238, 150), PINE_WEDGE),
    "pitaya_juice": lambda: juice(rgb(236, 74, 150), rgb(250, 140, 196), PITAYA_SLICE),
    "cheese": lambda: grid(CHEESE, CHEESE_P),
    "yogurt": lambda: grid(YOGURT, YOGURT_P),
    "kimchi": lambda: grid(KIMCHI, KIMCHI_P),
    "smoked_beef": lambda: steam(grid(SMOKED_BEEF, SMOKED_BEEF_P, (SPRIG[0], (11, 3), SPRIG[1])), cols=(6, 9), top=1),
    "bacon": lambda: grid(BACON, BACON_P),
    "smoked_salmon": lambda: grid(SALMON, SALMON_P),
    "beef_stew": lambda: bowl_steam(SOUP, BEEF_STEW_P),
    "corn_soup": lambda: bowl_steam(SOUP, CORN_SOUP_P),
    "bacon_and_eggs": lambda: grid(BACON_EGGS, BACON_EGGS_P),
    "kimchi_fried_rice": lambda: steam(grid(KFR, KFR_P), cols=(6, 9), top=0),
    "apple_pie": lambda: steam(grid(PIE_SLICE, PIE_SLICE_P), cols=(5, 8), top=1),
    "pizza": pizza_slice,
    "mortar": lambda: grid(MORTAR, MORTAR_P),
}


# ═════════════ 시안 2026-11-15: 애플파이·피자 통째 아이콘 ═════════════
WHOLE_PIE = [
    E, E,
    "......rRrR......",
    "....rRLaLaRr....",
    "..rRLLLLLLLLRr..",
    ".rRaLAaLaaLaaRr.",
    ".rRaLaaLaAaLaRr.",
    ".RLLLLLLLLLLLLr.",
    ".rRaLaaLaaLAaRr.",
    ".RrRrRrRrRrRrRr.",
    ".ssssssssssssss.",
    ".sSssSssSssSssS.",
    "..SSSSSSSSSSSS..",
    E, E, E,
]
WHOLE_PIE_P = {"r": rgb(244, 194, 106), "R": rgb(208, 142, 62), "L": rgb(252, 216, 140), "a": rgb(176, 46, 34),
               "A": rgb(224, 86, 60), "s": rgb(222, 158, 76), "S": rgb(182, 116, 48)}


def whole_apple_pie():
    """통 애플파이 (살짝 위에서): 주름진 두꺼운 테두리, 가로·세로 격자 사이로 붉은 사과 속, 옆면 껍질, 반짝임"""
    img = grid(WHOLE_PIE, WHOLE_PIE_P)
    for x, y in ((5, 4), (6, 4)):
        img[y][x] = rgb(255, 240, 190)
    return img


def whole_pizza():
    """통 피자 (위에서 본 둥근 판): 두꺼운 테두리 빵, 토마토 소스 띠, 녹은 치즈, 큰 페퍼로니, 바질"""
    img = blank(16)
    cx = cy = 7.5
    for y in range(16):
        for x in range(16):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            r = math.hypot(dx, dy)
            if r > 7.4:
                continue
            if r > 6.0:
                c = rgb(240, 186, 100) if dy < 0 and dx < 2 else (rgb(214, 150, 72) if dy < 2 else rgb(190, 124, 54))
            elif r > 5.5:
                c = rgb(206, 58, 38)                                               # 소스 (얇은 띠)
            else:
                c = rgb(254, 220, 104) if (x * 3 + y * 2) % 7 else rgb(242, 190, 72)   # 치즈
                if dx < -1 and dy < -1 and (x + y) % 3 == 0:
                    c = rgb(255, 238, 160)
            img[y][x] = c
    for px, py in ((4, 4), (9, 4), (4, 9), (9, 9)):                                # 페퍼로니 (둥근 3x3)
        for ddx, ddy in ((1, 0), (0, 1), (1, 1), (2, 1), (1, 2)):
            img[py + ddy][px + ddx] = rgb(180, 40, 30)
        for ddx, ddy in ((0, 0), (2, 0), (0, 2), (2, 2)):
            img[py + ddy][px + ddx] = rgb(200, 66, 46)                                # 둥근 모서리
        img[py + 1][px + 1] = rgb(226, 92, 72)
    for bx, by in ((7, 3), (11, 7), (7, 11), (3, 7)):                              # 바질
        img[by][bx] = rgb(76, 160, 54)
        img[by + 1][bx] = rgb(52, 120, 40)
    return dark_outline(img)


SET2["apple_pie"] = whole_apple_pie
SET2["pizza"] = whole_pizza


# ═════════════ 파이류 공통: 타르트 바탕 (사용자 시안 2026-11-15) + 가운데 우묵한 곳에 내용물 ═════════════
# 파이는 모두 이 타르트를 바탕으로 하고 내용물만 바꾼다. 빈 타르트 = 파이 껍질.
TART = [
    E, E, E, E,
    ".....aaaaaa.....",
    "...aabbbcccaa...",
    "..accdaaaadcca..",
    ".acdaaaaaaaadca.",
    ".acaaeeeeeeaace.",
    ".ecaeeeeeeeeabe.",
    ".efcdaeeeeacbae.",
    ".eaffcccbbbfaae.",
    "..eacffffcfcae..",
    "...eeaffcfaee...",
    ".....eeeeee.....",
    E,
]
TART_P = {"a": rgb(171, 119, 92), "b": rgb(254, 204, 126), "c": rgb(234, 181, 99), "d": rgb(216, 139, 80),
          "e": rgb(119, 86, 22), "f": rgb(213, 159, 75)}
# 내용물이 들어가는 우묵한 곳 (안쪽 벽 a·바닥 e 칸)
TART_HOLLOW = {(6, 6), (7, 6), (8, 6), (9, 6),
               *((x, 7) for x in range(4, 12)),
               (3, 8), (4, 8), *((x, 8) for x in range(5, 11)), (11, 8), (12, 8),
               (3, 9), *((x, 9) for x in range(4, 12)), (12, 9),
               (5, 10), *((x, 10) for x in range(6, 10)), (10, 10)}


def tart(filling=None):
    """타르트 바탕에 filling(x, y) → 색 (None 이면 빈 껍질) 을 우묵한 곳에 채운다"""
    rows = [list(r) for r in TART]
    img = blank(16)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == ".":
                continue
            c = TART_P[ch]
            if filling and (x, y) in TART_HOLLOW:
                c = filling(x, y) or c
            img[y][x] = c
    return dark_outline(img)


def apple_filling(x, y):
    """부채꼴로 겹쳐 놓은 사과 조각: 줄마다 앞쪽 가장자리에 얇은 붉은 껍질, 그 뒤로 윤기 나는 호박빛 과육"""
    skin = {(4, 7), (5, 7), (7, 7), (8, 7), (10, 7), (11, 7),
            (3, 9), (5, 9), (6, 9), (8, 9), (9, 9), (11, 9), (12, 9)}
    if (x, y) in skin:
        return rgb(190, 60, 44)                                                    # 붉은 껍질
    if (x, y) in ((6, 6), (7, 6), (5, 8), (6, 8)):
        return rgb(255, 236, 176)                                                  # 시럽 윤기
    return (rgb(246, 200, 104) if (x + y) % 2 else rgb(232, 176, 82)) if y < 10 else rgb(214, 150, 66)


SET2["pie_crust"] = lambda: tart()
SET2["apple_pie"] = lambda: tart(apple_filling)


# ═════════════ 피자 (사용자 시안 2026-11-16): 살짝 위에서 본 타원 피자 ═════════════
# 두꺼운 황금 테두리, 안쪽 토마토 소스 띠, 녹은 치즈(반짝임), 가운데서 퍼지는 8조각 칼선(치즈보다 살짝 짙게), 바질 잎, 토마토 조각, 앞쪽에 도우 두께
PIZZA_REF = [
    E, E,
    ".....KKKKKK.....",
    "...KKCSSSSCKK...",
    "..KCSSGyYYYSCK..",
    ".KCSYyTyTtWGSCK.",
    ".CSYGgyyYyTYYSC.",
    "KCSYYyyyyyyyTSCc",
    "CSTtYWyyYyGgYSCc",
    ".CSYGgYyYyYTtSC.",
    ".cCSYyYyYWyYSCc.",
    "..cCSSYyYYSSCc..",
    "...ccCCCCCCcc...",
    "...DDccccccDD...",
    ".....DDDDDD.....",
    E,
]
PIZZA_REF_P = {"K": rgb(250, 208, 124), "C": rgb(232, 168, 84), "c": rgb(194, 124, 54), "D": rgb(150, 90, 40),
               "S": rgb(204, 58, 36), "Y": rgb(252, 224, 136), "W": rgb(255, 246, 210), "y": rgb(236, 192, 100),
               "G": rgb(58, 128, 44), "g": rgb(98, 170, 62), "T": rgb(222, 70, 46), "t": rgb(168, 38, 28)}

SET2["pizza_hand"] = lambda: grid(PIZZA_REF, PIZZA_REF_P)                     # 손으로 다시 그린 판 (예비)


def pizza_from_art():
    """사용자 시안 그림을 줄여 만든 피자 아이콘 (tools/cooking/art/pizza.png, downsample_icon.py)"""
    import png as _png
    return _png.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), "art", "pizza.png"))


SET2["pizza"] = pizza_from_art


# ═════════════ 밀가루·옥수수가루 (사용자 시안 2026-11-16): 열린 삼베 자루 + 수북한 가루 + 앞면 작물 + 옆 가루 더미 ═════════════
SACK3 = [
    E,
    "......wWWw......",
    "..R.wwWWWWww.R..",
    "..RrswwWwwwsrR..",
    "..RrLLLLLLLLrR..",
    "...tTtTtTtTtT...",
    "..LbbbbbbbbbBb..",
    "..LbLbbbbbbkBb..",
    "..LbbLbbbbkbBb..",
    "..LbbbbbbbbbBb..",
    "..LLbbbbbbbbkb..",
    "..LbbLbbbbbkBb..",
    "..LbbbbbbbbbBB..",
    "...BBBBBBBBBB...",
    E,
    E,
]
SACK3_P = {"L": rgb(224, 190, 136), "b": rgb(198, 162, 110), "B": rgb(150, 116, 74), "k": rgb(172, 136, 90),
           "r": rgb(206, 170, 116), "R": rgb(140, 106, 64), "t": rgb(234, 200, 128), "T": rgb(170, 128, 70)}
WHEAT_MARK = (["..y..", ".yYy.", "yyYyy", ".yYy.", "yyYyy", "..Y..", "..Y.."],
              {"y": rgb(252, 198, 70), "Y": rgb(214, 148, 40)})
CORN_MARK = ([".YYY.", ".YyY.", "gYYYg", "gYyYg", ".gYg.", "..g..", "..g.."],
             {"Y": rgb(252, 212, 70), "y": rgb(232, 172, 40), "g": rgb(96, 162, 56)})
PILE = (["..W.", ".wWw", "wwws"], None)


def flour_sack(powder, shine, shade, mark):
    pal = dict(SACK3_P, w=powder, W=shine, s=shade)
    art, mpal = mark
    pile = (PILE[0], (12, 12), dict(w=powder, W=shine, s=shade))
    return grid(SACK3, pal, (art, (5, 6), mpal), pile)


SET2["flour"] = lambda: flour_sack(rgb(246, 244, 236), rgb(255, 255, 255), rgb(218, 212, 198), WHEAT_MARK)
SET2["cornmeal"] = lambda: flour_sack(rgb(252, 212, 90), rgb(255, 236, 146), rgb(224, 176, 58), CORN_MARK)


# ═════════════ 식빵·사과 주스·포도 주스 (사용자 시안 2026-11-16) ═════════════
# 식빵: 칼집 난 둥근 윗껍질의 식빵 한 덩이(왼쪽 끝은 부드러운 속살 단면) + 앞에 눕힌 한 조각
LOAF2 = [
    E,
    E,
    ".......cccccc...",
    ".....cCCwCCwCc..",
    "....cCCwCCwCCCc.",
    "...cFFFcCCwCCCc.",
    "...cFfFFcCCCCCc.",
    "...cFFFfcCCCCCc.",
    "...cFFFFcCCCCCd.",
    "...cFfFFcCCCCdd.",
    "...cFFFFcCCCddd.",
    "...ccccccddddd..",
    E, E, E, E,
]
LOAF_SLICE = [
    ".ccccc.",
    "cFFfFFc",
    "cFfFFFc",
    "cFFFFfc",
    ".ccccc.",
]
LOAF2_P = {"c": rgb(196, 112, 40), "C": rgb(232, 152, 62), "w": rgb(250, 194, 104), "d": rgb(162, 88, 30),
           "F": rgb(252, 234, 194), "f": rgb(234, 208, 158)}

# 주스 병: 코르크 마개 네모 유리병, 목에 감은 끈과 과일 그림 꼬리표, 병 앞에 과일
BOTTLE2 = [
    E,
    "......kkkk......",
    "......kKKk......",
    ".....gkKKkg.....",
    ".....gtTtTg.....",
    "....gwLLLLLgt...",
    "...gwLLLLLLLgPP.",
    "...gwLLLLLLLgPaP",
    "...gLLLLLLLLgPPP",
    "...gLLLLLLLlg...",
    "...glLLLLLLlg...",
    "...gllllllllg...",
    "....gggggggg....",
    E, E, E,
]
BOTTLE2_BASE = {"k": rgb(196, 140, 84), "K": rgb(222, 170, 110), "g": rgb(214, 228, 230), "w": rgb(255, 255, 255),
                "t": rgb(240, 220, 170), "T": rgb(200, 166, 104), "P": rgb(240, 222, 176)}
APPLE_FRUIT = (["...s..", "..Gs..", ".rrrr.", "rwRRRr", "rRRRRr", ".rRRr."],
               {"s": rgb(120, 80, 40), "G": rgb(96, 168, 56), "r": rgb(232, 64, 52), "R": rgb(206, 40, 36),
                "w": rgb(255, 170, 160)})
GRAPE_FRUIT = (["..G...", ".GGs..", "pPpPp.", ".pPpP.", "..pPp.", "...p.."],
               {"G": rgb(118, 176, 60), "s": rgb(120, 80, 40), "p": rgb(150, 70, 170), "P": rgb(104, 40, 124)})


def juice_bottle(liquid, dark, tag_mark, fruit):
    pal = dict(BOTTLE2_BASE, L=liquid, l=dark, a=tag_mark)
    art, fpal = fruit
    return grid(BOTTLE2, pal, (art, (0, 9), fpal))


SET2["bread_loaf"] = lambda: grid(LOAF2, LOAF2_P, (LOAF_SLICE, (0, 10), LOAF2_P))
SET2["apple_juice"] = lambda: juice_bottle(rgb(248, 180, 44), rgb(216, 134, 26), rgb(220, 50, 40), APPLE_FRUIT)
SET2["grape_juice"] = lambda: juice_bottle(rgb(156, 32, 74), rgb(112, 20, 52), rgb(130, 50, 150), GRAPE_FRUIT)


# ═════════════ 시안 축소본 손질 (2026-11-16): 색은 시안 축소본(art/*.png)에서, 뭉개진 형태만 손으로 ═════════════
# 식빵: 오른쪽 위로 뻗은 식빵 덩어리(칼집 난 윗껍질), 왼쪽 앞 크림색 속살 단면, 앞에 눕힌 한 조각
LOAF_REF = [
    E,
    E,
    "........hijjh...",
    "......hijkkjih..",
    ".....ijkjjkjjih.",
    "....jkjlljkjjli.",
    "...uqqjljkjlliig",
    "...qqqrljjlllih.",
    "...qrqqrlllllhg.",
    "..xqqqqrlilllhg.",
    ".xtxqqrrllllhg..",
    "xqqqqrxllllhf...",
    "tqqqrrtlhhgf....",
    ".ttxxtlhgff.....",
    "..ffgghf........",
    E,
]
LOAF_REF_P = {"h": rgb(182, 73, 6), "i": rgb(195, 82, 7), "j": rgb(237, 136, 38), "k": rgb(251, 163, 61),
              "l": rgb(215, 100, 11), "g": rgb(134, 49, 4), "f": rgb(163, 63, 5), "q": rgb(255, 220, 152),
              "r": rgb(255, 210, 134), "u": rgb(255, 198, 117), "x": rgb(255, 188, 103), "t": rgb(255, 179, 86)}

# 주스 병 (시안 색): 따뜻한 유리, 코르크, 끈·꼬리표, 병 앞 과일
BOTTLE_REF_BASE = {"k": rgb(232, 164, 62), "K": rgb(152, 118, 60), "g": rgb(200, 180, 166), "w": rgb(255, 214, 160),
                   "t": rgb(240, 214, 160), "T": rgb(178, 140, 84), "P": rgb(244, 220, 172)}
APPLE_REF = (["...s..", "..Gs..", ".rrrr.", "rwRRRr", "rRRRRr", ".rRRr."],
             {"s": rgb(105, 77, 25), "G": rgb(100, 156, 52), "r": rgb(234, 57, 36), "R": rgb(174, 26, 20),
              "w": rgb(255, 150, 130)})
GRAPE_REF = (["..G...", ".GGs..", "pPpPp.", ".pPpP.", "..pPp.", "...p.."],
             {"G": rgb(118, 160, 60), "s": rgb(122, 72, 47), "p": rgb(155, 58, 95), "P": rgb(102, 41, 77)})


def juice_bottle_ref(liquid, dark, tag_mark, fruit):
    pal = dict(BOTTLE_REF_BASE, L=liquid, l=dark, a=tag_mark)
    art, fpal = fruit
    return grid(BOTTLE2, pal, (art, (0, 9), fpal))


SET2["bread_loaf"] = lambda: grid(LOAF_REF, LOAF_REF_P)
SET2["apple_juice"] = lambda: juice_bottle_ref(rgb(255, 160, 5), rgb(206, 104, 8), rgb(234, 57, 36), APPLE_REF)
SET2["grape_juice"] = lambda: juice_bottle_ref(rgb(142, 31, 50), rgb(101, 23, 37), rgb(155, 58, 95), GRAPE_REF)


# ═════════════ 확정 (2026-11-16): 사용자 시안을 그대로 줄인 축소본 (tools/cooking/art/<ID>.png, shrink_icon.py) ═════════════
def art_icon(item_id):
    """시안 축소본 아이콘을 그대로 쓴다"""
    import png as _png
    return lambda: _png.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), "art", item_id + ".png"))


for _id in ("bread_loaf", "apple_juice", "grape_juice"):
    SET2[_id] = art_icon(_id)
for _id in ("pineapple_juice", "pitaya_juice", "cheese"):                       # 시안 축소본 (2026-11-16)
    SET2[_id] = art_icon(_id)
for _id in ("yogurt", "kimchi", "smoked_beef"):                                  # 시안 축소본 (2026-11-16)
    SET2[_id] = art_icon(_id)
for _id in ("bacon", "smoked_salmon"):                                           # 시안 축소본 (2026-11-16)
    SET2[_id] = art_icon(_id)
for _id in ("beef_stew", "corn_soup", "bacon_and_eggs", "kimchi_fried_rice", "apple_pie", "pizza", "mortar"):   # 시안 축소본 (2026-11-16)
    SET2[_id] = art_icon(_id)
for _id in ("flour", "cornmeal"):                                                # 시안 축소본 (2026-11-16)
    SET2[_id] = art_icon(_id)
for _id in ("salmon_sushi", "cabbage_wrap", "kimbap", "mushroom_fried_rice", "meatball_pasta", "ratatouille",
            "fried_rice", "dumplings", "cooked_rice", "honey_cookie", "hamburger", "patty",
            "tomato_sauce", "chicken_soup", "vegetable_soup"):                                     # 시안 축소본 (2026-11-16, 첫 세트 아이콘 교체)
    SET2[_id] = art_icon(_id)

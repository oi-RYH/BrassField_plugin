"""
개인 요리 기기 6종 모델 — 시안 2026-11-15 "요리 제작 시스템" (제분기·착즙기·발효조·훈연기·대형 솥·제빵 오븐).
플레이어가 각자 여러 개 설치하므로 바닥 1칸(1x1), 높이 2블록 이하. 앞면 = north, 키우지 않는다 (1픽셀 = 1/16 블록).
조리대와 같은 방식: 바닐라 블록 텍스처를 참조하고, 스팀펑크(황동·리벳 쇠판·구리·게이지·톱니)와 기기별 그림만 직접 그린다.
입체감: 빈 곳은 비우고(화덕·창 구멍, 깔때기, 유리 탱크) 채운 곳은 채운다(테·띠·손잡이는 튀어나옴).

사용: python3 -I tools/machines/make_cooking_tools.py <리소스팩 assets 폴더> [기기 이름 ...]
  → <assets>/rustport/models/machine/cooking/<이름>.json, textures/machine/cooking/<이름>/
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from furniture_kit import Model, CUSTOM, EXTERNAL, ANIMATED, BRASS, BRASS_MID, IRON, IRON_EDGE, IRON_BOLT, rgb, noisy, picture, add_framed_palette  # noqa: E402

FOLDER = "machine/cooking"

# ═════════════ 기기별 그림 ═════════════
K_IRON_DARK, K_IRON, K_EDGE = rgb(0x3B, 0x2B, 0x23), rgb(0x5A, 0x3E, 0x32), rgb(0x8B, 0x5A, 0x2B)
K_BRASS, K_BRASS_HI, K_FIRE, K_HOT = rgb(0xC9, 0x96, 0x44), rgb(0xF2, 0xC5, 0x5C), rgb(0xFF, 0x9A, 0x00), rgb(0xFF, 0xF4, 0xE0)


# 제빵 오븐: 레퍼런스 "제빵 오븐(베이커리 오븐)" 팔레트 (황동 #C9913D · #F2C55C · 테 #8B5A2B, 받침 #8B5A2B · #4A3224,
# 불 #FF8A00 · #FFB23D · #FFE9C8). 몸체는 솥과 같은 산업용 철
O_DARK, O_MID, O_EDGE, O_BRASS = rgb(0x4A, 0x32, 0x24), rgb(0x6B, 0x4A, 0x37), rgb(0x8B, 0x5A, 0x2B), rgb(0xC9, 0x91, 0x3D)
O_HI, O_GOLD, O_FIRE, O_HOT = rgb(0xF2, 0xC5, 0x5C), rgb(0xFF, 0xB2, 0x3D), rgb(0xFF, 0x8A, 0x00), rgb(0xFF, 0xE9, 0xC8)
add_framed_palette("o_brass", O_EDGE, O_EDGE, O_EDGE, O_HI, O_BRASS, O_BRASS, O_BRASS)
add_framed_palette("o_copper", O_DARK, O_DARK, O_DARK, O_BRASS, O_EDGE, O_EDGE, O_EDGE)
# 발효조: 레퍼런스 "발효조(양조 탱크)" 팔레트 (구리 #A86A3A · #6B4532, 받침 #3B2B22, 황동 #D9A23A · #F2C55C,
# 발효액 #FFB23D · #FF8A00 · 거품 #FFF3D9)
F_DARK, F_COPPER_D, F_COPPER, F_BRASS = rgb(0x3B, 0x2B, 0x22), rgb(0x6B, 0x45, 0x32), rgb(0xA8, 0x6A, 0x3A), rgb(0xD9, 0xA2, 0x3A)
F_HI, F_GOLD, F_FIRE, F_FOAM = rgb(0xF2, 0xC5, 0x5C), rgb(0xFF, 0xB2, 0x3D), rgb(0xFF, 0x8A, 0x00), rgb(0xFF, 0xF3, 0xD9)
add_framed_palette("f_brass", F_COPPER_D, F_COPPER_D, F_COPPER_D, F_HI, F_BRASS, F_BRASS, F_BRASS)
add_framed_palette("f_base", F_DARK, F_DARK, F_DARK, F_COPPER, F_COPPER_D, F_COPPER_D, F_COPPER_D)
# 훈연기: 레퍼런스 "훈연기(스모커)" 팔레트 (몸체 #5A3E32 · #3B2B23, 테 #8B5A2B, 황동 #C9913D · #F2C55C,
# 불 #FF8A00 · #FFB23D, 연기 · 유리 #FFF4E0)
S_DARK, S_BODY, S_EDGE, S_BRASS = rgb(0x3B, 0x2B, 0x23), rgb(0x5A, 0x3E, 0x32), rgb(0x8B, 0x5A, 0x2B), rgb(0xC9, 0x91, 0x3D)
S_HI, S_GOLD, S_FIRE, S_SMOKE = rgb(0xF2, 0xC5, 0x5C), rgb(0xFF, 0xB2, 0x3D), rgb(0xFF, 0x8A, 0x00), rgb(0xFF, 0xF4, 0xE0)
SMOKER_MEATS = ("beef", "porkchop", "salmon")                                          # 훈연기 레시피 재료 (훈제 소고기 · 베이컨 · 훈제 연어)
EXTERNAL.update({"meat_" + n: "minecraft:item/" + n for n in SMOKER_MEATS})            # 매다는 바닐라 고기 아이템 그림
add_framed_palette("s_brass", S_EDGE, S_EDGE, S_EDGE, S_HI, S_BRASS, S_BRASS, S_BRASS)
# 제분기: 레퍼런스 "제분기(밀가루 분쇄기)" 팔레트 (몸체 #6B4A37 · #3B2B23, 테 #8B5A2B, 황동 #C99644 · #FFB23D, 크림 #FFF4E0).
# 맷돌은 회색 돌 (방사형 홈 · 세로 홈). 깔때기 · 수납칸은 넣은 재료 (밀 · 옥수수 · 소고기) 에 따라 다르다
M_DARK, M_BODY, M_EDGE, M_BRASS = rgb(0x3B, 0x2B, 0x23), rgb(0x6B, 0x4A, 0x37), rgb(0x8B, 0x5A, 0x2B), rgb(0xC9, 0x96, 0x44)
M_GOLD, M_CREAM = rgb(0xFF, 0xB2, 0x3D), rgb(0xFF, 0xF4, 0xE0)
MILL_INGREDIENTS = {      # 재료 → (깔때기 낟알: 하이라이트 · 몸통 · 그늘 · 틈, 수납칸 결과물 바탕 · 점)
    "wheat": ((rgb(0xFF, 0xE2, 0x9A), M_GOLD, M_BRASS, M_EDGE), (M_CREAM, rgb(0xF2, 0xE6, 0xCC))),
    "corn": ((M_CREAM, rgb(0xFF, 0xD8, 0x6A), M_GOLD, M_BRASS), (rgb(0xFF, 0xD8, 0x6A), M_GOLD)),
    "beef": ((rgb(0xF0, 0x9A, 0x88), rgb(0xC8, 0x48, 0x3A), rgb(0x8E, 0x2C, 0x24), rgb(0x5A, 0x1E, 0x18)),
             (rgb(0x9A, 0x4A, 0x36), rgb(0xC8, 0x6A, 0x50))),
}
GRAIN_TILE = ["hbbg", "bbsg", "gggg"]     # 낟알 하나 (3x2 타원, 위왼쪽 하이라이트 · 아래오른쪽 그늘) + 틈, 줄마다 2칸 엇갈림
CHUNK_TILE = ["hhbbg", "hbbsg", "bbssg", "ggggg"]   # 고기 조각 (4x3)


def kernel_img(colors):
    """낟알 하나 (16x16, 면에 늘여 붙임): 둥근 모서리 · 위왼쪽 하이라이트 · 가운데 몸통 · 아래오른쪽 그늘"""
    h, b, sh, g = colors
    img = []
    for y in range(16):
        row = []
        for x in range(16):
            d = x + y
            if (x in (0, 15) and y in (0, 1, 14, 15)) or (y in (0, 15) and x in (0, 1, 14, 15)):
                c = sh                                                          # 깎인 모서리
            elif d < 9 and x < 9 and y < 9:
                c = h
            elif d > 21:
                c = sh
            else:
                c = b
            row.append(c)
        img.append(row)
    return img


STONE = [rgb(0xC8, 0xC4, 0xBC), rgb(0xA8, 0xA4, 0x9C), rgb(0x84, 0x80, 0x7A), rgb(0x5E, 0x5A, 0x55)]   # 맷돌 (밝음 → 어둠)


def stone_side(k, shift=0):
    """맷돌 옆면 (16x16, 면에 늘여 붙임): 둥근 명암 단계 k (0 = 앞으로 가장 나온 가운데 · 밝음, 2 = 양옆 · 어둠),
    위 깎인 가장자리 밝은 줄 · 아래 그늘 줄 · 성긴 옅은 세로 홈"""
    body = (STONE[0], STONE[1], STONE[2])[k]
    groove = (STONE[1], STONE[2], STONE[3])[k]
    img = []
    for y in range(16):
        row = []
        for x in range(16):
            if y < 2:
                c = STONE[0] if k < 2 else STONE[1]
            elif y > 13:
                c = STONE[3]
            elif (x + shift) % 8 == 4 and 3 < y < 13:
                c = groove
            else:
                c = body
            row.append(c)
        img.append(row)
    return img


def stone_top(turn=0.0):
    """맷돌 윗면 (16x16): 가장자리 밝은 테 · 가운데 구멍 · 8 방향 방사형 홈"""
    import math
    img = []
    for y in range(16):
        row = []
        for x in range(16):
            dx, dy = x - 7.5, y - 7.5
            r = math.hypot(dx, dy)
            ang = (math.degrees(math.atan2(dy, dx)) - turn) % 45
            if r < 1.8:
                c = STONE[3]                                                    # 가운데 구멍
            elif r < 2.8:
                c = STONE[2]
            elif x in (0, 15) or y in (0, 15):
                c = STONE[0]                                                    # 가장자리 테
            elif ang < 6:
                c = STONE[2]                                                    # 방사형 홈
            else:
                c = STONE[1]
            row.append(c)
        img.append(row)
    return img


def grain_img(colors, tile):
    h, b, sh, g = colors
    pal = {"h": h, "b": b, "s": sh, "g": g}
    th, tw = len(tile), len(tile[0])
    return [[pal[tile[y % th][(x + (tw // 2 if (y // th) % 2 else 0)) % tw]] for x in range(16)] for y in range(16)]
add_framed_palette("m_brass", M_EDGE, M_EDGE, M_EDGE, M_GOLD, M_BRASS, M_EDGE, M_GOLD)     # 기둥 · 테: 사선 하이라이트 결


def _lerp(c1, c2, k):
    return tuple(int(round(c1[i] + (c2[i] - c1[i]) * k)) for i in range(3)) + (255,)


def _shade(pal, v):
    """0(하이라이트) ~ 4(어둠) 실수 단계 → 색 (machine_kit.shade 와 같음)"""
    v = max(0.0, min(4.0, v))
    i = min(3, int(v))
    return _lerp(pal[i], pal[i + 1], v - i)


def metal_plate(pal, brushed="h"):
    """매끄러운 금속 판 (machine_kit.plate_fn 과 같은 방식): 위 밝고 아래로 살짝 어두운 명암 · 아주 옅은 결 · 사선 반사띠 ·
    위왼쪽 가장자리 반사 · 아래오른쪽 그늘. 면 하나에 한 장을 늘여 붙인다"""
    img = []
    for y in range(16):
        row = []
        for x in range(16):
            if y == 0 or x == 0:
                v = 0.6
            elif y == 15 or x == 15:
                v = 3.4
            else:
                v = 1.7 + 0.9 * y / 16
                v += 0.12 if (((y * 7) % 5 == 0) if brushed == "h" else ((x * 7) % 5 == 0)) else 0.0
                if abs((x + y) - 13) <= 1:
                    v -= 0.45
            row.append(_shade(pal, v))
        img.append(row)
    return img


def metal_rod(pal, vertical):
    """원통 명암 (machine_kit.rod_fn): 어둠 → 밝음 → 하이라이트 → 밝음 → 어둠 (16칸으로 늘림)"""
    profile = [3.2, 2.2, 1.2, 0.3, 0.9, 1.7, 2.4, 3.3]
    return [[_shade(pal, profile[(x if vertical else y) // 2]) for x in range(16)] for y in range(16)]


ANIMATED.update({"m_stone_spin_0": 2, "m_stone_spin_1": 2, "m_stone_spin_2": 2, "m_stone_top_spin": 2})   # 0.1 초마다 한 장면

FILL_LEVELS = (20, 50, 70)                                                             # 넣은 개수 단계 (%): 1~499 · 500~699 · 700 이상

JUICER_FRUITS = {        # 과일 → (아이템 그림, 주스 몸통 · 밝은 줄 · 거품 점)
    "apple": ("minecraft:item/apple", (M_GOLD, rgb(0xFF, 0xD2, 0x78), M_CREAM)),
    "grape": ("customcrops:item/crop/grape/grape", (rgb(0x7A, 0x2E, 0x6A), rgb(0xA8, 0x52, 0x94), rgb(0xD8, 0xA8, 0xD0))),
    "pineapple": ("customcrops:item/crop/pineapple/pineapple", (rgb(0xFF, 0xD8, 0x4A), rgb(0xFF, 0xEA, 0x8E), M_CREAM)),
    "pitaya": ("customcrops:item/crop/pitaya/pitaya", (rgb(0xD8, 0x32, 0x78), rgb(0xF0, 0x6E, 0xA4), rgb(0xFF, 0xD0, 0xE4))),
    "tomato": ("customcrops:item/crop/tomato/tomato", (rgb(0xD8, 0x3A, 0x2A), rgb(0xF0, 0x6A, 0x54), rgb(0xFF, 0xC8, 0xB8))),
}
EXTERNAL.update({"fruit_" + n: v[0] for n, v in JUICER_FRUITS.items()})               # 유리통에 담는 과일 아이템 그림

# 제분기 금속 명암 (밝음 → 어둠): 레퍼런스 팔레트 사이를 섞은 5 단계
MILL_BRASS_PAL = [_lerp(M_GOLD, M_CREAM, 0.45), M_GOLD, M_BRASS, _lerp(M_BRASS, M_EDGE, 0.6), M_EDGE]
MILL_BODY_PAL = [M_EDGE, _lerp(M_EDGE, M_BODY, 0.5), M_BODY, _lerp(M_BODY, M_DARK, 0.5), M_DARK]


def metal_block(edge, corner, line, body, low, shine):
    """노이즈 없는 금속 판 (16x16): 테 · 모서리(볼트) · 위왼쪽 밝은 줄 · 아래오른쪽 어두운 줄 + 대각선 반사 띠 두 줄"""
    img = clean_block(edge, corner, line, body, low)
    for y in range(2, 14):
        for x in range(2, 14):
            if x + y in (8, 9, 16):
                img[y][x] = shine
    return img
add_framed_palette("k_brass_framed", K_EDGE, K_EDGE, K_EDGE, K_BRASS_HI, K_BRASS, K_BRASS, K_BRASS)   # 결 없이 깔끔하게


def clean_block(edge, corner, line, body, low):
    """노이즈 없는 블록 면 (16x16): 바깥 1픽셀 테 · 네 모서리 · 안쪽 위·왼쪽 밝은 줄 · 아래·오른쪽 어두운 줄 · 나머지 한 색
    (Create 황동 블록 · 산업용 철 블록 형식, 결 무늬 없음)"""
    img = []
    for y in range(16):
        row = []
        for x in range(16):
            if (x, y) in ((0, 0), (15, 0), (0, 15), (15, 15)):
                c = corner
            elif x in (0, 15) or y in (0, 15):
                c = edge
            elif x == 1 or y == 1:
                c = line
            elif x == 14 or y == 14:
                c = low
            else:
                c = body
            row.append(c)
        img.append(row)
    return img
ART = dict(CUSTOM)
ART.update({
    "sack": noisy([rgb(222, 200, 156), rgb(204, 180, 136), rgb(236, 218, 178)], [4, 3, 2], 31),
    "apple": noisy([rgb(214, 40, 36), rgb(180, 26, 24), rgb(240, 90, 70)], [4, 3, 1], 33),
    "leaf": noisy([rgb(84, 156, 50), rgb(62, 128, 38)], [3, 2], 34),
    "porthole": picture([".bbbb.", "boooob", "boyoob", "booyob", "boooob", ".bbbb."],
                        {"b": BRASS[1], "o": rgb(244, 150, 46), "y": rgb(255, 214, 120)}),
    "ham": noisy([rgb(196, 70, 62), rgb(170, 52, 48), rgb(224, 120, 100), rgb(240, 200, 180)], [4, 3, 2, 1], 35),
    "bone": noisy([rgb(236, 228, 210), rgb(214, 204, 184)], [3, 1], 36),
    "ember": noisy([rgb(220, 70, 24), rgb(255, 150, 40), rgb(110, 30, 16), rgb(60, 24, 16)], [3, 2, 2, 2], 37),
    "pot": noisy([rgb(89, 88, 88), rgb(79, 79, 79), rgb(103, 97, 97)], [4, 3, 2], 38),   # 산업용 철과 같은 회색
    "milk_soup": noisy([rgb(246, 236, 210), rgb(232, 218, 186), rgb(252, 248, 232)], [4, 3, 2], 39),
    "bread": noisy([rgb(222, 150, 70), rgb(196, 120, 50), rgb(240, 186, 110)], [4, 3, 2], 40),
    # 대형 솥: 노이즈 없이. 몸체는 산업용 철 블록(형식·색), 황동·불은 레퍼런스 "스팀 조리기" 팔레트 (테 #8B5A2B, 황동 #C99644 · #F2C55C, 불 #FF9A00 · #FFF4E0)
    **{"mt_%s_%s" % (n, k): f for n, pal in (("brass", MILL_BRASS_PAL), ("body", MILL_BODY_PAL))
       for k, f in (("plate", metal_plate(pal)), ("rod_v", metal_rod(pal, True)), ("rod_h", metal_rod(pal, False)))},
    "m_body": metal_block(M_DARK, M_BRASS, M_EDGE, M_BODY, M_DARK, M_EDGE),             # 제분기 몸체 (갈색 금속 판 · 황동 볼트 · 반사 띠)
    "s_body": clean_block(S_DARK, S_DARK, S_EDGE, S_BODY, S_BODY),                      # 훈연기 몸체 (짙은 갈색 판, 결 없음)
    "c_copper": clean_block(F_COPPER_D, F_COPPER_D, F_BRASS, F_COPPER, F_COPPER),            # 구리 판 (테 · 밝은 줄, 결 없음)
    "c_iron": clean_block(IRON_EDGE, IRON_BOLT, IRON[0], IRON[1], IRON[2]),
    "k_iron": clean_block(IRON_EDGE, IRON_BOLT, IRON[0], IRON[1], IRON[2]),            # 산업용 철 블록 (형식 · 색 그대로, 결 없음)
    "k_iron_dark": clean_block(IRON[3], IRON[2], IRON[2], IRON[3], IRON[3]),           # 솥 안쪽 (산업용 철, 한 단계 어둡게)
    "k_brass": clean_block(K_EDGE, K_EDGE, K_BRASS_HI, K_BRASS, K_BRASS),              # Create 황동 블록 형식 · 팔레트 색 (결 없음)
    "k_rivet": noisy([K_EDGE], [1], 47),
    "k_glow": noisy([K_FIRE], [1], 44),                                                 # 불빛 (한 색)
    "k_steam": noisy([K_HOT], [1], 48),
    "k_firebox": picture(["bbbbbbbbbbbb", "bkfkhkfkhkfb", "bkhkhkhkhkhb", "bkhkhkhkhkhb", "bkfkhkfkhkfb",
                          "bkfkfkfkfkfb", "bkfkfkfkfkfb", "bkfkfkfkfkfb", "bbbbbbbbbbbb"],
                         {"b": K_BRASS, "k": K_IRON_DARK, "f": K_FIRE, "h": K_HOT}),
    "k_soup": picture(["ssssssssssssssss", "sssssbbsssssssss", "ssssbssbssssssss", "ssssbssbssssbbss", "sssssbbssssbssbs",
                       "sssssssssssbssbs", "ssssssssssssbbss", "ssssssssssssssss", "ssbbssssssssssss", "sbssbsssssssssss",
                       "sbssbssssssbbsss", "ssbbsssssssbbsss", "ssssssssssssssss", "sssssssbbsssssss", "ssssssbssbssssss",
                       "sssssssbbsssssss"], {"s": K_EDGE, "b": K_BRASS}),                     # 끓는 스튜 (한 색 + 거품 고리)
    "o_glow": noisy([O_GOLD], [1], 51),
    "o_fire": noisy([O_FIRE], [1], 52),
    "o_rivet": noisy([O_EDGE], [1], 53),
    "o_pie_top": picture(["..eeeeeeeeeeee..", ".egggggggggggge.", "egglggglggglgge", "eggglglglglglgge"[:16], "egglggglggglgge",
                          "eggglglglglglgge"[:16], "egglggglggglgge", ".egggggggggggge.", "..eeeeeeeeeeee.."],
                         {"e": O_EDGE, "g": O_GOLD, "l": O_BRASS}),
    "o_pie_side": noisy([O_BRASS], [1], 54),
    "o_dial": picture(["..bbbb..", ".bhhhhb.", "bhhhhfhb", "bhhhfhhb", "bhhkhhhb", "bhkhhhhb", ".bhhhhb.", "..bbbb.."],
                      {"b": O_BRASS, "h": O_HOT, "k": O_DARK, "f": O_FIRE}),
    "f_rivet": noisy([F_COPPER_D], [1], 61),
    "f_band": noisy([F_BRASS], [1], 64),
    "s_band": noisy([S_BRASS], [1], 71),
    "m_band": metal_block(M_EDGE, M_EDGE, M_GOLD, M_BRASS, M_EDGE, M_GOLD),             # 황동 띠 · 깔때기 (금속 판 · 반사 띠)
    "m_inner": noisy([M_DARK], [1], 82),
    "m_pane": [[rgb(255, 255, 255, 110) if (x + y) % 16 in (3, 4, 10) else rgb(0xFF, 0xF4, 0xE0, 40)
                for x in range(16)] for y in range(16)],
    **{"m_stone_side_%d" % k: stone_side(k) for k in range(3)},                       # 맷돌 옆면 (0 가운데 밝음 → 2 양옆 어둠)
    **{"m_stone_spin_%d" % k: [row for f in range(8) for row in stone_side(k, f)] for k in range(3)},   # 도는 윗돌 옆면 (홈이 흘러감, 8 장면)
    "m_stone_top_spin": [row for f in range(8) for row in stone_top(f * 45 / 8)],      # 도는 윗돌 윗면 (방사형 홈이 돎, 8 장면)
    "m_stone_top": stone_top(),                                                         # 맷돌 윗면 (방사형 홈 · 가운데 구멍)
    **{"j_juice_" + n: [[c[2] if (x * 7 + y * 5) % 23 == 0 else c[1] if y == 0 else c[0] for x in range(16)]
                        for y in range(16)] for n, (_, c) in JUICER_FRUITS.items()},   # 주스 (윗줄 밝게 · 거품 점)
    "j_gear": picture(["..b.bb.b..", ".bbbbbbbb.", "bbbkkkkbbb", ".bbk..kbb.", "bbk.hh.kbb", "bbk.hh.kbb",
                       ".bbk..kbb.", "bbbkkkkbbb", ".bbbbbbbb.", "..b.bb.b.."], {"b": M_GOLD, "k": M_BRASS, "h": M_EDGE}),
    "j_screw": [[_lerp(M_GOLD, M_EDGE, 0.7) if (y + x // 4) % 4 == 0 else M_BRASS if (y + x // 4) % 4 == 1 else M_GOLD
                 for x in range(16)] for y in range(16)],                              # 나사 기둥 (사선 나사산)
    "m_emblem": picture(["bbbbbb", "bkgkkb", "bkggkb", "bggkkb", "bkgkkb", "bbbbbb"], {"b": M_BRASS, "k": M_DARK, "g": M_GOLD}),
    "m_wheel": picture(["...bbbb...", ".bb.bb.bb.", ".b..bb..b.", "b...bb...b", "bbbbkkbbbb", "bbbbkkbbbb",
                        "b...bb...b", ".b..bb..b.", ".bb.bb.bb.", "...bbbb..."], {"b": M_BRASS, "k": M_EDGE}),
    "m_play_off": picture([".bb.", "bkbb", "bkkb", ".bb."], {"b": M_BRASS, "k": M_DARK}),
    "m_play_on": picture([".bb.", "bgbb", "bggb", ".bb."], {"b": M_BRASS, "g": M_GOLD}),
    "m_bar_off": picture(["bbbbbbbb", "bkkkkkkb", "bbbbbbbb"], {"b": M_BRASS, "k": M_DARK}),
    "m_bar_on": picture(["bbbbbbbb", "bggggkkb", "bbbbbbbb"], {"b": M_BRASS, "k": M_DARK, "g": M_GOLD}),
    **{"m_grain_" + n: grain_img(c, CHUNK_TILE if n == "beef" else GRAIN_TILE)
       for n, (c, _) in MILL_INGREDIENTS.items()},                                     # 깔때기 속 재료 (낟알 · 고기 조각 무늬)
    **{"m_kernel_" + n: kernel_img(c) for n, (c, _) in MILL_INGREDIENTS.items()},   # 낟알 · 고기 조각 하나 (면마다 늘여 붙임)
    **{"m_gap_" + n: noisy([c[3]], [1], 90) for n, (c, _) in MILL_INGREDIENTS.items()},  # 더미 바닥 (낟알 사이 틈)
    **{"m_pile_" + n: [[c[1] if (x + y * 3) % 6 == 0 else c[0] for x in range(16)] for y in range(16)]
       for n, (_, c) in MILL_INGREDIENTS.items()},                                     # 수납칸 결과물 더미
    "s_rivet": noisy([S_EDGE], [1], 72),
    "s_inner": noisy([S_DARK], [1], 73),
    "s_pane": [[rgb(255, 255, 255, 110) if (x + y) % 16 in (3, 4, 10) else rgb(0xFF, 0xF4, 0xE0, 40)
                for x in range(16)] for y in range(16)],
    "s_vent_off": picture(["bbbbbbbb", "bkbkbkbb", "bbbbbbbb"], {"b": S_BRASS, "k": S_DARK}),
    "s_vent_on": picture(["bbbbbbbb", "bfbgbfbb", "bbbbbbbb"], {"b": S_BRASS, "f": S_FIRE, "g": S_GOLD}),
    "s_play_off": picture([".bb.", "bkbb", "bkkb", ".bb."], {"b": S_BRASS, "k": S_DARK}),
    "s_play_on": picture([".bb.", "bfbb", "bffb", ".bb."], {"b": S_BRASS, "f": S_FIRE}),
    "s_bar_off": picture(["bbbbbbbb", "bkkkkkkb", "bbbbbbbb"], {"b": S_BRASS, "k": S_DARK}),
    "s_bar_on": picture(["bbbbbbbb", "bggggkkb", "bbbbbbbb"], {"b": S_BRASS, "k": S_DARK, "g": S_GOLD}),
    "s_grille": picture(["bbbbb", "bkkkb", "bbbbb", "bkkkb", "bbbbb", "bkkkb", "bbbbb"], {"b": S_BRASS, "k": S_DARK}),
    "f_inner": noisy([F_COPPER_D], [1], 65),                                            # 창 안쪽 벽 (짙은 구리)
    "f_pane": [[rgb(255, 255, 255, 110) if (x + y) % 16 in (3, 4, 10) else rgb(0xFF, 0xF3, 0xD9, 40)
                for x in range(16)] for y in range(16)],                               # 반투명 유리 (옅은 크림빛 + 대각선 반사)
    "f_liquid": [[F_HI if (x * 7 + y * 5) % 23 == 0 else F_GOLD for x in range(16)] for y in range(16)],   # 발효액 (기포 점)
    "f_foam": [[F_HI if (x + 2 * (y // 2)) % 5 == 0 else F_FOAM for x in range(16)] for y in range(16)],   # 거품                                                  # 황동 띠 · 테 (한 색)
    "f_dial": picture(["..bbbb..", ".bhhhhb.", "bhhhhfhb", "bhhhfhhb", "bhhkhhhb", "bhkhhhhb", ".bhhhhb.", "..bbbb.."],
                      {"b": F_BRASS, "h": F_FOAM, "k": F_DARK, "f": F_FIRE}),
    "f_power_off": picture([".bb.", "bkkb", "bkkb", ".bb."], {"b": F_BRASS, "k": F_COPPER_D}),
    "f_power_on": picture([".bb.", "bffb", "bffb", ".bb."], {"b": F_BRASS, "f": F_FIRE}),
    "f_bar_off": picture(["bbbbbbbb", "bddddddb", "bbbbbbbb"], {"b": F_BRASS, "d": F_DARK}),
    "f_bar_on": picture(["bbbbbbbb", "bggggddb", "bbbbbbbb"], {"b": F_BRASS, "d": F_DARK, "g": F_GOLD}),
    "k_dial": picture(["..bbbb..", ".bwwwwb.", "bwwwkwwb", "bwwkwwwb", "bwkwwwwb", "bwwwwwwb", ".bwwwwb.", "..bbbb.."],
                      {"b": K_BRASS, "w": K_HOT, "k": K_IRON_DARK}),
})


def legs(m, h, inset=1, size=2):
    """네 모서리 황동 다리"""
    for x in (inset, 16 - inset - size):
        for z in (inset, 16 - inset - size):
            m.box([x, 0, z], [x + size, h, z + size], "brass")


def ring(m, x0, x1, y0, y1, z0, z1, tex):  # noqa: E302
    """속이 빈 네모 테 (두께 1)"""
    m.box([x0, y0, z0], [x1, y1, z0 + 1], tex)
    m.box([x0, y0, z1 - 1], [x1, y1, z1], tex)
    m.box([x0, y0, z0 + 1], [x0 + 1, y1, z1 - 1], tex)
    m.box([x1 - 1, y0, z0 + 1], [x1, y1, z1 - 1], tex)


# ═════════════ 제분기 (1x1x2): 레퍼런스 "제분기(밀가루 분쇄기)" — 갈색 몸체 · 황동 테 프레임, 위 큰 깔때기, 앞 유리창 안 맷돌 두 짝 ·
# 아래 수납칸, 위 밀 문장, 오른쪽 큰 황동 바퀴, 왼쪽 배관 · 유리관, 받침대 재생 버튼 · 진행 막대.
# 재료가 없으면 빈 깔때기(mill), 재료를 넣으면 깔때기에 그 재료(mill_<재료>), 제분 중이면 수납칸 결과물 더미 · 버튼 · 막대 빛(mill_<재료>_on) ═════════════
def metal_box(m, u0, y0, w0, u1, y1, w1, tex, light=0, faces=None):
    """tex 가 "brass" · "body" 면 자판기 · 공작대 · 거래기와 같은 금속 명암 (얇고 긴 큐브는 원통, 나머지는 판재를 면마다 늘여 붙임)"""
    if tex in ("brass", "body"):
        dx, dy, dz = u1 - u0, y1 - y0, w1 - w0
        dims = sorted((dx, dy, dz))
        rod = dims[1] <= 2 and dims[2] >= 3 * dims[1]
        out = {}
        for view, (fw, fh) in (("front", (dx, dy)), ("back", (dx, dy)), ("left", (dz, dy)), ("right", (dz, dy)),
                               ("top", (dx, dz)), ("bottom", (dx, dz))):
            kind = "rod_v" if rod and fh >= 2 * fw else "rod_h" if rod and fw >= 2 * fh else "plate"
            out[view] = ("mt_%s_%s" % (tex, kind), [0, 0, 16, 16])
        out.update(faces or {})
        m.box([u0, y0, w0], [u1, y1, w1], "mt_%s_plate" % tex, light=light, faces=out)
        return
    m.box([u0, y0, w0], [u1, y1, w1], tex, light=light, faces=faces)


def mill(ingredient=None, lit=False, fill=70):
    """fill: 넣은 개수 단계 % (FILL_LEVELS) — 깔때기 낟알 더미가 20% 한 층 · 50% 두 층 · 70% 세 층"""
    m = Model("mill" + ("_%s_%d" % (ingredient, fill) if ingredient else "") + ("_on" if lit else ""))

    def b(u0, y0, w0, u1, y1, w1, tex, light=0, faces=None):
        if tex in ("brass", "body"):                                                   # 금속: 자판기 · 공작대 · 거래기와 같은 명암
            dx, dy, dz = u1 - u0, y1 - y0, w1 - w0
            dims = sorted((dx, dy, dz))
            rod = dims[1] <= 2 and dims[2] >= 3 * dims[1]
            out = {}
            for view, (fw, fh) in (("front", (dx, dy)), ("back", (dx, dy)), ("left", (dz, dy)), ("right", (dz, dy)),
                                   ("top", (dx, dz)), ("bottom", (dx, dz))):
                kind = "rod_v" if rod and fh >= 2 * fw else "rod_h" if rod and fw >= 2 * fh else "plate"
                out[view] = ("mt_%s_%s" % (tex, kind), [0, 0, 16, 16])
            out.update(faces or {})
            m.box([u0, y0, w0], [u1, y1, w1], "mt_%s_plate" % tex, light=light, faces=out)
            return
        m.box([u0, y0, w0], [u1, y1, w1], tex, light=light, faces=faces)

    def ring(u0, u1, y0, y1, w0, w1, tex):
        """속이 빈 네모 테 (두께 1)"""
        b(u0, y0, w0, u1, y1, w0 + 1, tex)
        b(u0, y0, w1 - 1, u1, y1, w1, tex)
        b(u0, y0, w0 + 1, u0 + 1, y1, w1 - 1, tex)
        b(u1 - 1, y0, w0 + 1, u1, y1, w1 - 1, tex)

    def plate(name, w, h, u0, y0, w0, light=0):
        b(u0, y0, w0, u0 + w, y0 + h, w0 + 0.5, "brass", light=light, faces={"front": (name, [0, 0, w, h])})

    for u, w in ((1, 2), (13, 2), (1, 12), (13, 12)):                                  # 다리
        b(u, 0, w, u + 2, 1, w + 2, "body")
    b(0.5, 1, 1, 15.5, 4.5, 15, "body")                                              # 받침대
    b(0.5, 4.5, 1, 15.5, 5, 15, "brass")                                              # 받침대 위 황동 띠 (받침대와 겹치지 않게)
    plate("m_play_on" if lit else "m_play_off", 4, 4, 1.5, 0.5, 0.5, light=10 if lit else 0)   # 재생 버튼
    plate("m_bar_on" if lit else "m_bar_off", 8, 3, 6.5, 1, 0.5, light=6 if lit else 0)        # 진행 막대
    # 몸체: 앞 창 (u 3~13, y 6~19) 을 w 9 까지 파낸다
    b(1, 5, 2, 3, 21, 14, "body")
    b(13, 5, 2, 15, 21, 14, "body")
    b(3, 5, 2, 13, 6, 14, "body")
    b(3, 19, 2, 13, 21, 14, "body")
    b(3, 6, 9, 13, 19, 14, "body")
    b(3, 6, 8.5, 13, 19, 9, "m_inner")                                                 # 창 안쪽 벽
    b(3, 6, 2, 3.5, 19, 8.5, {"all": "m_inner", "left": "mt_body_plate"})
    b(12.5, 6, 2, 13, 19, 8.5, {"all": "m_inner", "right": "mt_body_plate"})
    b(3.5, 18.5, 2, 12.5, 19, 8.5, "m_inner")
    b(3.5, 6, 2, 12.5, 6.5, 8.5, "m_inner")
    b(7, 17.75, 4.25, 9, 18.5, 6.25, "brass")                                          # 맷돌 위 깔때기 목 (창 위 천장)
    def millstone(y0, y1, r, spin=False):
        """둥근 맷돌 (가운데 u 8 · w 5.25, 반지름 r, 앞뒤는 창 깊이 안으로 눌림): 모서리를 두 번 깎은 세 큐브를 겹친다.
        앞뒤로 가장 나온 가운데 큐브 면은 밝게, 양옆으로 물러난 큐브 면은 어둡게 (원기둥처럼 휘어 보이게)"""
        k = min(1.0, 3.0 / r)                                                          # 앞뒤 반지름 비율 (창 안 깊이 w 2.25~8.25)
        side_name = "m_stone_spin_%d" if spin else "m_stone_side_%d"                    # spin: 도는 장면 그림 (제분 중 윗돌)
        for shade, (hu, hw) in ((2, (r, r * 0.45)), (1, (r * 0.82, r * 0.82)), (0, (r * 0.45, r))):
            side = (side_name % shade, [0, 0, 16, 16])
            stone = {v: side for v in ("front", "back")}
            stone.update({v: (side_name % 2, [0, 0, 16, 16]) for v in ("left", "right")})
            stone.update({"top": ("m_stone_top_spin" if spin else "m_stone_top", [0, 0, 16, 16]),
                          "bottom": ("m_stone_side_2", [0, 0, 16, 16])})
            b(8 - hu, y0, 5.25 - hw * k, 8 + hu, y1, 5.25 + hw * k, "m_inner", faces=stone)

    millstone(13.4, 15.2, 4.0)                                                          # 아래 바닥돌 (고정, 두툼)
    millstone(15.7, 17.3, 3.7, spin=bool(ingredient and lit))                           # 위 윗돌 (제분 중이면 홈이 흘러 도는 것처럼) · 사이 틈
    b(7.5, 17.3, 4.75, 8.5, 18.5, 5.75, "brass")                                        # 깔때기 목 → 윗돌 축
    b(3.5, 12.75, 2.5, 12.5, 13.25, 8.5, "brass")                                     # 맷돌 아래 칸막이
    if ingredient and lit:                                                             # 수납칸 결과물 더미 (가운데 높게)
        pile = "m_pile_" + ingredient
        b(4, 6.5, 3, 12, 8, 8, pile, light=4)
        b(5.5, 8, 4, 10.5, 9.5, 7.5, pile, light=4)
        b(7, 9.5, 5, 9, 10.5, 6.5, pile, light=4)
    b(3, 6, 1.9, 13, 19, 2, {"all": None, "front": "m_pane"})                          # 반투명 유리
    for y0, y1, u0, u1 in ((19, 20, 2, 14), (5, 6, 2, 14), (6, 19, 2, 3), (6, 19, 13, 14), (12.5, 13.5, 3, 13)):  # 창 황동 테 · 가운데 띠
        b(u0, y0, 1.5, u1, y1, 2, "brass")
    for u0 in (0.5, 14):                                                               # 네 모서리 황동 기둥
        for w0 in (1.5, 12.5):
            b(u0, 5, w0, u0 + 1.5, 21, w0 + 2, "brass")
    b(0.5, 21, 1.5, 15.5, 22.5, 14.5, "brass")                                        # 윗판 황동 띠
    plate("m_emblem", 4, 4, 6, 19.5, 1)                                                # 밀 문장
    # 깔때기: 목 · 아래로 좁고 위로 넓은 속 빈 단
    b(6, 22.5, 6, 10, 24, 10, "body")
    ring(5, 11, 24, 26, 5, 11, "brass")
    ring(3.5, 12.5, 26, 28, 3.5, 12.5, "brass")
    ring(2, 14, 28, 30, 2, 14, "brass")
    ring(1.5, 14.5, 30, 31, 1.5, 14.5, "brass")
    b(6, 24, 6, 10, 24.5, 10, "m_inner")                                               # 깔때기 바닥 (벽 안쪽에만)
    if ingredient:                                                                     # 깔때기 속 재료: 낟알(고기 조각)을 하나씩 쌓은 더미
        kernel = "m_kernel_" + ingredient
        b(4.5, 26, 4.5, 11.5, 28, 11.5, "m_gap_" + ingredient)                         # 깔때기 목 쪽 채움 · 더미 바닥 (틈 색)
        b(3, 28, 3, 13, 28.5, 13, "m_gap_" + ingredient)
        import random
        rnd = random.Random("mill-" + ingredient)                                      # 재료마다 정해진 무작위 (넣을 때마다 같은 모양)
        tex = {"uv": [0, 0, 16, 16], "texture": "#" + kernel}
        faces = {f: tex for f in ("north", "south", "east", "west", "up")}
        big = ingredient == "beef"
        layers = ((3.2, 12.8, 28.5, 22 if big else 40), (4.2, 11.8, 29.2, 14 if big else 26),
                  (5.5, 10.5, 29.9, 7 if big else 13), (6.8, 9.2, 30.1, 2 if big else 4))
        for lo, hi, y, n in layers[:{20: 1, 50: 2, 70: 3}.get(fill, 4)]:
            for _ in range(n):
                sx = rnd.uniform(1.8, 2.5) if big else rnd.uniform(1.1, 1.6)            # 크기도 조금씩 다르게
                sz = rnd.uniform(1.6, 2.3) if big else rnd.uniform(0.8, 1.2)
                sy = rnd.uniform(0.9, 1.3) if big else rnd.uniform(0.7, 1.0)
                cu = rnd.uniform(lo + sx / 2, hi - sx / 2)
                cw = rnd.uniform(lo + sx / 2, hi - sx / 2)
                cy = min(y + rnd.uniform(0, 0.35), 31 - sy)                            # 깔때기 테(31) 위로 넘지 않게
                axis = rnd.choices(("y", "x", "z"), (6, 2, 2))[0]                       # 대부분 수평으로 돌리고 일부는 기울임
                angle = rnd.choice((-45, -22.5, 22.5, 45)) if axis == "y" else rnd.choice((-22.5, 22.5))
                x = 16 - cu                                                            # 정면 기준 u → 모델 x
                m.raw([x - sx / 2, cy, cw - sz / 2], [x + sx / 2, cy + sy, cw + sz / 2], faces,
                      rotation={"origin": [x, cy + sy / 2, cw], "axis": axis, "angle": angle})
    # 오른쪽 큰 황동 바퀴: 바깥 면만 있는 그림 판을 몸체 밖으로 띄운다 (몸체 면과 겹치면 지직거림) · 가운데 입체 축
    b(15.75, 7, 3, 16.25, 17, 13, {"all": None}, faces={"right": ("m_wheel", [0, 0, 10, 10])})
    b(16.25, 11, 7, 17, 13, 9, "brass")
    b(15, 11.25, 7.25, 15.75, 12.75, 8.75, "brass")
    # 왼쪽 배관 · 유리관
    b(0, 17, 6, 1.5, 18, 10, "brass")                                                # 유리관 위 테
    b(0, 9, 6, 1.5, 10, 10, "brass")                                                 # 유리관 아래 테
    b(0.25, 10, 6.5, 1.25, 17, 9.5, "m_pane")
    b(0.25, 18, 7.5, 1.25, 24, 8.5, "brass")                                         # 위로 올라가는 배관
    return m


# ═════════════ 착즙기 (1x1x2): 레퍼런스 "착즙기(과일 프레스)" — 받침대 · 기둥 받침, 황동 테를 두른 반투명 유리통 (네 모서리 황동 기둥),
# 돔 뚜껑 · 나사 기둥 · T자 손잡이, 앞 꼭지 · 유리병, 오른쪽 압력계 · 옆 톱니, 받침대 재생 버튼 · 진행 막대.
# 재료가 없으면 빈 통(juicer), 과일을 넣으면 통 바닥에 그 과일 그림을 쌓음(juicer_<과일>), 착즙 중이면 압착판이 내려오고 과일 색 주스가
# 통 · 병에 차고 꼭지에 방울 (juicer_<과일>_on) ═════════════
def juicer(fruit=None, lit=False, fill=70):
    """fill: 넣은 과일 개수 단계 % (FILL_LEVELS). 쉬는 동안은 과일 더미, 착즙 중이면 주스가 통의 fill% 만큼 찬다"""
    m = Model("juicer" + ("_%s_%d" % (fruit, fill) if fruit else "") + ("_on" if lit else ""))
    level = fill / 10

    def b(*a, **k):
        metal_box(m, *a, **k)

    def plate(name, w, h, u0, y0, w0, light=0):
        b(u0, y0, w0, u0 + w, y0 + h, w0 + 0.5, "brass", light=light, faces={"front": (name, [0, 0, w, h])})

    pane = {"all": None}
    pane.update({v: "m_pane" for v in ("front", "back", "left", "right")})
    juice = "j_juice_" + fruit if fruit else None
    for u, w in ((1, 2), (13, 2), (1, 12), (13, 12)):                                  # 다리
        b(u, 0, w, u + 2, 1, w + 2, "body")
    b(0.5, 1, 1, 15.5, 3, 15, "body")                                                  # 받침대
    plate("m_play_on" if lit else "m_play_off", 3, 2, 9, 1, 0.5, light=10 if lit else 0)       # 재생 버튼
    plate("m_bar_on" if lit else "m_bar_off", 4, 1.5, 11.5, 1.25, 0.5, light=6 if lit else 0)  # 진행 막대
    b(4, 3, 4, 12, 7.5, 12, "body")                                                    # 기둥 받침
    b(3, 7.5, 3, 13, 9, 13, "brass")                                                   # 유리통 아래 테
    for u in (5, 8, 11):                                                               # 아래 테 리벳
        b(u - 0.25, 7.75, 2.75, u + 0.25, 8.75, 3, "m_inner")
    b(3.5, 9, 3.5, 12.5, 9.5, 12.5, "m_inner")                                         # 통 바닥
    # 통 안: 과일 (아이템 그림 십자 판) · 착즙 중이면 주스 · 내려온 압착판
    if fruit:
        import random
        rnd = random.Random("juicer-" + fruit)
        tex = {"uv": [0, 0, 16, 16], "texture": "#fruit_" + fruit}
        f = level / 10
        juice_top = 9.5 + max(0.5, f * 4.5)                                            # 착즙 중 주스 높이 (압착판 14.5 아래)
        pile_top = 9.5 + f * 10.5                                                      # 쉬는 동안 과일 더미 높이 (통 안 9.5 ~ 20)
        top = juice_top - 0.6 if lit else 9.5
        for _ in range(max(1, round(level * 0.4)) if lit else max(1, round(level * 1.4))):
            sz = rnd.uniform(4.2, 5.4)                                                 # 과일 그림 크기 (작으면 잘 안 보임)
            cu, cw = rnd.uniform(5.6, 10.4), rnd.uniform(5.6, 10.4)
            cy = top + rnd.uniform(0, 0.4) if lit else rnd.uniform(9.5, max(9.5, pile_top - sz))
            ang = rnd.choice((-45, -22.5, 0, 22.5, 45))
            x = 16 - cu
            for rot in (ang, ang + 90 if ang <= 0 else ang - 90):                     # 십자 두 판 (어느 쪽에서 봐도 보이게)
                m.raw([x - sz / 2, cy, cw], [x + sz / 2, cy + sz, cw], {"north": tex, "south": tex},
                      rotation={"origin": [x, cy, cw], "axis": "y", "angle": rot}, light=4 if lit else 0)
        if lit:
            b(3.6, 9.5, 3.6, 12.4, juice_top, 12.4, juice, light=8)                    # 주스 (개수만큼)
    press_y = 14.5 if lit else 18.5                                                    # 압착판 (착즙 중이면 내려옴)
    b(4, press_y, 4, 12, press_y + 1, 12, "brass")
    b(7.25, press_y + 1, 7.25, 8.75, 21, 8.75, "brass")                                # 압착판 → 뚜껑 축
    b(3.5, 9.5, 3.5, 12.5, 20, 12.5, pane)                                             # 반투명 유리통 (바깥 네 면)
    for u0 in (2.75, 12.25):                                                           # 네 모서리 황동 기둥
        for w0 in (2.75, 12.25):
            b(u0, 9, w0, u0 + 1, 20, w0 + 1, "brass")
    b(3, 20, 3, 13, 21.5, 13, "brass")                                                 # 유리통 위 테
    for u in (5, 8, 11):
        b(u - 0.25, 20.25, 2.75, u + 0.25, 21.25, 3, "m_inner")
    b(3.5, 21.5, 3.5, 12.5, 23, 12.5, "body")                                          # 돔 뚜껑
    b(5, 23, 5, 11, 24, 11, "body")
    b(6.5, 24, 6.5, 9.5, 24.75, 9.5, "brass")
    b(7.25, 24.75, 7.25, 8.75, 29.5, 8.75, "brass", faces={v: ("j_screw", [0, 0, 16, 16]) for v in ("front", "back", "left", "right")})  # 나사
    b(6.75, 29.5, 6.75, 9.25, 31, 9.25, "brass")                                       # T자 손잡이 가운데
    b(2, 29.75, 7.5, 14, 30.75, 8.5, "brass")                                          # 손잡이 막대
    for u0 in (1, 13):                                                                 # 손잡이 끝 손잡이 알
        b(u0, 29.5, 7, u0 + 2, 31, 9, "brass")
    # 앞 꼭지 · 유리병
    b(4.5, 11, 1.5, 6.5, 12.5, 3.5, "brass")                                           # 꼭지 (통에서 앞으로)
    b(4.75, 9, 1.5, 6.25, 11, 2.75, "brass")                                           # 꼭지 아래로 꺾임
    if lit:
        b(5.25, 8.25, 1.9, 5.75, 8.75, 2.35, juice, light=8)                           # 떨어지는 방울
    b(3, 3, 0.25, 8, 7, 3.75, pane)                                                    # 유리병 (반투명)
    b(3.5, 7, 0.75, 7.5, 7.75, 3.25, "brass")                                          # 병 뚜껑 테
    if lit:
        b(3.25, 3, 0.5, 7.75, 5.5, 3.5, juice, light=6)                                # 병 속 주스
    # 오른쪽: 압력계 · 옆 톱니
    b(13, 15, 2.5, 14, 16, 3.5, "brass")                                               # 압력계 받침 (유리통 오른쪽 기둥)
    plate("o_dial", 4.5, 4.5, 11.75, 13.25, 1.75)                                      # 압력계 (오른쪽 앞, 크게)
    b(16, 18, 5, 16.5, 24, 11, {"all": None}, faces={"right": ("j_gear", [0, 0, 10, 10])})   # 옆 톱니 (바깥 면만, 몸체와 띄움)
    b(15.5, 20.5, 7.5, 16.5, 21.5, 8.5, "brass")                                       # 톱니 축
    b(12.5, 20.5, 7.5, 15.5, 21.5, 8.5, "brass")
    return m


# ═════════════ 훈연기 (1x1x2): 레퍼런스 "훈연기(스모커)" — 짙은 갈색 캐비닛, 네 모서리 황동 기둥 · 위아래 띠 · 리벳, 계단 뚜껑,
# 앞 큰 창 (파낸 공간 + 반투명 유리, 걸이 막대 · 갈고리), 창 아래 통풍구, 받침대 앞 재생 버튼 · 진행 막대, 위 굴뚝 · 오른쪽 배관 · 유리관,
# 왼쪽 통풍 그릴. 재료가 없으면 빈 갈고리(smoker), 고기를 넣으면 그 고기 3개를 매닮(smoker_<고기>), 훈연 중이면 통풍구 · 재생 버튼이
# 빛나고 진행 막대가 참(smoker_<고기>_on). 연기는 플러그인 입자 (굴뚝 모닥불 연기 · 창 안 바닥 작은 연기) ═════════════
def smoker(meat=None, lit=False, fill=70):
    """meat: 갈고리에 건 고기 (넣은 재료, None 이면 빈 갈고리), lit: 훈연 중 (통풍구 · 재생 버튼 빛, 진행 막대),
    fill: 넣은 개수 단계 % (FILL_LEVELS) — 거는 고기 20% 1개(가운데) · 50% 2개 · 70% 3개"""
    m = Model("smoker" + ("_%s_%d" % (meat, fill) if meat else "") + ("_on" if lit else ""))
    hung = {20: (1,), 50: (0, 2), 70: (0, 1, 2)}.get(fill, (0, 1, 2))

    def b(u0, y0, w0, u1, y1, w1, tex, light=0, faces=None):
        m.box([u0, y0, w0], [u1, y1, w1], tex, light=light, faces=faces)

    def plate(name, w, h, u0, y0, w0, light=0):
        b(u0, y0, w0, u0 + w, y0 + h, w0 + 0.5, "s_brass", light=light, faces={"front": (name, [0, 0, w, h])})

    for u, w in ((0.5, 1.5), (13.5, 1.5), (0.5, 12.5), (13.5, 12.5)):                  # 황동 다리
        b(u, 0, w, u + 2, 1, w + 2, "s_brass")
    b(0, 1, 1, 16, 6, 15, "s_body")                                                    # 받침대
    plate("s_play_on" if lit else "s_play_off", 4, 4, 1.5, 1.5, 0.5, light=10 if lit else 0)   # 재생 버튼
    plate("s_bar_on" if lit else "s_bar_off", 8, 3, 6.5, 2, 0.5, light=6 if lit else 0)        # 진행 막대
    # 캐비닛: 앞 창 자리 (u 3~13, y 10~23) 를 w 8 까지 파낸다
    b(1, 6, 2, 3, 26, 14, "s_body")
    b(13, 6, 2, 15, 26, 14, "s_body")
    b(3, 6, 2, 13, 10, 14, "s_body")
    b(3, 23, 2, 13, 26, 14, "s_body")
    b(3, 10, 8, 13, 23, 14, "s_body")
    b(3, 10, 7.5, 13, 23, 8, "s_inner")                                                # 창 안쪽 벽
    b(3, 10, 2, 3.5, 23, 7.5, {"all": "s_inner", "left": "s_body"})
    b(12.5, 10, 2, 13, 23, 7.5, {"all": "s_inner", "right": "s_body"})
    b(3.5, 22.5, 2, 12.5, 23, 7.5, "s_inner")
    b(3.5, 10, 2, 12.5, 10.5, 7.5, "s_inner")
    b(3.5, 20.5, 4.5, 12.5, 21, 5.5, "s_band")                                         # 걸이 막대
    for i, (u, w) in enumerate(((4.0, 4.6), (7.5, 5.0), (11.0, 4.8))):              # 갈고리 · 고기 (단계만큼)
        b(u + 0.25, 19.5, 4.75, u + 0.75, 20.5, 5.25, "s_band")
        if meat and i in hung:                                                                       # 넣은 고기의 바닐라 아이템 그림 판 (대각선 그림을 45도 돌려 세로로 매닮)
            cu, cy, half = u + 0.5, 16.4, 2.5
            face = {"uv": [0, 0, 16, 16], "texture": "#meat_" + meat}
            m.raw([16 - (cu + half), cy - half, w], [16 - (cu - half), cy + half, w], {"north": face, "south": face},
                  rotation={"origin": [16 - cu, cy, w], "axis": "z", "angle": -45}, light=6 if lit else 0)
    b(3, 10, 1.9, 13, 23, 2, {"all": None, "front": "s_pane"})                         # 반투명 유리
    for y0, y1, u0, u1 in ((23, 24, 2, 14), (9, 10, 2, 14), (10, 23, 2, 3), (10, 23, 13, 14)):   # 창 황동 테
        b(u0, y0, 1.5, u1, y1, 2, "s_brass")
    plate("s_vent_on" if lit else "s_vent_off", 8, 3, 4, 6.5, 1.5, light=12 if lit else 0)    # 통풍구
    for u0 in (0.5, 14):                                                               # 네 모서리 황동 기둥
        for w0 in (1.5, 12.5):
            b(u0, 6, w0, u0 + 1.5, 26, w0 + 2, "s_brass")
    for y0 in (6, 25):                                                                 # 위아래 황동 띠
        b(0.5, y0, 1.5, 15.5, y0 + 1, 14.5, "s_band")
    for u in (3, 6, 9, 12):                                                            # 위 띠 리벳
        b(u, 25.25, 1.25, u + 1, 25.75, 1.5, "s_rivet")
    b(1.5, 26, 2.5, 14.5, 27, 13.5, "s_body")                                          # 계단 뚜껑
    b(2.5, 27, 3.5, 13.5, 28, 12.5, "s_body")
    b(5, 28, 6, 9, 30.5, 10, {"all": "s_body", "top": "s_inner"})                      # 굴뚝
    b(4.5, 30.5, 5.5, 9.5, 31.5, 10.5, {"all": "s_brass", "top": "s_inner"})
    b(9, 28.5, 7, 14, 30, 9, "s_brass")                                                # 오른쪽으로 가는 배관
    b(13.5, 22, 7, 15, 30, 9, "s_brass")                                               # 내려오는 배관
    b(14, 21, 6.5, 16, 22, 9.5, "s_brass")                                             # 유리관 위 테
    b(14, 13, 6.5, 16, 14, 9.5, "s_brass")                                             # 유리관 아래 테
    b(14.25, 14, 7, 15.75, 21, 9, "s_pane")                                            # 반투명 유리관
    b(13.5, 10, 7, 15, 13, 9, "s_brass")                                               # 아래 배관 → 캐비닛
    b(0.5, 12, 6, 1, 19, 11, "s_brass", faces={"left": ("s_grille", [0, 0, 5, 7])})    # 왼쪽 통풍 그릴
    return m


# ═════════════ 발효조 (1x1x2): 레퍼런스 "발효조(양조 탱크)" — 팔각 구리 탱크, 위아래 황동 테 · 리벳 · 세로 띠, 앞 큰 유리창,
# 돔 뚜껑 · 꼭대기 배관, 오른쪽 계기판 배관 · 유리관, 앞 밸브 바퀴, 구리 다리, 받침대 앞 전원 버튼 · 진행 막대.
# 쉬는 동안(fermenter)은 빈 유리, 발효 중(fermenter_on)은 노란 발효액 · 거품, 유리관 · 전원 버튼 빛, 진행 막대 참 ═════════════
def fermenter(lit=False):
    m = Model("fermenter_on" if lit else "fermenter")

    def b(u0, y0, w0, u1, y1, w1, tex, light=0, faces=None):
        m.box([u0, y0, w0], [u1, y1, w1], tex, light=light, faces=faces)

    def octa(y0, y1, inset, cut, tex, light=0):
        """팔각 기둥 (16 칸 안, 모서리 cut 칸 깎음)"""
        b(inset + cut, y0, inset, 16 - inset - cut, y1, 16 - inset, tex, light)
        b(inset, y0, inset + cut, inset + cut, y1, 16 - inset - cut, tex, light)
        b(16 - inset - cut, y0, inset + cut, 16 - inset, y1, 16 - inset - cut, tex, light)

    def plate(name, w, h, u0, y0, w0, light=0):
        b(u0, y0, w0, u0 + w, y0 + h, w0 + 1, "f_brass", light=light, faces={"front": (name, [0, 0, w, h])})

    for u, w in ((1, 2), (13, 2), (1, 12), (13, 12)):                                  # 받침 다리
        b(u, 0, w, u + 2, 1, w + 2, "f_base")
    b(0, 1, 1, 16, 5, 15, "f_base")                                                    # 받침대
    plate("f_power_on" if lit else "f_power_off", 4, 4, 1.5, 1, 0, light=10 if lit else 0)   # 전원 버튼
    plate("f_bar_on" if lit else "f_bar_off", 8, 3, 6.5, 1.5, 0, light=6 if lit else 0)       # 진행 막대
    for u, w in ((2, 3), (12, 3), (2, 11), (12, 11)):                                  # 구리 다리 (받침 → 탱크)
        b(u, 5, w, u + 2, 8, w + 2, "f_brass")
    # 구리 탱크 (팔각): 앞 가운데 판을 창 높이에서 w 7 까지 파낸다 (유리 너머 안이 보이게)
    b(2, 8, 5, 5, 23, 11, "c_copper")
    b(11, 8, 5, 14, 23, 11, "c_copper")
    b(5, 8, 2, 11, 11, 14, "c_copper")
    b(5, 21, 2, 11, 23, 14, "c_copper")
    b(5, 11, 7, 11, 21, 14, "c_copper")
    b(5, 11, 6.5, 11, 21, 7, "f_inner")                                                # 창 안쪽 벽 (뒤 · 옆 · 위 · 아래)
    b(5, 11, 2, 5.5, 21, 6.5, {"all": "f_inner", "left": "c_copper"})                 # 바깥 면은 구리 (모서리 틈으로 보임)
    b(10.5, 11, 2, 11, 21, 6.5, {"all": "f_inner", "right": "c_copper"})
    b(5.5, 20.5, 2, 10.5, 21, 6.5, "f_inner")
    b(5.5, 11, 2, 10.5, 11.5, 6.5, "f_inner")
    if lit:                                                                            # 발효액 (빛남) + 거품
        b(5.5, 11.5, 2.5, 10.5, 16.5, 6.5, "f_liquid", light=9)
        b(5.5, 16.5, 2.5, 10.5, 18, 6.5, "f_foam", light=9)
    b(5, 11, 1.9, 11, 21, 2, {"all": None, "front": "f_pane"})                         # 반투명 유리 (앞면만)
    b(4, 10, 1.5, 12, 11, 2, "f_brass")                                                # 창 아래 테
    for y0 in (8, 21):                                                                 # 위아래 황동 테 (1픽셀 튀어나옴)
        octa(y0, y0 + 2, 1, 4, "f_band")
    for k in (5, 8, 11):                                                               # 테 리벳 (앞 · 뒤 · 옆)
        for y in (8.5, 21.5):
            for u0, w0, u1, w1 in ((k, 0.5, k + 1, 1), (k, 15, k + 1, 15.5), (0.5, k, 1, k + 1), (15, k, 15.5, k + 1)):
                b(u0, y, w0, u1, y + 1, w1, "f_rivet")
    for u in (4, 11):                                                                  # 앞 세로 황동 띠 (창 양옆)
        b(u, 10, 1.5, u + 1, 21, 2, "f_brass")
    for u0, y0, u1, y1 in ((6.5, 8, 9.5, 8.5), (6.5, 11.5, 9.5, 12), (6, 8.5, 6.5, 11.5), (9.5, 8.5, 10, 11.5),
                           (7.75, 8.5, 8.25, 11.5), (6.5, 9.75, 9.5, 10.25)):           # 앞 밸브 바퀴
        b(u0, y0, 0.5, u1, y1, 1, "f_brass")
    octa(23, 25, 3, 3, "c_copper")                                                     # 돔 뚜껑
    octa(25, 27, 4, 3, "c_copper")
    b(6, 27, 6, 10, 28, 10, "f_band")                                                  # 꼭대기 테
    b(7, 28, 7, 9, 31, 9, "c_iron")                                                    # 꼭대기 배관
    b(6.5, 31, 6.5, 9.5, 32, 9.5, "f_brass")
    b(9, 28, 7.5, 13, 29.5, 8.5, "f_brass")                                            # 계기판 배관 (위 → 오른쪽)
    b(12, 23, 7.5, 13.5, 29.5, 8.5, "f_brass")
    plate("f_dial", 5, 5, 11, 23, 6.5)                                                 # 계기판 (오른쪽 위)
    b(14, 12, 6.5, 16, 13, 9.5, "f_brass")                                             # 오른쪽 유리관 (아래 · 위 테)
    b(14, 20, 6.5, 16, 21, 9.5, "f_brass")
    if lit:                                                                            # 유리관 안 발효액 기둥
        b(14.5, 13, 7.25, 15.5, 18, 8.75, "f_liquid", light=9)
        b(14.5, 18, 7.25, 15.5, 19, 8.75, "f_foam", light=9)
    b(14.25, 13, 7, 15.75, 20, 9, "f_pane")                                            # 반투명 유리관
    b(14, 21, 7.5, 15, 23, 8.5, "f_brass")                                             # 유리관 → 계기판 배관
    return m


# ═════════════ 대형 솥 (2x2): 레퍼런스 "스팀 조리기(보일러)" — 짙은 무쇠 솥(팔각), 황동 띠·리벳·세로 띠, 위 황동 테 안 스튜와 김,
# 팔레트는 레퍼런스 그대로. 쉬는 동안(kettle)은 화구 안이 어둡고 솥이 비고, 조리 중(kettle_on)은 화구 안 바닐라 불 · 솥 밑 불빛 · 스튜, 왼쪽 밸브 바퀴·배관, 오른쪽 계기판·빛나는 유리관 배관, 네 모서리 황동 다리 ═════════════
# 바닥 2x2: 설치한 블록을 가운데에 두고 사방 반 블록씩 (모델 x·z -8~24, 증폭 공작대와 같은 방식). 좌표는 u(왼→오)·y·w(앞→뒤) 0~32.
FIRE_HOLE, FIRE_TOP = (11, 21, 9), 14                                                 # 화구 자리: u 11~21, 앞에서 w 9 까지 판다 (y 14 아래)


def kettle(lit=False):
    """lit: 조리 중 모델 (kettle_on) — 화구 안 바닐라 불 · 장작, 솥 밑 불빛, 솥 안 스튜. 아니면 화구 안이 어둡고 솥이 빔"""
    m = Model("kettle_on" if lit else "kettle")
    m.display = {                                                                      # 2x2 크기라 손 · 인벤토리 아이콘을 줄인다
        "gui": {"rotation": [25, 205, 0], "translation": [0, -1, 0], "scale": [0.28, 0.28, 0.28]},
        "ground": {"translation": [0, 2, 0], "scale": [0.14, 0.14, 0.14]},
        "firstperson_righthand": {"rotation": [0, 45, 0], "scale": [0.16, 0.16, 0.16]},
        "thirdperson_righthand": {"rotation": [75, 45, 0], "translation": [0, 2.5, 0], "scale": [0.14, 0.14, 0.14]},
    }

    def plate(name, w, h, u0, y0, w0, light=0):
        """그림 판 (옆면도 팔레트 황동 — 공용 회색 쇠 대신)"""
        m.box([u0 - 8, y0, w0 - 8], [u0 + w - 8, y0 + h, w0 - 7], "k_brass_framed", light=light,
              faces={"front": (name, [0, 0, w, h])})

    def b(u0, y0, w0, u1, y1, w1, tex, light=0, faces=None):
        m.box([u0 - 8, y0, w0 - 8], [u1 - 8, y1, w1 - 8], tex, light=light, faces=faces)

    def rows(inset, cut):
        """팔각(모서리 45도 깎음) 칸: 줄(w)마다 (u0, u1)"""
        out = {}
        for w in range(inset, 32 - inset):
            d = max(0, cut - (w - inset), cut - (32 - inset - 1 - w))
            out[w] = (inset + d, 32 - inset - d)
        return out

    def slab(y0, y1, cells, tex, light=0, hole=None):
        """줄마다 (u0, u1) 칸을 같은 범위끼리 묶어 큐브로. hole = (u0, u1, w 끝): 앞쪽에서 판 화구 자리 (그 칸은 비움)"""
        if hole:
            hu0, hu1, hw = hole
            left = {w: (r[0], min(r[1], hu0)) if w < hw else r for w, r in cells.items()}
            right = {w: (max(r[0], hu1), r[1]) for w, r in cells.items() if w < hw}
            slab(y0, y1, left, tex, light)
            if right:
                slab(y0, y1, right, tex, light)
            return
        ws = sorted(cells)
        start = ws[0]
        for k, w in enumerate(ws):
            nxt = ws[k + 1] if k + 1 < len(ws) else None
            if nxt is None or cells[nxt] != cells[w] or nxt != w + 1:
                u0, u1 = cells[w]
                if u1 > u0:
                    b(u0, y0, start, u1, y1, w + 1, tex, light)
                start = nxt

    def octa(y0, y1, inset, cut, tex, light=0, hole=None):
        slab(y0, y1, rows(inset, cut), tex, light, hole)

    def ring(y0, y1, inset, cut, thick, tex):
        """속이 빈 팔각 테: 바깥 팔각에서 안쪽 팔각을 뺀 칸 (줄마다 왼쪽·오른쪽 조각)"""
        outer, inner = rows(inset, cut), rows(inset + thick, max(0, cut - 1))
        left, right = {}, {}
        for w, (u0, u1) in outer.items():
            if w in inner:
                i0, i1 = inner[w]
                left[w], right[w] = (u0, i0), (i1, u1)
            else:
                left[w] = (u0, u1)
        slab(y0, y1, left, tex)
        slab(y0, y1, {w: v for w, v in right.items()}, tex)

    for u, w in ((5, 5), (22, 5), (5, 22), (22, 22)):                                  # 황동 다리 (발판 + 기둥)
        b(u, 0, w, u + 5, 2, w + 5, "k_brass_framed")
        b(u + 1, 2, w + 1, u + 4, 9, w + 4, "k_brass_framed")
    octa(5, 7, 8, 4, "k_iron")                                                      # 솥 바닥 (좁게)
    octa(7, 9, 5, 6, "k_iron")
    octa(9, FIRE_TOP, 3, 7, "k_iron", hole=FIRE_HOLE)                               # 배 (가장 넓게, 앞에 화구 자리를 판다)
    octa(FIRE_TOP, 21, 3, 7, "k_iron")
    octa(21, 23, 4, 7, {"all": "k_iron", "top": "k_soup"} if lit else "k_iron", light=6 if lit else 0)                   # 어깨 (솥 안 바닥 — 내용물 없음)
    for y0 in (11, 18):                                                                # 황동 띠 (배에서 1픽셀 튀어나옴)
        octa(y0, y0 + 2, 2, 7, "k_brass", hole=FIRE_HOLE if y0 < FIRE_TOP else None)
    for y in (11, 18):                                                                 # 띠 리벳 (앞·뒤·옆, 띠 위로 1픽셀)
        for k in (11, 15, 19):
            for u0, w0, u1, w1 in ((k, 1, k + 2, 2), (k, 30, k + 2, 31), (1, k, 2, k + 2), (30, k, 31, k + 2)):
                if w0 == 1 and y < FIRE_TOP and FIRE_HOLE[0] <= k < FIRE_HOLE[1]:
                    continue                                                           # 화구 자리 리벳은 없음
                b(u0, y, w0, u1, y + 2, w1, "k_rivet")
    for u in (9, 22):                                                                  # 세로 황동 띠 (앞 · 뒤)
        b(u, 9, 2, u + 1, 21, 3, "k_brass_framed")
        b(u, 9, 29, u + 1, 21, 30, "k_brass_framed")
    ring(23, 25, 4, 7, 3, "k_iron_dark")                                            # 솥 안쪽 벽 (짙게)
    ring(25, 28, 3, 7, 3, "k_brass")                                               # 위 황동 테
    # 정면 화구: 몸통을 파낸 깊은 구멍 (어두운 안벽) + 앞 황동 테 · 창살. 조리 중이면 안에 바닐라 불 · 장작, 솥 밑 불빛
    b(12, 6, 8, 20, 13, 9, "k_iron_dark")                                              # 안벽 (뒤 · 옆 · 위 · 바닥)
    b(11, 6, 4, 12, 13, 9, "k_iron_dark")
    b(20, 6, 4, 21, 13, 9, "k_iron_dark")
    b(11, 13, 4, 21, 14, 9, "k_iron_dark")
    b(11, 5, 4, 21, 6, 9, "k_iron_dark")
    for y0, y1, u0, u1 in ((13, 14, 11, 21), (5, 6, 11, 21), (6, 13, 11, 12), (6, 13, 20, 21)):   # 앞 황동 테 (10x9)
        b(u0, y0, 2, u1, y1, 4, "k_brass_framed")
    for u in (13, 15, 17, 19):                                                         # 창살
        b(u, 6, 2.5, u + 1, 13, 3.5, "k_brass_framed")
    if lit:
        m.logs(12 - 8, 20 - 8, 6, (5 - 8,))                                            # 모닥불 장작 (빛남)
        m.fire(12 - 8, 20 - 8, 7, 13, 7 - 8)                                           # 바닐라 불 (움직임)
        b(11, 3, 6, 21, 5, 26, "k_glow", light=14)                                     # 솥 밑 불빛 (다리 사이)
    # 왼쪽 옆: 입체 밸브 바퀴 + 위로 올라가는 배관
    b(2, 16, 11, 3, 17, 18, "k_brass_framed")                                                   # 바퀴 테
    b(2, 9, 11, 3, 10, 18, "k_brass_framed")
    b(2, 10, 10, 3, 16, 11, "k_brass_framed")
    b(2, 10, 18, 3, 16, 19, "k_brass_framed")
    b(2, 10, 14, 3, 16, 15, "k_brass_framed")                                                   # 바퀴 살
    b(2, 12, 11, 3, 13, 18, "k_brass_framed")
    b(1, 11, 13, 3, 14, 16, "k_brass_framed")                                                   # 축
    b(3, 12, 13, 4, 13, 16, "k_brass_framed")
    b(2, 13, 22, 4, 27, 24, "k_brass_framed")                                                   # 세로 배관 → 테
    b(2, 13, 19, 4, 15, 22, "k_brass_framed")
    # 오른쪽: 계기판 (정면 오른쪽 위) + 빛나는 유리관 + 배관
    b(25, 18, 1, 27, 20, 3, "k_brass_framed")                                                   # 계기판 받침
    plate("k_dial", 8, 8, 22, 17, 0)
    b(29, 8, 8, 31, 10, 20, "k_brass_framed")                                                   # 아래 가로 배관
    b(29, 10, 18, 31, 17, 20, "k_brass_framed")
    b(29, 17, 17, 32, 18, 21, "k_brass_framed")                                                 # 유리관 아래 테
    b(29.5, 18, 17.5, 31.5, 26, 20.5, "k_glow", light=12)                           # 빛나는 유리관
    b(29, 26, 17, 32, 27, 21, "k_brass_framed")                                                 # 유리관 위 테
    b(28, 27, 18, 31, 29, 20, "k_brass_framed")                                                 # 위 꺾인 배관 → 테
    return m


# ═════════════ 제빵 오븐 (1x1x2): 레퍼런스 "제빵 오븐(베이커리 오븐)" — 산업용 철 캐비닛, 황동 띠 · 리벳,
# 위 굽는 칸 창(황동 테) · 오른쪽 계기판, 아래 화구(창살), 왼쪽 석탄 · 오른쪽 삽, 위 굴뚝 · 밸브 바퀴 배관, 구리 받침.
# 쉬는 동안(oven)은 굽는 칸 · 화구 안이 어둡고, 굽는 중(oven_on)은 굽는 칸이 빛나며 쟁반 위 파이, 화구 안 바닐라 불 · 장작 ═════════════
OVEN_FIRE = (3, 11, 5, 13, 8)          # 화구 구멍: u0, u1, y0, y1, 앞에서 w 까지
OVEN_WINDOW = (2, 11, 16, 23, 6)       # 굽는 칸 구멍


def oven(lit=False):
    m = Model("oven_on" if lit else "oven")

    def b(u0, y0, w0, u1, y1, w1, tex, light=0, faces=None):
        m.box([u0, y0, w0], [u1, y1, w1], tex, light=light, faces=faces)

    def body(u0, u1, y0, y1, w0, w1, holes, tex):
        """속이 찬 상자에서 앞쪽 구멍들을 뺀 큐브들 (w 구간마다 u · y 면을 줄 단위로 나눠 묶음)"""
        cuts = sorted({w0, w1, *[h[4] for h in holes if w0 < h[4] < w1]})
        for wa, wb in zip(cuts, cuts[1:]):
            active = [h for h in holes if wa < h[4]]
            ys = sorted({y0, y1, *[v for h in active for v in (h[2], h[3]) if y0 < v < y1]})
            for ya, yb in zip(ys, ys[1:]):
                spans, u = [], u0
                for h in sorted((h for h in active if h[2] <= ya and yb <= h[3]), key=lambda h: h[0]):
                    if h[0] > u:
                        spans.append((u, h[0]))
                    u = max(u, h[1])
                if u < u1:
                    spans.append((u, u1))
                for sa, sb in spans:
                    b(sa, ya, wa, sb, yb, wb, tex)

    m.display = None
    for u, w in ((1, 2), (13, 2), (1, 12), (13, 12)):                                  # 구리 받침 다리
        b(u, 0, w, u + 2, 1, w + 2, "o_copper")
    b(0, 1, 1, 16, 4, 15, "o_copper")                                                  # 구리 받침 판
    body(1, 15, 4, 25, 2, 14, [OVEN_FIRE, OVEN_WINDOW], "k_iron")                       # 산업용 철 캐비닛 (화구 · 굽는 칸 구멍)
    for y in (4, 14, 24):                                                              # 황동 띠 (아래 · 가운데 · 위)
        b(0.5, y, 1, 15.5, y + 1 + (y == 14), 14.5, "o_brass")
    for u in (2, 5, 8, 11, 14):                                                        # 가운데 띠 리벳
        b(u, 14.5, 0.5, u + 1, 15.5, 1, "o_rivet")
    for u0 in (0, 14.5):                                                               # 네 모서리 황동 기둥
        for w0 in (1, 13.5):
            b(u0, 4, w0, u0 + 1.5, 25, w0 + 1.5, "o_brass")
    b(1, 25, 2, 15, 26, 14, "k_iron")                                                  # 윗판

    # 아래 화구: 깊은 구멍 · 어두운 안벽 · 황동 테 · 창살 (+ 불 · 장작)
    fu0, fu1, fy0, fy1, fw = OVEN_FIRE
    b(fu0, fy0, fw - 1, fu1, fy1, fw, "k_iron_dark")
    b(fu0, fy0, 2, fu0 + 1, fy1, fw - 1, "k_iron_dark")
    b(fu1 - 1, fy0, 2, fu1, fy1, fw - 1, "k_iron_dark")
    b(fu0, fy1 - 1, 2, fu1, fy1, fw - 1, "k_iron_dark")
    b(fu0, fy0, 2, fu1, fy0 + 1, fw - 1, "k_iron_dark")
    for y0, y1, u0, u1 in ((fy1 - 1, fy1, fu0, fu1), (fy0, fy0 + 1, fu0, fu1), (fy0 + 1, fy1 - 1, fu0, fu0 + 1),
                           (fy0 + 1, fy1 - 1, fu1 - 1, fu1)):
        b(u0, y0, 1, u1, y1, 2, "o_brass")
    for u in (5, 7, 9):                                                                # 창살
        b(u, fy0 + 1, 1.5, u + 1, fy1 - 1, 2, "o_brass")
    if lit:
        m.logs(fu0 + 1, fu1 - 1, fy0 + 1, (3,))                                        # 모닥불 장작
        m.fire(fu0 + 1, fu1 - 1, fy0 + 2, fy1 - 1, 5)                                  # 바닐라 불

    # 위 굽는 칸: 구멍 · 안벽(굽는 중이면 빛남) · 황동 테 · 쟁반 (+ 파이)
    wu0, wu1, wy0, wy1, ww = OVEN_WINDOW
    inner = "o_fire" if lit else "k_iron_dark"                                         # 굽는 중: 진한 불빛 (파이 금색과 구분)
    glow = 10 if lit else 0
    b(wu0, wy0, ww - 1, wu1, wy1, ww, inner, light=glow)
    b(wu0, wy0, 2, wu0 + 1, wy1, ww - 1, inner, light=glow)
    b(wu1 - 1, wy0, 2, wu1, wy1, ww - 1, inner, light=glow)
    b(wu0, wy1 - 1, 2, wu1, wy1, ww - 1, inner, light=glow)
    b(wu0, wy0, 2, wu1, wy0 + 1, ww - 1, "k_iron_dark")
    for y0, y1, u0, u1 in ((wy1 - 1, wy1, wu0, wu1), (wy0, wy0 + 1, wu0, wu1), (wy0 + 1, wy1 - 1, wu0, wu0 + 1),
                           (wy0 + 1, wy1 - 1, wu1 - 1, wu1)):
        b(u0, y0, 1, u1, y1, 2, "o_brass")
    b(wu0 + 2, wy1 - 0.5, 0.5, wu1 - 2, wy1 + 0.5, 1, "o_brass")                       # 창 위 손잡이
    b(wu0 + 1, wy0 + 1, 2, wu1 - 1, wy0 + 1.5, ww - 1, "k_iron")                       # 쟁반
    if lit:
        b(wu0 + 1.5, wy0 + 1.5, 2.5, wu1 - 1.5, wy0 + 3.5, ww - 1.5, {"all": "o_pie_side", "top": "o_pie_top"}, light=8)   # 파이

    # 오른쪽 계기판 (창 오른쪽, 몸통 밖으로 살짝) · 세로 배관
    b(11, 16, 0, 16, 21, 1, "o_brass", faces={"front": ("o_dial", [0, 0, 8, 8])})
    b(13.5, 21, 3, 15, 27, 4.5, "o_brass")                                             # 계기판 → 위 배관
    b(13.5, 21, 0.5, 15, 22, 3, "o_brass")

    # 아래 장식: 왼쪽 석탄 더미 · 오른쪽 삽
    b(0.5, 4, 0, 4.5, 5.5, 2, "k_iron_dark")
    b(1, 5.5, 0.5, 3.5, 6.5, 1.5, "k_iron_dark")
    b(12.5, 4, 0, 14.5, 7, 0.5, "k_iron")                                              # 삽 날
    b(13, 7, 0, 14, 13, 0.5, "o_brass")                                                # 삽 자루
    b(12.5, 13, 0, 14.5, 14, 0.5, "o_brass")

    # 위: 굴뚝 (왼쪽) · 밸브 바퀴 배관
    b(2, 26, 5, 6, 30, 9, {"all": "k_iron", "top": "k_iron_dark"})
    b(1.5, 29, 4.5, 6.5, 30.5, 9.5, "o_brass")
    b(7, 26, 6, 15, 28, 8, "o_brass")                                                  # 가로 배관
    for u0, y0, u1, y1 in ((8.5, 30, 12.5, 31), (8.5, 26.5, 12.5, 27.5), (8, 27, 9, 30.5), (12, 27, 13, 30.5),
                           (10, 27, 11, 30.5), (8.5, 28.5, 12.5, 29)):                 # 밸브 바퀴 (테 · 살)
        b(u0, y0, 5, u1, y1, 5.5, "o_brass")
    return m


TOOLS = {**{"juicer_%s_%d%s" % (n, lv, "_on" if on else ""): (lambda n=n, on=on, lv=lv: juicer(n, on, lv))
            for n in JUICER_FRUITS for lv in FILL_LEVELS for on in (False, True)},
         **{"smoker_%s_%d%s" % (n, lv, "_on" if on else ""): (lambda n=n, on=on, lv=lv: smoker(n, on, lv))
            for n in SMOKER_MEATS for lv in FILL_LEVELS for on in (False, True)},
         "mill": mill, **{"mill_%s_%d%s" % (n, lv, "_on" if on else ""): (lambda n=n, on=on, lv=lv: mill(n, on, lv))
                         for n in MILL_INGREDIENTS for lv in FILL_LEVELS for on in (False, True)}, "juicer": juicer, "fermenter": fermenter, "smoker": smoker, "kettle": kettle,
         "kettle_on": lambda: kettle(lit=True), "oven": oven, "oven_on": lambda: oven(lit=True),
         "fermenter_on": lambda: fermenter(lit=True)}

if __name__ == "__main__":
    assets = sys.argv[1]
    for name in sys.argv[2:] or TOOLS:
        model = TOOLS[name]()
        model.save(assets, FOLDER, ART, getattr(model, "display", None))

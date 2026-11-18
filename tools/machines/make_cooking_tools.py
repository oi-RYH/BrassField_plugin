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
from furniture_kit import Model, CUSTOM, BRASS, BRASS_MID, IRON, IRON_EDGE, IRON_BOLT, rgb, noisy, picture, add_framed_palette  # noqa: E402

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


# ═════════════ 제분기: 리벳 쇠 몸통 + 큰 톱니, 위 깔때기(곡식), 앞 구리 배출구와 밀가루 자루 ═════════════
def mill():
    m = Model("mill")
    legs(m, 4)
    m.box([0, 4, 0], [16, 5, 16], "brass")                                      # 받침판
    m.box([1, 5, 2], [15, 17, 14], "iron_plate")                                # 몸통
    m.plate("gear", 8, 8, 4, 8, 1)                                              # 큰 톱니
    m.box([1, 17, 2], [15, 18, 14], "brass")                                    # 몸통 위 테
    m.box([6, 18, 6], [10, 20, 10], "brass")                                    # 깔때기 목
    ring(m, 4, 12, 20, 22, 4, 12, "brass")                                      # 깔때기 (위로 넓어짐, 속이 빔)
    ring(m, 3, 13, 22, 24, 3, 13, "brass")
    ring(m, 2, 14, 24, 26, 2, 14, "brass")
    ring(m, 1, 15, 26, 27, 1, 15, "brass")
    m.box([3, 24, 3], [13, 25, 13], {"all": "hay_block_side", "top": "hay_block_top"})   # 곡식
    m.box([8, 6, 0], [11, 9, 2], "cut_copper")                                  # 배출구
    m.box([9, 5, 0], [10, 6, 1], "cut_copper")
    m.box([5, 0, 0], [12, 5, 5], "sack")                                        # 밀가루 자루
    m.box([7, 5, 1], [10, 6, 3], "sack")                                        # 묶은 목
    return m


# ═════════════ 착즙기: 황동 받침 위 유리 탱크(주스), 위 뚜껑과 구리 관, 압력 게이지, 꼭지, 사과 ═════════════
def juicer():
    m = Model("juicer")
    for x in (2, 12):
        for z in (2, 12):
            m.box([x, 0, z], [x + 2, 6, z + 2], "brass")                        # 다리
    m.box([1, 6, 1], [15, 7, 15], "iron_plate")                                 # 받침판
    m.box([4, 7, 4], [12, 18, 12], "juice", light=6)                            # 주스
    m.box([3, 7, 3], [13, 21, 13], "glass")                                     # 유리 탱크 (속 보임)
    m.box([2, 21, 2], [14, 23, 14], "brass")                                    # 뚜껑
    m.box([6, 23, 6], [10, 24, 10], "brass")
    m.box([8, 24, 7], [10, 28, 9], "cut_copper")                                # 구리 관: 위로
    m.box([10, 26, 7], [16, 28, 9], "cut_copper")                               # 오른쪽으로
    m.box([14, 8, 7], [16, 26, 9], "cut_copper")                                # 아래로 (옆면)
    m.plate("gauge", 6, 6, 10, 9, 1)                                            # 압력 게이지
    m.box([7, 6, 1], [9, 8, 3], "brass")                                        # 꼭지
    m.box([2, 7, 1], [4, 9, 3], "apple")                                        # 사과
    m.box([3, 9, 2], [4, 10, 3], "leaf")
    return m


# ═════════════ 발효조: 배럴 몸통(쇠테 셋), 빛나는 둥근 창, 구리 뚜껑과 꼭지 밸브, 옆 구리 관과 아래 꼭지 ═════════════
def fermenter():
    m = Model("fermenter")
    for x in (2, 12):
        for z in (2, 12):
            m.box([x, 0, z], [x + 2, 2, z + 2], "brass")                        # 짧은 발
    body = {"all": "barrel_side", "top": "barrel_top", "bottom": "barrel_top"}
    m.box([1, 2, 3], [15, 20, 13], body)                                        # 배럴 (십자로 겹쳐 둥글게)
    m.box([3, 2, 1], [13, 20, 15], body)
    for y in (4, 11, 17):
        m.box([0, y, 3], [16, y + 1, 13], "iron")                               # 쇠테
        m.box([3, y, 0], [13, y + 1, 16], "iron")
    m.plate("porthole", 6, 6, 5, 6, 0, light=8)                                 # 빛나는 둥근 창 (쇠테 사이)
    m.box([3, 20, 3], [13, 22, 13], "copper_block")                             # 구리 뚜껑
    m.box([5, 22, 5], [11, 23, 11], "copper_block")
    m.box([7, 23, 7], [9, 25, 9], "brass")                                      # 꼭지 밸브
    m.box([6, 25, 7], [10, 26, 9], "brass")
    m.box([11, 22, 7], [16, 24, 9], "cut_copper")                               # 옆 구리 관
    m.box([14, 6, 7], [16, 22, 9], "cut_copper")
    m.box([11, 2, 0], [13, 4, 1], "brass")                                      # 아래 꼭지
    return m


# ═════════════ 훈연기: 리벳 쇠 찬장, 황동 테 유리문 너머 매달린 햄 두 개와 빛나는 숯, 뒤 굴뚝과 연기 ═════════════
def smoker():
    m = Model("smoker")
    legs(m, 3)
    m.box([1, 3, 13], [15, 23, 15], "iron_plate")                               # 뒤
    m.box([1, 3, 2], [2, 23, 13], "iron_plate")                                 # 옆
    m.box([14, 3, 2], [15, 23, 13], "iron_plate")
    m.box([1, 3, 2], [15, 5, 13], "iron_plate")                                 # 아래
    m.box([1, 21, 2], [15, 23, 13], "iron_plate")                               # 위
    m.box([2, 5, 12], [14, 21, 13], "polished_blackstone")                      # 안쪽 그을린 벽
    m.box([2, 5, 3], [14, 6, 12], "ember", light=10)                            # 빛나는 숯
    m.box([2, 18, 6], [14, 19, 7], "iron")                                      # 걸이 막대
    for hx in (3, 9):
        m.box([hx + 2, 16, 6], [hx + 3, 18, 7], "iron")                         # 고리
        m.box([hx, 9, 5], [hx + 4, 16, 9], "ham")                               # 햄
        m.box([hx + 1, 16, 6], [hx + 3, 17, 8], "bone")                         # 뼈 끝
    for frm, to in (([1, 20, 1], [15, 21, 2]), ([1, 5, 1], [15, 6, 2]),        # 문 황동 테
                    ([1, 6, 1], [2, 20, 2]), ([14, 6, 1], [15, 20, 2])):
        m.box(frm, to, "brass")
    m.box([2, 6, 1], [14, 20, 2], None, faces={"front": ("glass", [2, 0, 14, 14]), "back": ("glass", [2, 0, 14, 14])})   # 유리
    m.box([12, 12, 0], [13, 15, 1], "brass")                                    # 문 손잡이
    m.box([0, 23, 1], [16, 24, 15], "brass")                                    # 지붕
    m.box([11, 24, 10], [14, 30, 13], "iron")                                   # 굴뚝
    m.box([10, 30, 9], [15, 31, 14], "brass")
    m.box([11, 31, 10], [13, 32, 12], "steam")                                  # 연기
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


TOOLS = {"mill": mill, "juicer": juicer, "fermenter": fermenter, "smoker": smoker, "kettle": kettle,
         "kettle_on": lambda: kettle(lit=True), "oven": oven, "oven_on": lambda: oven(lit=True)}

if __name__ == "__main__":
    assets = sys.argv[1]
    for name in sys.argv[2:] or TOOLS:
        model = TOOLS[name]()
        model.save(assets, FOLDER, ART, getattr(model, "display", None))

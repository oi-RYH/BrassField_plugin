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
from furniture_kit import Model, CUSTOM, BRASS, rgb, noisy, picture  # noqa: E402

FOLDER = "machine/cooking"

# ═════════════ 기기별 그림 ═════════════
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
})


def legs(m, h, inset=1, size=2):
    """네 모서리 황동 다리"""
    for x in (inset, 16 - inset - size):
        for z in (inset, 16 - inset - size):
            m.box([x, 0, z], [x + size, h, z + size], "brass")


def ring(m, x0, x1, y0, y1, z0, z1, tex):
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


# ═════════════ 대형 솥: 리벳 쇠 화덕(불), 위 큰 무쇠 솥(흰 수프, 황동 띠·손잡이, 게이지), 김 ═════════════
def kettle():
    m = Model("kettle")
    m.box([1, 0, 1], [15, 1, 15], "iron_plate")                                 # 화덕 아래
    m.box([1, 7, 1], [15, 8, 15], "iron_plate")                                 # 화덕 위
    m.box([1, 1, 1], [3, 7, 15], "iron_plate")                                  # 화덕 옆
    m.box([13, 1, 1], [15, 7, 15], "iron_plate")
    m.box([3, 1, 9], [13, 7, 15], "iron_plate")                                 # 화덕 뒤
    m.box([3, 1, 8], [13, 7, 9], "polished_blackstone")                         # 그을린 안벽
    for frm, to in (([2, 0, 0], [14, 1, 1]), ([2, 7, 0], [14, 8, 1]),          # 화덕 구멍 황동 테
                    ([2, 1, 0], [3, 7, 1]), ([13, 1, 0], [14, 7, 1])):
        m.box(frm, to, "brass")
    m.logs(4, 12, 1, (3, 5))
    m.fire(4, 12, 2, 7, 5)
    m.box([1, 8, 1], [15, 18, 15], {"all": "iron_plate", "top": "milk_soup"}, light=4)   # 솥 (쇠 판, 수프는 테 아래)
    ring(m, 1, 15, 18, 20, 1, 15, "iron_plate")                                 # 솥 테 (속이 빔)
    for y in (10, 16):
        m.box([0, y, 0], [16, y + 1, 16], "brass")                              # 황동 띠
    m.box([0, 14, 7], [1, 15, 9], "brass")                                      # 손잡이 (띠 사이)
    m.box([15, 14, 7], [16, 15, 9], "brass")
    m.plate("gauge", 6, 6, 9, 11, 0)                                            # 게이지
    for sx, sy, sz, s in ((6, 20, 6, 3), (7, 23, 7, 3), (5, 25, 7, 2)):
        m.box([sx, sy, sz], [sx + s, sy + s, sz + s], "steam")                  # 김
    return m


# ═════════════ 제빵 오븐: 석재 벽돌 받침, 벽돌 돔(계단식), 아치 구멍 속 불과 빵, 위 굴뚝 ═════════════
def oven():
    m = Model("oven")
    m.box([0, 0, 1], [16, 6, 16], "stone_bricks")                               # 받침
    m.box([0, 6, 0], [16, 7, 16], {"all": "smooth_stone_slab_side", "top": "smooth_stone"})   # 받침 판
    m.box([1, 7, 2], [5, 11, 15], "bricks")                                     # 1단 (가운데 아치 구멍)
    m.box([11, 7, 2], [15, 11, 15], "bricks")
    m.box([5, 7, 10], [11, 11, 15], "bricks")
    m.box([5, 7, 9], [11, 12, 10], "polished_blackstone")                       # 그을린 안벽
    m.box([2, 11, 3], [5, 14, 14], "bricks")                                    # 2단
    m.box([11, 11, 3], [14, 14, 14], "bricks")
    m.box([5, 12, 3], [11, 14, 14], "bricks")                                   # 아치 위
    m.box([5, 11, 3], [6, 12, 9], "bricks")                                     # 아치 모서리
    m.box([10, 11, 3], [11, 12, 9], "bricks")
    m.box([5, 11, 9], [11, 12, 14], "bricks")
    m.box([4, 14, 4], [12, 16, 13], "bricks")                                   # 3단
    m.box([6, 16, 6], [10, 17, 11], "bricks")                                   # 4단
    m.logs(6, 10, 7, (7,))                                                      # 안쪽 불
    m.fire(6, 10, 8, 11, 8)
    m.box([6, 7, 3], [8, 9, 6], "bread", light=6)                               # 빵 두 덩이
    m.box([8, 7, 4], [10, 9, 7], "bread", light=6)
    m.box([6, 17, 8], [10, 21, 12], "bricks")                                   # 굴뚝
    m.box([5, 21, 7], [11, 22, 13], "brass")
    return m


TOOLS = {"mill": mill, "juicer": juicer, "fermenter": fermenter, "smoker": smoker, "kettle": kettle, "oven": oven}

if __name__ == "__main__":
    assets = sys.argv[1]
    for name in sys.argv[2:] or TOOLS:
        TOOLS[name]().save(assets, FOLDER, ART)

"""
요리 3D 손 모델: 큐브를 쌓고, 재질 그림은 sprites.py 아이콘과 같은 팔레트로 픽셀마다 거칠게 섞는다 (Farmer's Delight·바닐라 느낌).
인벤토리 칸에는 sprites.py 의 16x16 아이콘이 보이고(graphics.icon), 손에 들었을 때만 이 모델이 보인다.

사용: python3 -I tools/cooking/make_food.py <ItemsAdder contents/rustport/resourcepack/assets/rustport>
  → models/item/food/<ID>.json, textures/item/food/3d/<ID>_<재질>.png
  PREVIEW=<png> 를 주면 등각 미리보기를 늘어놓는다.

인벤토리·바닥·액자에는 아이콘이, 손에 들었을 때는 3D 모델이 보인다 (ItemsAdder graphics.icon 규칙).
같은 모델을 나중에 요리를 놓는 가구에도 쓴다.
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from food_kit import Model, blank, rgb, png  # noqa: E402
import sprites as S  # noqa: E402


def rough(colors, seed, weights=None, pattern=None):
    """16x16 재질: colors 중에서 칸마다 무작위로 고른다. pattern(x, y, rnd) 가 색을 주면 그 색을 쓴다."""
    rnd = random.Random(seed)
    img = blank(16)
    for y in range(16):
        for x in range(16):
            c = pattern(x, y, rnd) if pattern else None
            img[y][x] = c or rnd.choices(colors, weights=weights)[0]
    return img


def sides(top, side, bottom=None):
    return {"up": top, "down": bottom or side, "north": side, "south": side, "east": side, "west": side}


def disc(m, cx, cz, y0, y1, r, mat, inset=1.0):
    """둥근 판: 십자 두 개를 겹쳐 모서리를 깎은 원판"""
    m.box([cx - r, y0, cz - r + inset], [cx + r, y1, cz + r - inset], mat)
    m.box([cx - r + inset, y0, cz - r], [cx + r - inset, y1, cz + r], mat)


def mound(m, cx, cz, y0, steps, mat):
    """계단식 봉우리: steps = [(반지름, 높이), ...] 아래부터"""
    y = y0
    for r, h in steps:
        disc(m, cx, cz, y, y + h, r, mat, inset=min(1.0, r * 0.3))
        y += h
    return y


# ═════════════ 공용 부품 ═════════════
W = S.WOOD
WOOD_TEX = lambda seed: rough([W["m"], W["m"], W["l"], W["d"]], seed, pattern=lambda x, y, r: W["d"] if y % 4 == 0 and r.random() < 0.7 else None)
RIM_TEX = lambda seed: rough([W["h"], W["l"], W["h"]], seed)
P = S.PLATE_P


def bowl(m, fill):
    """나무 그릇 (내용물 윗면 높이 fill)"""
    m.tex("wood", WOOD_TEX(1))
    m.tex("rim", RIM_TEX(2))
    m.tex("woodin", rough([W["d"], W["k"]], 3))
    m.box([5, 0, 5], [11, 1, 11], "wood")
    m.box([3.5, 1, 3.5], [12.5, 2, 12.5], "wood")
    for frm, to in (([2.5, 2, 2.5], [13.5, 6.5, 3.5]), ([2.5, 2, 12.5], [13.5, 6.5, 13.5]),
                    ([2.5, 2, 3.5], [3.5, 6.5, 12.5]), ([12.5, 2, 3.5], [13.5, 6.5, 12.5])):
        m.box(frm, to, sides("rim", "wood"))
    return fill


def plate(m):
    m.tex("plate", rough([P["W"], P["w"], P["w"]], 4))
    m.tex("plateside", rough([P["Y"], P["X"]], 5))
    m.box([4, 0, 4], [12, 0.5, 12], "plateside")
    disc(m, 8, 8, 0.5, 1, 6.5, sides("plate", "plateside"), inset=1.5)
    for frm, to in (([2, 1, 2.5], [14, 1.6, 3.2]), ([2, 1, 12.8], [14, 1.6, 13.5]),
                    ([1.5, 1, 3.2], [2.2, 1.6, 12.8]), ([13.8, 1, 3.2], [14.5, 1.6, 12.8])):
        m.box(frm, to, sides("plate", "plateside"))
    return 1.0


# ═════════════ 요리별 모델 ═════════════
def rice_bowl(name, pal, specks=(), seed=10, toppings=None):
    m = Model(name)
    base = [pal["i"], pal["i"], pal["I"], pal["W"]]
    m.tex("rice", rough(base + list(specks), seed, weights=[4, 4, 3, 2] + [1] * len(specks)))
    m.tex("riceside", rough([pal["I"], pal["j"], pal["i"]], seed + 1))
    bowl(m, 6)
    m.box([3.5, 2, 3.5], [12.5, 6.5, 12.5], sides("rice", "riceside"))
    mound(m, 8, 8, 6.5, [(5.2, 1.4), (4.0, 1.2), (2.6, 1.0), (1.4, 0.6)], sides("rice", "riceside"))
    if toppings:
        toppings(m)
    return m


def soup_bowl(name, pal, chunks, seed):
    m = Model(name)
    m.tex("broth", rough([pal["y"], pal["y"], pal["z"], pal["Y"]], seed))
    bowl(m, 5)
    m.box([3.5, 2, 3.5], [12.5, 5.2, 12.5], "broth", skip=("down",))
    for i, (key, colors, frm, to) in enumerate(chunks):
        if key not in m.textures:
            m.tex(key, rough(colors, seed + i + 1))
        m.box(frm, to, key)
    return m


def thin_bowl(m, mound, foot):
    """얇은 그릇(벽 1칸) + 봉긋한 밥: 재질 "bowl"(그릇), foot(굽), "top"(밥 윗면)을 미리 등록해 둔다. mound = 가운데 밥 높이(칸)."""
    import math
    rr = lambda gx, gz: math.hypot(gx + 0.5 - 8, gz + 0.5 - 8)
    IN = 6.9                                                     # 밥 반지름: 그 바깥 1칸만 그릇 벽 (얇은 그릇)
    rim = {(gx, gz) for gz in range(16) for gx in range(16) if IN < rr(gx, gz) <= 7.9}
    cols = {}
    for gz in range(16):
        for gx in range(16):
            r = rr(gx, gz)
            if r > 7.9:
                continue
            parts = []
            if r <= 4.6:
                parts.append((0, 1, foot))                        # 굽
            if r <= 6.6:
                parts.append((1, 2, "bowl"))
            if r > IN:
                parts.append((2 if r <= 6.6 else 2.5, 6, "bowl"))  # 몸통 바깥 (맨 바깥 칸은 조금 위에서 시작)
                parts.append((6, 6.8, "bowl"))                    # 테두리
            else:
                parts.append((2, 5, "bowl"))                      # 몸통 안쪽 (위는 밥)
                ey = round(6 + mound * (1 - (r / IN) ** 2))      # 봉긋한 밥 (1칸 단위 계단)
                if any((gx + dx, gz + dz) in rim for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    ey = max(ey - 1, 5.5)                         # 그릇 벽과 면으로 맞닿은 밥은 한 칸 낮게
                parts.append((5, ey, "top"))
            cols[(gx, gz)] = parts
    relief(m, cols, "top", up_top=False)


def cooked_rice():
    """익힌 밥 (사용자 3D 시안 그대로): 크림색 그릇(주황 굽 + 오므라든 몸통 + 테두리)에 수북한 흰 쌀밥. 그릇 벽은 1칸 두께로 얇게.
    그릇·밥 자리는 시안 비율대로 쌓고, 밥은 시안 팔레트의 흰색 계열로 칠한다 (상단 그림 축소본은 그릇 그림자가 섞여 칙칙함)."""
    import math
    src = png.read(os.path.join(REF_DIR, "sauce_rice.png"))
    m = Model("cooked_rice")
    rnd = random.Random(290)
    rice = [rgb(255, 255, 239), rgb(251, 247, 239), rgb(242, 232, 219), rgb(234, 217, 198)]
    top = [[rnd.choices(rice, weights=[4, 4, 2, 1])[0] for _ in range(32)] for _ in range(32)]    # 흰 쌀밥 (시안 팔레트)
    m.tex("top", top)
    cream, groove = [rgb(242, 232, 219), rgb(234, 217, 198)], [rgb(217, 196, 168), rgb(198, 169, 141)]
    m.tex("bowl", [[rnd.choice(groove if x % 3 == 2 else cream) for x in range(32)] for _ in range(32)])   # 크림색 그릇 + 세로 홈
    m.tex("foot", [[tuple(max(0, min(255, int(v * rnd.uniform(0.9, 1.08)))) for v in (196, 120, 60)) + (255,) for _ in range(32)] for _ in range(32)])
    thin_bowl(m, 4.2, "foot")
    return m


def fried_rice():
    """볶음밥 (사용자 3D 시안): 빨간 체크 천 위 얇은 크림색 그릇(주황 굽)에 봉긋한 볶음밥, 위에 쪽파, 앞 오른쪽에 쪽파 조각.
    볶음밥 윗면은 시안 UV 전개도를 줄여 쓴다."""
    src = png.read(os.path.join(REF_DIR, "four3d.png"))
    m = Model("fried_rice")
    rnd = random.Random(360)
    m.tex("top", cell_tex(ref_cells(src, (527, 271, 617, 354), 16, 16, bg=90)))
    cream, groove = [rgb(249, 233, 199), rgb(240, 222, 186)], [rgb(222, 198, 160), rgb(201, 167, 125)]
    m.tex("bowl", [[rnd.choice(groove if x % 3 == 2 else cream) for x in range(32)] for _ in range(32)])
    m.tex("foot", [[rnd.choice([rgb(201, 122, 58), rgb(184, 108, 50)]) for _ in range(32)] for _ in range(32)])
    m.tex("cloth", [[rgb(233, 107, 90) if (x // 3) % 3 == 0 or (y // 3) % 3 == 0 else rgb(249, 233, 222) for x in range(32)] for y in range(32)])
    m.tex("onion", [[rnd.choice([rgb(113, 166, 75), rgb(92, 146, 60)]) for _ in range(32)] for _ in range(32)])
    m.box([3, -0.4, 4], [16, 0, 16], "cloth")                       # 체크 천 (그릇 밑, 뒤 왼쪽으로)
    thin_bowl(m, 3.0, "foot")
    for x, z in ((7, 8), (8.6, 9.2), (9.2, 7.4), (7.6, 10), (6.4, 9.4)):   # 쪽파 (밥 위)
        m.box([x, 8.8, z], [x + 0.8, 9.4, z + 0.8], "onion")
    for x, z in ((1.2, 1.4), (2.6, 0.6), (0.6, 3), (2.2, 2.4)):            # 쪽파 조각 (앞 오른쪽)
        m.box([x, -0.4, z], [x + 1, 0.4, z + 1], "onion")
    fit_block(m)
    return m


def mushroom_fried_rice():
    """버섯볶음밥 (사용자 3D 시안): 얇은 크림색 그릇에 낮게 봉긋한 볶음밥, 위에 버섯 세 쪽, 앞 오른쪽에 버섯 한 송이와 반쪽.
    볶음밥 윗면은 시안 UV 전개도의 볶음밥을 줄여 쓴다."""
    src = png.read(os.path.join(REF_DIR, "kimbap_rice3d.png"))
    m = Model("mushroom_fried_rice")
    rnd = random.Random(330)
    m.tex("top", cell_tex(ref_cells(src, (1142, 690, 1286, 807), 16, 16, bg=90)))
    cream, groove = [rgb(248, 230, 199), rgb(238, 215, 180)], [rgb(217, 196, 168), rgb(201, 167, 125)]
    m.tex("bowl", [[rnd.choice(groove if x % 3 == 2 else cream) for x in range(32)] for _ in range(32)])
    m.tex("cap", [[rnd.choice([rgb(139, 90, 60), rgb(120, 74, 46), rgb(160, 106, 70)]) for _ in range(32)] for _ in range(32)])
    m.tex("stem", [[rnd.choice([rgb(240, 222, 196), rgb(226, 204, 172)]) for _ in range(32)] for _ in range(32)])
    m.tex("slice", cell_tex(ref_cells(src, (1301, 702, 1360, 750), 8, 8, bg=90)))
    thin_bowl(m, 2.6, "bowl")
    for cx, cz, y in ((6.5, 9, 8.4), (9.5, 9.5, 8.4), (8, 6.5, 8.6)):   # 밥 위 버섯 쪽 (갓 + 대)
        m.box([cx - 1.2, y, cz - 0.9], [cx + 1.2, y + 0.9, cz + 0.9], "cap")
        m.box([cx - 0.4, y - 0.6, cz - 0.4], [cx + 0.4, y, cz + 0.4], "stem")
    m.box([-3.4, 0, -1.4], [0.4, 1.6, 2.4], "cap")                   # 앞 오른쪽 버섯 한 송이 (갓 둥글게 두 판)
    m.box([-3.0, 1.6, -1.0], [0, 2.4, 2.0], "cap")
    m.box([-2.0, 0, 0], [-1.0, 0.6, 1.0], "stem")
    m.box([0.6, 0, -3.2], [3.4, 0.7, -0.4], {"up": "slice", "down": "stem", "north": "stem", "south": "stem", "east": "cap", "west": "cap"},
          uv={"up": [0, 0, 4, 4]})                                     # 반쪽 버섯 (단면이 위)
    fit_block(m)
    return m


def chicken_soup():
    return pot_item("chicken_soup")


def vegetable_soup():
    return pot_item("vegetable_soup")


def salmon_sushi():
    """연어 초밥 (사용자 3D 시안): 다리 달린 나무 게타 위에 잎을 깔고 초밥 세 점(손으로 쥔 타원형 밥 + 둥글게 덮은 연어 + 쪽파), 앞에 와사비와 초생강.
    모양은 시안 비율대로 쌓고, 무늬는 시안 UV 전개도(연어 결·밥알·나무결)를 줄여 쓴다."""
    src = png.read(os.path.join(REF_DIR, "sushi_wrap3d.png"))
    m = Model("salmon_sushi")
    rnd = random.Random(310)
    m.tex("salmon", cell_tex(ref_cells(src, (372, 612, 490, 667), 16, 8, bg=90)))
    m.tex("salmontop", cell_tex(ref_cells(src, (627, 607, 717, 659), 16, 10, bg=90)))
    m.tex("rice", cell_tex(ref_cells(src, (372, 681, 531, 741), 16, 8, bg=90)))
    m.tex("wood", cell_tex(ref_cells(src, (372, 754, 531, 787), 16, 6, bg=90)))
    m.tex("leaf", cell_tex(ref_cells(src, (544, 680, 591, 722), 8, 8, bg=60)))
    m.tex("ginger", cell_tex(ref_cells(src, (601, 672, 662, 722), 8, 8, bg=90)))
    m.tex("wasabi", cell_tex(ref_cells(src, (671, 672, 717, 715), 8, 8, bg=90)))
    m.tex("onion", [[rnd.choice([rgb(123, 170, 58), rgb(100, 150, 44)]) for _ in range(32)] for _ in range(32)])
    fit = lambda w, h: {f: [0, 0, w, h] for f in ("north", "south", "east", "west", "up", "down")}   # 그림 안쪽만 (빈 영역 = 투명 구멍 방지)
    m.box([0.5, 2, 2.5], [15.5, 3.5, 13.5], "wood", uv=fit(8, 3))                     # 게타 판
    for x0 in (2, 12):                                            # 다리 두 줄
        m.box([x0, 0, 3], [x0 + 2, 2, 13], "wood", uv=fit(8, 3))
    m.box([1.5, 3.5, 6], [14.5, 3.7, 12.5], "leaf", uv=fit(4, 4))                    # 잎
    def oval(cx, cz, y0, y1, hx, hz, mat, uv):                    # 모서리를 깎은 납작한 타원 판 (두 판을 십자로)
        for k, (dx, dz) in enumerate(((hx * 0.72, hz), (hx, hz * 0.8))):
            e = 0.01 * k
            m.box([cx - dx, y0 + e, cz - dz], [cx + dx, y1 - e, cz + dz], mat, uv=uv)

    salmon = {"up": "salmontop", "north": "salmon", "south": "salmon", "east": "salmon", "west": "salmon", "down": "salmon"}
    s_uv = {"up": [0, 0, 8, 5], "down": [0, 0, 8, 5], "north": [0, 0, 4, 1], "south": [0, 0, 4, 1], "east": [0, 0, 5, 1], "west": [0, 0, 5, 1]}
    for cx, cz in ((12, 9.6), (8.3, 9.9), (4.6, 10.2)):          # 초밥 세 점: 손으로 쥔 타원형 밥 + 둥글게 덮은 연어
        oval(cx, cz, 3.7, 4.2, 1.3, 1.9, "rice", fit(4, 2.4))     # 밥 아래 (안쪽으로)
        oval(cx, cz, 4.2, 5.5, 1.6, 2.2, "rice", fit(4, 2.4))     # 밥 가운데 (가장 넓게)
        oval(cx, cz, 5.5, 6.1, 1.3, 1.9, "rice", fit(4, 2.4))     # 밥 위 (안쪽으로)
        oval(cx, cz, 6.0, 7.0, 1.85, 2.6, salmon, s_uv)           # 연어: 밥보다 넓게 덮는다
        m.box([cx - 1.5, 5.2, cz - 2.75], [cx + 1.5, 6.0, cz - 2.35], "salmon", uv=fit(4, 1))   # 앞 끝이 밥 위로 늘어짐
        m.box([cx - 1.5, 5.2, cz + 2.35], [cx + 1.5, 6.0, cz + 2.75], "salmon", uv=fit(4, 1))   # 뒤 끝
        for ox, oz in ((-0.6, -0.4), (0.5, 0.5), (0.1, -1.4)):    # 쪽파
            m.box([cx + ox - 0.35, 7.0, cz + oz - 0.35], [cx + ox + 0.35, 7.5, cz + oz + 0.35], "onion")
    m.box([2.4, 3.5, 3.6], [4.6, 4.9, 5.8], "wasabi", uv=fit(4, 4))                  # 와사비 (앞 오른쪽)
    m.box([2.8, 4.9, 4.0], [4.2, 5.4, 5.4], "wasabi", uv=fit(4, 4))
    m.box([5.3, 3.5, 3.4], [8.1, 4.5, 6.0], "ginger", uv=fit(4, 4))                  # 초생강
    m.box([5.8, 4.5, 3.9], [7.6, 5.1, 5.5], "ginger", uv=fit(4, 4))
    fit_block(m)
    return m


def cabbage_wrap():
    """양배추 쌈 (사용자 3D 시안): 크림색 접시 위에 양배추 쌈 세 개를 눕혀(앞쪽 끝에 속재료 단면), 오른쪽에 소스 종지.
    쌈은 양 끝을 오므리고 단면을 둥글게 깎은 통통한 모양(공에 가까움), 무늬는 시안 UV 전개도(양배추 잎·속재료·종지)를 줄여 쓴다."""
    import math
    src = png.read(os.path.join(REF_DIR, "sushi_wrap3d.png"))
    m = Model("cabbage_wrap")
    rnd = random.Random(320)
    def cooked(img):                                              # 익은 양배추: 초록을 연한 미색으로 섞고, 밝은 잎맥은 더 하얗게
        out = blank(32)
        for y, row in enumerate(img):
            for x, c in enumerate(row):
                if not c[3]:
                    continue
                greenish = c[1] > c[2] + 25 and c[1] >= c[0] * 0.9          # 초록·연두·올리브 (잎)
                if not greenish:
                    out[y][x] = c
                    continue
                t = 0.72 if sum(c[:3]) > 480 else 0.55                      # 밝은 잎맥은 더 하얗게
                out[y][x] = tuple(int(v + (w - v) * t) for v, w in zip(c[:3], (238, 242, 222))) + (255,)
        return out

    m.tex("leaf", cooked(cell_tex(ref_cells(src, (1143, 616, 1259, 679), 16, 10, bg=60))))
    m.tex("leaflight", cooked(cell_tex(ref_cells(src, (1284, 607, 1380, 680), 16, 12, bg=60))))
    m.tex("fill", cooked(cell_tex(ref_cells(src, (1284, 692, 1380, 749), 12, 8, bg=60))))
    m.tex("sauce", cell_tex(ref_cells(src, (1412, 612, 1478, 655), 12, 8, bg=60)))
    m.tex("bowl", cell_tex(ref_cells(src, (1394, 692, 1497, 732), 16, 6, bg=90)))
    plate = [rgb(233, 220, 200), rgb(226, 210, 188), rgb(211, 183, 160)]
    m.tex("plate", [[rnd.choice(plate[:2]) for _ in range(32)] for _ in range(32)])
    m.tex("platerim", [[rnd.choice(plate[1:]) for _ in range(32)] for _ in range(32)])
    cols = {}                                                     # 접시: 낮은 원판 + 살짝 올라온 테두리
    for gz in range(16):
        for gx in range(16):
            r = math.hypot(gx + 0.5 - 8, gz + 0.5 - 8)
            if r <= 7.9:
                cols[(gx, gz)] = [(0, 0.8, "plate")] + ([(0.8, 1.4, "platerim")] if r > 6.9 else [])
    relief(m, cols, "plate", up_top=False)

    def roll(cx, cz, r, L):                                       # 눕힌 쌈 (공에 가까운 통통한 모양): 길이 방향 양 끝을 오므리고 단면도 둥글게
        cy = 0.8 + r
        segs = [(-L / 2, -L / 2 + 0.8, 0.72), (-L / 2 + 0.8, L / 2 - 0.8, 1.0), (L / 2 - 0.8, L / 2, 0.72)]
        for si, (a0, a1, k) in enumerate(segs):
            rr = r * k
            for j, (dx, dy) in enumerate(((rr * 0.45, rr), (rr * 0.82, rr * 0.82), (rr, rr * 0.45))):
                e = 0.01 * j
                front = si == 0                                   # 맨 앞 마디의 앞면만 속재료 단면
                m.box([cx - dx, cy - dy + e, cz + a0 + e], [cx + dx, cy + dy - e, cz + a1 - e],
                      {"north": "fill" if front else "leaf", "south": "leaflight" if si == 2 else "leaf",
                       "east": "leaf", "west": "leaf", "up": "leaf", "down": "leaf"},
                      uv={"north": [(1 - dx / rr) * 3, (1 - dy / rr) * 2, 6 - (1 - dx / rr) * 3, 4 - (1 - dy / rr) * 2] if front
                          else [0, 0, dx, dy],
                          "south": [0, 0, 8, 6], "east": [0, 0, (a1 - a0) / 2 + 1, dy], "west": [0, 0, (a1 - a0) / 2 + 1, dy],
                          "up": [0, 0, dx, (a1 - a0) / 2 + 1], "down": [0, 0, dx, (a1 - a0) / 2 + 1]})

    roll(9.4, 11.4, 2.8, 5.2)                                     # 뒤 가운데
    roll(12.4, 5.4, 2.6, 4.8)                                     # 앞 왼쪽
    roll(7.0, 4.8, 2.6, 4.8)                                      # 앞 가운데
    m.box([1.2, 0.8, 6.6], [5.2, 3, 10.6], {"up": "sauce", "north": "bowl", "south": "bowl", "east": "bowl", "west": "bowl", "down": "bowl"},
          uv={"up": [0, 0, 6, 4], "north": [0, 0, 8, 3], "south": [0, 0, 8, 3], "east": [0, 0, 8, 3], "west": [0, 0, 8, 3]})   # 소스 종지
    m.box([1.6, 0.8, 7], [4.8, 3.2, 10.2], "bowl", skip=("up",), uv={f: [0, 0, 8, 3] for f in ("north", "south", "east", "west", "down")})
    fit_block(m)
    return m


def kimbap():
    """김밥 (사용자 3D 시안): 나무 판 위에 김밥 한 줄(가로로 눕힘, 오른쪽 끝이 단면), 앞에 썬 조각 셋(판 위에 눕힘, 단면이 위), 단무지와 잎.
    김 무늬·단면·단무지는 시안 UV 전개도를 줄여 쓴다."""
    src = png.read(os.path.join(REF_DIR, "kimbap_rice3d.png"))
    m = Model("kimbap")
    rnd = random.Random(340)
    m.tex("nori", cell_tex(ref_cells(src, (365, 612, 527, 695), 16, 8, bg=40)))
    m.tex("cut", cell_tex(ref_cells(src, (549, 606, 631, 692), 12, 12, bg=60)))
    m.tex("radish", cell_tex(ref_cells(src, (541, 707, 640, 749), 12, 6, bg=90)))
    m.tex("wood", [[rnd.choice([rgb(190, 120, 62), rgb(170, 104, 52), rgb(204, 134, 72)]) for _ in range(32)] for _ in range(32)])
    m.tex("leaf", [[rnd.choice([rgb(110, 160, 60), rgb(90, 140, 50)]) for _ in range(32)] for _ in range(32)])
    m.box([0.5, 0, 2.5], [15.5, 1.4, 14], "wood")                  # 나무 판
    m.box([1, 1.4, 9], [6, 1.6, 13], "leaf")                       # 잎 (단무지 밑)
    m.box([3, 1.4, 3], [12, 1.6, 6.5], "leaf")                     # 잎 (조각 밑)

    def disc(cx, cy, z0, z1, r, north, south, side, axis="z"):     # 모서리를 깎은 원기둥 (axis 방향으로 누움)
        for j, (a, b) in enumerate(((r * 0.45, r), (r * 0.82, r * 0.82), (r, r * 0.45))):
            e = 0.01 * j
            if axis == "z":
                frm, to = [cx - a, cy - b + e, z0 + e], [cx + a, cy + b - e, z1 - e]
                faces = {"north": north, "south": south, "east": side, "west": side, "up": side, "down": side}
                uv = {"north": [(1 - a / r) * 3, (1 - b / r) * 3, 6 - (1 - a / r) * 3, 6 - (1 - b / r) * 3]}
            elif axis == "y":                                      # 위아래 방향 (눕힌 조각): z0..z1 이 높이, cy 가 z 중심, 단면이 위
                frm, to = [cx - a + e, z0, cy - b], [cx + a - e, z1, cy + b]
                faces = {"up": north, "down": south, "north": side, "south": side, "east": side, "west": side}
                uv = {"up": [(1 - a / r) * 3, (1 - b / r) * 3, 6 - (1 - a / r) * 3, 6 - (1 - b / r) * 3],
                      "north": [0, 0, 8, 1], "south": [0, 0, 8, 1], "east": [0, 0, 8, 1], "west": [0, 0, 8, 1]}
            else:                                                  # x 방향: z0..z1 이 x 범위, cx 가 z 중심
                frm, to = [z0 + e, cy - b + e, cx - a], [z1 - e, cy + b - e, cx + a]
                faces = {"west": north, "east": south, "north": side, "south": side, "up": side, "down": side}
                uv = {"west": [(1 - a / r) * 3, (1 - b / r) * 3, 6 - (1 - a / r) * 3, 6 - (1 - b / r) * 3],
                      "north": [0, 0, 8, 4], "south": [0, 0, 8, 4], "up": [0, 0, 8, 4], "down": [0, 0, 8, 4]}
            m.box(frm, to, faces, uv=uv)

    disc(10, 1.4 + 2.7, 5.5, 15, 2.7, "cut", "nori", "nori", axis="x")   # 김밥 한 줄 (뒤, 오른쪽 끝 = 단면)
    for cx, cz in ((12.6, 4.6), (8.2, 4.2), (3.8, 4.8)):          # 썬 조각 셋 (판 위에 눕힘, 단면이 위)
        disc(cx, cz, 1.6, 3.0, 2.2, "cut", "cut", "nori", axis="y")
    for i, (x, z) in enumerate(((1.4, 9.6), (2.2, 10.4), (3.0, 11.2))):   # 단무지 (오른쪽 뒤, 겹쳐 놓음)
        m.box([x, 1.6, z], [x + 2.4, 2.6 + i * 0.4, z + 1.4], "radish", uv={f: [0, 0, 6, 3] for f in ("north", "south", "east", "west", "up", "down")})
    fit_block(m)
    return m


def dumplings():
    """만두 (사용자 3D 시안): 초록 체크 천 위 대나무 찜기에 만두 다섯 개, 뚜껑은 뒤 오른쪽에 기대 세우고, 앞 오른쪽에 간장 종지.
    찜기 옆면·뚜껑 무늬·만두·간장은 시안 UV 전개도를 줄여 쓴다."""
    import math
    src = png.read(os.path.join(REF_DIR, "four3d.png"))
    m = Model("dumplings")
    rnd = random.Random(370)
    m.tex("bamboo", cell_tex(ref_cells(src, (1287, 231, 1377, 263), 16, 6, bg=90)))
    m.tex("lid", cell_tex(ref_cells(src, (1452, 215, 1512, 267), 16, 16, bg=90)))
    m.tex("dumpling", cell_tex(ref_cells(src, (1288, 307, 1377, 352), 12, 6, bg=90)))
    m.tex("sauce", cell_tex(ref_cells(src, (1457, 313, 1510, 352), 8, 6, bg=40)))
    m.tex("paper", [[rnd.choice([rgb(255, 243, 220), rgb(234, 215, 169)]) for _ in range(32)] for _ in range(32)])
    m.tex("cloth", [[rgb(127, 179, 81) if (x // 3) % 3 == 0 or (y // 3) % 3 == 0 else rgb(248, 248, 234) for x in range(32)] for y in range(32)])
    m.tex("dish", [[rnd.choice([rgb(248, 248, 234), rgb(234, 215, 169)]) for _ in range(32)] for _ in range(32)])
    m.box([1, -0.4, 1], [15, 0, 15], "cloth")                       # 초록 체크 천
    cols = {}                                                       # 찜기: 둥근 바닥 + 1칸 대나무 벽
    for gz in range(16):
        for gx in range(16):
            r = math.hypot(gx + 0.5 - 8, gz + 0.5 - 8)
            if r > 7.4:
                continue
            cols[(gx, gz)] = [(0, 1, "bamboo")] + ([(1, 5, "bamboo")] if r > 6.4 else [(1, 1.3, "paper")])
    relief(m, cols, "paper", up_top=False)
    full = {f: [0, 0, 6, 3] for f in ("north", "south", "east", "west", "up", "down")}

    def dumpling(cx, cz, s):                                        # 만두: 둥근 몸통 + 주름 잡힌 위 + 꼭지
        for j, (a, b) in enumerate(((s * 0.7, s), (s, s * 0.7))):
            e = 0.01 * j
            m.box([cx - a, 1.3 + e, cz - b], [cx + a, 1.3 + s * 0.9 - e, cz + b], "dumpling", uv=full)
        m.box([cx - s * 0.65, 1.3 + s * 0.9, cz - s * 0.65], [cx + s * 0.65, 1.3 + s * 1.4, cz + s * 0.65], "dumpling", uv=full)
        m.box([cx - 0.35, 1.3 + s * 1.4, cz - 0.35], [cx + 0.35, 1.3 + s * 1.7, cz + 0.35], "dumpling", uv=full)

    for cx, cz in ((8, 8), (5.4, 6.2), (10.6, 6.2), (5.6, 10.2), (10.4, 10.2)):
        dumpling(cx, cz, 1.9)
    n = len(m.elements)                                             # 뚜껑: 뒤 오른쪽에 기대 세움 (위가 뒤로)
    for j, (a, b) in enumerate(((5.5 * 0.72, 5.5), (5.5, 5.5 * 0.72))):
        e = 0.01 * j
        m.box([4.5 - a, 5.5 - b, 15.2 + e], [4.5 + a, 5.5 + b, 16.4 - e],
              {"north": "lid", "south": "lid", "east": "bamboo", "west": "bamboo", "up": "bamboo", "down": "bamboo"},
              uv={"north": [(5.5 - a) / 11 * 8, (5.5 - b) / 11 * 8, 8 - (5.5 - a) / 11 * 8, 8 - (5.5 - b) / 11 * 8],
                  "south": [0, 0, 8, 8], "east": [0, 0, 1, 3], "west": [0, 0, 1, 3], "up": [0, 0, 6, 1], "down": [0, 0, 6, 1]})
    for e in m.elements[n:]:
        e["rotation"] = {"origin": [4.5, 0, 15.8], "axis": "x", "angle": 22.5}
    m.box([0, 0, -1], [4, 1.4, 3], {"up": "sauce", "north": "dish", "south": "dish", "east": "dish", "west": "dish", "down": "dish"},
          uv={"up": [0, 0, 4, 3]})                                  # 간장 종지 (앞 오른쪽)
    fit_block(m)
    return m


def meatball_pasta():
    """미트볼 파스타 (사용자 3D 시안): 빨간 체크 천 위 크림색 접시에 봉긋한 파스타(가운데 소스, 둘레 면), 미트볼 셋·바질·치즈 가루,
    앞 오른쪽에 방울토마토. 파스타·소스·미트볼 무늬는 시안 UV 전개도를 줄여 쓴다."""
    import math
    src = png.read(os.path.join(REF_DIR, "pasta_rata3d.png"))
    m = Model("meatball_pasta")
    rnd = random.Random(350)
    pasta = ref_cells(src, (385, 695, 487, 805), 16, 16, bg=90)
    sauce = ref_cells(src, (497, 695, 575, 805), 16, 16, bg=90)
    top = blank(32)                                               # 윗면: 가운데는 소스, 둘레는 면
    for gz in range(16):
        for gx in range(16):
            r = math.hypot(gx + 0.5 - 8, gz + 0.5 - 8)
            top[gz][gx] = (sauce if r < 3.4 else pasta)[gz][gx] or rgb(232, 170, 60)
    m.tex("top", top)
    m.tex("meatball", cell_tex(ref_cells(src, (587, 697, 627, 737), 8, 8, bg=90)))
    plate = [rgb(248, 230, 201), rgb(255, 246, 238), rgb(241, 224, 190)]
    m.tex("plate", [[rnd.choice(plate) for _ in range(32)] for _ in range(32)])
    m.tex("cloth", [[rgb(196, 70, 40) if (x // 3) % 3 == 0 or (y // 3) % 3 == 0 else rgb(255, 246, 238) for x in range(32)] for y in range(32)])
    m.tex("basil", [[rnd.choice([rgb(110, 160, 60), rgb(90, 140, 50)]) for _ in range(32)] for _ in range(32)])
    m.tex("cheese", [[rnd.choice([rgb(255, 246, 225), rgb(241, 224, 170)]) for _ in range(32)] for _ in range(32)])
    m.tex("tomato", [[rnd.choice([rgb(214, 52, 40), rgb(196, 40, 34), rgb(232, 80, 60)]) for _ in range(32)] for _ in range(32)])
    m.box([4, 0, 6], [16, 0.4, 16], "cloth")                      # 체크 천 (뒤 왼쪽으로 삐져나옴)
    cols = {}
    for gz in range(16):
        for gx in range(16):
            r = math.hypot(gx + 0.5 - 8, gz + 0.5 - 8)
            if r > 7.9:
                continue
            parts = [(0.4, 1.0 if r > 5.6 else 1.2, "plate")]     # 접시 바닥 (가장자리는 비스듬히)
            if r > 6.6:
                parts.append((1.0, 2.2, "plate"))                 # 접시 테두리
            elif r <= 6.0:                                        # 봉긋한 파스타
                parts.append((1.2, 1.2 + round((1.6 + 2.4 * (1 - (r / 6.0) ** 2)) * 2) / 2, "top"))
            cols[(gx, gz)] = parts
    relief(m, cols, "top", up_top=False)

    def ball(cx, cz, y, r):                                       # 미트볼: 모서리 깎은 공
        for j, (a, b) in enumerate(((r * 0.6, r), (r, r * 0.6))):
            e = 0.01 * j
            m.box([cx - a, y + e, cz - b], [cx + a, y + 2 * r * 0.85 - e, cz + b], "meatball",
                  uv={f: [0, 0, 4, 4] for f in ("north", "south", "east", "west", "up", "down")})
        m.box([cx - r * 0.6, y + 2 * r * 0.85, cz - r * 0.6], [cx + r * 0.6, y + 2 * r * 0.85 + 0.5, cz + r * 0.6], "meatball",
              uv={f: [1, 1, 3, 3] for f in ("north", "south", "east", "west", "up", "down")})

    for cx, cz in ((6.8, 9.2), (9.6, 9.6), (8.2, 6.8)):           # 미트볼 셋
        ball(cx, cz, 4.4, 1.5)
    for x, z in ((7.8, 8.6), (6.0, 7.0), (10.4, 7.6), (8.8, 11.0), (5.6, 10.6)):   # 치즈 가루
        m.box([x, 4.6, z], [x + 0.6, 4.9, z + 0.6], "cheese")
    m.box([7.2, 7.3, 8.4], [8.6, 7.6, 10.4], "basil")              # 바질 잎 (미트볼 위에 얹음)
    m.box([8.4, 7.2, 7.8], [9.8, 7.5, 9.2], "basil")
    for cx, cz in ((1.8, 2.0), (4.0, 0.8)):                        # 방울토마토 (앞 오른쪽)
        m.box([cx - 1.2, 0, cz - 1.0], [cx + 1.2, 2.0, cz + 1.0], "tomato")
        m.box([cx - 1.0, 0.2, cz - 1.2], [cx + 1.0, 1.8, cz + 1.2], "tomato")
        m.box([cx - 0.5, 2.0, cz - 0.5], [cx + 0.5, 2.4, cz + 0.5], "basil")
    fit_block(m)
    return m


def ratatouille():
    return pot_item("ratatouille")


def honey_cookie():
    """꿀 쿠키 (사용자 3D 시안 그대로): 빨간 체크 천 위에 쿠키 세 장을 쌓고, 한 장은 앞에 기대 세우고, 꿀이 든 유리병과 꿀 막대를 곁들인다.
    쿠키 윗면은 상단 그림(꿀·설탕 알갱이), 옆면은 옆면 그림의 쿠키 테두리."""
    src = png.read(os.path.join(REF_DIR, "cookie_soups.png"))
    m = Model("honey_cookie")
    rnd = random.Random(300)
    m.tex("top", cell_tex(ref_cells(src, (348, 458, 408, 511), 16, 16, bg=90)))
    m.tex("edge", cell_tex(ref_cells(src, (118, 478, 170, 500), 16, 4, bg=90)))
    m.tex("cloth", [[rgb(186, 52, 44) if (x // 3) % 3 == 0 or (y // 3) % 3 == 0 else rgb(240, 226, 204) for x in range(32)] for y in range(32)])

    def jitter(col, lo=0.9, hi=1.08):
        return [[tuple(max(0, min(255, int(v * rnd.uniform(lo, hi)))) for v in col[:3]) + (255,) for _ in range(32)] for _ in range(32)]

    m.tex("honey", jitter(rgb(232, 163, 56)))
    m.tex("lid", jitter(rgb(248, 230, 194)))
    m.tex("rope", jitter(rgb(139, 74, 31)))
    m.tex("stick", jitter(rgb(201, 122, 41)))

    def cookie(cx, cz, y, r, t):                                  # 누운 쿠키: 모서리 깎은 원판 (윗면 = 상단 그림 전체)
        for k, (dx, dz) in enumerate(((r - r * 0.3, r), (r, r - r * 0.3))):
            e = 0.01 * k
            u = lambda x: (x - (cx - r)) / (2 * r) * 8
            v = lambda z: (cz + r - z) / (2 * r) * 8
            m.box([cx - dx, y + e, cz - dz], [cx + dx, y + t - e, cz + dz],
                  {"up": "top", "down": "top", "north": "edge", "south": "edge", "east": "edge", "west": "edge"},
                  uv={"up": [u(cx - dx), v(cz - dz), u(cx + dx), v(cz + dz)], "down": [u(cx - dx), v(cz + dz), u(cx + dx), v(cz - dz)],
                      "north": [0, 0, 8, 1], "south": [0, 0, 8, 1], "east": [0, 0, 8, 1], "west": [0, 0, 8, 1]})

    m.box([5.5, 0, 2.5], [16, 0.4, 13], "cloth")                  # 체크 천
    for i, (ox, oz) in enumerate(((0, 0), (0.4, -0.3), (-0.3, 0.3))):          # 쿠키 세 장 쌓기
        cookie(11 + ox, 8 + oz, 0.4 + i * 1.4, 4, 1.4)
    n = len(m.elements)                                           # 앞에 기대 세운 쿠키 (위가 뒤로 기운다)
    r, cx, cy, cz = 3.6, 8.5, 3.8, 3
    for k, (dx, dy) in enumerate(((r - r * 0.3, r), (r, r - r * 0.3))):
        e = 0.01 * k
        u = lambda x: (cx + r - x) / (2 * r) * 8
        v = lambda y: (cy + r - y) / (2 * r) * 8
        m.box([cx - dx, cy - dy, cz - 1.3 + e], [cx + dx, cy + dy, cz - e],
              {"north": "top", "south": "top", "east": "edge", "west": "edge", "up": "edge", "down": "edge"},
              uv={"north": [u(cx + dx), v(cy + dy), u(cx - dx), v(cy - dy)], "south": [u(cx + dx), v(cy + dy), u(cx - dx), v(cy - dy)],
                  "east": [0, 0, 1, 8], "west": [0, 0, 1, 8], "up": [0, 0, 8, 1], "down": [0, 0, 8, 1]})
    for e in m.elements[n:]:
        e["rotation"] = {"origin": [cx, 0.4, cz], "axis": "x", "angle": 22.5}
    glass = blank(32)                                             # 유리: 테두리와 반사 줄만 보이고 나머지는 투명 (안의 꿀이 보이게)
    for yy in range(32):
        for xx in range(32):
            if xx in (0, 1, 30, 31) or yy in (0, 1, 30, 31):
                glass[yy][xx] = rgb(214, 232, 236)
            elif xx in (5, 6) and 5 <= yy <= 24:
                glass[yy][xx] = rgb(250, 254, 255)
    m.tex("glass", glass)
    full = {f: [0, 0, 16, 16] for f in ("north", "south", "east", "west", "up", "down")}
    m.box([0.95, 0.15, 9.45], [4.55, 3.8, 13.05], "honey")         # 병 안의 꿀 (3/4 높이)
    m.box([0.5, 0, 9], [5, 5, 13.5], "glass", skip=("up",), uv=full)   # 유리병 (오른쪽 뒤 = 작은 x)
    m.box([0.2, 5, 8.7], [5.3, 6.2, 13.8], "lid")                 # 천 덮개
    m.box([0.1, 4.6, 8.6], [5.4, 5.1, 13.9], "rope")              # 끈
    m.box([2.4, 0.4, 6.2], [3.1, 7.5, 6.9], "stick")              # 꿀 막대 (단지 앞에 세움)
    m.box([1.4, 0.4, 5.2], [4.1, 2.6, 7.9], "honey")              # 막대 끝 꿀
    fit_block(m)
    return m


def hamburger():
    """햄버거 (사용자 3D 시안): 체크 천 위에 아래 빵·패티·흘러내린 치즈·토마토·들쭉날쭉한 양상추·둥근 참깨 윗빵을 쌓고,
    앞 오른쪽 나무 판에 감자튀김과 케첩 종지. 윗빵·패티 무늬는 시안 UV 전개도, 나머지는 시안 팔레트."""
    import math
    src = png.read(os.path.join(REF_DIR, "hamburger3d.png"))
    m = Model("hamburger")
    rnd = random.Random(380)

    def jitter(cols):
        return [[rnd.choice(cols) for _ in range(32)] for _ in range(32)]

    m.tex("buntop", cell_tex(ref_cells(src, (1040, 435, 1140, 525), 16, 16, bg=90)))
    m.tex("patty", cell_tex(ref_cells(src, (1283, 435, 1380, 525), 16, 16, bg=60)))
    m.tex("bun", jitter([rgb(224, 131, 52), rgb(232, 150, 64), rgb(246, 197, 82)]))
    m.tex("bunlow", jitter([rgb(246, 197, 82), rgb(255, 224, 138), rgb(232, 160, 70)]))
    m.tex("cheese", jitter([rgb(246, 197, 82), rgb(255, 214, 100), rgb(240, 180, 60)]))
    m.tex("tomato", jitter([rgb(217, 74, 58), rgb(200, 52, 44), rgb(178, 30, 30)]))
    m.tex("lettuce", jitter([rgb(111, 158, 62), rgb(167, 217, 74), rgb(130, 180, 66)]))
    m.tex("cloth", [[rgb(212, 74, 58) if (x // 3) % 3 == 0 or (y // 3) % 3 == 0 else rgb(255, 242, 220) for x in range(32)] for y in range(32)])
    m.tex("wood", jitter([rgb(184, 90, 44), rgb(160, 80, 40), rgb(122, 67, 30)]))
    m.tex("fries", jitter([rgb(246, 197, 82), rgb(255, 214, 100), rgb(232, 170, 60)]))
    m.tex("dish", jitter([rgb(255, 255, 255), rgb(255, 242, 220)]))
    m.tex("ketchup", jitter([rgb(178, 30, 30), rgb(212, 74, 58)]))
    m.box([3, 0, 4], [16, 0.4, 16], "cloth")                         # 체크 천 (햄버거 밑, 뒤 왼쪽으로)
    B = 0.4
    cols = {}
    for gz in range(16):
        for gx in range(16):
            dx, dz = gx + 0.5 - 8, gz + 0.5 - 8
            r = math.hypot(dx, dz)
            ang = math.atan2(dz, dx)
            parts = []
            if r <= 6.0:
                parts.append((B, B + 2.0, "bunlow"))                  # 아래 빵
            if r <= 6.3:
                parts.append((B + 2.0, B + 3.6, "patty"))             # 패티
            drip = int((ang + math.pi) / (2 * math.pi) * 9) % 3 == 0
            if r <= 6.4 or (drip and r <= 6.9):
                parts.append((B + 3.0 if r > 6.4 else B + 3.6, B + 4.1, "cheese"))   # 치즈 (군데군데 흘러내림)
            if r <= 6.0:
                parts.append((B + 4.1, B + 4.9, "tomato"))           # 토마토
            frill = int((ang + math.pi) / (2 * math.pi) * 14) % 2 == 0
            if r <= (6.9 if frill else 6.4):
                parts.append((B + 4.9, B + 5.6, "lettuce"))          # 양상추 (가장자리 들쭉날쭉)
            if r <= 6.4:                                              # 둥근 참깨 윗빵
                parts.append((B + 5.6, B + 5.6 + round((1.4 + 2.6 * (1 - (r / 6.4) ** 2)) * 2) / 2, "buntop"))
            if parts:
                cols[(gx, gz)] = parts
    relief(m, cols, "buntop", up_top=False)
    for e in m.elements:                                              # 패티 옆·윗면은 그릴 무늬 그림 안쪽만
        for f, face in e["faces"].items():
            if face["texture"] == "#patty" and f != "up":
                face["uv"] = [0, 0, 8, 1.6]
    m.box([-4.5, 0, -3.5], [3.5, 1.2, 4.5], "wood")                   # 나무 판 (앞 오른쪽)
    n = len(m.elements)
    for x, z in ((-3.4, 2.2), (-2.2, 2.6), (-1.0, 2.2), (0.2, 2.6)):   # 감자튀김 (뒤로 기대 세움)
        m.box([x, 1.2, z], [x + 0.9, 7.2, z + 0.9], "fries")
    for e in m.elements[n:]:
        e["rotation"] = {"origin": [-1.5, 1.2, 2.6], "axis": "x", "angle": 22.5}
    m.box([-3.6, 1.2, -2.8], [0.6, 2.6, 0.8], {"up": "ketchup", "north": "dish", "south": "dish", "east": "dish", "west": "dish", "down": "dish"})
    m.box([-3.2, 2.6, -2.4], [0.2, 2.8, 0.4], "dish", skip=("down",))   # 종지 테두리
    m.box([-2.4, 2.6, -1.6], [-0.6, 3.0, 0.0], "ketchup")              # 케첩
    fit_block(m)
    return m

def dough():
    m = Model("dough")
    dp = S.DOUGH_P
    m.tex("dough", rough([dp["F"], dp["f"], dp["F"], dp["W"]], 140))
    m.tex("doughside", rough([dp["f"], dp["d"]], 141))
    mound(m, 8, 8, 0, [(5, 1.5), (4.5, 1.2), (3.2, 0.8)], sides("dough", "doughside"))
    return m


def noodles():
    m = Model("noodles")
    np_ = S.NOODLES_P
    m.tex("noodle", rough([np_["n"], np_["N"], np_["L"]], 150, pattern=lambda x, y, r: np_["M"] if (x + 2 * y) % 4 == 0 else None))
    mound(m, 8, 8, 0, [(5, 1.5), (4.2, 1.2), (2.8, 0.8)], "noodle")
    return m


def tomato_sauce():
    return jar_item("tomato_sauce")

def patty():
    m = Model("patty")
    pp = S.PATTY_P
    m.tex("meat", rough([pp["P"], pp["p"], pp["P"], pp["f"]], 170, weights=[4, 3, 4, 1]))
    m.tex("meatside", rough([pp["p"], pp["r"]], 171))
    disc(m, 8, 8, 0, 2, 5, sides("meat", "meatside"), inset=1.3)
    return m



# ═════════════════════════ 두 번째 세트 ═════════════════════════
def pie_tin(m):
    m.tex("tin", rough([S.PIE_P["t"], S.PIE_P["T"]], 210))
    disc(m, 8, 8, 0, 1, 5.5, "tin", inset=1.4)


def pie_crust():
    m = Model("pie_crust")
    pp = S.PIE_P
    m.tex("crust", rough([pp["c"], pp["C"], pp["c"]], 211))
    m.tex("floor", rough([pp["d"], pp["d"], pp["c"]], 212))
    pie_tin(m)
    disc(m, 8, 8, 1, 2, 5.5, sides("floor", "crust"), inset=1.4)
    for frm, to in (([2.5, 2, 2.5], [13.5, 3, 3.6]), ([2.5, 2, 12.4], [13.5, 3, 13.5]),
                    ([2.5, 2, 3.6], [3.6, 3, 12.4]), ([12.4, 2, 3.6], [13.5, 3, 12.4])):
        m.box(frm, to, "crust")                                                  # 둘레 테 (속이 빔)
    return m


REF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "art", "ref")      # 사용자 3D 시안


def ref_cells(src, box, nx, ny, boost=1.08, bg=260, drop=None):
    """시안 영역을 nx×ny 칸으로 줄인다: 칸 가운데 픽셀들의 중앙값 색, 절반 넘게 배경(어두운 색)이면 None.
    drop(색) 이 참인 픽셀(뒤에 겹친 다른 물건)도 배경으로 친다."""
    x0, y0, x1, y1 = box
    out = []
    for gy in range(ny):
        row = []
        for gx in range(nx):
            ax, ay = x0 + gx * (x1 - x0) / nx, y0 + gy * (y1 - y0) / ny
            bx, by = x0 + (gx + 1) * (x1 - x0) / nx, y0 + (gy + 1) * (y1 - y0) / ny
            px = [src[int(ay + (by - ay) * (0.15 + 0.7 * i / 6))][int(ax + (bx - ax) * (0.15 + 0.7 * j / 6))][:3]
                  for i in range(7) for j in range(7)]
            fg = sorted((c for c in px if sum(c) > bg and not (drop and drop(c))), key=sum)
            if len(fg) < len(px) * 0.5:
                row.append(None)
                continue
            c = fg[len(fg) // 2]
            mean = sum(c) / 3
            row.append(tuple(max(0, min(255, int(mean + (v - mean) * boost))) for v in c) + (255,))
        out.append(row)
    return out


def cell_tex(cells, transpose=False):
    """칸 그림 → 32x32 텍스처 (1칸 = 1픽셀 = 모델 0.5칸). 빈 칸은 이웃 색으로 메운다"""
    img = blank(32)
    rows = [list(r) for r in (zip(*cells) if transpose else cells)]
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            img[y][x] = c or next((rows[yy][xx] for yy, xx in ((y, x + 1), (y, x - 1), (y + 1, x), (y - 1, x))
                                   if 0 <= yy < len(rows) and 0 <= xx < len(r) and rows[yy][xx]), rgb(166, 96, 46))
    return img


def fit_block(m, margin=0.5, grow=False):
    """돌린 큐브까지 포함한 바닥 범위와 높이가 1블록(0..16) 안에 들어오게 모델 전체를 같은 비율로 줄이고 가운데로 옮긴다 (바닥 y=0 유지)"""
    import math
    pts = []                                                      # 큐브 꼭짓점 8개를 회전(x·y·z 축 모두)까지 반영해 모은다
    for e in m.elements:
        rot = e.get("rotation")
        for x in (e["from"][0], e["to"][0]):
            for y in (e["from"][1], e["to"][1]):
                for z in (e["from"][2], e["to"][2]):
                    if rot:
                        ox, oy, oz = rot["origin"]
                        a = math.radians(rot["angle"])
                        c, s_ = math.cos(a), math.sin(a)
                        dx, dy, dz = x - ox, y - oy, z - oz
                        if rot["axis"] == "x":
                            dy, dz = dy * c - dz * s_, dy * s_ + dz * c
                        elif rot["axis"] == "y":
                            dx, dz = dx * c + dz * s_, -dx * s_ + dz * c
                        else:
                            dx, dy = dx * c - dy * s_, dx * s_ + dy * c
                        pts.append((ox + dx, oy + dy, oz + dz))   # (반복 변수는 건드리지 않는다)
                    else:
                        pts.append((x, y, z))
    x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts)
    z0, z1 = min(p[2] for p in pts), max(p[2] for p in pts)
    top = max(p[1] for p in pts)
    k = min(99.0 if grow else 1.0, (16 - 2 * margin) / max(x1 - x0, z1 - z0), (16 - margin) / top)   # grow: 작으면 키운다
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2

    def move(p):
        return [round(8 + (p[0] - cx) * k, 3), round(p[1] * k, 3), round(8 + (p[2] - cz) * k, 3)]

    for e in m.elements:
        e["from"], e["to"] = move(e["from"]), move(e["to"])
        if e.get("rotation"):
            e["rotation"]["origin"] = move(e["rotation"]["origin"])
    return k


def bread_loaf():
    """식빵 덩어리 + 앞에 누운 두 조각 (사용자 3D 시안 그대로, 시안 크기의 절반, 덩어리 길이는 다시 절반).
    정면 그림의 줄마다 칠해진 폭을 그대로 길이 방향으로 밀어 낸 판을 쌓고(어깨가 불룩한 식빵 실루엣),
    정면·후면·좌우·상단·하단 그림을 줄여 각 면에 입힌다. 1칸 = 시안 1픽셀의 2배 (텍스처 1칸 = 2픽셀).
    조각은 같은 실루엣을 바닥에 눕힌 얇은 판. 위 조각은 22.5도(모델이 허용하는 가장 작은 각) 비튼다."""
    src = png.read(os.path.join(REF_DIR, "bread_loaf.png"))
    m = Model("bread_loaf")
    W, H, L = 20, 18, 16                                        # 시안 픽셀: 폭, 높이, 길이(시안 32 의 절반)
    X0, Z0 = 8 - W / 4, 8                                       # 덩어리: x 3..13, y 0..9, z 8..16 (앞쪽은 조각 자리)
    front = ref_cells(src, (559, 95, 675, 196), W, H)
    back = ref_cells(src, (893, 95, 1013, 196), W, H)
    m.tex("front", cell_tex(front))
    m.tex("back", cell_tex(back))
    m.tex("right", cell_tex(ref_cells(src, (725, 103, 844, 196), L, H)))
    m.tex("left", cell_tex(ref_cells(src, (1054, 103, 1170, 195), L, H)))
    m.tex("top", cell_tex(ref_cells(src, (1216, 102, 1336, 194), L, W), transpose=True))
    m.tex("bottom", cell_tex(ref_cells(src, (1379, 100, 1498, 193), L, W), transpose=True))
    crust = [c for row in front for c in (row[2], row[W - 3]) if c and sum(c[:3]) < 520]    # 테두리 껍질 색
    rnd = random.Random(230)
    m.tex("crust", [[rnd.choice(crust) for _ in range(32)] for _ in range(32)])
    # 정면 실루엣: 줄마다 (왼쪽 칸, 오른쪽 칸+1) → 같은 폭끼리 묶어 판 하나
    spans = []
    for r, row in enumerate(front):
        filled = [c for c, v in enumerate(row) if v]
        span = (min(filled), max(filled) + 1) if filled else None
        if spans and spans[-1][2] == span:
            spans[-1][1] = r + 1
        else:
            spans.append([r, r + 1, span])
    spans = [sp for sp in spans if sp[2]]
    top_y = H / 2
    GROOVE_Y, GAP, PIECES = 8, 0.4, 4                            # 이 높이 위(불룩한 윗부분)는 칼집 3줄로 4조각
    seg = (L / 2 - (PIECES - 1) * GAP) / PIECES
    for r0, r1, (c0, c1) in spans:
        xa, xb = 8 - (c1 - c0) / 4, 8 + (c1 - c0) / 4             # 좌우 대칭으로 가운데 맞춤
        y0, y1 = top_y - r1 / 2, top_y - r0 / 2
        v0, v1 = r0 / 2, r1 / 2
        cuts = ([(Z0 + i * (seg + GAP), Z0 + i * (seg + GAP) + seg) for i in range(PIECES)]
                if y0 >= GROOVE_Y else [(Z0, Z0 + L / 2)])
        for za, zb in cuts:
            m.box([xa, y0, za], [xb, y1, zb],
                  {"north": "front", "south": "back", "east": "right", "west": "left", "up": "top", "down": "bottom"},
                  uv={"north": [c0 / 2, v0, c1 / 2, v1], "south": [(W - c1) / 2, v0, (W - c0) / 2, v1],
                      "east": [Z0 + L / 2 - zb, v0, Z0 + L / 2 - za, v1], "west": [za - Z0, v0, zb - Z0, v1],
                      "up": [xa - X0, za - Z0, xb - X0, zb - Z0], "down": [xa - X0, za - Z0, xb - X0, zb - Z0]})
    # 누운 조각 두 장: 윗면 = 정면 그림(속살 + 껍질 테두리), 둥근 머리는 덩어리 쪽(+z)
    def lying_slice(cx, cz, y, angle):
        n = len(m.elements)
        for r0, r1, (c0, c1) in spans:
            xa, xb = cx - (c1 - c0) / 4, cx + (c1 - c0) / 4
            za, zb = cz + H / 4 - r1 / 2, cz + H / 4 - r0 / 2
            m.box([xa, y, za], [xb, y + 0.75, zb], {"up": "front", "down": "back", "north": "crust", "south": "crust",
                                                    "east": "crust", "west": "crust"},
                  uv={"up": [c0 / 2, r1 / 2, c1 / 2, r0 / 2], "down": [c0 / 2, r0 / 2, c1 / 2, r1 / 2]})
        if angle:
            for e in m.elements[n:]:
                e["rotation"] = {"origin": [cx, y, cz], "axis": "y", "angle": angle}

    lying_slice(7.5, 3.2, 0, 0)
    lying_slice(8.6, 2.6, 0.75, 22.5)
    fit_block(m)
    return m


def bottle(name, pal):
    """주스 병: 유리(반투명) 안에 주스, 코르크, 라벨"""
    m = Model(name)
    # 유리: 테두리와 반사 줄만 보이고 나머지는 투명 (안의 주스가 보이게)
    glass = blank(16)
    for yy in range(16):
        for xx in range(16):
            if xx in (0, 15) or yy in (0, 15):
                glass[yy][xx] = rgb(186, 214, 220)
            elif xx == 2 and 2 <= yy <= 12:
                glass[yy][xx] = rgb(240, 250, 252)
    m.tex("glass", glass)
    m.tex("juice", rough([pal["L"], pal["L"], pal["l"]], 231))
    m.tex("cork", rough([pal["c"], pal["C"]], 232))
    m.tex("label", rough([pal["P"]], 233, pattern=lambda x, y, r: pal["F"] if 6 <= x <= 9 and 5 <= y <= 9 else None))
    m.box([5, 0.5, 5], [11, 8, 11], "juice")
    m.box([4.6, 3, 4.6], [11.4, 6, 11.4], sides("juice", "label"))
    m.box([4.5, 0, 4.5], [11.5, 9, 11.5], "glass")
    m.box([6.5, 9, 6.5], [9.5, 11.5, 9.5], "glass")
    m.box([6.8, 9, 6.8], [9.2, 10.5, 9.2], "juice")
    m.box([6.4, 11.5, 6.4], [9.6, 13, 9.6], "cork")
    return m


def row_spans(cells):
    """칸 그림의 줄마다 칠해진 범위 (첫 줄, 끝 줄+1, (왼쪽 칸, 오른쪽 칸+1)) — 같은 폭끼리 묶는다"""
    spans = []
    for r, row in enumerate(cells):
        filled = [c for c, v in enumerate(row) if v]
        span = (min(filled), max(filled) + 1) if filled else None
        if spans and spans[-1][2] == span:
            spans[-1][1] = r + 1
        else:
            spans.append([r, r + 1, span])
    return [sp for sp in spans if sp[2]]


def lathe(m, cells, cx, cz, y_top, side, top=None, top_origin=None, chamfer=8, slim=1.0, north=None):
    """정면 실루엣(cells)을 줄마다 정사각 단면 판으로 쌓는다 (1칸 = 모델 1칸). 네 옆면에 side 텍스처(같은 그림),
    맨 위 층 윗면은 top 텍스처를 (top_origin 기준 1칸 = 1픽셀), 나머지 층 윗면은 그 층 첫 줄 색을 입힌다. 폭이 chamfer 칸 이상이면 모서리를 1칸 깎는다."""
    for i, (r0, r1, (c0, c1)) in enumerate(row_spans(cells)):
        h = (c1 - c0) / 2
        y0, y1 = y_top - r1, y_top - r0
        cut = 1 if c1 - c0 >= chamfer else 0
        for k, (dx, dz) in enumerate((((h - cut), h), (h, (h - cut))) if cut else ((h, h),)):
            e = 0.01 * k                                         # 겹친 두 번째 판은 위아래를 살짝 줄여 윗면 깜빡임(z-fighting) 방지
            xa, xb, za, zb = cx - dx * slim, cx + dx * slim, cz - dz * slim, cz + dz * slim     # slim: 가로·세로만 줄임 (그림은 그대로)
            cap = top and i == 0                                     # 맨 위 층만 상단 그림, 나머지 층 윗면은 그 층 첫 줄 색
            mat = {"north": north or side, "south": side, "east": side, "west": side, "up": top if cap else side, "down": side}
            uv = {}
            for f in ("north", "south", "east", "west"):
                half = dx if f in ("north", "south") else dz
                uv[f] = [(c0 + (h - half)) / 2, r0 / 2, (c1 - (h - half)) / 2, r1 / 2]
            if cap:
                ox, oz = top_origin
                uv["up"] = [(cx - dx - ox) / 2, (cz - dz - oz) / 2, (cx + dx - ox) / 2, (cz + dz - oz) / 2]
            else:
                uv["up"] = [c0 / 2 + 0.5, r0 / 2, c1 / 2 - 0.5, r0 / 2 + 0.5]
            uv["down"] = [c0 / 2 + 0.5, r1 / 2 - 0.5, c1 / 2 - 0.5, r1 / 2]
            m.box([xa, y0 + e, za], [xb, y1 - e, zb], mat, uv=uv)


def cut_tex(cells):
    """칸 그림 → 32x32 텍스처, 빈 칸은 투명 그대로 (꼬리표처럼 모양대로 오린 판)"""
    img = blank(32)
    for y, row in enumerate(cells):
        for x, c in enumerate(row):
            if c:
                img[y][x] = c
    return img


SLIM = 0.75           # 병 홀쭉하게 (시안 12칸 폭 → 9칸)
JUICE_REF = {          # 사용자 3D 시안 속 영역: 후면 병, 상단, 과일(큰 그림), 꼬리표(큰 그림)
    "apple_juice": {"src": "juice.png", "back": (266, 562, 320, 651), "top": (450, 581, 502, 634),
                    "fruit": (167, 327, 300, 460), "tag": (362, 255, 478, 363)},
    "grape_juice": {"src": "juice.png", "back": (893, 562, 947, 651), "top": (1077, 581, 1129, 634),
                    "fruit": (785, 325, 925, 468), "tag": (993, 228, 1110, 362)},
    "pineapple_juice": {"src": "juice2.png", "back": (200, 454, 250, 534), "top": (353, 470, 403, 518),
                        "fruit": (125, 205, 278, 375), "tag": (298, 168, 392, 282)},
    "pitaya_juice": {"src": "juice2.png", "back": (708, 454, 758, 534), "top": (863, 470, 912, 518),
                     "fruit": (628, 222, 778, 377), "tag": (798, 172, 892, 282)},
}


def juice_bottle(name):
    """주스 병 (사용자 3D 시안 그대로, 12×18×12): 후면 그림(과일·꼬리표 없는 병)의 실루엣을 줄마다 정사각 판으로 쌓아
    코르크·유리 입구·끈·몸통을 만들고 그 그림을 네 옆면에, 상단 그림을 윗면에 입힌다.
    앞 오른쪽에 과일 그림을 오린 꼬리표, 앞 왼쪽 바닥에 과일(큰 그림 실루엣을 같은 방식으로 쌓음). 마지막에 1블록 안으로 줄인다."""
    ref = JUICE_REF[name]
    src = png.read(os.path.join(REF_DIR, ref["src"]))
    m = Model(name)
    bottle_cells = ref_cells(src, ref["back"], 12, 18, bg=120)
    m.tex("bottle", cell_tex(bottle_cells))
    m.tex("top", cell_tex(ref_cells(src, ref["top"], 12, 12, bg=120)))
    lathe(m, bottle_cells, 8, 8, 18, "bottle", top="top", top_origin=(2, 2), slim=SLIM)      # 몸통 x 3.5..12.5
    fruit_cells = ref_cells(src, ref["fruit"], 7, 7, bg=120)
    m.tex("fruit", cell_tex(fruit_cells))
    lathe(m, fruit_cells, 12.5, 3.5, 7, "fruit", chamfer=5)        # 화면 왼쪽 = 큰 x
    m.tex("tag", cut_tex(ref_cells(src, ref["tag"], 10, 10, bg=120)))
    m.box([1.5, 6.5, 3.1], [6.5, 11.5, 3.3], {f: "tag" for f in ("north", "south", "east", "west", "up", "down")},
          uv={"north": [0, 0, 5, 5], "south": [5, 0, 0, 5], "east": [0, 0, 0.1, 5], "west": [0, 0, 0.1, 5],
              "up": [0, 0, 5, 0.1], "down": [0, 4.9, 5, 5]})
    m.tex("string", rough([rgb(150, 92, 48), rgb(122, 72, 36)], 240))
    m.box([6, 11.2, 3.3], [6.4, 13, 3.9], "string")                 # 목의 끈에서 꼬리표로
    fit_block(m)
    return m


def apple_juice():
    return juice_bottle("apple_juice")


def grape_juice():
    return juice_bottle("grape_juice")


def pineapple_juice():
    return juice_bottle("pineapple_juice")


def pitaya_juice():
    return juice_bottle("pitaya_juice")


JAR_REF = {            # 사용자 3D 시안 (art/ref/jars.png): 후면 단지(칸 수), 상단, 꼬리표(큰 그림), 옆에 놓인 것(큰 그림)
    "yogurt": {"back": (299, 441, 370, 521), "front": (64, 441, 135, 521), "size": (12, 14), "body_from": 5, "top": (534, 443, 604, 513), "tag": (440, 150, 543, 275),
               # 요구르트 컵 (뒤에 겹친 파란 단지는 뺀다), 블루베리, 잎
               "props": [("cup", (258, 282, 364, 371), 6, 5, lambda c: c[2] > c[0] + 20, (3.5, -1.5)),
                         ("berry", (235, 313, 283, 358), 3, 3, None, (7, -2.5)),
                         ("berry2", (268, 333, 314, 374), 3, 3, lambda c: c[0] > c[2], (5.5, -4.5))],
               "leaf": (205, 258, 293, 316)},
    "tomato_sauce": {"src": "sauce_rice.png", "back": (296, 443, 357, 503), "size": (12, 12), "top": (525, 439, 599, 505),
                     "tag": (425, 175, 519, 275),
                     # 소스 그릇 (왼쪽 앞), 토마토·반쪽 토마토 (오른쪽 앞, 단지 앞에 겹친 붉은 단지 색은 범위로 피함)
                     "props": [("saucebowl", (212, 262, 387, 375), 7, 5, None, (2.5, -1.5)),
                               ("tomato", (468, 258, 560, 368), 5, 5, None, (-12.5, -1)),
                               ("halftomato", (404, 308, 492, 374), 4, 3, None, (-8.5, -3.5))]},
    "kimchi": {"back": (1071, 442, 1140, 521), "size": (14, 16), "top": (1304, 446, 1373, 513), "tag": (1205, 140, 1307, 255),
               # 김치 그릇 (오른쪽 뒤 빨간 단지는 범위에서 뺀다)
               "props": [("bowl", (967, 270, 1111, 376), 8, 6, None, (3, -1.5))]},
}


def jar_item(name):
    """단지 음식 (사용자 3D 시안 그대로): 후면 그림(꼬리표 없는 단지)의 실루엣을 줄마다 정사각 판으로 쌓아
    천 덮개·끈·단지를 만들고 그 그림을 네 옆면에, 상단 그림을 덮개 윗면에 입힌다. 앞 오른쪽 어깨에 꼬리표,
    앞 왼쪽 바닥에 옆 소품(컵·블루베리·그릇)을 같은 방식으로 쌓는다. 마지막에 1블록 안으로 줄인다."""
    ref = JAR_REF[name]
    src = png.read(os.path.join(REF_DIR, ref.get("src", "jars.png")))
    m = Model(name)
    w, h = ref["size"]
    half = w / 2
    front = 8 - half
    cells = ref_cells(src, ref["back"], w, h, bg=120)

    def even_body(cc):                                           # 덮개 아래 단지는 몸통 폭에 맞춘다 (축소 때 좌우가 들쭉날쭉해 튀어나온 줄 정리)
        if "body_from" not in ref:
            return
        widths = [sum(1 for v in row if v) for row in cc[-4:]]
        body_w = max(set(widths), key=widths.count)
        for row in cc[ref["body_from"]:]:
            filled = [x for x, v in enumerate(row) if v]
            extra = len(filled) - body_w
            for x in filled[:extra // 2] + filled[len(filled) - (extra - extra // 2):] if extra > 0 else []:
                row[x] = None

    even_body(cells)
    m.tex("jar", cell_tex(cells))
    m.tex("top", cell_tex(ref_cells(src, ref["top"], w, w, bg=120)))
    north = None
    if "front" in ref:                                           # 앞면은 정면 그림 (요구르트 그릇 그림), 꼬리표가 가린 오른쪽 칸은 왼쪽 칸 거울 복사
        fc = ref_cells(src, ref["front"], w, h, bg=120)
        for y in range(h):
            for x in range(w - 3, w):
                fc[y][x] = fc[y][w - 1 - x]
        even_body(fc)
        m.tex("front", cell_tex(fc))
        north = "front"
    lathe(m, cells, 8, 8, h, "jar", top="top", top_origin=(8 - half, 8 - half), north=north)
    for key, box, nx, ny, drop, (dx, dz) in ref["props"]:        # (dx, dz): 단지 앞 왼쪽 모서리(큰 x, 앞면)에서 떨어진 거리
        pc = ref_cells(src, box, nx, ny, bg=120, drop=drop)
        m.tex(key, cell_tex(pc))
        lathe(m, pc, 8 + half + dx - nx / 2, front + dz, ny, key, chamfer=4)
    if "leaf" in ref:                                            # 잎: 모양대로 오린 판, 블루베리 뒤에 세운다
        m.tex("leaf", cut_tex(ref_cells(src, ref["leaf"], 8, 5, bg=120)))
        x0 = 8 + half + 3
        m.box([x0, 2, front - 2.6], [x0 + 4, 4.5, front - 2.4], {f: "leaf" for f in ("north", "south", "east", "west", "up", "down")},
              uv={"north": [0, 0, 4, 2.5], "south": [4, 0, 0, 2.5], "east": [0, 0, 0.1, 2.5], "west": [0, 0, 0.1, 2.5],
                  "up": [0, 0, 4, 0.1], "down": [0, 2.4, 4, 2.5]})
    m.tex("tag", cut_tex(ref_cells(src, ref["tag"], 10, 12, bg=120)))
    tx, ty = 8 - half - 2, h - 3.5                               # 꼬리표: 오른쪽 어깨, 윗변이 덮개 끈 높이 바로 아래
    m.box([tx, ty - 6, front - 0.4], [tx + 5, ty, front - 0.2], {f: "tag" for f in ("north", "south", "east", "west", "up", "down")},
          uv={"north": [0, 0, 5, 6], "south": [5, 0, 0, 6], "east": [0, 0, 0.1, 6], "west": [0, 0, 0.1, 6],
              "up": [0, 0, 5, 0.1], "down": [0, 5.9, 5, 6]})
    m.tex("string", rough([rgb(150, 92, 48), rgb(122, 72, 36)], 241))
    m.box([tx + 4.5, ty - 0.3, front - 0.2], [tx + 4.9, h - 2.5, front + 0.6], "string")
    fit_block(m)
    return m


def yogurt():
    return jar_item("yogurt")


def kimchi():
    return jar_item("kimchi")


def relief(m, cols, top_key, up_top=True):
    """위에서 본 그림(16x16 칸, 왼쪽 = 큰 x, 위쪽 = 뒤 +z) 칸마다 기둥을 세운다. cols: {(gx, gz): [(y0, y1, 옆면 재질), ...]}.
    윗면은 top_key 그림의 그 칸 (up_top=False 면 재료가 아닌 재질은 윗면도 제 재질), 옆면은 주어진 재질. 같은 줄에서 이웃하고 높이·재질이 같은 칸을 묶고,
    앞뒤 줄의 묶음이 똑같으면 다시 하나로 합친다 (큐브 수를 줄인다)."""
    layers = {}
    for (gx, gz), parts in cols.items():
        merged = []                                              # 같은 재질로 위아래 이어진 층은 한 기둥으로
        for y0, y1, side in sorted(parts):
            if merged and merged[-1][2] == side and merged[-1][1] == y0 and side != top_key:
                merged[-1] = (merged[-1][0], y1, side)
            else:
                merged.append((y0, y1, side))
        for y0, y1, side in merged:
            layers.setdefault((gz, y0, y1, side), []).append(gx)
    runs = {}                                                    # (g0, g1, y0, y1, side) → [gz, ...]
    for (gz, y0, y1, side), xs in layers.items():
        xs.sort()
        start = prev = xs[0]
        for gx in xs[1:] + [None]:
            if gx is not None and gx == prev + 1:
                prev = gx
                continue
            runs.setdefault((start, prev + 1, y0, y1, side), []).append(gz)
            if gx is not None:
                start = prev = gx
    for (g0, g1, y0, y1, side), zs in runs.items():
        zs.sort()
        groups = [[zs[0], zs[0] + 1]]
        for gz in zs[1:]:
            if gz == groups[-1][1]:
                groups[-1][1] = gz + 1
            else:
                groups.append([gz, gz + 1])
        for r0, r1 in groups:
            xa, xb, za, zb = 16 - g1, 16 - g0, 16 - r1, 16 - r0
            top = [g1 / 2, r1 / 2, g0 / 2, r0 / 2]
            strip = side == top_key                              # 재료 옆면: 윗면 그림 가장자리 색을 늘인다
            ns = [g0 / 2, r0 / 2, g1 / 2, (r0 + 0.5) / 2] if strip else [g0 / 2, 0, g1 / 2, (y1 - y0) / 2]
            ew = [g0 / 2, r0 / 2, (g0 + 0.5) / 2, r1 / 2] if strip else [0, 0, 0.5, (y1 - y0) / 2]
            up_key = top_key if strip or up_top else side            # 그릇 같은 재질은 윗면도 제 무늬 (위 그림의 이웃 색이 묻지 않게)
            m.box([xa, y0, za], [xb, y1, zb], {f: (up_key if f == "up" else side) for f in ("north", "south", "east", "west", "up", "down")},
                  uv={"up": top if up_key == top_key else [0, 0, 0.5, 0.5], "down": top if strip else [0, 0, 0.5, 0.5],
                      "north": ns, "south": ns, "east": ew, "west": ew})


def bacon_and_eggs():
    """베이컨 에그 (사용자 3D 시안 그대로): 둥근 나무 판 위에 베이컨 세 줄(왼쪽 위), 계란 프라이(오른쪽), 허브(아래).
    판·재료 자리는 시안 배치대로 정하고, 윗면은 상단 그림을 칸 위치 그대로 입힌다 (재료마다 높이만 다르게)."""
    import math
    src = png.read(os.path.join(REF_DIR, "plates.png"))
    m = Model("bacon_and_eggs")
    m.tex("top", cell_tex(ref_cells(src, (528, 433, 612, 512), 16, 16, bg=90)))
    m.tex("wood", cell_tex(ref_cells(src, (286, 462, 376, 491), 16, 6, bg=90)))
    near = lambda g, c, r: math.hypot(g[0] - c[0], g[1] - c[1]) <= r
    cols = {}
    for gz in range(16):
        for gx in range(16):
            g = (gx + 0.5, gz + 0.5)
            if not near(g, (8, 8), 7.9):
                continue
            parts = [(0, 1.2, "wood")]                            # 나무 판
            if near(g, (10.5, 8.3), 3.6):                         # 계란: 흰자 낮게, 노른자 볼록
                parts.append((1.2, 1.6, "top"))
                if near(g, (10.2, 7.3), 1.8):
                    parts.append((1.6, 2.3, "top"))
            elif near(g, (5.8, 12.4), 1.7):                       # 허브
                parts.append((1.2, 1.7, "top"))
            elif near(g, (8, 8), 6.6) and gz < 10.5 and gx + 0.6 * gz < 13.5:   # 베이컨 세 줄 (왼쪽 위 띠)
                parts.append((1.2, 1.9, "top"))
            cols[(gx, gz)] = parts
    relief(m, cols, "top")
    return m


def kimchi_fried_rice():
    """김치볶음밥 (사용자 3D 시안 그대로): 짙은 그릇(굽 + 오므라든 몸통 + 테두리)에 봉긋한 볶음밥, 꼭대기에 계란 프라이.
    그릇·밥·계란 자리는 시안 배치대로 정하고, 윗면은 상단 그림을 칸 위치 그대로 입힌다."""
    import math
    src = png.read(os.path.join(REF_DIR, "plates.png"))
    m = Model("kimchi_fried_rice")
    m.tex("top", cell_tex(ref_cells(src, (1295, 430, 1381, 515), 16, 16, bg=90)))
    bowl = ref_cells(src, (813, 478, 902, 508), 16, 6, bg=60)
    reddish = lambda c: c[0] > c[1] * 1.6 + 20                   # 밥의 붉은 기가 섞인 칸
    browns = sorted((c for row in bowl for c in row if c and not reddish(c)), key=sum)
    for row in bowl:                                             # 붉은 칸은 그릇 갈색으로
        for x, c in enumerate(row):
            if c and reddish(c):
                row[x] = browns[(x * 7) % len(browns)]
    m.tex("bowl", cell_tex(bowl))
    rr = lambda gx, gz: math.hypot(gx + 0.5 - 8, gz + 0.5 - 8)
    rim = {(gx, gz) for gz in range(16) for gx in range(16) if 6.4 < rr(gx, gz) <= 7.9}
    cols = {}
    for gz in range(16):
        for gx in range(16):
            r = rr(gx, gz)
            if r > 7.9:
                continue
            parts = []
            if r <= 4.6:
                parts.append((0, 1, "bowl"))                      # 굽
            if r <= 6.6:
                parts.append((1, 2, "bowl"))
            if r > 6.4:
                parts.append((2 if r <= 6.6 else 2.5, 6, "bowl"))  # 몸통 바깥 (맨 바깥 칸은 조금 위에서 시작해 둥글게 오므라든다)
                parts.append((6, 6.8, "bowl"))                    # 테두리
            else:
                parts.append((2, 5, "bowl"))                      # 몸통 안쪽 (위는 볶음밥)
                ey = round(6 + 3.6 * (1 - (r / 6.4) ** 2))       # 가운데가 봉긋 (1칸 단위 계단)
                if any((gx + dx, gz + dz) in rim for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    ey = max(ey - 1, 5.5)                         # 그릇 벽과 면으로 맞닿은 밥은 한 칸 낮게
                parts.append((5, ey, "top"))
                e = math.hypot(gx + 0.5 - 8.3, gz + 0.5 - 4.8)
                if e <= 2.9:                                      # 계란 프라이 (뒤쪽 꼭대기)
                    parts.append((ey, ey + 0.4, "top"))
                    if math.hypot(gx + 0.5 - 8.2, gz + 0.5 - 4.2) <= 1.5:
                        parts.append((ey + 0.4, ey + 1.0, "top"))
            cols[(gx, gz)] = parts
    relief(m, cols, "top", up_top=False)
    return m


def punch(img, cx, cy, rx, ry):
    """치즈 구멍: 타원 안을 짙게 (위쪽 절반은 더 짙은 그늘)"""
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            if not (0 <= y < len(img) and 0 <= x < len(img[0])):
                continue
            d = ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2
            if d <= 1:
                img[y][x] = rgb(150, 88, 22) if y + 0.5 < cy else rgb(196, 124, 34)


def cheese():
    """치즈 바퀴 (사용자 3D 시안 그대로, 16×8×16): 상단 그림(앞쪽이 쐐기 모양으로 잘린 원)을 칸마다 따서 칠해진 칸을
    높이 8칸 판으로 세운다. 같은 줄에서 이어진 칸끼리, 같은 모양인 줄끼리 묶는다. 윗면 = 상단, 밑면 = 하단,
    앞뒤 = 정면·후면, 옆 = 우측·좌측 그림. 상단 그림 위쪽이 뒤(+z), 왼쪽이 큰 x."""
    src = png.read(os.path.join(REF_DIR, "juice2.png"))
    m = Model("cheese")
    top = ref_cells(src, (1366, 455, 1431, 515), 16, 16, bg=150)
    top_img = cell_tex(top)
    for h in ((5, 5, 2.2, 1.9), (11, 4, 1.2, 1.0), (13, 10, 1.4, 1.2), (4, 11, 1.2, 1.0)):
        punch(top_img, *h)                                       # 윗면 구멍 (쐐기 자리는 피함)
    m.tex("top", top_img)
    import math
    notch = set()                                                # 판 쐐기 칸 (자른 면 판별용)
    for gz in range(16):                                         # 앞쪽(그림 아래) 쐐기를 가운데까지 판다 (시안처럼 약 1/7 조각)
        for gx in range(16):
            dx, dz = gx + 0.5 - 8, gz + 0.5 - 8
            if dz > 0 and abs(dx) < dz * math.tan(math.radians(26)):
                top[gz][gx] = None
                notch.add((gx, gz))
    rnd = random.Random(250)
    inner = [[rgb(255, 222, 120) if rnd.random() < 0.6 else rgb(250, 206, 92) for _ in range(32)] for _ in range(32)]
    for h in ((4, 4, 2.6, 2.2), (12, 7, 2.0, 1.7), (6, 12, 2.2, 1.9), (13, 14, 2.6, 2.2), (2, 9, 1.4, 1.2)):  # 속살 구멍 (1칸 = 2픽셀)
        punch(inner, *h)
    m.tex("inner", inner)
    m.tex("bottom", cell_tex(ref_cells(src, (1447, 462, 1506, 519), 16, 16, bg=150)))
    rind = {"front": (1052, 480, 1114, 511), "back": (1211, 480, 1273, 511),
            "right": (1132, 480, 1193, 511), "left": (1290, 480, 1351, 511)}
    holes = {"front": [(3, 4, 1.6, 1.3), (10, 3, 1.2, 1.0), (13, 5, 1.4, 1.2)],        # (가운데 x, y, 반지름 x, y) 칸
             "back": [(4, 3, 1.4, 1.2), (11, 5, 1.6, 1.3)],
             "right": [(5, 5, 1.6, 1.3), (12, 3, 1.2, 1.0)],
             "left": [(4, 3, 1.2, 1.0), (10, 5, 1.6, 1.3)]}
    for key, box in rind.items():
        img = cell_tex(ref_cells(src, box, 16, 8, bg=150))
        img[1][:16] = img[2][:16]                                # 시안 축소 때 생긴 2번째 줄의 밝은 띠 → 아래 줄 색
        for h in holes[key]:
            punch(img, *h)
        m.tex(key, img)
    runs = []                                                    # [첫 줄, 끝 줄+1, (열 시작, 열 끝+1)]
    open_runs = {}
    for gz, row in enumerate(top):
        cur, x = [], 0
        while x < 16:
            if row[x]:
                x0 = x
                while x < 16 and row[x]:
                    x += 1
                cur.append((x0, x))
            x += 1
        nxt = {}
        for span in cur:
            if span in open_runs:
                open_runs[span][1] = gz + 1
                nxt[span] = open_runs[span]
            else:
                nxt[span] = [gz, gz + 1, span]
                runs.append(nxt[span])
        open_runs = nxt
    def cut(cells):                                              # 면 바깥 칸 중 드러난 칸(치즈가 아닌 칸)이 대부분 쐐기 칸이면 자른 면 (속살)
        shown = [c for c in cells if not (0 <= c[0] < 16 and 0 <= c[1] < 16 and top[c[1]][c[0]])]
        return bool(shown) and sum(c in notch for c in shown) * 2 > len(shown)

    pieces = []                                                  # 앞면이 쐐기 홈 쪽·바깥 둘레 쪽에 함께 드러나는 판은 바뀌는 곳에서 둘로 나눈다
    for gz0, gz1, (gx0, gx1) in runs:
        kind = [(gx, gz1) in notch if not (gz1 < 16 and top[gz1][gx]) else None for gx in range(gx0, gx1)]
        for i in range(len(kind)):                               # 막힌 칸(None)은 이웃 쪽을 따른다
            if kind[i] is None:
                kind[i] = next((k for k in kind[i:] + kind[:i][::-1] if k is not None), False)
        start = gx0
        for gx in range(gx0 + 1, gx1 + 1):
            if gx == gx1 or kind[gx - gx0] != kind[gx - gx0 - 1]:
                pieces.append((gz0, gz1, (start, gx)))
                start = gx
    for gz0, gz1, (gx0, gx1) in pieces:
        xa, xb, za, zb = 16 - gx1, 16 - gx0, 16 - gz1, 16 - gz0
        m.box([xa, 0, za], [xb, 8, zb], {"up": "top", "down": "bottom",
                                         "north": "inner" if cut([(gx, gz1) for gx in range(gx0, gx1)]) else "front",
                                         "south": "back",
                                         "west": "inner" if cut([(gx1, gz) for gz in range(gz0, gz1)]) else "right",
                                         "east": "inner" if cut([(gx0 - 1, gz) for gz in range(gz0, gz1)]) else "left"},
              uv={"up": [gx1 / 2, gz1 / 2, gx0 / 2, gz0 / 2], "down": [gx1 / 2, gz0 / 2, gx0 / 2, gz1 / 2],
                  "north": [gx0 / 2, 0, gx1 / 2, 4], "south": [xa / 2, 0, xb / 2, 4],
                  "west": [za / 2, 0, zb / 2, 4], "east": [gz0 / 2, 0, gz1 / 2, 4]})
    return m


POT_REF = {            # 사용자 3D 시안 (art/ref/pots.png): 정면·후면 몸통(손잡이 뺀 부분), 상단 안쪽 원
    "beef_stew": {"front": (61, 449, 125, 493), "back": (296, 449, 361, 493), "top": (531, 441, 596, 502),
                  "rim": rgb(150, 80, 40), "chunks": [((5, 6), (2, 1, 2), rgb(110, 58, 34)), ((9, 8.5), (2, 1, 2), rgb(96, 50, 30)),
                                                       ((7.5, 10), (1.5, 0.8, 1.5), rgb(230, 110, 40)), ((10.5, 5.5), (1.5, 0.8, 1.5), rgb(236, 120, 44)),
                                                       ((6, 8.5), (1.5, 0.8, 1.5), rgb(236, 196, 90)), ((8, 7), (1, 0.5, 1), rgb(90, 150, 50))],
                  "cloth": True},
    "chicken_soup": {"src": "cookie_soups.png", "front": (547, 464, 599, 506), "back": (707, 470, 758, 506), "top": (862, 458, 915, 511),
                     "rim": rgb(240, 220, 190),
                     "chunks": [((7, 7), (3, 0.6, 1.2), rgb(240, 222, 196)), ((8.5, 9), (2.5, 0.6, 1.2), rgb(232, 210, 180)),
                                ((10, 6.5), (1.2, 0.6, 1.2), rgb(230, 110, 40)), ((5.5, 9.5), (1.2, 0.6, 1.2), rgb(236, 120, 44)),
                                ((9, 5), (1, 0.5, 1), rgb(150, 196, 80)), ((8, 8), (1, 0.4, 1), rgb(80, 150, 50))],
                     "extras": [([-2, 0, -1.5], [1.5, 1.4, 1], rgb(240, 214, 180), 22.5), ([-1, 0, 1.2], [2.2, 1.2, 3.2], rgb(232, 204, 168), 22.5),
                                ([1.8, 0, -2], [3.6, 0.6, -0.4], rgb(80, 150, 50), 0)]},
    "vegetable_soup": {"src": "cookie_soups.png", "front": (1058, 464, 1110, 506), "back": (1217, 466, 1268, 506),
                       "top": (1373, 458, 1425, 511), "rim": rgb(150, 90, 50),
                       "chunks": [((6, 7), (1.4, 0.8, 1.4), rgb(245, 226, 170)), ((9.5, 8.5), (1.4, 0.8, 1.4), rgb(240, 220, 160)),
                                  ((8, 5.5), (1.2, 0.7, 1.2), rgb(230, 110, 40)), ((10.5, 6), (1.2, 0.7, 1.2), rgb(100, 150, 60)),
                                  ((7, 10), (1.2, 0.7, 1.2), rgb(210, 60, 40)), ((8, 8), (1, 0.4, 1), rgb(80, 150, 50))],
                       "extras": [([-3, 0, -1], [3, 1.6, 0.6], rgb(232, 120, 40), 22.5), ([-2.5, 0, 1.5], [0.5, 3, 4.5], rgb(206, 44, 36), 0),
                                  ([1.5, 0, -3.5], [4.3, 2.6, -0.7], rgb(244, 226, 190), 0), ([3.5, 0, -1], [5, 1, 3], rgb(140, 196, 80), 0)]},
    "ratatouille": {"src": "pasta_rata3d.png", "front": (827, 452, 894, 498), "back": (1062, 452, 1132, 498),
                    "top": (1145, 692, 1271, 808), "rim": rgb(168, 78, 43), "cloth": True, "cloth_color": rgb(125, 143, 46),
                    "chunks": [((8, 8), (1.2, 0.4, 1.2), rgb(90, 140, 50)), ((7.4, 8.6), (2.6, 0.2, 0.5), rgb(110, 160, 60))],
                    "extras": [([-2.5, 0.5, -1.5], [0.5, 3, 1.2], rgb(214, 66, 43), 0), ([10.5, 0, -2.4], [16, 2.4, 0.2], rgb(102, 92, 156), 22.5),
                               ([0.8, 0.5, -3], [3.6, 1.2, -0.4], rgb(125, 143, 46), 0), ([3.2, 0.5, -2.6], [5.6, 1.1, -0.2], rgb(212, 216, 120), 0)]},
    "corn_soup": {"front": (829, 448, 893, 501), "back": (1064, 448, 1129, 501), "top": (1299, 441, 1364, 504),
                  "rim": rgb(236, 206, 160), "chunks": [((7, 7), (1, 0.6, 1), rgb(250, 196, 40)), ((8.5, 8), (1, 0.6, 1), rgb(244, 180, 30)),
                                                        ((8, 6), (1, 0.6, 1), rgb(252, 206, 60)), ((9.5, 6.5), (0.6, 0.4, 0.6), rgb(110, 160, 60)),
                                                        ((6, 9), (1, 0.6, 1), rgb(248, 190, 40))],
                  "corn": True},
}


def pot_item(name):
    """냄비 요리 (사용자 3D 시안 비율, 16×12×12): 바닥 받침 + 둥근 몸통(모서리 2칸 깎은 8각) + 둥근 테두리 고리 + 좌우 고리 손잡이.
    앞면 = 정면 그림, 옆·뒤 = 후면 그림, 내용물 윗면(상단 그림)은 테두리보다 한 칸 아래, 건더기 몇 개를 도드라지게 올린다.
    스튜는 빨간 체크 천 위에, 수프는 옆에 옥수수. 시안의 냄비가 배경과 비슷하게 어두워 실루엣은 따지 않고 모양을 직접 쌓는다."""
    ref = POT_REF[name]
    src = png.read(os.path.join(REF_DIR, ref.get("src", "pots.png")))
    m = Model(name)
    m.tex("front", cell_tex(ref_cells(src, ref["front"], 12, 8, bg=70)))
    m.tex("side", cell_tex(ref_cells(src, ref["back"], 12, 8, bg=70)))
    m.tex("top", cell_tex(ref_cells(src, ref["top"], 13, 13, bg=70)))
    rnd = random.Random(270)
    rim = ref["rim"]
    def jitter(col, lo, hi):                                     # 한 색을 칸마다 살짝 흔든 32x32 재질
        return [[tuple(max(0, min(255, int(v * rnd.uniform(lo, hi)))) for v in col[:3]) + (255,) for _ in range(32)] for _ in range(32)]

    m.tex("rim", jitter(rim, 0.9, 1.08))
    base = 0.5 if ref.get("cloth") else 0
    if ref.get("cloth"):                                         # 빨간 체크 천 (냄비 받침)
        stripe = ref.get("cloth_color", rgb(186, 52, 44))
        m.tex("cloth", [[stripe if (x // 3) % 3 == 0 or (y // 3) % 3 == 0 else rgb(240, 226, 204) for x in range(32)] for y in range(32)])
        m.box([0.5, 0, 1.5], [15.5, 0.5, 14.5], "cloth")

    def octo(x0, x1, y0, y1, cut, mat, uv_rows=None, top=None):  # 모서리를 깎은 8각 판 (두 판을 십자로 겹침)
        h = (x1 - x0) / 2
        for k, (dx, dz) in enumerate(((h - cut, h), (h, h - cut))):
            e = 0.01 * k
            faces = {"north": "front" if uv_rows else mat, "south": mat, "east": mat, "west": mat,
                     "up": top or mat, "down": mat}
            uv = {}
            if uv_rows:
                v0, v1 = uv_rows
                for f in ("north", "south", "east", "west"):
                    half = dx if f in ("north", "south") else dz
                    uv[f] = [(6 - half) / 2, v0 / 2, (6 + half) / 2, v1 / 2]
            if top:
                uv["up"] = [(6.5 - dx) / 2, (6.5 - dz) / 2, (6.5 + dx) / 2, (6.5 + dz) / 2]
            m.box([8 - dx, y0 + e, 8 - dz], [8 + dx, y1 - e, 8 + dz], faces, uv=uv or None)

    octo(3, 13, base, base + 1, 2, "side", uv_rows=(7, 8))                     # 바닥 받침
    octo(2, 14, base + 1, base + 7, 2.5, "side", uv_rows=(1, 7), top="top")    # 몸통 (윗면 = 내용물, 테두리보다 한 칸 아래)
    import math
    for i in range(13):                                          # 테두리: 몸통 위 둥근 고리 벽 (1칸 높이), 칸마다 원 안팎으로 판단해 줄 단위로 묶는다
        z0 = 1.5 + i
        run = None
        for j in range(14):
            d = math.hypot(1.5 + j + 0.5 - 8, z0 + 0.5 - 8) if j < 13 else 99
            on = d <= 6.6 and d > 5.4
            if on and run is None:
                run = j
            elif not on and run is not None:
                m.box([1.5 + run, base + 7, z0], [1.5 + j, base + 8, z0 + 1], "rim")
                run = None
    for x0, x1, xo in ((0, 0.8, 0.8), (15.2, 16, 14.5)):                       # 고리 손잡이 (바깥 막대 + 위아래 연결)
        m.box([x0, base + 4.5, 7], [x1, base + 7.5, 9], "rim")
        for yy in (base + 4.5, base + 6.7):
            m.box([min(x0, xo), yy, 7], [max(x1, xo + 0.7), yy + 0.8, 9], "rim")
    for i, ((cx, cz), (w, h, d), col) in enumerate(ref["chunks"]):            # 건더기
        key = "chunk%d" % i
        m.tex(key, jitter(col, 0.85, 1.1))
        m.box([cx - w / 2, base + 7, cz - d / 2], [cx + w / 2, base + 7 + h, cz + d / 2], key)
    for i, (frm, to, col, angle) in enumerate(ref.get("extras", [])):       # 옆에 놓인 재료 (앞 오른쪽 = 작은 x)
        key = "extra%d" % i
        m.tex(key, jitter(col, 0.88, 1.1))
        m.box(frm, to, key)
        if angle:
            m.elements[-1]["rotation"] = {"origin": [(frm[0] + to[0]) / 2, frm[1], (frm[2] + to[2]) / 2], "axis": "y", "angle": angle}
    if ref.get("corn"):                                          # 옆에 놓인 옥수수 (앞 오른쪽 = 작은 x) + 낱알
        m.tex("cob", [[rgb(252, 204, 52) if (x + y // 2) % 2 else rgb(232, 160, 30) for x in range(32)] for y in range(32)])
        m.tex("husk", rough([rgb(110, 160, 60), rgb(80, 130, 44)], 271))
        n = len(m.elements)
        m.box([-3, 0, -1], [0.5, 3.2, 7], "cob")
        m.box([-3.4, 0, 7], [0.9, 2.6, 9.5], "husk")
        for e in m.elements[n:]:
            e["rotation"] = {"origin": [-1.2, 0, 4], "axis": "y", "angle": 22.5}
        for x, z in ((2.5, -1.5), (4, -2.5), (1.5, -3)):
            m.box([x, 0, z], [x + 1, 0.8, z + 1], "cob")
    fit_block(m)
    return m


def beef_stew():
    return pot_item("beef_stew")


def corn_soup():
    return pot_item("corn_soup")


def meat_slab(name, top_colors, side_colors, seed, pattern=None):
    m = Model(name)
    m.tex("top", rough(top_colors, seed, pattern=pattern))
    m.tex("side", rough(side_colors, seed + 1))
    disc(m, 8, 8, 0, 3, 5.5, sides("top", "side"), inset=1.6)
    return m


MEAT_REF = {           # 사용자 3D 시안 (art/ref/meats.png): 정면 단면(조각 위 덩어리 부분), 후면, 좌우, 상단, 하단, 꼬리표(큰 그림)
    "smoked_beef": {"meat": lambda c: (c[0] - c[2]) / 2 >= 67,                 # 살 칸 구분 (껍질은 어둡고 덜 붉다)
                    "front": (40, 465, 97, 497), "back": (199, 465, 255, 517), "right": (118, 466, 179, 516),
                    "left": (277, 466, 334, 516), "top": (355, 464, 409, 520), "bottom": (430, 470, 487, 512)},
    "bacon": {"meat": lambda c: sum(c[:3]) / 3 >= 100,
              "front": (546, 469, 604, 501), "back": (709, 465, 765, 516), "right": (625, 465, 687, 516),
              "left": (788, 465, 845, 516), "top": (868, 465, 922, 517), "bottom": (944, 470, 999, 514),
              "tag": (853, 180, 941, 295)},
    "smoked_salmon": {"meat": lambda c: (c[0] - c[2]) / 2 >= 95,
                      "front": (1054, 469, 1113, 499), "back": (1216, 465, 1271, 514), "right": (1132, 465, 1193, 516),
                      "left": (1295, 465, 1353, 516), "top": (1375, 465, 1430, 519), "bottom": (1450, 470, 1509, 515),
                      "tag": (1370, 170, 1465, 290)},
}


def meat_roast(name):
    """끈으로 묶은 고기 덩어리 + 앞에 누운 두 조각 (사용자 3D 시안 그대로, 덩어리 16×12×12).
    정면 단면 그림의 줄마다 길이(z) 방향으로 밀어 낸 판을 쌓되, 껍질은 살 둘레 1칸만 남기고 나머지는 깎는다.
    맨 위에 끈 매듭(후면 그림 위 줄)을 가운데에 작게. 앞면 = 단면, 뒤·옆 = 후면·우측·좌측의 몸통 부분, 위 = 상단(끈).
    윗면 네 변은 위 두 줄을 좌우·앞뒤 2·1칸 들여 둥글게 깎는다.
    조각은 크기·놓임을 달리한 두 장 (바닥에 비스듬히 하나, 앞면에 기대 하나). 꼬리표는 오른쪽 옆면(화면 오른쪽 = 작은 x)에 건다."""
    ref = MEAT_REF[name]
    src = png.read(os.path.join(REF_DIR, "meats.png"))
    m = Model(name)
    W, H, L, FH = 16, 15, 12, 9                                  # 폭, 후면 줄 수(끈 매듭 포함), 길이, 단면 줄 수
    Z0 = 4                                                       # 덩어리 z 4..16, 앞쪽은 조각 자리
    FR = 12                                                      # 몸통 단면 줄 수 (정면 그림을 이 줄 수로 줄인다)
    back = ref_cells(src, ref["back"], W, H, bg=120)             # 끈 매듭 + 겉면 (매듭은 위 몇 줄)
    front = ref_cells(src, ref["front"], W, FH, bg=120)          # 조각용 단면
    face = ref_cells(src, ref["front"], W, FR, bg=120)           # 몸통 단면

    def body_rows(box):                                          # 옆·뒤 그림에서 끈 매듭(위 1/5)을 뺀 몸통 부분을 FR 줄로
        x0, y0, x1, y1 = box
        return cell_tex(ref_cells(src, (x0, y0 + (y1 - y0) // 5, x1, y1), {"right": L, "left": L}.get(key, W), FR, bg=120))

    for key in ("right", "left"):
        m.tex(key, body_rows(ref[key]))
    key = "back"
    m.tex("back", body_rows(ref["back"]))
    m.tex("knot", cell_tex(back))
    m.tex("face", cell_tex(face))
    m.tex("front", cell_tex(front))
    m.tex("top", cell_tex(ref_cells(src, ref["top"], W, L, bg=120)))
    m.tex("bottom", cell_tex(ref_cells(src, ref["bottom"], W, L, bg=120)))
    # 껍질은 1칸만: 살 줄(살 칸이 4할 이상) 위아래로 껍질 한 줄씩, 살 줄 안에서는 살 칸 좌우로 한 칸씩만 남기고 나머지는 깎는다
    meat = ref["meat"]
    meat_rows = [r for r, row in enumerate(face)
                 if [c for c in row if c] and sum(meat(c) for c in row if c) >= 0.4 * len([c for c in row if c])]
    r_first, r_last = max(0, meat_rows[0] - 1), min(FR - 1, meat_rows[-1] + 1)

    def meat_span(r):
        cols = [x for x, c in enumerate(face[r]) if c and meat(c)]
        filled = [x for x, c in enumerate(face[r]) if c]
        return (max(min(filled), min(cols) - 1), min(max(filled), max(cols) + 1) + 1)

    rows = []
    for r in range(r_first, r_last + 1):
        if r in meat_rows:
            span = meat_span(r)
        else:                                                    # 껍질 줄: 이웃한 살 줄 폭 안으로
            near = meat_rows[0] if r < meat_rows[0] else meat_rows[-1]
            span = meat_span(near)
        i = r - r_first                                          # 윗면 모서리를 둥글게: 위 두 줄은 좌우·앞뒤를 2·1칸 들인다
        ins = (2, 1)[i] if i < 2 else 0
        rows.append((r, (span[0] + ins, span[1] - ins), ins))
    BH = len(rows)                                               # 몸통 높이 (칸)
    widest = max(c1 - c0 for _, (c0, c1), _ in rows)
    spans = row_spans(back)
    knot = [sp for sp in spans if sp[2][1] - sp[2][0] < (max(c1 - c0 for _, _, (c0, c1) in spans)) * 0.6 and sp[0] < 4]
    body_top = max((sp[1] for sp in knot), default=0)            # 후면 그림에서 매듭 줄 수
    H = BH + body_top                                            # 전체 높이 (매듭 포함)
    crust_cols = [c for row in back[body_top:] for c in row if c]
    crust_cols.sort(key=sum)
    crust_pal = crust_cols[len(crust_cols) // 5: len(crust_cols) * 4 // 5: max(1, len(crust_cols) // 12)]
    rnd = random.Random(260)
    m.tex("crust", [[rnd.choice(crust_pal) for _ in range(32)] for _ in range(32)])      # 그을린 겉면 (조각 둘레)
    u = lambda x: (16 - x) / 2                                   # 상단·하단 그림: 왼쪽 = 큰 x, 위쪽 = 뒤(+z)
    v = lambda z: (Z0 + L - z) / 2
    for r, (c0, c1), ins in rows:                                # 몸통: 한 줄씩 (정면 단면 줄 r 이 그대로 앞면)
        xa, xb = 8 - (c1 - c0) / 2, 8 + (c1 - c0) / 2
        y0 = BH - 1 - (r - r_first)
        za, zb = Z0 + ins, Z0 + L - ins
        m.box([xa, y0, za], [xb, y0 + 1, zb],
              {"north": "face", "south": "back", "east": "left", "west": "right", "up": "top", "down": "bottom"},
              uv={"north": [c0 / 2, r / 2, c1 / 2, (r + 1) / 2], "south": [c0 / 2, r / 2, c1 / 2, (r + 1) / 2],
                  "east": [(Z0 + L - zb) / 2, r / 2, (Z0 + L - za) / 2, (r + 1) / 2],
                  "west": [(za - Z0) / 2, r / 2, (zb - Z0) / 2, (r + 1) / 2],
                  "up": [u(xa), v(za), u(xb), v(zb)], "down": [u(xa), v(zb), u(xb), v(za)]})
    for r0, r1, (c0, c1) in knot:                                # 끈 매듭: 몸통 위 가운데에 작게
        xa, xb = 8 - (c1 - c0) / 2, 8 + (c1 - c0) / 2
        y0, y1 = H - r1, H - r0
        uv = [c0 / 2, r0 / 2, c1 / 2, r1 / 2]
        m.box([xa, y0, Z0 + L / 2 - 1.5], [xb, y1, Z0 + L / 2 + 1.5], "knot",
              uv={f: uv for f in ("north", "south", "east", "west", "up", "down")})
    # 조각 두 장: 크기·놓임을 달리 (하나는 바닥에 비스듬히, 하나는 덩어리 앞면에 기대 세움). 가장자리는 껍질 테두리
    sl = [row[:] for row in front]
    for y in range(FH):
        for x in range(W):
            if front[y][x] and any(not (0 <= y + dy < FH and 0 <= x + dx < W and front[y + dy][x + dx])
                                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                sl[y][x] = rnd.choice(crust_pal)
    m.tex("slice", cell_tex(sl))
    fspans = row_spans(front)
    T = 0.6                                                      # 조각 두께

    def faces(r0, r1, c0, c1, flat):
        top = [c0 / 2, r1 / 2, c1 / 2, r0 / 2] if flat else [c0 / 2, r0 / 2, c1 / 2, r1 / 2]
        return ({f: "slice" if f in (("up", "down") if flat else ("north", "south")) else "crust"
                 for f in ("north", "south", "east", "west", "up", "down")},
                {("up" if flat else "north"): top, ("down" if flat else "south"): top})

    def lying_slice(cx, cz, K, angle):                           # 바닥에 누운 조각
        n = len(m.elements)
        for r0, r1, (c0, c1) in fspans:
            mat, uv = faces(r0, r1, c0, c1, True)
            m.box([cx - (c1 - c0) / 2 * K, 0, cz + (FH / 2 - r1) * K], [cx + (c1 - c0) / 2 * K, T, cz + (FH / 2 - r0) * K],
                  mat, uv=uv)
        for e in m.elements[n:]:
            e["rotation"] = {"origin": [cx, 0, cz], "axis": "y", "angle": angle}

    def leaning_slice(cx, cz, K, angle):                         # 덩어리 앞면에 기대 세운 조각 (위가 뒤로 기운다)
        n = len(m.elements)
        for r0, r1, (c0, c1) in fspans:
            mat, uv = faces(r0, r1, c0, c1, False)
            m.box([cx - (c1 - c0) / 2 * K, (FH - r1) * K, cz - T], [cx + (c1 - c0) / 2 * K, (FH - r0) * K, cz], mat, uv=uv)
        for e in m.elements[n:]:
            e["rotation"] = {"origin": [cx, 0, cz], "axis": "x", "angle": angle}

    leaning_slice(9.5, Z0 - 2.2, 0.62, 22.5)
    lying_slice(5.5, 1.8, 0.5, -22.5)
    if "tag" in ref:                                             # 꼬리표: 오른쪽 옆면에 걸린 판
        m.tex("tag", cut_tex(ref_cells(src, ref["tag"], 10, 12, bg=120)))
        x0 = 8 - widest / 2 - 0.4
        ty = max(0.5, BH - 6.5)
        m.box([x0, ty, Z0 + 1.5], [x0 + 0.2, ty + 6, Z0 + 6.5], {f: "tag" for f in ("north", "south", "east", "west", "up", "down")},
              uv={"west": [0, 0, 5, 6], "east": [5, 0, 0, 6], "north": [0, 0, 0.1, 6], "south": [0, 0, 0.1, 6],
                  "up": [0, 0, 0.1, 5], "down": [0, 0, 0.1, 5]})
        m.tex("string", rough([rgb(214, 170, 100), rgb(180, 132, 70)], 242))
        m.box([x0 + 0.1, ty + 6, Z0 + 5.6], [x0 + 0.5, BH, Z0 + 6], "string")
    fit_block(m)
    return m


def smoked_beef():
    return meat_roast("smoked_beef")


def bacon():
    return meat_roast("bacon")


def smoked_salmon():
    return meat_roast("smoked_salmon")


def mortar():
    m = Model("mortar")
    p = S.MORTAR_P
    m.tex("stone", rough([p["s"], p["s"], p["S"]], 350))
    m.tex("rim", rough([p["L"], p["s"]], 351))
    m.tex("inside", rough([p["d"]], 352))
    m.tex("wood", rough([p["w"], p["W"]], 353))
    disc(m, 8, 8, 0, 1, 3.5, "stone", inset=1)                                   # 받침
    for frm, to in (([3, 1, 3], [13, 6, 4]), ([3, 1, 12], [13, 6, 13]),        # 그릇 벽 (속이 빔)
                    ([3, 1, 4], [4, 6, 12]), ([12, 1, 4], [13, 6, 12])):
        m.box(frm, to, sides("rim", "stone"))
    m.box([4, 1, 4], [12, 2, 12], "inside")
    m.box([8, 2, 7.5], [9, 11, 8.5], "wood")                                     # 공이
    m.box([7.6, 2, 7.1], [9.4, 3.5, 8.9], "wood")
    return m



# ═════════════ 시안 2026-11-15: 나무 도마 위, 한 조각 잘린 통 파이·피자 + 옆에 놓인 조각 ═════════════
def board(m, seed):
    m.tex("board", rough([rgb(150, 98, 54), rgb(128, 82, 44), rgb(164, 110, 62)], seed,
                         pattern=lambda x, y, r: rgb(116, 72, 38) if y % 5 == 4 else None))
    m.tex("board_side", rough([rgb(112, 70, 36), rgb(96, 60, 30)], seed + 1))
    m.box([0.5, 0, 1], [15.5, 1, 15], sides("board", "board_side"))


def layered(rows, seed):
    """옆면 단면 그림 (위→아래 층: [(색 목록, 줄 수), ...]) 16x16"""
    import random as _r
    rnd = _r.Random(seed)
    img = blank(16)
    y = 0
    for colors, n in rows:
        for _ in range(n):
            for x in range(16):
                img[min(15, y)][x] = rnd.choice(colors)
            y += 1
    while y < 16:
        img[y] = img[y - 1][:]
        y += 1
    return img


def quarter_round(m, cx, cz, r, y0, y1, keep, mat, uv=None, inset=1.4):
    """둥근 판을 사분면으로 쌓는다. keep: 남길 사분면 [(sx, sz)] (sx, sz = ±1, 모델 좌표 방향)"""
    for sx, sz in keep:
        xa, xb = sorted((cx, cx + sx * r))
        za, zb = sorted((cz, cz + sz * r))
        xi = (xa, xb - inset) if sx > 0 else (xa + inset, xb)
        zi = (za, zb - inset) if sz > 0 else (za + inset, zb)
        m.box([xi[0], y0, za], [xi[1], y1, zb], mat, uv=uv)
        m.box([xa, y0, zi[0]], [xb, y1, zi[1]], mat, uv=uv)


def wedge(m, x0, z0, length, width, y0, y1, mat, uv=None, steps=4):
    """뾰족한 조각: 앞(x0)이 뾰족하고 뒤로 갈수록 넓어지는 계단 쐐기 (x 방향 길이 length, z 방향 최대 폭 width)"""
    for i in range(steps):
        t0, t1 = i / steps, (i + 1) / steps
        w = width * t1
        m.box([x0 + length * t0, y0, z0 + (width - w) / 2], [x0 + length * t1, y1, z0 + (width + w) / 2], mat, uv=uv)


def apple_pie():
    """애플파이 (사용자 3D 시안 그대로): 갈색 파이 접시 + 울퉁불퉁 주름진 테두리 + 격자 반죽(도드라짐)과 그 사이 사과 속(낮음).
    윗면은 시안 팔레트로 격자 모양에 맞춰 칠하고(축소 그림은 격자 위치가 어긋나 읽히지 않음), 앞 오른쪽에 사과 한 알과 반쪽."""
    import math
    src = png.read(os.path.join(REF_DIR, "pies.png"))
    m = Model("apple_pie")
    rnd = random.Random(280)
    lattice = lambda gx, gz: (gx + 1) % 4 < 2 or (gz + 1) % 4 < 2
    gold, light, shade = rgb(242, 166, 59), rgb(255, 215, 122), rgb(210, 122, 46)
    fill_c = [rgb(154, 77, 38), rgb(170, 88, 40), rgb(130, 62, 30)]
    top = blank(32)                                              # 윗면: 시안 팔레트로 격자에 딱 맞춰 칠한다 (1칸 = 1픽셀)
    for gz in range(16):
        for gx in range(16):
            if math.hypot(gx + 0.5 - 8, gz + 0.5 - 8) > 6.2:
                top[gz][gx] = rnd.choice([gold, gold, light, shade])          # 테두리 반죽
            elif lattice(gx, gz):
                edge = not lattice(gx + 1, gz) or not lattice(gx, gz + 1)
                top[gz][gx] = shade if edge else rnd.choice([gold, light])    # 격자 띠 (아래·오른쪽 가장자리는 그늘)
            else:
                top[gz][gx] = rnd.choice(fill_c)                              # 사과 속
    m.tex("top", top)
    m.tex("dish", cell_tex(ref_cells(src, (281, 481, 377, 505), 16, 4, bg=90)))
    m.tex("crust", cell_tex(ref_cells(src, (281, 457, 377, 479), 16, 4, bg=90)))
    cols = {}
    for gz in range(16):
        for gx in range(16):
            dx, dz = gx + 0.5 - 8, gz + 0.5 - 8
            r = math.hypot(dx, dz)
            if r > 7.9:
                continue
            parts = [(0 if r <= 6.6 else 1, 4, "dish")]           # 접시 (바깥 칸은 조금 위에서 시작해 비스듬히)
            if r > 6.2:                                           # 주름진 테두리: 둘레를 따라 높낮이가 번갈아
                bump = int((math.atan2(dz, dx) + math.pi) / (2 * math.pi) * 22) % 2
                parts.append((4, 5.5 if bump else 5, "crust"))
            elif lattice(gx, gz):                                 # 격자 반죽 띠
                parts.append((4, 5, "top"))
            else:                                                 # 격자 사이 사과 속
                parts.append((4, 4.5, "top"))
            cols[(gx, gz)] = parts
    relief(m, cols, "top")

    def jitter(col, lo=0.88, hi=1.1):
        return [[tuple(max(0, min(255, int(v * rnd.uniform(lo, hi)))) for v in col[:3]) + (255,) for _ in range(32)] for _ in range(32)]

    m.tex("apple", jitter(rgb(206, 40, 36)))
    m.tex("flesh", jitter(rgb(250, 232, 190)))
    m.tex("stem", jitter(rgb(110, 70, 36)))
    m.tex("leaf", jitter(rgb(110, 160, 50)))
    ax, az = -2.5, -0.5                                           # 사과 한 알 (앞 오른쪽 = 작은 x)
    m.box([ax - 2, 0, az - 1.5], [ax + 2, 3.6, az + 1.5], "apple")
    m.box([ax - 1.5, 0.3, az - 2], [ax + 1.5, 3.3, az + 2], "apple")
    m.box([ax - 0.25, 3.6, az - 0.25], [ax + 0.25, 4.6, az + 0.25], "stem")
    m.box([ax + 0.25, 4, az - 0.2], [ax + 2, 4.3, az + 0.8], "leaf")
    hx, hz = 1.5, -3                                              # 반쪽 사과 (자른 면이 위)
    m.box([hx - 1.6, 0, hz - 1.6], [hx + 1.6, 1.6, hz + 1.6], {"up": "flesh", "down": "apple", "north": "apple",
                                                              "south": "apple", "east": "apple", "west": "apple"})
    fit_block(m)
    return m


def pizza():
    """피자 (사용자 3D 시안 그대로): 손잡이 달린 둥근 나무 판 + 도톰한 테두리와 토핑 얹은 피자, 앞 오른쪽으로 한 조각 잘라 낸 홈.
    윗면은 상단 그림을 칸 위치 그대로, 판은 하단 그림의 나무결."""
    import math
    src = png.read(os.path.join(REF_DIR, "pies.png"))
    m = Model("pizza")
    m.tex("top", cell_tex(ref_cells(src, (1281, 432, 1373, 516), 16, 16, bg=90)))
    m.tex("wood", cell_tex(ref_cells(src, (1402, 440, 1468, 506), 16, 16, bg=90)))
    m.tex("crust", cell_tex(ref_cells(src, (926, 463, 1024, 496), 16, 4, bg=90)))
    cols = {}
    for gz in range(16):
        for gx in range(16):
            dx, dz = gx + 0.5 - 8, gz + 0.5 - 8
            r = math.hypot(dx, dz)
            if r > 7.9:
                continue
            parts = [(0, 1, "wood")]                              # 나무 판
            cut = r > 0.6 and (dx + dz) / (r * math.sqrt(2)) > math.cos(math.radians(24))   # 앞 오른쪽으로 잘라 낸 조각
            if r <= 7.0 and not cut:
                parts.append((1, 2.4 if r > 5.8 else 1.7, "crust" if r > 5.8 else "top"))   # 도톰한 테두리 / 토핑 얹은 면
            cols[(gx, gz)] = parts
    relief(m, cols, "top", up_top=False)
    m.box([7, 0, -2], [9, 1, 1.5], "wood")                        # 손잡이 (앞쪽으로 뺀 뒤 45도 돌려 앞 오른쪽으로, 짧게)
    m.box([7.4, 0, -2.4], [8.6, 1, -2], "wood")
    for e in m.elements[-2:]:
        e["rotation"] = {"origin": [8, 0, 8], "axis": "y", "angle": 45}
    k = 7 / 8                                                     # 판을 블록 가운데에 두고 둘레가 경계에서 1픽셀 남게 (손잡이는 대각선 모서리 쪽 빈 곳으로)
    sc = lambda p: [round(8 + (p[0] - 8) * k, 3), round(p[1] * k, 3), round(8 + (p[2] - 8) * k, 3)]
    for e in m.elements:
        e["from"], e["to"] = sc(e["from"]), sc(e["to"])
        if e.get("rotation"):
            e["rotation"]["origin"] = sc(e["rotation"]["origin"])
    return m

MODELS = {
    "cooked_rice": cooked_rice, "salmon_sushi": salmon_sushi, "cabbage_wrap": cabbage_wrap, "honey_cookie": honey_cookie,
    "kimbap": kimbap, "mushroom_fried_rice": mushroom_fried_rice, "meatball_pasta": meatball_pasta,
    "ratatouille": ratatouille, "chicken_soup": chicken_soup, "fried_rice": fried_rice, "dumplings": dumplings,
    "vegetable_soup": vegetable_soup, "hamburger": hamburger,
    "tomato_sauce": tomato_sauce,                # 반죽·면·패티는 설치하지 않는 재료라 3D 없음 (2D 아이콘만)
    "pie_crust": pie_crust, "apple_pie": apple_pie,
    "bread_loaf": bread_loaf, "apple_juice": apple_juice, "grape_juice": grape_juice,
    "pineapple_juice": pineapple_juice, "pitaya_juice": pitaya_juice, "cheese": cheese, "yogurt": yogurt,
    "kimchi": kimchi, "beef_stew": beef_stew, "corn_soup": corn_soup, "kimchi_fried_rice": kimchi_fried_rice,
    "smoked_beef": smoked_beef, "bacon": bacon, "smoked_salmon": smoked_salmon, "bacon_and_eggs": bacon_and_eggs,
    "pizza": pizza, "mortar": mortar,
}

if __name__ == "__main__":
    assets = sys.argv[1]
    views = []
    for name, build in MODELS.items():
        model = build()
        model.save(assets)
        views.append(model.preview(5))
    if os.environ.get("PREVIEW"):
        cell = len(views[0])
        sheet = png.blank(cell * 6, cell * 3)
        for i, v in enumerate(views):
            png.paste(sheet, v, (i % 6) * cell, (i // 6) * cell)
        png.write(os.environ["PREVIEW"], sheet)
    print("ok: %d" % len(MODELS))

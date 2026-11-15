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


def cooked_rice():
    return rice_bowl("cooked_rice", S.RICE_P)


def fried_rice():
    p = S.FRIED_RICE_P
    return rice_bowl("fried_rice", p, specks=(p["a"], p["g"], p["e"]), seed=20)


def mushroom_fried_rice():
    p = S.MUSHROOM_RICE_P

    def tops(m):
        m.tex("mush", rough([p["u"], p["U"], p["u"]], 33))
        for x, z in ((5, 6), (9, 5.5), (7.5, 9.5), (10, 9)):
            m.box([x, 7.9, z], [x + 1.6, 8.6, z + 1.2], "mush")
    return rice_bowl("mushroom_fried_rice", p, specks=(p["t"], p["u"]), seed=30, toppings=tops)


def chicken_soup():
    p = S.CHICKEN_SOUP_P
    return soup_bowl("chicken_soup", p, [
        ("chicken", [p["w"], p["W"], p["w"]], [5, 4.8, 5.5], [7, 6.4, 7.5]),
        ("chicken", None, [9, 4.8, 8.5], [11, 6.2, 10.5]),
        ("chicken", None, [6, 4.8, 9.5], [7.8, 6, 11.2]),
        ("carrot", [p["a"], rgb(250, 160, 60)], [8.5, 4.8, 5], [10, 5.8, 6.5]),
        ("carrot", None, [4.5, 4.8, 8], [5.8, 5.7, 9.3]),
        ("herb", [p["e"], rgb(110, 180, 70)], [7.6, 5.0, 7.2], [8.6, 5.6, 8.2]),
    ], 40)


def vegetable_soup():
    p = S.VEGETABLE_SOUP_P
    return soup_bowl("vegetable_soup", p, [
        ("potato", [p["w"], p["W"]], [5, 4.8, 5.5], [7, 6.2, 7.5]),
        ("potato", None, [9, 4.8, 9], [10.8, 6, 10.8]),
        ("carrot", [p["a"], rgb(250, 180, 70)], [8.5, 4.8, 5], [10, 5.8, 6.5]),
        ("cabbage", [p["c"], p["e"], p["c"]], [5.5, 4.8, 9], [7.5, 5.6, 11]),
        ("carrot", None, [4.5, 4.8, 8], [5.8, 5.7, 9.3]),
    ], 50)


def salmon_sushi():
    m = Model("salmon_sushi")
    sp = S.SUSHI_P
    m.tex("board", rough([sp["n"], sp["n"], sp["N"]], 60, pattern=lambda x, y, r: sp["N"] if y % 5 == 0 else None))
    m.tex("boardside", rough([sp["N"], sp["M"]], 61))
    m.tex("rice", rough([sp["i"], sp["i"], sp["I"], sp["j"]], 62))
    m.tex("salmon", rough([sp["S"], sp["s"]], 63, pattern=lambda x, y, r: sp["f"] if (x + y) % 4 == 0 else None))
    m.tex("salmonside", rough([sp["s"], sp["t"]], 64))
    m.box([1.5, 0, 4], [3, 1, 12], "boardside")
    m.box([13, 0, 4], [14.5, 1, 12], "boardside")
    m.box([1, 1, 3.5], [15, 2, 12.5], sides("board", "boardside"))
    for x in (2.5, 9):
        m.box([x, 2, 5.5], [x + 4.5, 4, 10.5], "rice")
        m.box([x - 0.3, 4, 5], [x + 4.8, 4.8, 11], sides("salmon", "salmonside"))
        m.box([x + 0.4, 4.8, 5.6], [x + 4.1, 5.2, 10.4], "salmon")
    return m


def cabbage_wrap():
    m = Model("cabbage_wrap")
    wp = S.WRAP_P
    m.tex("leaf", rough([wp["G"], wp["y"], wp["G"], wp["g"]], 70, pattern=lambda x, y, r: wp["y"] if x % 5 == 2 else None))
    m.tex("end", rough([wp["q"], wp["P"], wp["p"]], 71, pattern=lambda x, y, r: wp["G"] if x in (0, 15) or y in (0, 15) else None))
    y = plate(m)
    for z, h in ((4.5, 0), (8.5, 0)):
        m.box([3, y, z], [12.5, y + 3, z + 3], {"up": "leaf", "down": "leaf", "north": "leaf", "south": "leaf", "east": "end", "west": "end"})
    return m


def kimbap():
    m = Model("kimbap")
    kp = S.KIMBAP_P
    face = blank(16)
    for yy in range(16):
        for xx in range(16):
            d = ((xx - 7.5) ** 2 + (yy - 7.5) ** 2) ** 0.5
            face[yy][xx] = kp["k"] if d > 6.5 else (kp["i"] if d > 3 else [kp["e"], kp["a"], kp["g"], kp["c"]][(xx // 3 + yy // 3) % 4])
    m.tex("slice", face)
    m.tex("wrap", rough([kp["k"], kp["K"], kp["k"]], 80))
    y = plate(m)
    for x, z in ((3, 7.5), (8.5, 8), (5.8, 3.5)):
        m.box([x, y, z], [x + 4, y + 2.5, z + 4], {"up": "slice", "down": "slice", "north": "wrap", "south": "wrap", "east": "wrap", "west": "wrap"},
              uv={"up": [0, 0, 16, 16], "down": [0, 0, 16, 16]})
    return m


def dumplings():
    m = Model("dumplings")
    dp = S.DUMPLING_P
    m.tex("skin", rough([dp["F"], dp["f"], dp["F"]], 90))
    m.tex("pleat", rough([dp["D"], dp["d"]], 91))
    m.tex("sear", rough([dp["s"], dp["d"]], 92))
    y = plate(m)
    for x, z in ((3, 8), (8.5, 8.5), (5.5, 3.8)):
        m.box([x, y, z], [x + 4.5, y + 1.8, z + 3], sides("skin", "skin", "sear"))
        m.box([x + 0.6, y + 1.8, z + 0.6], [x + 3.9, y + 2.6, z + 2.4], "skin")
        m.box([x + 0.8, y + 2.6, z + 1.2], [x + 3.7, y + 3.1, z + 1.8], "pleat")
    return m


def meatball_pasta():
    m = Model("meatball_pasta")
    mp = S.MEATBALL_PASTA_P
    m.tex("noodle", rough([mp["n"], mp["N"], mp["n"]], 100, pattern=lambda x, y, r: mp["N"] if (x + 2 * y) % 5 == 0 else None))
    m.tex("sauce", rough([mp["R"], mp["r"], mp["R"]], 101))
    m.tex("meat", rough([mp["P"], mp["q"], mp["p"], mp["Q"]], 102))
    m.tex("basil", rough([mp["v"], rgb(110, 190, 70)], 103))
    y = plate(m)
    y = mound(m, 8, 8, y, [(5, 1.2), (4, 1.0)], "noodle")
    disc(m, 8, 8, y, y + 0.5, 3, "sauce", inset=0.8)
    for x, z in ((5.5, 6), (8.5, 5.5), (7, 8.5)):
        m.box([x, y, z], [x + 2.2, y + 2.2, z + 2.2], "meat")
    m.box([9.5, y + 0.5, 9], [10.5, y + 0.8, 10], "basil")
    return m


def ratatouille():
    m = Model("ratatouille")
    rp = S.RATATOUILLE_P
    m.tex("sauce", rough([rp["s"], rp["a"]], 110))
    m.tex("tomato", rough([rp["A"], rp["a"]], 111))
    m.tex("eggplant", rough([rp["B"], rp["b"]], 112))
    m.tex("pumpkin", rough([rp["C"], rp["c"]], 113))
    y = plate(m)
    disc(m, 8, 8, y, y + 0.4, 5.5, "sauce", inset=1.2)
    y += 0.4
    kinds = ("tomato", "eggplant", "pumpkin")
    for row, z in enumerate((4.5, 7, 9.5)):
        for i in range(5):
            x = 3.2 + i * 2
            m.box([x, y, z], [x + 1.6, y + 2.2, z + 2], kinds[(i + row) % 3])
    return m


def honey_cookie():
    m = Model("honey_cookie")
    hp = S.HONEY_COOKIE_P
    m.tex("cookie", rough([hp["c"], hp["C"], hp["c"], hp["b"]], 120))
    m.tex("edge", rough([hp["b"], hp["B"]], 121))
    m.tex("honey", rough([hp["H"], hp["h"], hp["H"]], 122))
    for i, (y0, dx) in enumerate(((0, 0), (1.6, 0.6))):
        disc(m, 8 + dx, 8 - dx, y0, y0 + 1.6, 5, sides("cookie", "edge"), inset=1.4)
    disc(m, 8.6, 7.4, 3.2, 3.5, 3, "honey", inset=0.8)
    m.box([11.2, 1.9, 7], [12, 3.3, 7.8], "honey")                          # 흘러내린 꿀
    return m


def hamburger():
    m = Model("hamburger")
    hp = S.HAMBURGER_P
    m.tex("bun", rough([hp["c"], hp["b"], hp["c"], hp["C"]], 130, pattern=lambda x, y, r: hp["s"] if r.random() < 0.06 else None))
    m.tex("bunside", rough([hp["b"], hp["B"], hp["b"]], 131))
    m.tex("cut", rough([hp["C"], hp["c"]], 132))
    m.tex("patty", rough([hp["P"], hp["p"], hp["q"]], 133))
    m.tex("lettuce", rough([hp["G"], hp["y"], hp["g"]], 134))
    m.tex("tomato", rough([hp["R"], hp["r"], hp["R"]], 135))
    disc(m, 8, 8, 0, 1.6, 4.6, sides("cut", "bunside", "bunside"), inset=1.2)
    disc(m, 8, 8, 1.6, 3.6, 5, "patty", inset=1.2)
    disc(m, 8, 8, 3.6, 4.2, 4.4, "tomato", inset=1.0)
    disc(m, 8, 8, 4.2, 4.8, 5.6, "lettuce", inset=1.0)
    mound(m, 8, 8, 4.8, [(4.8, 2.2), (3.8, 1.2), (2.4, 0.6)], sides("bun", "bunside", "cut"))
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
    m = Model("tomato_sauce")
    tp = S.TOMATO_SAUCE_P
    m.tex("sauce", rough([tp["R"], tp["r"], tp["R"]], 160, pattern=lambda x, y, r: tp["G"] if x == 2 and 2 < y < 13 else None))
    m.tex("label", rough([tp["L"]], 161, pattern=lambda x, y, r: tp["s"] if 5 <= x <= 9 and 4 <= y <= 9 else None))
    m.tex("lid", rough([tp["B"], tp["O"], tp["b"]], 162))
    m.box([5, 0, 5], [11, 7, 11], "sauce")
    m.box([4.8, 2.5, 4.8], [11.2, 4.8, 11.2], {"up": "sauce", "down": "sauce", "north": "label", "south": "label", "east": "label", "west": "label"})
    m.box([4.6, 7, 4.6], [11.4, 8.6, 11.4], "lid")
    return m


def patty():
    m = Model("patty")
    pp = S.PATTY_P
    m.tex("meat", rough([pp["P"], pp["p"], pp["P"], pp["f"]], 170, weights=[4, 3, 4, 1]))
    m.tex("meatside", rough([pp["p"], pp["r"]], 171))
    disc(m, 8, 8, 0, 2, 5, sides("meat", "meatside"), inset=1.3)
    return m


MODELS = {
    "cooked_rice": cooked_rice, "salmon_sushi": salmon_sushi, "cabbage_wrap": cabbage_wrap, "honey_cookie": honey_cookie,
    "kimbap": kimbap, "mushroom_fried_rice": mushroom_fried_rice, "meatball_pasta": meatball_pasta,
    "ratatouille": ratatouille, "chicken_soup": chicken_soup, "fried_rice": fried_rice, "dumplings": dumplings,
    "vegetable_soup": vegetable_soup, "hamburger": hamburger,
    "dough": dough, "noodles": noodles, "tomato_sauce": tomato_sauce, "patty": patty,
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

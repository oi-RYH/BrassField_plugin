"""
요리 아이템을 만든다: 인벤토리 아이콘·손 3D 모델·ItemsAdder 정의. 노션 경제 설계 > 요리.

단계: 0단계(작물·바닐라 재료) → 보조 도구·절구 → 1단계(재료·음식) → 조리대 → 2단계 요리. 레시피는 BrassField config.yml.
- 아이콘: sprites.py (16x16 손 픽셀, 인벤토리·바닥·액자) / 3D 모델: make_food.py (손에 들었을 때)
- 아직 그림이 없는 아이템은 종류별 임시 아이콘(병·자루·그릇·고기·빵·접시·덩어리)으로 만들고 3D 없이 아이콘만 쓴다.
- 회복량(배고픔·포만감)은 아래 ITEMS 표. 재료(None)는 먹을 수 없다. 주스·요구르트는 마시는 동작.

사용: python3 -I tools/cooking/make_dishes.py <ItemsAdder contents/rustport>
  → resourcepack/assets/rustport/textures/item/food/<ID>.png, models/item/food/<ID>.json, configs/food.yml
  PREVIEW=<png> 를 주면 아이콘을 6배로 늘어놓은 미리보기를 그린다.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from food_kit import png, rgb, blank, dark_outline  # noqa: E402
from sprites import SPRITES  # noqa: E402
from make_food import MODELS  # noqa: E402

# 3D 가 지금 아이콘(시안 축소본)에 맞게 다시 만들어지기 전인 아이템: 확정 전까지 2D 아이콘만 쓴다
PENDING_3D = {"pie_crust", "mortar"}

# (ID, 이름, 단계 설명, (배고픔, 포만감) 또는 None=먹지 못함, 마시는지, 임시 아이콘 (모양, 색))
# 회복량 기준: 1단계 = 바닐라 날재료 범위(배고픔 2~4), 2단계 = 바닐라 가공 음식 범위(5~10, 포만감 = 배고픔 × 1.2).
# 그 안에서는 재료 수집 난이도로 매긴다: 0단계 재료 쉬움 1 (밀·감자·당근·사과·설탕·켈프·호박·버섯·달걀·물) /
# 보통 2 (생고기·연어·우유·토마토·양배추·양파·쌀·옥수수·마늘) / 어려움 3 (꿀·배추·고추·가지·포도·파인애플·용과).
# 요리 점수 = 0단계까지 풀어 개수만큼 더한 합 ÷ 한 번에 나오는 개수.
#   1단계: 2점 미만 2/1.2 · 2점 3/1.8 · 4점까지 3/3.6 · 6점까지 4/4.8 · 그 이상 4/6
#   2단계: 3점 5 · 4점 6 · 6점까지 7 · 8점까지 8 · 그 이상 10
S1_ING, S1_FOOD, S2 = "1단계 재료", "1단계 음식", "2단계 요리"
ITEMS = [
    # ── 1단계 재료 (보조 도구·절구) ──
    ("flour", "밀가루", S1_ING, None, False, ("sack", rgb(244, 240, 228))),
    ("cornmeal", "옥수수가루", S1_ING, None, False, ("sack", rgb(244, 206, 96))),
    ("dough", "반죽", S1_ING, None, False, None),
    ("noodles", "면", S1_ING, None, False, None),
    ("tomato_sauce", "토마토소스", S1_ING, None, False, None),
    ("patty", "패티", S1_ING, None, False, None),
    ("pie_crust", "파이 껍질", S1_ING, None, False, ("plate", rgb(222, 170, 96))),
    # ── 1단계 음식 (보조 도구) ──
    ("cooked_rice", "익힌 밥", S1_FOOD, (3, 1.8), False, None),
    ("honey_cookie", "꿀 쿠키", S1_FOOD, (3, 3.6), False, None),
    ("bread_loaf", "식빵", S1_FOOD, (3, 1.8), False, ("loaf", rgb(222, 160, 84))),
    ("apple_juice", "사과 주스", S1_FOOD, (3, 1.8), True, ("bottle", rgb(236, 196, 72))),
    ("grape_juice", "포도 주스", S1_FOOD, (4, 4.8), True, ("bottle", rgb(128, 52, 120))),
    ("pineapple_juice", "파인애플 주스", S1_FOOD, (3, 3.6), True, ("bottle", rgb(250, 220, 90))),
    ("pitaya_juice", "용과 주스", S1_FOOD, (3, 3.6), True, ("bottle", rgb(230, 70, 140))),
    ("cheese", "치즈", S1_FOOD, (3, 1.8), False, ("lump", rgb(250, 210, 90))),
    ("yogurt", "요구르트", S1_FOOD, (4, 4.8), True, ("bowl", rgb(246, 244, 236))),
    ("kimchi", "김치", S1_FOOD, (4, 6), False, ("bowl", rgb(214, 70, 44))),
    ("smoked_beef", "훈제 소고기", S1_FOOD, (3, 1.8), False, ("meat", rgb(140, 62, 40))),
    ("bacon", "베이컨", S1_FOOD, (3, 1.8), False, ("meat", rgb(196, 80, 66))),
    ("smoked_salmon", "훈제 연어", S1_FOOD, (3, 1.8), False, ("meat", rgb(236, 120, 70))),
    ("chicken_soup", "치킨 수프", S1_FOOD, (2, 1.2), False, None),
    ("vegetable_soup", "야채 수프", S1_FOOD, (3, 1.8), False, None),
    ("beef_stew", "소고기 스튜", S1_FOOD, (2, 1.2), False, ("bowl", rgb(132, 70, 36))),
    ("corn_soup", "옥수수 수프", S1_FOOD, (2, 1.2), False, ("bowl", rgb(248, 214, 110))),
    # ── 2단계 요리 (조리대) ──
    ("salmon_sushi", "연어 초밥", S2, (6, 7.2), False, None),
    ("cabbage_wrap", "양배추 쌈", S2, (6, 7.2), False, None),
    ("kimbap", "김밥", S2, (6, 7.2), False, None),
    ("mushroom_fried_rice", "버섯볶음밥", S2, (6, 7.2), False, None),
    ("bacon_and_eggs", "베이컨 에그", S2, (5, 6), False, ("plate", rgb(250, 230, 120))),
    ("kimchi_fried_rice", "김치볶음밥", S2, (10, 12), False, ("bowl", rgb(222, 100, 50))),
    ("meatball_pasta", "미트볼 파스타", S2, (8, 9.6), False, None),
    ("ratatouille", "라타투이", S2, (10, 12), False, None),
    ("fried_rice", "볶음밥", S2, (7, 8.4), False, None),
    ("dumplings", "만두", S2, (8, 9.6), False, None),
    ("apple_pie", "애플파이", S2, (7, 8.4), False, ("plate", rgb(214, 150, 70))),
    ("pizza", "피자", S2, (8, 9.6), False, ("plate", rgb(214, 70, 44))),
    ("hamburger", "햄버거", S2, (10, 12), False, None),
]


# ═════════════ 임시 아이콘 (종류별 모양 + 색) ═════════════
def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c[:3]) + (255,)


def placeholder(kind, color):
    img = blank(16)

    def fill(test, col):
        for y in range(16):
            for x in range(16):
                if test(x, y):
                    img[y][x] = col(x, y)

    body = lambda x, y: shade(color, 1.15 if x < 7 else (0.85 if x > 10 else 1.0))
    if kind == "bottle":
        fill(lambda x, y: 6 <= x <= 9 and 1 <= y <= 3, lambda x, y: rgb(150, 110, 70))          # 코르크
        fill(lambda x, y: 6 <= x <= 9 and 4 <= y <= 5, lambda x, y: rgb(200, 226, 230))         # 병목
        fill(lambda x, y: 4 <= x <= 11 and 6 <= y <= 14, body)
        fill(lambda x, y: x == 5 and 7 <= y <= 12, lambda x, y: shade(color, 1.4))              # 유리 반사
    elif kind == "sack":
        fill(lambda x, y: 6 <= x <= 9 and 2 <= y <= 4, lambda x, y: rgb(200, 176, 132))
        fill(lambda x, y: (x - 7.5) ** 2 / 30 + (y - 10) ** 2 / 22 <= 1, lambda x, y: shade(rgb(214, 190, 146), 1.05 - (y - 5) * 0.02))
        fill(lambda x, y: (x - 7.5) ** 2 / 10 + (y - 8) ** 2 / 4 <= 1, body)                      # 안에 든 가루
    elif kind == "bowl":
        fill(lambda x, y: (x - 7.5) ** 2 / 40 + (y - 9) ** 2 / 14 <= 1 and y <= 9, body)
        fill(lambda x, y: (x - 7.5) ** 2 / 46 + (y - 9) ** 2 / 25 <= 1 and y > 9, lambda x, y: shade(rgb(140, 92, 50), 1.1 - (y - 9) * 0.05))
    elif kind == "plate":
        fill(lambda x, y: (x - 7.5) ** 2 / 52 + (y - 10) ** 2 / 12 <= 1, lambda x, y: rgb(236, 238, 244) if y < 11 else rgb(196, 202, 212))
        fill(lambda x, y: (x - 7.5) ** 2 / 28 + (y - 8.5) ** 2 / 9 <= 1, body)
    elif kind == "loaf":
        fill(lambda x, y: 2 <= x <= 13 and 6 <= y <= 12 and not ((x in (2, 13)) and y == 6), body)
        fill(lambda x, y: 3 <= x <= 12 and y == 6, lambda x, y: shade(color, 1.25))
    elif kind == "meat":
        fill(lambda x, y: (x - 7.5) ** 2 / 34 + (y - 8.5) ** 2 / 16 <= 1, body)
        fill(lambda x, y: abs((x - y) - 1) <= 0 and (x - 7.5) ** 2 / 34 + (y - 8.5) ** 2 / 16 <= 0.8,
             lambda x, y: rgb(244, 220, 200))                                                      # 지방 줄
    else:                                                                                          # lump
        fill(lambda x, y: (x - 7.5) ** 2 / 30 + (y - 9) ** 2 / 18 <= 1, body)
        fill(lambda x, y: (x, y) in ((6, 7), (9, 10), (8, 8)), lambda x, y: shade(color, 0.8))      # 구멍
    return dark_outline(img)


def mortar_icon():
    """절구 (임시): 회색 돌 그릇 + 나무 공이"""
    img = blank(16)
    for y in range(16):
        for x in range(16):
            if 2 <= y <= 9 and abs(x - (9 + (y - 2) * 0.3)) <= 0.8 and x >= 8:
                img[y][x] = rgb(170, 122, 70) if x % 2 else rgb(140, 98, 54)                       # 공이
            if (x - 7.5) ** 2 / 36 + (y - 10) ** 2 / 16 <= 1 and y >= 8:
                img[y][x] = shade(rgb(150, 150, 154), 1.15 - (y - 8) * 0.06)
            if 8 <= y <= 9 and 3 <= x <= 12:
                img[y][x] = rgb(84, 84, 88)                                                         # 그릇 속
    return dark_outline(img)


def entry(item_id, name, lore, art, food=None, drink=False):
    if art == "full":
        graphics = f"""    graphics:
      model: item/food/{item_id}
      icon: item/food/{item_id}"""
    else:
        graphics = f"""    resource:
      material: PAPER
      generate: true
      textures:
        - item/food/{item_id}"""
    out = f"""  {item_id}:
    display_name: "{name}"
    lore:
""" + "".join(f'      - "{line}"\n' for line in lore) + graphics + "\n"
    if food:
        out += f"""    consumable:
      nutrition: {food[0]}
      saturation: {food[1]}
""" + ("      animation: drink\n" if drink else "")
    return out


pack = sys.argv[1]
assets = os.path.join(pack, "resourcepack/assets/rustport")
tex_dir = os.path.join(assets, "textures/item/food")
os.makedirs(tex_dir, exist_ok=True)
lines = ["info:", "  namespace: rustport", "",
         "# 요리 아이템 (tools/cooking/make_dishes.py 로 생성, 직접 수정하지 말 것). 레시피는 BrassField config.yml",
         "# 단계: 0단계 재료 → 보조 도구·절구 → 1단계 → 조리대 → 2단계", "items:"]
preview = []
for item_id, name, stage, food, drink, temp in ITEMS:
    drawn = item_id in SPRITES
    full = drawn and item_id in MODELS and item_id not in PENDING_3D    # 확정된 3D 만 (가루 같은 재료는 2D 아이콘만)
    img = SPRITES[item_id]() if drawn else placeholder(*temp)
    png.write(os.path.join(tex_dir, item_id + ".png"), img)
    preview.append(img)
    if full:
        MODELS[item_id]().save(assets)
    lore = ["&7" + stage] + ([] if drawn else ["&8(임시 그림)"])
    lines.append(entry(item_id, name, lore, "full" if full else "temp", food, drink))

# 절구: 제작 칸에서 쓰는 도구 (닳지 않음). 제작법: 위 막대기, 양옆·아래 매끄러운 돌
mortar_img = SPRITES["mortar"]() if "mortar" in SPRITES else mortar_icon()
png.write(os.path.join(tex_dir, "mortar.png"), mortar_img)
lines.append(entry("mortar", "절구", ["&7요리 도구 (닳지 않음)", "&8제작 칸에 절구와 재료를 함께 넣으면", "&8반죽 등을 만듭니다."]
                   + ([] if "mortar" in SPRITES else ["&8(임시 그림)"]), "temp"))
lines.append("""
recipes:
  crafting_table:
    mortar:
      enabled: true
      pattern:
        - " S "
        - "X X"
        - " X "
      ingredients:
        S: STICK
        X: SMOOTH_STONE
      result:
        item: rustport:mortar
        amount: 1
""")
with open(os.path.join(pack, "configs/food.yml"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
if os.environ.get("PREVIEW"):
    cols = 10
    rows = math.ceil((len(preview) + 1) / cols)
    sheet = png.blank(18 * cols, 18 * rows)
    for i, img in enumerate(preview + [mortar_img]):
        png.paste(sheet, img, (i % cols) * 18, (i // cols) * 18)
    png.write(os.environ["PREVIEW"], png.scale(sheet, 6))
print("ok: %d items + mortar" % len(ITEMS))

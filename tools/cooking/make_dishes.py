"""
첫 요리 세트(요리 13 + 중간 재료 4)의 아이템을 만든다: 인벤토리 아이콘·손 3D 모델·ItemsAdder 정의. 노션 경제 설계 > 첫 요리 세트.

- 아이콘: sprites.py (16x16 손 픽셀, 인벤토리·바닥·액자)
- 3D 모델: make_food.py (손에 들었을 때)
- 회복량(배고픔·포만감): 초간단 4·3 / 간단 6·6 / 중급 8·10 / 복잡 10·14. 중간 재료는 먹을 수 없다.

사용: python3 -I tools/cooking/make_dishes.py <ItemsAdder contents/rustport>
  → resourcepack/assets/rustport/textures/item/food/<ID>.png (아이콘)
    resourcepack/assets/rustport/models/item/food/<ID>.json, textures/item/food/3d/ (3D 모델)
    configs/food.yml
  PREVIEW=<png> 를 주면 아이콘을 6배로 늘어놓은 미리보기를 그린다.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from food_kit import png  # noqa: E402
from sprites import SPRITES  # noqa: E402
from make_food import MODELS  # noqa: E402

FOOD = {"초간단": (4, 3), "간단": (6, 6), "중급": (8, 10), "복잡": (10, 14)}
DISHES = [
    ("cooked_rice", "익힌 밥", "초간단"),
    ("salmon_sushi", "연어 초밥", "초간단"),
    ("cabbage_wrap", "양배추 쌈", "초간단"),
    ("honey_cookie", "꿀 쿠키", "초간단"),
    ("kimbap", "김밥", "간단"),
    ("mushroom_fried_rice", "버섯볶음밥", "간단"),
    ("meatball_pasta", "미트볼 파스타", "중급"),
    ("ratatouille", "라타투이", "중급"),
    ("chicken_soup", "치킨 수프", "중급"),
    ("fried_rice", "볶음밥", "중급"),
    ("dumplings", "만두", "중급"),
    ("vegetable_soup", "야채 수프", "복잡"),
    ("hamburger", "햄버거", "복잡"),
]
INGREDIENTS = [
    ("dough", "반죽"),
    ("noodles", "면"),
    ("tomato_sauce", "토마토소스"),
    ("patty", "패티"),
]


def entry(item_id, name, lore, extra=""):
    return f"""  {item_id}:
    display_name: "{name}"
    lore:
      - "&7{lore}"
    graphics:
      model: item/food/{item_id}
      icon: item/food/{item_id}
{extra}"""


pack = sys.argv[1]
assets = os.path.join(pack, "resourcepack/assets/rustport")
tex_dir = os.path.join(assets, "textures/item/food")
os.makedirs(tex_dir, exist_ok=True)
lines = ["info:", "  namespace: rustport", "",
         "# 첫 요리 세트 (tools/cooking/make_dishes.py 로 생성, 직접 수정하지 말 것)",
         "# 회복량(배고픔·포만감): 초간단 4·3 / 간단 6·6 / 중급 8·10 / 복잡 10·14. 중간 재료는 먹을 수 없다.", "items:"]
preview = []
for item_id, name, tier in DISHES:
    nutrition, saturation = FOOD[tier]
    lines.append(entry(item_id, name, tier + " 요리", f"""    consumable:
      nutrition: {nutrition}
      saturation: {saturation}
"""))
for item_id, name in INGREDIENTS:
    lines.append(entry(item_id, name, "요리 재료"))
for item_id, *_ in DISHES + INGREDIENTS:
    img = SPRITES[item_id]()
    png.write(os.path.join(tex_dir, item_id + ".png"), img)
    preview.append(img)
    MODELS[item_id]().save(assets)
with open(os.path.join(pack, "configs/food.yml"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
if os.environ.get("PREVIEW"):
    sheet = png.blank(18 * 9, 18 * 2)
    for i, img in enumerate(preview):
        png.paste(sheet, img, (i % 9) * 18, (i // 9) * 18)
    png.write(os.environ["PREVIEW"], png.scale(sheet, 6))
print("ok: %d dishes, %d ingredients" % (len(DISHES), len(INGREDIENTS)))

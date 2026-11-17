"""
요리 등급(은별·금별) 아이템을 만든다. 요리 기기는 재료 등급 평균(일반 0 · 은별 1 · 금별 2, 소수점 버림)으로
요리 등급을 정하고, 은별·금별 요리는 <ID>_silver_star · <ID>_golden_star 로 나온다 (작물과 같은 이름 규칙).
  - 아이콘: 기본 아이콘(textures/item/food/<ID>.png) 오른쪽 아래에 별 (작물 별과 같은 자리·크기, 색만 은·금)
  - 정의: food.yml 의 기본 요리 정의를 그대로 복사하고 이름 뒤에 " (은별)"·" (금별)", 아이콘 경로만 바꾼다
         (손에 든 3D 모델·회복량·마시는 동작은 기본 요리와 같다)
  - 대상: BrassField config.yml 의 cooking.stations 요리 결과 전부

사용: python3 tools/cooking/make_food_grades.py <ItemsAdder contents/rustport> <BrassField config.yml>
  → resourcepack/assets/rustport/textures/item/food/<ID>_<등급>_star.png, configs/food_grades.yml
"""
import os
import re
import sys

from PIL import Image

GRADES = [("silver_star", "은별"), ("golden_star", "금별")]
# 8x8 별 (아이콘 오른쪽 아래 8~15). O 테 · M 가운데 · H 밝은 면 · S 그늘
STAR = ["....OO..",
        "...OHO..",
        "OOOMHOOO",
        "OHHHHHHO",
        ".OMHHMO.",
        ".OHMMHO.",
        "OHMSSMHO",
        "OOS..SOO"]
COLORS = {"silver_star": {"O": (96, 100, 100), "M": (162, 164, 166), "H": (218, 223, 229), "S": (124, 128, 129)},
          "golden_star": {"O": (168, 92, 0), "M": (234, 194, 12), "H": (255, 250, 26), "S": (186, 118, 4)}}


def star_icon(base, grade):
    img = base.copy()
    for y, line in enumerate(STAR):
        for x, c in enumerate(line):
            if c != ".":
                img.putpixel((8 + x, 8 + y), COLORS[grade][c] + (255,))
    return img


def recipe_results(config_path):
    results, in_stations, in_recipes = [], False, False
    for line in open(config_path, encoding="utf-8"):
        if re.match(r"^  stations:", line):
            in_stations = True
            continue
        if in_stations and re.match(r"^  \S", line):
            break
        if not in_stations:
            continue
        if re.match(r"^      recipes:", line):
            in_recipes = True
        elif re.match(r"^      \S", line) or re.match(r"^    \S", line):
            in_recipes = False
        elif in_recipes:
            m = re.match(r"^        ([a-z0-9_]+):\s*$", line)
            if m:
                results.append(m.group(1))
    return results


def food_blocks(food_yml):
    """food.yml 의 items 아래 아이템 정의: ID → 줄 목록 (들여쓰기 4칸 이상 본문)"""
    blocks, current, in_items = {}, None, False
    for line in open(food_yml, encoding="utf-8").read().split("\n"):
        if re.match(r"^items:", line):
            in_items = True
            continue
        if in_items and re.match(r"^\S", line):
            break
        m = re.match(r"^  ([a-z0-9_]+):\s*$", line)
        if in_items and m:
            current = m.group(1)
            blocks[current] = []
        elif current and (line.startswith("    ") or not line.strip()):
            blocks[current].append(line)
    return blocks


def graded_block(item_id, lines, grade, label):
    out = []
    for line in lines:
        m = re.match(r'^(\s+display_name:\s*)"(.*)"\s*$', line)
        if m:
            line = '%s"%s (%s)"' % (m.group(1), m.group(2), label)
        line = re.sub(r"^(\s+icon:\s*item/food/)%s\s*$" % item_id, r"\g<1>%s_%s" % (item_id, grade), line)
        line = re.sub(r"^(\s+-\s*item/food/)%s\s*$" % item_id, r"\g<1>%s_%s" % (item_id, grade), line)
        out.append(line)
    while out and not out[-1].strip():
        out.pop()
    return ["  %s_%s:" % (item_id, grade)] + out


def main(content, config_path):
    tex = os.path.join(content, "resourcepack", "assets", "rustport", "textures", "item", "food")
    blocks = food_blocks(os.path.join(content, "configs", "food.yml"))
    lines = ["info:", "  namespace: rustport", "",
             "# 자동 생성 파일 (BrassField tools/cooking/make_food_grades.py) — 은별·금별 요리. 직접 수정하지 말 것.",
             "items:"]
    made = 0
    for item_id in recipe_results(config_path):
        icon_path = os.path.join(tex, item_id + ".png")
        if item_id not in blocks or not os.path.exists(icon_path):
            print("건너뜀 (정의나 아이콘 없음):", item_id)
            continue
        base = Image.open(icon_path).convert("RGBA")
        for grade, label in GRADES:
            star_icon(base, grade).save(os.path.join(tex, "%s_%s.png" % (item_id, grade)))
            lines += graded_block(item_id, blocks[item_id], grade, label) + [""]
        made += 1
    with open(os.path.join(content, "configs", "food_grades.yml"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")
    print("요리", made, "종 x 2 등급")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

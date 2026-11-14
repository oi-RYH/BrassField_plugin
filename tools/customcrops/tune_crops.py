"""
BrassField 농사 규칙을 CustomCrops 작물 설정에 적용한다. (노션 DR-08)

- 물이 없으면 자라지 않는다: 모든 작물의 성장 조건을 "물이 1 이상일 때 1단계씩"으로 맞춘다.
- 물이 없어도 시들지 않는다: 사망 조건 no_water 삭제
- 까마귀 없음: 사망 조건 crow_attack 삭제

사용: python3 -I tools/customcrops/tune_crops.py <crops/*.yml ...>
"""
import re
import sys
import pathlib

GROW_BLOCK = [
    "  grow-conditions:",
    "    default:",
    "      point: 1",
    "      conditions:",
    "        water_condition:",
    "          type: water-more-than",
    "          value: 0",
]
REMOVED_DEATH = ("no_water", "crow_attack")


def indent(line):
    return len(line) - len(line.lstrip(" "))


def meaningful(line):
    s = line.strip()
    return bool(s) and not s.startswith("#")


def block_end(lines, i):
    base = indent(lines[i])
    j = i + 1
    while j < len(lines) and (not meaningful(lines[j]) or indent(lines[j]) > base):
        j += 1
    while j > i + 1 and not meaningful(lines[j - 1]):
        j -= 1
    return j


def find_key(lines, key, level):
    for i, line in enumerate(lines):
        if indent(line) == level and re.match(r"\s*" + re.escape(key) + r":(\s|$)", line):
            return i
    return -1


def tune(text, report):
    lines = text.split("\n")

    # 성장 조건: 물 조건이 없으면 표준 성장 조건으로 바꾼다
    g = find_key(lines, "grow-conditions", 2)
    if g >= 0:
        body = "\n".join(lines[g:block_end(lines, g)])
        if "water-more-than" not in body:
            lines[g:block_end(lines, g)] = GROW_BLOCK
            report.append("grow-conditions -> water-more-than 0")

    # 사망 조건: 물 부족 시듦, 까마귀 삭제
    d = find_key(lines, "death-conditions", 2)
    if d >= 0 and not lines[d].strip().endswith("{}"):
        for name in REMOVED_DEATH:
            end = block_end(lines, d)
            for i in range(d + 1, end):
                if indent(lines[i]) == 4 and lines[i].strip() == name + ":":
                    del lines[i:block_end(lines, i)]
                    report.append("death-conditions: removed " + name)
                    break
        if not any(meaningful(line) for line in lines[d + 1:block_end(lines, d)]):
            lines[d] = "  death-conditions: {}"
            report.append("death-conditions -> {}")
    return "\n".join(lines)


for path in sys.argv[1:]:
    p = pathlib.Path(path)
    report = []
    new = tune(p.read_text(encoding="utf-8"), report)
    if report:
        p.write_text(new, encoding="utf-8")
        print("== " + p.name)
        for r in report:
            print("  " + r)

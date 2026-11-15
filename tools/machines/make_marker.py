"""
기계 표시 마커 모델: 기계 위에 떠서 위아래로 움직이며 도는 빨간 역삼각형 (2D).
마인크래프트 일반 아이템처럼 그림 한 장에 얇은 두께만 준 모델(item/generated)이라, 돌면 정면에선 삼각형, 옆에선 얇은 판으로 보인다.
표시 엔티티가 밝기 15로 띄우므로 밤에도 잘 보인다.

사용: python3 -I tools/machines/make_marker.py <ItemsAdder rustport resourcepack/assets/rustport>
  → textures/machine/machine_marker.png (32x32), models/machine/machine_marker.json
  PREVIEW=<png> 를 주면 8배 확대 미리보기를 그린다.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "hud"))
import png  # noqa: E402

SIZE = 32
T = (0, 0, 0, 0)
EDGE = (120, 14, 12, 255)        # 가장자리 (짙은 빨강)
DARK = (190, 28, 22, 255)        # 아래쪽 그늘
MID = (232, 52, 40, 255)         # 몸통
LIGHT = (255, 112, 92, 255)      # 위쪽 밝은 면
SHINE = (255, 214, 200, 255)     # 안쪽 반사선

# 역삼각형: 위 변 y=TOP (폭 전체), 아래 꼭짓점 y=BOTTOM
TOP, BOTTOM, LEFT, RIGHT = 5, 28, 3, 28
CX = (LEFT + RIGHT) / 2


def half_width(y):
    """y 줄에서 삼각형의 반폭 (위로 갈수록 넓다)"""
    return (RIGHT - LEFT) / 2 * (BOTTOM - y) / (BOTTOM - TOP)


def inside(x, y, shrink=0.0):
    if y < TOP + shrink or y > BOTTOM - shrink * 1.6:
        return False
    return abs(x + 0.5 - CX - 0.5) <= half_width(y) - shrink


img = png.blank(SIZE, SIZE)
for y in range(SIZE):
    for x in range(SIZE):
        if not inside(x, y):
            continue
        if not inside(x, y, 1.4):
            img[y][x] = EDGE
            continue
        depth = (y - TOP) / (BOTTOM - TOP)                  # 0 위 → 1 아래
        color = LIGHT if depth < 0.18 else (MID if depth < 0.62 else DARK)
        # 왼쪽 위 변을 따라 흐르는 반사선
        if inside(x, y, 2.4) and not inside(x, y, 3.4) and x < CX and y < TOP + 12:
            color = SHINE
        img[y][x] = color

assets = sys.argv[1]
os.makedirs(os.path.join(assets, "textures/machine"), exist_ok=True)
os.makedirs(os.path.join(assets, "models/machine"), exist_ok=True)
png.write(os.path.join(assets, "textures/machine/machine_marker.png"), img)
model = {
    "parent": "minecraft:item/generated",
    "textures": {"layer0": "rustport:machine/machine_marker"},
    "display": {
        # 표시 엔티티(FIXED)에서의 크기: 약 0.6블록
        "fixed": {"rotation": [0, 0, 0], "scale": [0.6, 0.6, 0.6]},
    },
}
with open(os.path.join(assets, "models/machine/machine_marker.json"), "w", encoding="utf-8") as f:
    json.dump(model, f, indent=1)
if os.environ.get("PREVIEW"):
    png.write(os.environ["PREVIEW"], png.scale(img, 8))
print("ok, machine_marker (2D)")

"""
강화 모루 (rustport:machine/enhance_anvil) — 무기 · 방어구 · 장신구를 강화하는 2x1 가구 (가로 2칸, 모델 u -8~24). 주변 장식은 마인크래프트 블록으로 꾸민다.
재질은 요리 기계와 같은 노이즈 없는 금속 명암: 몸체는 산업용 철 회색, 띠 · 테 · 리벳은 황동 (make_cooking_tools.metal_box).

- 받침: 넓은 발판 + 한 단 좁은 계단 + 황동 띠
- 허리: 좁은 기둥, 앞면에 주황빛 창(강화창 유리관 빛), 위 황동 깃
- 머리: 큰 몸통 + 왼쪽으로 가늘어지는 뿔 + 오른쪽 뒤꿈치, 윗면 테두리 황동 띠, 앞면 황동 리벳

좌표는 정면(north)에서 본 기준 u: 왼쪽 0 → 오른쪽 16, w: 앞 0 → 뒤 16.
사용: python3 tools/machines/make_enhance_anvil.py <ItemsAdder resourcepack/assets> [enhance_anvil enhance_hammer]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_cooking_tools as ct  # noqa: E402
from furniture_kit import Model, rgb  # noqa: E402

NAME = "enhance_anvil"

# 모루 몸체: 산업용 철 회색 명암 (밝음 → 어둠), make_cooking_tools 의 금속 판 · 원통 그림 방식 그대로
IRON_PAL = [rgb(150, 146, 146), rgb(117, 113, 113), rgb(89, 88, 88), rgb(66, 65, 67), rgb(46, 45, 48)]
for kind, img in (("plate", ct.metal_plate(IRON_PAL)), ("rod_v", ct.metal_rod(IRON_PAL, True)),
                  ("rod_h", ct.metal_rod(IRON_PAL, False))):
    ct.ART["mt_iron_" + kind] = img


def iron(m, u0, y0, w0, u1, y1, w1):
    """회색 철 판 (얇고 긴 큐브는 원통 명암)"""
    dx, dy, dz = u1 - u0, y1 - y0, w1 - w0
    dims = sorted((dx, dy, dz))
    rod = dims[1] <= 2 and dims[2] >= 3 * dims[1]
    faces = {}
    for view, (fw, fh) in (("front", (dx, dy)), ("back", (dx, dy)), ("left", (dz, dy)), ("right", (dz, dy)),
                           ("top", (dx, dz)), ("bottom", (dx, dz))):
        kind = "rod_v" if rod and fh >= 2 * fw else "rod_h" if rod and fw >= 2 * fh else "plate"
        faces[view] = ("mt_iron_" + kind, [0, 0, 16, 16])
    m.box([u0, y0, w0], [u1, y1, w1], "mt_iron_plate", faces=faces)


# 2x1 크기: 1칸 설계를 가운데(u 8 · w 8) 기준으로 가로 SX · 높이 SY · 깊이 SZ 배 늘린다 (창 · 리벳은 크기 그대로, 위치만 옮김)
SX, SY, SZ = 1.75, 1.15, 1.15


def _u(u):
    return round(8 + (u - 8) * SX, 3)


def _w(w):
    return round(8 + (w - 8) * SZ, 3)


def _y(y):
    return round(y * SY, 3)


def anvil():
    m = Model(NAME)

    def I(u0, y0, w0, u1, y1, w1):
        iron(m, _u(u0), _y(y0), _w(w0), _u(u1), _y(y1), _w(w1))

    def B(u0, y0, w0, u1, y1, w1):
        ct.metal_box(m, _u(u0), _y(y0), _w(w0), _u(u1), _y(y1), _w(w1), "brass")

    def small(cu, cy, w_front, size_u, size_y, depth, tex, **kw):
        """크기는 그대로 두고 가운데만 늘린 좌표로 옮긴다"""
        u, y = _u(cu), _y(cy)
        frm, to = [u - size_u / 2, y - size_y / 2, _w(w_front) - depth], [u + size_u / 2, y + size_y / 2, _w(w_front)]
        if tex == "brass":
            ct.metal_box(m, *frm, *to, "brass")
        else:
            m.box(frm, to, tex, **kw)

    # 받침: 넓은 철 발판 · 황동 띠 · 한 단 좁은 계단
    I(1, 0, 3, 15, 2, 13)
    B(2, 2, 4, 14, 3, 12)
    I(3, 3, 4.5, 13, 5, 11.5)
    # 허리 + 앞 주황빛 창 + 황동 깃
    I(5, 5, 5.5, 11, 9, 10.5)
    small(8, 7, 5.5, 4, 4, 0.3, "porthole", light=10, faces={"front": ("porthole", [0, 0, 16, 16])})
    B(4, 9, 5, 12, 10, 11)
    # 머리: 몸통 · 왼쪽으로 가늘어지는 뿔 · 오른쪽 뒤꿈치
    I(2, 10, 4, 14, 14, 12)
    I(0, 10.75, 5, 2, 14, 11)
    I(-2, 11.5, 6, 0, 14, 10)
    I(-3.75, 12.25, 6.75, -2, 14, 9.25)
    I(-5, 13, 7.5, -3.75, 14, 8.5)
    I(14, 11, 5, 16.5, 14, 11)
    # 윗면 황동 테 (가운데 철 면이 보이게)
    B(2, 14, 4, 14, 14.5, 4.6)
    B(2, 14, 11.4, 14, 14.5, 12)
    B(2, 14, 4.6, 2.4, 14.5, 11.4)
    B(13.6, 14, 4.6, 14, 14.5, 11.4)
    # 앞면 리벳
    for u in (3, 13):
        for y in (11.2, 13.1):
            small(u, y, 4, 1, 1, 0.4, "brass")
    # "fixed" 는 넣지 않는다 — 가구(item_display)가 이 표시로 그려져, 넣으면 그만큼 작아진다
    m.display = {
        "gui": {"rotation": [30, 225, 0], "translation": [0, 0, 0], "scale": [0.4, 0.4, 0.4]},
        "ground": {"translation": [0, 2, 0], "scale": [0.2, 0.2, 0.2]},
        "firstperson_righthand": {"rotation": [0, 45, 0], "scale": [0.25, 0.25, 0.25]},
        "thirdperson_righthand": {"rotation": [75, 45, 0], "translation": [0, 2.5, 0], "scale": [0.2, 0.2, 0.2]},
    }
    return m


def hammer():
    """강화 연출용 망치 (rustport:machine/enhance_hammer). 자루 끝이 모델 가운데(8, 8, 8) = 표시 엔티티 위치 →
    플러그인이 그 점을 축으로 휘두른다. 자루는 위(+y), 머리는 앞뒤(w) 방향으로 길다 (휘두르는 방향 = w)."""
    m = Model("enhance_hammer")
    b = ct.metal_box
    b(m, 7.25, 8, 7.25, 8.75, 21, 8.75, "body")                  # 자루
    b(m, 7, 8, 7, 9, 11, 9, "brass")                             # 손잡이 감개
    b(m, 7, 18, 7, 9, 19, 9, "brass")                            # 머리 아래 깃
    iron(m, 6.5, 19, 3.5, 9.5, 23, 12.5)                         # 머리
    iron(m, 6, 18.5, 3, 10, 23.5, 4)                             # 앞 타격면
    iron(m, 6, 18.5, 12, 10, 23.5, 13)                           # 뒤 타격면
    b(m, 6.25, 18.75, 6, 9.75, 23.25, 6.5, "brass")              # 머리 황동 띠
    b(m, 6.25, 18.75, 9.5, 9.75, 23.25, 10, "brass")
    m.display = {
        "gui": {"rotation": [30, 225, 0], "translation": [0, -4, 0], "scale": [0.6, 0.6, 0.6]},
        "ground": {"translation": [0, 0, 0], "scale": [0.4, 0.4, 0.4]},
    }
    return m


MODELS = {"enhance_anvil": anvil, "enhance_hammer": hammer}

if __name__ == "__main__":
    for name in sys.argv[2:] or MODELS:
        model = MODELS[name]()
        model.save(sys.argv[1], "machine", ct.ART, model.display)

"""
요리 그림 공용 도구: 아이콘 색 외곽선, 3D 손 모델(큐브) 만들기·저장·등각 미리보기. (sprites.py·make_food.py 공용)

- 외곽선은 검정 대신 이웃 색을 짙고 진하게 만든 색.
- 3D 모델은 재질마다 16x16 텍스처 한 장(textures/item/food/3d/<모델>_<재질>.png)을 쓰고, 큐브 면 크기만큼 잘라 붙인다.
"""
import colorsys
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "hud"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import png  # noqa: E402
from pixelart import rgb, blank  # noqa: E402,F401


def dark_outline(img):
    """투명 칸 중 불투명 칸과 맞닿은 곳을 이웃 색의 짙고 진한 색으로 칠한다"""
    h, w = len(img), len(img[0])
    out = [row[:] for row in img]
    for y in range(h):
        for x in range(w):
            if img[y][x][3] > 128:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and img[ny][nx][3] > 128:
                    r, g, b = (c / 255 for c in img[ny][nx][:3])
                    hh, ss, vv = colorsys.rgb_to_hsv(r, g, b)
                    hh = (hh - 0.03) % 1.0
                    r, g, b = colorsys.hsv_to_rgb(hh, min(1.0, ss * 1.25 + 0.15), vv * 0.32)
                    out[y][x] = rgb(int(r * 255), int(g * 255), int(b * 255))
                    break
    return out


# ═════════════ 3D 모델 ═════════════
FACES = ("north", "south", "east", "west", "up", "down")


class Model:
    def __init__(self, name):
        self.name = name
        self.elements = []
        self.textures = {}     # 재질 이름 → 16x16 그림

    def tex(self, key, img):
        self.textures[key] = img
        return key

    def box(self, frm, to, mat, faces=None, skip=(), uv=None):
        """mat: 재질 이름 또는 {면: 재질}. uv: {면: [u0,v0,u1,v1]} 직접 지정"""
        out = {}
        for face in FACES:
            if face in skip:
                continue
            m = mat[face] if isinstance(mat, dict) else mat
            if uv and face in uv:
                u = uv[face]
            else:
                w, h = _face_size(face, frm, to)
                # 같은 재질이라도 큐브·면마다 조금씩 다른 부분을 쓴다 (실행마다 같은 결과)
                ox = ((len(self.elements) * 5 + FACES.index(face) * 3) % 7) * 0.5
                ox = min(ox, max(0.0, 16 - w))
                u = [ox, 0, ox + min(16, w), min(16, h)]
            out[face] = {"uv": [round(c, 3) for c in u], "texture": "#" + m}
        self.elements.append({"from": [round(v, 3) for v in frm], "to": [round(v, 3) for v in to], "faces": out})

    def save(self, assets, display=None):
        tex_dir = os.path.join(assets, "textures/item/food/3d")
        model_dir = os.path.join(assets, "models/item/food")
        os.makedirs(tex_dir, exist_ok=True)
        os.makedirs(model_dir, exist_ok=True)
        textures = {}
        for key, img in self.textures.items():
            png.write(os.path.join(tex_dir, "%s_%s.png" % (self.name, key)), img)
            textures[key] = "rustport:item/food/3d/%s_%s" % (self.name, key)
        textures["particle"] = textures[next(iter(self.textures))]
        model = {"textures": textures, "elements": self.elements, "display": display or HAND_DISPLAY}
        with open(os.path.join(model_dir, self.name + ".json"), "w", encoding="utf-8") as f:
            json.dump(model, f, indent=1)
        bad = [e for e in self.elements if not all(-16 <= v <= 32 for v in e["from"] + e["to"])]
        assert not bad, "좌표 범위 밖 큐브: %s" % bad[:1]

    # ── 등각 미리보기 (남·동·위 면, 깊이 버퍼) ──
    def preview(self, scale=8):
        size = 34 * scale
        img = [[rgb(70, 92, 110)] * size for _ in range(size)]
        depth = [[-1e9] * size for _ in range(size)]
        c30, s30 = math.cos(math.radians(30)), math.sin(math.radians(30))

        def screen(x, y, z):
            return (size / 2 + (x - z) * c30 * scale, size * 0.62 + ((x + z - 16) * s30 - y) * scale)

        for e in self.elements:
            (x0, y0, z0), (x1, y1, z1) = e["from"], e["to"]
            for face, light in (("up", 1.0), ("south", 0.86), ("east", 0.72)):
                if face not in e["faces"]:
                    continue
                f = e["faces"][face]
                timg = self.textures[f["texture"][1:]]
                u0, v0, u1, v1 = f["uv"]
                n = int(max(x1 - x0, y1 - y0, z1 - z0) * scale * 1.6) + 2
                for i in range(n):
                    for j in range(n):
                        a, b = (i + 0.5) / n, (j + 0.5) / n
                        if face == "up":
                            p = (x0 + (x1 - x0) * a, y1, z0 + (z1 - z0) * b)
                        elif face == "south":
                            p = (x0 + (x1 - x0) * a, y1 - (y1 - y0) * b, z1)
                        else:
                            p = (x1, y1 - (y1 - y0) * b, z1 - (z1 - z0) * a)
                        tx = int(u0 + (u1 - u0) * a) % 16
                        ty = int(v0 + (v1 - v0) * b) % 16
                        c = timg[min(15, ty)][min(15, tx)]
                        if not c[3]:
                            continue
                        sx, sy = screen(*p)
                        sx, sy = int(sx), int(sy)
                        d = p[0] + p[1] * 1.2 + p[2]
                        if 0 <= sx < size and 0 <= sy < size and d >= depth[sy][sx]:
                            depth[sy][sx] = d
                            img[sy][sx] = tuple(int(c[k] * light) for k in range(3)) + (255,)
        return img


def _face_size(face, frm, to):
    dx, dy, dz = (to[i] - frm[i] for i in range(3))
    return {"north": (dx, dy), "south": (dx, dy), "east": (dz, dy), "west": (dz, dy),
            "up": (dx, dz), "down": (dx, dz)}[face]


# 손에 들었을 때. (인벤토리·바닥·액자는 graphics.icon 의 2D 아이콘이 대신 보인다)
HAND_DISPLAY = {
    "thirdperson_righthand": {"rotation": [70, 30, 0], "translation": [0, 3, 1.5], "scale": [0.5, 0.5, 0.5]},
    "thirdperson_lefthand": {"rotation": [70, 30, 0], "translation": [0, 3, 1.5], "scale": [0.5, 0.5, 0.5]},
    "firstperson_righthand": {"rotation": [0, -25, 0], "translation": [1, 4, 0], "scale": [0.55, 0.55, 0.55]},
    "firstperson_lefthand": {"rotation": [0, -25, 0], "translation": [1, 4, 0], "scale": [0.55, 0.55, 0.55]},
    "ground": {"translation": [0, 2, 0], "scale": [0.5, 0.5, 0.5]},
    "fixed": {"rotation": [-90, 0, 0], "translation": [0, 0, -4], "scale": [0.9, 0.9, 0.9]},
    "head": {"translation": [0, 14, 0]},
    "gui": {"rotation": [30, 225, 0], "scale": [0.62, 0.62, 0.62]},
}


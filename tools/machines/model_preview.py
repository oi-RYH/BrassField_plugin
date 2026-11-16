"""
모델 미리보기: 마인크래프트 블록·아이템 모델(JSON)을 읽어 정면·오른쪽 옆면·후면·왼쪽 옆면과 비스듬한 3D 두 방향을 한 장으로 그린다.
게임에 넣기 전에 모양을 확인하는 용도. 회전한 큐브(불·사슬·랜턴 고리 등), 투명 픽셀, 면별 밝기(바닐라처럼 위 > 앞뒤 > 옆 > 아래)를 그린다.
바닥에는 블록 격자(16단위)를 깔아 크기를 보여 준다.

텍스처 찾기
- "minecraft:..." → 마인크래프트 클라이언트 jar 안의 assets/minecraft/textures/... (애니메이션 텍스처는 첫 장면)
- "<namespace>:..." → <assets 폴더>/<namespace>/textures/...

사용: python3 -I tools/machines/model_preview.py <모델.json> <리소스팩 assets 폴더> <출력.png> [클라이언트 jar]
  클라이언트 jar 기본값: ~/Library/Application Support/minecraft/versions/26.1.2/26.1.2.jar
"""
import json
import math
import os
import sys
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "hud"))
import png  # noqa: E402

DEFAULT_JAR = os.path.expanduser("~/Library/Application Support/minecraft/versions/26.1.2/26.1.2.jar")
BG = (46, 52, 62, 255)
FLOOR = [(86, 96, 108, 255), (74, 84, 96, 255)]
SHADE = {"up": 1.0, "north": 0.8, "south": 0.8, "east": 0.62, "west": 0.62, "down": 0.5}


class Textures:
    def __init__(self, model, assets, jar_path):
        self.model = model
        self.assets = assets
        self.jar = zipfile.ZipFile(jar_path) if os.path.exists(jar_path) else None
        self.cache = {}

    def resolve(self, ref, depth=0):
        """'#name' → 모델 textures 의 실제 경로(다른 #참조면 따라감)"""
        if ref.startswith("#") and depth < 8:
            return self.resolve(self.model.get("textures", {}).get(ref[1:], "minecraft:missingno"), depth + 1)
        return ref

    def get(self, ref):
        path = self.resolve(ref)
        if path in self.cache:
            return self.cache[path]
        ns, _, rel = path.partition(":") if ":" in path else ("minecraft", ":", path)
        img = None
        try:
            if ns == "minecraft":
                if self.jar:
                    img = png.read(self.jar.read("assets/minecraft/textures/%s.png" % rel))
            else:
                img = png.read(os.path.join(self.assets, ns, "textures", rel + ".png"))
        except (KeyError, OSError, AssertionError):
            img = None
        if img is None:                                    # 없는 텍스처: 보라·검정 체크
            img = [[(200, 0, 200, 255) if (x // 8 + y // 8) % 2 else (0, 0, 0, 255) for x in range(16)] for y in range(16)]
        w = len(img[0])
        img = img[:w]                                      # 애니메이션 띠는 첫 장면(정사각)만
        self.cache[path] = img
        return img


def rotate(p, rot):
    """요소 회전 (축, 각도, 중심)"""
    if not rot:
        return p
    ang = math.radians(rot["angle"])
    ox, oy, oz = rot["origin"]
    x, y, z = p[0] - ox, p[1] - oy, p[2] - oz
    c, s = math.cos(ang), math.sin(ang)
    if rot["axis"] == "x":
        y, z = y * c - z * s, y * s + z * c
    elif rot["axis"] == "y":
        x, z = x * c + z * s, -x * s + z * c
    else:
        x, y = x * c - y * s, x * s + y * c
    return (x + ox, y + oy, z + oz)


def face_frame(face, f, t):
    """면의 (왼쪽 위 모서리, u 방향 끝, v 방향 끝) — 바닐라 UV 방향 그대로"""
    (x0, y0, z0), (x1, y1, z1) = f, t
    return {
        "north": ((x1, y1, z0), (x0, y1, z0), (x1, y0, z0)),
        "south": ((x0, y1, z1), (x1, y1, z1), (x0, y0, z1)),
        "east": ((x1, y1, z1), (x1, y1, z0), (x1, y0, z1)),
        "west": ((x0, y1, z0), (x0, y1, z1), (x0, y0, z0)),
        "up": ((x0, y1, z0), (x1, y1, z0), (x0, y1, z1)),
        "down": ((x0, y0, z1), (x1, y0, z1), (x0, y0, z0)),
    }[face]


def camera(forward):
    fx, fy, fz = forward
    n = math.sqrt(fx * fx + fy * fy + fz * fz)
    f = (fx / n, fy / n, fz / n)
    r = (f[1] * 0 - f[2] * 1, f[2] * 0 - f[0] * 0, f[0] * 1 - f[1] * 0)     # f x (0,1,0)
    rn = math.sqrt(sum(c * c for c in r)) or 1
    r = tuple(c / rn for c in r)
    u = (r[1] * f[2] - r[2] * f[1], r[2] * f[0] - r[0] * f[2], r[0] * f[1] - r[1] * f[0])
    return f, r, u


def render(model, textures, forward, scale, size):
    f, r, u = camera(forward)
    w, h = size
    img = [[BG] * w for _ in range(h)]
    depth = [[1e9] * w for _ in range(h)]
    elements = model.get("elements", [])
    pts = [rotate(p, e.get("rotation")) for e in elements for p in
           ((e["from"][0], e["from"][1], e["from"][2]), (e["to"][0], e["to"][1], e["to"][2]))]
    xs = [p[0] for p in pts] + [0, 16]
    zs = [p[2] for p in pts] + [0, 16]
    # 바닥 격자 범위 (블록 칸 단위)
    gx0, gx1 = math.floor(min(xs) / 16) * 16, math.ceil(max(xs) / 16) * 16
    gz0, gz1 = math.floor(min(zs) / 16) * 16, math.ceil(max(zs) / 16) * 16
    corners = [(x, y, z) for x in (gx0, gx1) for y in (min(p[1] for p in pts + [(0, 0, 0)]), max(p[1] for p in pts))
               for z in (gz0, gz1)]
    sxs = [sum(c[i] * r[i] for i in range(3)) for c in corners]
    sys_ = [-sum(c[i] * u[i] for i in range(3)) for c in corners]
    cx = (min(sxs) + max(sxs)) / 2
    cy = (min(sys_) + max(sys_)) / 2

    def project(p):
        sx = (sum(p[i] * r[i] for i in range(3)) - cx) * scale + w / 2
        sy = (-sum(p[i] * u[i] for i in range(3)) - cy) * scale + h / 2
        return sx, sy, sum(p[i] * f[i] for i in range(3))

    def plot(sx, sy, d, color):
        ix, iy = int(sx), int(sy)
        if 0 <= ix < w and 0 <= iy < h and d < depth[iy][ix]:
            depth[iy][ix] = d
            img[iy][ix] = color

    # 바닥 (y = 0, 블록 칸 체크무늬) — 위에서 보일 때만
    if f[1] < -0.05:
        n = int((gx1 - gx0) * scale * 1.2) + 2
        m = int((gz1 - gz0) * scale * 1.2) + 2
        for i in range(n):
            for j in range(m):
                x = gx0 + (gx1 - gx0) * (i + 0.5) / n
                z = gz0 + (gz1 - gz0) * (j + 0.5) / m
                sx, sy, d = project((x, -0.01, z))
                plot(sx, sy, d + 0.5, FLOOR[(math.floor(x / 16) + math.floor(z / 16)) % 2])

    for e in elements:
        rot = e.get("rotation")
        shade_on = e.get("shade", True)
        for face, info in e.get("faces", {}).items():
            tex = textures.get(info["texture"])
            th, tw = len(tex), len(tex[0])
            k = tw / 16.0
            u0, v0, u1, v1 = info.get("uv", [0, 0, 16, 16])
            p0, pu, pv = (rotate(p, rot) for p in face_frame(face, e["from"], e["to"]))
            a0, a1, a2 = project(p0), project(pu), project(pv)
            span = max(math.hypot(a1[0] - a0[0], a1[1] - a0[1]), math.hypot(a2[0] - a0[0], a2[1] - a0[1]))
            steps = int(span * 1.5) + 2
            light = SHADE[face] if shade_on else 1.0
            if e.get("light_emission", 0) >= 8:
                light = max(light, 0.95)
            for i in range(steps):
                a = (i + 0.5) / steps
                for j in range(steps):
                    b = (j + 0.5) / steps
                    tx = int((u0 + (u1 - u0) * a) * k)
                    ty = int((v0 + (v1 - v0) * b) * k)
                    c = tex[min(th - 1, max(0, ty))][min(tw - 1, max(0, tx))]
                    if c[3] < 128:
                        continue
                    sx = a0[0] + (a1[0] - a0[0]) * a + (a2[0] - a0[0]) * b
                    sy = a0[1] + (a1[1] - a0[1]) * a + (a2[1] - a0[1]) * b
                    d = a0[2] + (a1[2] - a0[2]) * a + (a2[2] - a0[2]) * b
                    plot(sx, sy, d, (int(c[0] * light), int(c[1] * light), int(c[2] * light), 255))
    return img


def label(img, text_img, x, y):
    png.paste(img, text_img, x, y)


def sheet(model_path, assets, out, jar=DEFAULT_JAR, scale=8):
    with open(model_path, encoding="utf-8") as fp:
        model = json.load(fp)
    textures = Textures(model, assets, jar)
    # 모델 크기에 맞춰 칸 크기·배율을 정한다 (1블록 아이템은 크게, 여러 블록 가구는 작게)
    pts = [v for e in model.get("elements", []) for v in (e["from"], e["to"])]
    ext = max(16, max(max(p[i] for p in pts) - min(p[i] for p in pts) for i in range(3))) if pts else 16
    scale = max(4, min(16, int(scale * 48 / ext)))
    small = (int(ext * 1.15 + 10) * scale, int(ext * 0.9 + 10) * scale)
    big = (int(ext * 1.75 + 12) * scale, int(ext * 1.35 + 12) * scale)
    views = [
        render(model, textures, (0, 0, 1), scale, small),          # 정면 (north를 봄)
        render(model, textures, (1, 0, 0), scale, small),          # 오른쪽 옆면 (정면에서 볼 때 오른쪽)
        render(model, textures, (0, 0, -1), scale, small),         # 후면
        render(model, textures, (-1, 0, 0), scale, small),         # 왼쪽 옆면
    ]
    iso = [
        render(model, textures, (-1, -0.75, 1), scale, big),       # 3D: 왼쪽 앞 위에서
        render(model, textures, (1, -0.75, 1), scale, big),        # 3D: 오른쪽 앞 위에서
    ]
    gap = 6
    W = max(small[0] * 4 + gap * 3, big[0] * 2 + gap)
    H = small[1] + gap + big[1]
    canvas = [[(24, 26, 30, 255)] * W for _ in range(H)]
    for i, v in enumerate(views):
        png.paste(canvas, v, i * (small[0] + gap), 0)
    for i, v in enumerate(iso):
        png.paste(canvas, v, i * (big[0] + gap), small[1] + gap)
    png.write(out, canvas)


if __name__ == "__main__":
    sheet(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else DEFAULT_JAR)
    print("ok:", sys.argv[3])

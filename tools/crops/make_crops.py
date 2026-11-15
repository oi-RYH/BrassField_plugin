"""
BrassField 자체 작물(쌀·양파)을 만든다: 그림(16x16), 성장 단계 3D 모델, ItemsAdder 아이템 정의, CustomCrops 작물 설정.
그림은 모두 직접 그린 것이라 공개 저장소에 둘 수 있다 (CustomCrops 구매자용 팩과 섞지 않음, rustport 네임스페이스).

표현 원칙
- 색: 단색 대신 5~6단계 명암. 빛은 왼쪽 위에서. 둥근 것(알뿌리·낟알)은 구 명암, 잎은 뿌리 쪽 어둡고 끝으로 밝게.
- 외곽선: 검정 대신 이웃 색을 어둡게 한 색 (아이템 그림).
- 형태: 성장 단계는 평면 X자 대신 실제 오브젝트. 양파는 흙에 반쯤 묻힌 3D 알뿌리가 단계마다 커지고,
  쌀은 바닐라 작물처럼 # 모양 판 4장으로 빽빽한 논을 표현한다.

농사 규칙(노션 DR-08): 물이 있어야 자라고, 시들지 않고, 까마귀·계절 없음. 품질은 일반·은별·금별.

사용:
  python3 -I tools/crops/make_crops.py <ItemsAdder contents/rustport> <CustomCrops contents/crops>
  PREVIEW=<png> 를 주면 그림 전체를 6배로 늘어놓은 미리보기를 그린다.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "hud"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import png  # noqa: E402
from pixelart import *  # noqa: E402,F401,F403

# ── 색 단계 (어둠 → 밝음) ──
GOLD = [rgb(120, 78, 26), rgb(168, 116, 40), rgb(206, 158, 60), rgb(232, 194, 96), rgb(248, 222, 140), rgb(255, 244, 196)]
STRAW = [rgb(120, 98, 44), rgb(160, 136, 66), rgb(196, 172, 92), rgb(222, 200, 122), rgb(240, 222, 156)]
TIE = [rgb(96, 40, 20), rgb(140, 62, 30), rgb(184, 90, 44), rgb(214, 126, 70)]
LEAF = [rgb(34, 74, 30), rgb(52, 104, 40), rgb(76, 136, 50), rgb(106, 166, 62), rgb(144, 194, 84), rgb(186, 222, 120)]
LEAF_DRY = [rgb(90, 84, 36), rgb(130, 120, 52), rgb(170, 158, 70), rgb(202, 190, 98), rgb(226, 214, 132)]
YOUNG_GRAIN = [rgb(70, 110, 44), rgb(100, 144, 58), rgb(136, 176, 74), rgb(174, 204, 100), rgb(206, 226, 138)]
ONION = [rgb(98, 44, 18), rgb(140, 70, 30), rgb(180, 104, 46), rgb(212, 140, 70), rgb(236, 178, 104), rgb(252, 216, 158)]
ROOT = [rgb(150, 128, 92), rgb(196, 176, 132), rgb(226, 212, 176)]
SEED_DARK = [rgb(24, 20, 18), rgb(46, 40, 36), rgb(84, 76, 70), rgb(130, 120, 112)]

# ── 품질 별 (오른쪽 아래 7x7, 직접 그림) ──
STAR = ["...O...",
        "..OSO..",
        "OOOSOOO",
        "OSSHSSO",
        ".OSSSO.",
        ".OSOSO.",
        ".OO.OO."]
STAR_PAL = {
    "silver": {"O": rgb(64, 66, 76), "S": rgb(192, 196, 206), "H": rgb(246, 248, 252)},
    "golden": {"O": rgb(118, 66, 8), "S": rgb(250, 192, 36), "H": rgb(255, 246, 170)},
}


def with_star(img, kind):
    out = [row[:] for row in img]
    for dy, row in enumerate(STAR):
        for dx, ch in enumerate(row):
            if ch != ".":
                out[9 + dy][9 + dx] = STAR_PAL[kind][ch]
    return out


# ═════════════ 아이템 그림 ═════════════
def rice_item():
    """익은 벼 한 단: 묶은 볏짚 + 고개 숙인 이삭 3개 (낟알 하나하나 구 명암)"""
    img = blank()
    # 볏짚: 아래는 벌어지고 끈 묶은 곳에서 모인다 (사이를 비워 짚 가닥으로 보이게)
    for sx, mx, ex in ((3, 6, 6), (6, 7, 7), (9, 8, 8), (12, 9, 9)):
        thick_line(img, [(sx, 15), (mx, 11), (ex, 8)], STRAW, base_dark=0.3, tip_light=0.85)
    for x in range(6, 10):                                                     # 묶은 끈 (한 줄)
        img[11][x] = ramp_color(TIE, 0.8 if x < 8 else 0.45)
    ears = [[(6.0, 8.5), (5.2, 7.0), (4.2, 5.6), (3.2, 4.6), (2.4, 5.0)],      # 왼쪽 이삭
            [(7.6, 8.0), (7.6, 6.2), (8.2, 4.4), (9.2, 3.0), (10.6, 2.6)],     # 가운데
            [(9.4, 8.6), (10.6, 7.0), (12.0, 6.0), (13.4, 6.4), (13.8, 8.0)]]  # 오른쪽
    for ear in ears:
        thick_line(img, [(int(x), int(y)) for x, y in ear], STRAW, base_dark=0.3, tip_light=0.6)
        for i, (gx, gy) in enumerate(ear[1:]):
            sphere(img, gx + 0.3, gy + 0.2, 1.15, 1.0 - i * 0.04, GOLD)
    return outline(img)


def onion_item():
    """양파: 위가 좁아지는 알뿌리(구 명암 + 세로 껍질 결) + 싹 + 잔뿌리"""
    img = blank()
    sphere(img, 7.8, 9.2, 5.4, 5.0, ONION, taper=0.55, stripes=3)
    thick_line(img, [(7, 4), (7, 2), (6, 0)], LEAF, base_dark=0.35, tip_light=0.85)   # 싹
    thick_line(img, [(8, 4), (9, 2), (10, 1)], LEAF, base_dark=0.3, tip_light=0.75)
    for rx in (6, 8, 10):                                                              # 잔뿌리
        img[14][rx] = ROOT[1]
        img[15][rx + (1 if rx > 7 else -1)] = ROOT[0]
    img[14][7] = ROOT[2]
    return outline(img)


def rice_seeds():
    img = blank()
    for gx, gy in ((4, 4), (11, 5), (8, 8), (3, 10), (11, 11), (7, 13)):
        sphere(img, gx + 0.5, gy + 0.5, 1.4, 0.9, GOLD)
    return outline(img, 0.5)


def onion_seeds():
    img = blank()
    for gx, gy in ((4, 3), (11, 4), (7, 7), (3, 10), (12, 10), (8, 12)):
        sphere(img, gx + 0.5, gy + 0.5, 1.1, 1.0, SEED_DARK)
    return img


# ═════════════ 성장 단계 그림 (판에 붙는 잎) ═════════════
def rice_stage_tex(n):
    """벼 잎: 단계마다 키·개수가 늘고, 3단계 초록 이삭, 4단계 황금 이삭이 고개를 숙인다"""
    img = blank()
    count, top = {1: (4, 10), 2: (6, 5), 3: (7, 3), 4: (7, 3)}[n]
    for i in range(count):
        x0 = 2 + i * 12 / max(1, count - 1)
        lean = (-1.5, 1.2, -0.6, 1.8, -1.2, 0.8, 0.2)[i]
        h = top + (i * 3) % 4
        ramp = LEAF_DRY if (n == 4 and i % 3 == 1) else LEAF
        thick_line(img, [(int(x0), 15), (int(x0 + lean / 2), (15 + h) // 2), (int(x0 + lean), h)], ramp,
                   base_dark=0.1, tip_light=0.9)
    if n >= 3:
        grain = YOUNG_GRAIN if n == 3 else GOLD
        for hx in (3, 8, 13):
            droop = 0 if n == 3 else 1
            for k in range(4):
                gx = hx + (k * 0.6 if n == 3 else k * 0.9)
                gy = 2 + k * (0.9 + droop * 0.5)
                sphere(img, gx, gy, 0.9, 0.8, grain)
    return img


def onion_stage_tex(n):
    """양파 잎: 속이 빈 통 잎(두 줄, 왼쪽 밝게). 4단계는 잎끝이 누렇게 꺾인다"""
    img = blank()
    leaves = {1: [[(7, 15), (7, 12)], [(9, 15), (9, 12), (10, 11)]],
              2: [[(6, 15), (5, 10), (4, 7)], [(8, 15), (8, 9), (8, 5)], [(10, 15), (11, 10), (12, 7)]],
              3: [[(5, 15), (4, 9), (2, 4)], [(7, 15), (7, 8), (6, 2)], [(9, 15), (9, 8), (10, 2)], [(11, 15), (12, 9), (14, 4)]],
              4: [[(5, 15), (3, 10), (1, 8)], [(7, 15), (6, 8), (5, 3)], [(9, 15), (10, 8), (11, 3)], [(11, 15), (13, 10), (15, 9)]]}[n]
    for i, pts in enumerate(leaves):
        ramp = LEAF_DRY if (n == 4 and i in (0, 3)) else LEAF
        thick_line(img, pts, ramp, width=2 if n >= 2 else 1, base_dark=0.15, tip_light=0.9)
    return img


def onion_skin_side():
    """3D 알뿌리 옆면 (8x8): 위 밝고 아래 어두운 껍질 + 세로 결"""
    img = blank(8)
    for y in range(8):
        for x in range(8):
            v = 0.85 - y * 0.08 - (0.15 if x in (2, 5) else 0) + (0.08 if x == 1 else 0)
            img[y][x] = ramp_color(ONION, v)
    return img


def onion_skin_top():
    img = blank(8)
    for y in range(8):
        for x in range(8):
            d = math.hypot(x - 3.5, y - 3.5)
            img[y][x] = ramp_color(ONION, 0.95 - d * 0.1)
    return img


# ═════════════ 성장 단계 모델 ═════════════
def plane(frm, to, axis_faces, rot=None, tex="#0"):
    e = {"from": frm, "to": to, "shade": False,
         "faces": {f: {"uv": [0, 0, 16, 16], "texture": tex} for f in axis_faces}}
    if rot is not None:
        e["rotation"] = {"angle": rot, "axis": "y", "origin": [8, 0, 8], "rescale": True}
    return e


def cross_planes():
    return [plane([0.8, 0, 8], [15.2, 16, 8], ("north", "south"), rot=45),
            plane([8, 0, 0.8], [8, 16, 15.2], ("east", "west"), rot=45)]


def hash_planes():
    """바닐라 작물처럼 # 모양 판 4장 (빽빽한 논)"""
    return [plane([4, 0, 0], [4, 16, 16], ("east", "west")), plane([12, 0, 0], [12, 16, 16], ("east", "west")),
            plane([0, 0, 4], [16, 16, 4], ("north", "south")), plane([0, 0, 12], [16, 16, 12], ("north", "south"))]


def bulb(size, height, neck=0.0):
    """흙(화분 위)에 반쯤 묻힌 3D 알뿌리"""
    lo, hi = 8 - size / 2, 8 + size / 2
    faces = {f: {"uv": [0, 0, 8 * 2, 8 * 2], "texture": "#1"} for f in ("north", "south", "east", "west")}
    faces["up"] = {"uv": [0, 0, 16, 16], "texture": "#2"}
    els = [{"from": [lo, -0.5, lo], "to": [hi, height, hi], "faces": faces}]
    if neck:
        n0, n1 = 8 - neck / 2, 8 + neck / 2
        els.append({"from": [n0, height, n0], "to": [n1, height + neck * 0.8, n1],
                    "faces": {f: {"uv": [0, 0, 16, 16], "texture": "#1"} for f in ("north", "south", "east", "west", "up")}})
    return els


def stage_model(cid, n):
    leaf = "rustport:block/crop/%s/stage_%d" % (cid, n)
    textures = {"0": leaf, "particle": leaf}
    if cid == "rice":
        elements = cross_planes() if n == 1 else hash_planes()
    else:
        elements = cross_planes()
        if n >= 2:
            textures["1"] = "rustport:block/crop/onion/bulb_side"
            textures["2"] = "rustport:block/crop/onion/bulb_top"
            elements = bulb(*{2: (2.4, 1.4, 0), 3: (4.2, 3.0, 1.4), 4: (5.6, 4.4, 1.8)}[n]) + elements
    return {"textures": textures, "elements": elements}


CROPS = {
    "rice": {"name": "쌀", "harvest": rice_item(), "seeds": rice_seeds(), "stage": rice_stage_tex, "drop": (2, 4)},
    "onion": {"name": "양파", "harvest": onion_item(), "seeds": onion_seeds(), "stage": onion_stage_tex, "drop": (1, 2)},
}


# ═════════════ 설정 파일 ═════════════
def ia_block(name, crop, n):
    return f"""  {name}:
    display_name: "{crop['name']} ({n}단계)"
    resource:
      generate: false
      material: PAPER
      model_path: block/crop/{crop['id']}/stage_{n}
    specific_properties:
      block:
        placed_model:
          type: REAL_WIRE
          break_particles: BLOCK
        hardness: 0
        blast_resistance: 0
        sound:
          break:
            name: block.crop.break
          place:
            name: item.crop.plant
          hit:
            name: block.grass.hit
          step:
            name: block.grass.step
          fall:
            name: block.grass.fall
"""


def ia_item(name, display, texture, material):
    return f"""  {name}:
    display_name: "{display}"
    resource:
      generate: true
      material: {material}
      textures:
        - {texture}
"""


def cc_crop(crop):
    cid = crop["id"]
    pid = "rustport:" + cid
    points = []
    for i in range(4):
        if i < 3:
            events = f"""      events:
        break:
          action_1:
            type: drop-item
            value:
              item: {pid}_seeds
              min: 1
              max: 1
            chance: {[0.3, 0.6, 0.9][i]}
"""
        else:
            lo, hi = crop["drop"]
            events = f"""      events:
        break:
          action_1:
            type: quality-crops
            value:
              min: {lo}
              max: {hi}
              items:
                '1': {pid}
                '2': {pid}_silver_star
                '3': {pid}_golden_star
          action_2:
            type: drop-item
            value:
              item: {pid}_seeds
              min: 1
              max: 2
            chance: 1
        interact:
          empty_hand_action:
            type: conditional
            value:
              conditions:
                requirement_empty_hand:
                  type: item-in-hand
                  value:
                    item: AIR
              actions:
                action_0:
                  type: swing-hand
                  value: true
                action_1:
                  type: break
                  value: true
"""
        points.append(f"""    '{i}':
      model: {pid}_stage_{i + 1}
      hologram-offset-correction: -0.4
{events}""")
    return f"""# BrassField 자체 작물: {crop['name']} (tools/crops/make_crops.py 로 생성, 직접 수정하지 말 것)
# 농사 규칙(노션 DR-08): 물이 있어야 자라고, 시들지 않고, 까마귀·계절 없음
{cid}:
  type: BLOCK
  pot-whitelist:
  - default
  seed: {pid}_seeds
  random-rotation: true
  requirements:
    plant: {{}}
  events:
    plant:
      action_1:
        type: sound
        value:
          source: player
          key: minecraft:item.hoe.till
          volume: 1
          pitch: 1
    break:
      action_1:
        type: sound
        value:
          source: player
          key: minecraft:block.crop.break
          volume: 1
          pitch: 1
  max-points: 4
  points:
{''.join(points)}  grow-conditions:
    default:
      point: 1
      conditions:
        water_condition:
          type: water-more-than
          value: 0
  death-conditions: {{}}
  custom-bone-meal:
    bone_meal_1:
      item: BONE_MEAL
      chance:
        '2': 0.2
        '1': 0.6
      actions:
        swing_action:
          type: swing-hand
          value: true
        sound_action:
          type: sound
          value:
            key: minecraft:item.bone_meal.use
            source: player
            volume: 1
            pitch: 1
"""


# ═════════════ 저장 ═════════════
pack, cc_crops = sys.argv[1], sys.argv[2]
assets = os.path.join(pack, "resourcepack/assets/rustport")
ia = ["info:", "  namespace: rustport", "",
      "# BrassField 자체 작물 (tools/crops/make_crops.py 로 생성, 직접 수정하지 말 것)", "items:"]
preview = []
for cid, crop in CROPS.items():
    crop["id"] = cid
    item_dir = os.path.join(assets, "textures/item/crop", cid)
    block_dir = os.path.join(assets, "textures/block/crop", cid)
    model_dir = os.path.join(assets, "models/block/crop", cid)
    for d in (item_dir, block_dir, model_dir):
        os.makedirs(d, exist_ok=True)
    harvest = crop["harvest"]
    for name, img in (("%s_seeds" % cid, crop["seeds"]), (cid, harvest),
                      ("%s_silver_star" % cid, with_star(harvest, "silver")),
                      ("%s_golden_star" % cid, with_star(harvest, "golden"))):
        png.write(os.path.join(item_dir, name + ".png"), img)
        preview.append(img)
    ia.append(ia_item(cid + "_seeds", crop["name"] + " 씨앗", "item/crop/%s/%s_seeds" % (cid, cid), "PAPER"))
    ia.append(ia_item(cid, crop["name"], "item/crop/%s/%s" % (cid, cid), "APPLE"))
    ia.append(ia_item(cid + "_silver_star", crop["name"] + " (은별)", "item/crop/%s/%s_silver_star" % (cid, cid), "APPLE"))
    ia.append(ia_item(cid + "_golden_star", crop["name"] + " (금별)", "item/crop/%s/%s_golden_star" % (cid, cid), "APPLE"))
    for n in range(1, 5):
        img = crop["stage"](n)
        png.write(os.path.join(block_dir, "stage_%d.png" % n), img)
        preview.append(img)
        with open(os.path.join(model_dir, "stage_%d.json" % n), "w", encoding="utf-8") as f:
            json.dump(stage_model(cid, n), f, indent=1)
        ia.append(ia_block("%s_stage_%d" % (cid, n), crop, n))
    with open(os.path.join(cc_crops, cid + ".yml"), "w", encoding="utf-8") as f:
        f.write(cc_crop(crop))
png.write(os.path.join(assets, "textures/block/crop/onion/bulb_side.png"), onion_skin_side())
png.write(os.path.join(assets, "textures/block/crop/onion/bulb_top.png"), onion_skin_top())
with open(os.path.join(pack, "configs/crops.yml"), "w", encoding="utf-8") as f:
    f.write("\n".join(ia))
if os.environ.get("PREVIEW"):
    sheet = png.blank(18 * 8, 18 * 2)
    for i, img in enumerate(preview):
        png.paste(sheet, img, (i % 8) * 18, (i // 8) * 18)
    png.write(os.environ["PREVIEW"], png.scale(sheet, 6))
print("ok:", ", ".join(CROPS))

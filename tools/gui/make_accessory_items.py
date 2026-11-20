"""
장신구 아이콘(tools/gui/art/accessory_{combat,farm,adventure}, 32x32, 세트 · 종류 · 등급 · 강화 0~3 = 240장)을
ItemsAdder rustport 리소스팩에 아이템 모델로 넣는다. 3D 없이 평면 아이콘(item/generated).
  textures/item/accessory/<이름>.png · models/item/accessory/<이름>.json · items/accessory/<이름>.json
플러그인(com.brassfield.accessory.Accessories)이 item_model = rustport:accessory/<이름> 으로 붙인다.

사용: python3 tools/gui/make_accessory_items.py <ItemsAdder contents 폴더>
"""
import glob
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main(content):
    root = os.path.join(content, "rustport", "resourcepack", "assets", "rustport")
    dirs = {k: os.path.join(root, k, "accessory") if k == "items" else os.path.join(root, k, "item", "accessory")
            for k in ("textures", "models", "items")}
    for d in dirs.values():
        os.makedirs(d, exist_ok=True)
    count = 0
    for png in sorted(glob.glob(os.path.join(HERE, "art", "accessory_*", "*.png"))):
        name = os.path.splitext(os.path.basename(png))[0]
        shutil.copyfile(png, os.path.join(dirs["textures"], name + ".png"))
        model = {"parent": "minecraft:item/generated", "textures": {"layer0": "rustport:item/accessory/" + name}}
        with open(os.path.join(dirs["models"], name + ".json"), "w") as f:
            json.dump(model, f, separators=(",", ":"))
        item = {"model": {"type": "minecraft:model", "model": "rustport:item/accessory/" + name}}
        with open(os.path.join(dirs["items"], name + ".json"), "w") as f:
            json.dump(item, f, separators=(",", ":"))
        count += 1
    # 장착 창 효과 단추: 세트 효과(왕관) · 종합 효과(크리스탈) — rustport:accessory_set · accessory_total
    for name in ("accessory_set", "accessory_total"):
        shutil.copyfile(os.path.join(HERE, "art", name + ".png"), os.path.join(root, "textures", "item", name + ".png"))
        with open(os.path.join(root, "models", "item", name + ".json"), "w") as f:
            json.dump({"parent": "minecraft:item/generated", "textures": {"layer0": "rustport:item/" + name}}, f, separators=(",", ":"))
        with open(os.path.join(root, "items", name + ".json"), "w") as f:
            json.dump({"model": {"type": "minecraft:model", "model": "rustport:item/" + name}}, f, separators=(",", ":"))
    print("accessory items", count, "+ set/total buttons")


if __name__ == "__main__":
    main(sys.argv[1])

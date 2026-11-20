"""
레시피 책(조합 도우미) 그림을 인벤토리 배경(make_inventory_bg.py)과 같은 황동 · 어두운 갈색으로 바꾼다.
바닐라 그림은 회색 몇 단계(0 · 55 · 85 · 106 · 139 · 198 · 204 · 255)로만 그려져 있어,
그림마다 회색 → 황동 색 대응표를 두고 칸 위치 · 모양은 그대로 둔 채 색만 바꾼다 (아이콘의 색 픽셀은 그대로).

- 테(창 · 탭 · 단추 · 팝업): 흰색 → 밝은 황동, 밝은 회색 → 황동, 어두운 회색 → 짙은 황동, 검정 → 짙은 갈색
- 칸(레시피 칸 · 쪽 넘김 · 필터 바탕): 강화 창 칸 색 (어두운 칸 바탕 + 밝은 금속 테)
- 레시피 책 단추의 초록 책 → 갈색 가죽 책

사용: python3 tools/gui/make_recipe_book.py <26.1.2 클라이언트 jar> <출력 assets 폴더> [미리보기 png] [인벤토리 배경 png]
"""
import io
import os
import sys
import zipfile

from PIL import Image

SP = "assets/minecraft/textures/gui/sprites/recipe_book/"
PANEL = "assets/minecraft/textures/gui/recipe_book.png"

DK = (13, 10, 7)
FRAME = {0: DK, 255: (226, 179, 99), 198: (187, 127, 54), 204: (187, 127, 54), 85: (146, 83, 40),
         55: (43, 36, 29), 139: (110, 61, 28)}
FRAME_HI = {0: DK, 255: (250, 214, 140), 198: (214, 160, 80), 204: (214, 160, 80), 85: (170, 104, 52),
            55: (43, 36, 29), 139: (150, 92, 40)}
TAB = {0: DK, 255: (187, 127, 54), 198: (146, 83, 40), 139: (74, 43, 24), 85: (52, 32, 20)}
TAB_SEL = {0: DK, 255: (226, 179, 99), 198: (58, 50, 40), 85: (146, 83, 40), 139: (58, 50, 40)}
SLOT = {0: DK, 55: (36, 35, 31), 85: (51, 43, 34), 106: (60, 50, 42), 139: (73, 69, 60),
        198: (121, 102, 75), 204: (121, 102, 75), 255: (174, 157, 125)}
SLOT_HI = {0: DK, 55: (60, 52, 40), 85: (90, 72, 50), 139: (110, 96, 72), 198: (174, 157, 125),
           204: (174, 157, 125), 255: (226, 200, 150)}
LEATHER = [(50, 28, 16), (78, 44, 22), (110, 62, 30), (150, 92, 45), (190, 130, 66)]   # 초록 책 → 갈색 가죽 (밝기 순)
GLOW = [(120, 72, 30), (170, 110, 48), (214, 160, 80), (240, 200, 120)]                  # 강조 단추의 파란 바탕 → 밝은 황동
OVERLAY = {0: DK, 255: (226, 179, 99), 198: (58, 50, 40), 85: (146, 83, 40)}           # 대체 레시피 팝업: 어두운 바탕 + 황동 테

SPRITES = {
    "button": FRAME, "button_highlighted": FRAME_HI,
    "tab": TAB, "tab_selected": TAB_SEL,
    "page_backward": SLOT, "page_forward": SLOT, "page_backward_highlighted": SLOT_HI, "page_forward_highlighted": SLOT_HI,
    "slot_craftable": SLOT, "slot_many_craftable": SLOT, "slot_uncraftable": SLOT, "slot_many_uncraftable": SLOT,
    "crafting_overlay": SLOT, "crafting_overlay_highlighted": SLOT_HI,
    "crafting_overlay_disabled": SLOT, "crafting_overlay_disabled_highlighted": SLOT_HI,
    "furnace_overlay": SLOT, "furnace_overlay_highlighted": SLOT_HI,
    "furnace_overlay_disabled": SLOT, "furnace_overlay_disabled_highlighted": SLOT_HI,
    "filter_disabled": SLOT, "filter_disabled_highlighted": SLOT_HI,
    "furnace_filter_disabled": SLOT, "furnace_filter_disabled_highlighted": SLOT_HI,
    "overlay_recipe": OVERLAY,
}


def recolor(img, table, book=False):
    img = img.convert("RGBA")
    px = img.load()
    keys = sorted(table)
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if not a:
                continue
            lum = (r + g + b) / 3
            if book and g > r + 12 and g > b + 12:     # 초록 책
                px[x, y] = LEATHER[min(len(LEATHER) - 1, int(lum / 256 * len(LEATHER) * 1.25))] + (a,)
            elif book and b > r + 12:                  # 강조 단추 파란 바탕
                px[x, y] = GLOW[min(len(GLOW) - 1, int(lum / 256 * len(GLOW) * 1.15))] + (a,)
            elif r == g == b:                          # 회색만 바꾸고 색 있는 아이콘 픽셀은 둔다
                k = min(keys, key=lambda k: abs(k - r))
                px[x, y] = table[k] + (a,)
    return img


def build(jar, out):
    z = zipfile.ZipFile(jar)

    def load(p):
        return Image.open(io.BytesIO(z.read(p)))
    made = {}
    for name, table in SPRITES.items():
        img = recolor(load(SP + name + ".png"), table, book=name.startswith(("button", "page_")))
        made[name] = img
        path = os.path.join(out, SP.replace("assets/", "", 1), name + ".png")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        img.save(path)
        meta = SP + name + ".png.mcmeta"
        if meta in z.namelist():
            with open(path + ".mcmeta", "wb") as f:
                f.write(z.read(meta))
    panel = recolor(load(PANEL), FRAME)
    path = os.path.join(out, PANEL.replace("assets/", "", 1))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    panel.save(path)
    made["panel"] = panel
    return made, z


def preview(made, z, inv_bg, path):
    """책을 연 인벤토리: 왼쪽 레시피 책(탭 · 검색 자리 · 레시피 칸 · 쪽 넘김) + 오른쪽 인벤토리"""
    W, H = 30 + 147 + 2 + 176, 168
    shot = Image.new("RGBA", (W, H), (110, 110, 110, 255))
    px0 = 30
    for i in range(5):                                       # 탭 (첫 탭 선택)
        t = made["tab_selected" if i == 0 else "tab"]
        shot.alpha_composite(t, (px0 - 30 + (2 if i == 0 else 4), 3 + 27 * i))
    shot.alpha_composite(made["panel"].crop((0, 0, 149, 168)), (px0 - 1, 0))
    shot.alpha_composite(made["filter_disabled"] if "filter_disabled" in made else made["slot_craftable"], (px0 + 110, 12))
    for i in range(20):
        name = "slot_craftable" if i % 3 else "slot_uncraftable"
        shot.alpha_composite(made[name], (px0 + 11 + (i % 5) * 25, 31 + (i // 5) * 25))
    shot.alpha_composite(made["page_backward"], (px0 + 38, 137))
    shot.alpha_composite(made["page_forward"], (px0 + 93, 137))
    inv = Image.open(inv_bg).convert("RGBA").crop((0, 0, 176, 166))
    shot.alpha_composite(inv, (px0 + 147 + 2, 0))
    shot.alpha_composite(made["button_highlighted"], (px0 + 147 + 2 + 104, 61))
    shot.resize((W * 4, H * 4), Image.NEAREST).save(path)


if __name__ == "__main__":
    made, z = build(sys.argv[1], sys.argv[2])
    if len(sys.argv) > 4:
        preview(made, z, sys.argv[4], sys.argv[3])

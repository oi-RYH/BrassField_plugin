import sys, random; sys.path.insert(0, '.')
import png
OUT = sys.argv[1]  # .../textures/font/hud/
random.seed(7)
O=(13,10,7,255)
BR=[(226,179,99,255),(187,127,54,255),(146,83,40,255),(74,43,24,255)]   # brass light→dark
BG=[(44,37,30,255),(42,35,28,255),(45,38,31,255),(43,36,29,255),(46,39,32,255)]
PLATE_TOP=(19,16,13,255); PLATE=(27,23,19,255); PLATE_BOT=(42,36,29,255)
TUBE=[(90,24,6,255),(212,102,26,255),(255,243,196,255),(240,154,50,255),(163,61,12,255)]
RIVET=[(255,236,170,255),(187,127,54,255),(74,43,24,255)]

PW, PH = 62, 58
p = png.blank(PW, PH)
# 안쪽 바탕: 어두운 질감
for y in range(PH):
    for x in range(PW):
        p[y][x] = random.choice(BG)
# 황동 파이프 테두리 (바깥 윤곽 → 밝음 → 중간 → 그늘 → 어둠 → 윤곽)
pipe = [O] + BR + [O]
for i, c in enumerate(pipe):
    for x in range(PW):
        p[i][x] = c; p[PH-1-i][x] = pipe[i] if i == 0 else c
    for y in range(PH):
        p[y][i] = c; p[y][PW-1-i] = c
# 아래·오른쪽 파이프는 빛 방향에 맞춰 뒤집기 (밝은 면이 위·왼쪽)
for i, c in enumerate(pipe):
    for x in range(i, PW-i):
        p[PH-1-i][x] = pipe[len(pipe)-1-i] if 0 < i < len(pipe)-1 else O
    for y in range(i, PH-i):
        p[y][PW-1-i] = pipe[len(pipe)-1-i] if 0 < i < len(pipe)-1 else O
# 모서리 이음쇠(8x8) + 리벳
def flange(x0, y0):
    for y in range(8):
        for x in range(8):
            edge = x in (0, 7) or y in (0, 7)
            p[y0+y][x0+x] = O if edge else (BR[0] if x == 1 or y == 1 else (BR[3] if x == 6 or y == 6 else BR[1]))
    cx, cy = x0+3, y0+3
    p[cy][cx] = RIVET[0]; p[cy][cx+1] = RIVET[1]; p[cy+1][cx] = RIVET[1]; p[cy+1][cx+1] = RIVET[2]
for fx, fy in ((0, 0), (PW-8, 0), (0, PH-8), (PW-8, PH-8)):
    flange(fx, fy)
# 제목 줄(y 6~15): 가로 주황 유리관 + 황동 마개
for x in range(14, 48):
    for i, c in enumerate(TUBE):
        p[8+i][x] = c
    p[7][x] = O; p[13][x] = O
for cap_x in (10, 48):
    for y in range(7, 14):
        for x in range(cap_x, cap_x+4):
            edge = x in (cap_x, cap_x+3) or y in (7, 13)
            p[y][x] = O if edge else (BR[0] if y == 8 else BR[1] if y < 11 else BR[2])
# 숫자 뒤 어두운 판 (강화 GUI 글자 보드와 같은 모양): x 21~55, y 16~51 → 프레임 안쪽까지
x0, x1, y0, y1 = 21, 55, 16, 51
for y in range(y0, y1+1):
    for x in range(x0, x1+1):
        if x == x0 or y == y0 or x == x1 or y == y1:
            p[y][x] = O
        elif y == y0+1:
            p[y][x] = PLATE_TOP
        elif y == y1-1:
            p[y][x] = PLATE_BOT
        else:
            p[y][x] = PLATE
# 줄 사이 얇은 구분선
for r in (1, 2, 3):
    y = 16 + 9*r - 1
    for x in range(x0+2, x1-1):
        p[y][x] = PLATE_TOP
png.write(OUT + 'panel.png', p)

T = (0, 0, 0, 0)
# 강화석 아이콘: 상자 그림(textures/item/*_enhancement_chest.png)과 같은 방향으로,
# 같은 호박색 결정이 등급마다 커지고 밝아진다. 받침은 철(하급) → 황동(중급·상급), 상급은 불꽃과 불티.
GEMS = {
    'gem_low': ([".........",
                 ".........",
                 "...OOO...",
                 "..OGGGO..",
                 "..OGHCO..",
                 "..OGCDO..",
                 "..OGCDO..",
                 "..OGGGO..",
                 "...OOO..."],
                {'O': (36, 36, 36, 255), 'G': (123, 116, 106, 255), 'H': (255, 200, 90, 255),
                 'C': (215, 120, 24, 255), 'D': (138, 75, 21, 255)}),
    'gem_mid': (["...OOO...",
                 "..OBBBO..",
                 ".OBHLCBO.",
                 ".OBLCCBO.",
                 ".OBCCDBO.",
                 ".OBCDDBO.",
                 ".OBBBBBO.",
                 "..OBBBO..",
                 "...OOO..."],
                {'O': (42, 33, 25, 255), 'B': (198, 139, 58, 255), 'H': (255, 246, 199, 255),
                 'L': (255, 224, 120, 255), 'C': (240, 138, 22, 255), 'D': (156, 74, 0, 255)}),
    'gem_high': (["S..F.F..S",
                  "..OFHFO..",
                  ".OHLLCDO.",
                  "OBLLCCDBO",
                  "OBLCCCDBO",
                  "OBCCCDDBO",
                  ".OBCDDBO.",
                  "..OBBBO..",
                  "...OOO..."],
                 {'O': (40, 21, 21, 255), 'B': (224, 164, 77, 255), 'H': (255, 246, 199, 255),
                  'L': (255, 240, 160, 255), 'C': (255, 106, 26, 255), 'D': (181, 40, 22, 255),
                  'F': (255, 106, 26, 255), 'S': (226, 121, 82, 255)}),
}
for name, (rows, pal) in GEMS.items():
    png.write(OUT + name + '.png', [[T if c == '.' else pal[c] for c in row] for row in rows])

W = (255, 255, 255, 255)
LETTERS = {
    'K': ["#...#", "#..#.", "###..", "#..#.", "#...#", "#...#", "#...#"],
    'M': ["#...#", "##.##", "#.#.#", "#...#", "#...#", "#...#", "#...#"],
    'B': ["####.", "#...#", "####.", "#...#", "#...#", "#...#", "####."],
    'T': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    'Q': [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    'E': ["#####", "#....", "###..", "#....", "#....", "#....", "#####"],
}
for ch, rows in LETTERS.items():
    img = png.blank(8, 8)
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            if c == '#':
                img[y][x] = W
    png.write(OUT + 'u_%04x.png' % ord(ch), img)
print('ok')

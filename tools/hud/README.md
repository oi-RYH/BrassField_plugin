# 재화 사이드바 그림 생성

강화 GUI 배경(`enhance_bg.png`)에서 뽑은 색으로 재화 사이드바용 그림을 만든다. 외부 라이브러리 없이 표준 Python만 쓴다.

```sh
T=~/mc-server-dev/plugins/ItemsAdder/contents/rustport/resourcepack/assets/rustport/textures
python3 -I tools/hud/make_hud.py $T/font/hud/ $T/item/
```

만드는 파일 (`textures/font/hud/`):

| 파일 | 크기 | 용도 |
|---|---|---|
| `panel.png` | 62×58 | 사이드바 전체를 덮는 황동 판 |
| `gem_low/mid/high.png` | 9×9 | 하급·중급·상급 강화석 아이콘 (상자 그림처럼 같은 결정이 등급마다 커짐) |
| `u_004b.png` 등 | 8×8 | 단위 글자 K M B T Q E (숫자·점은 `font/board` 재사용) |
| `item/stone_icon_low/mid/high.png` | 32×32 | 강화 GUI·상점의 강화석 아이콘 (결정을 2배로 키워 가운데 배치, 두 번째 인자를 줄 때만) |

동전(`coin.png`)은 따로 그린 그림이라 이 스크립트가 만들지 않는다.
그림 크기를 바꾸면 `CurrencySidebar`의 좌표 상수와 ItemsAdder `rustport/configs/hud_font.yml`의 `scale_ratio`·`y_position`도 함께 맞춘다.

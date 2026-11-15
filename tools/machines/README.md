# 거래 기계 모델

마을에 설치하는 스팀펑크 기계(ItemsAdder 가구)와 기계 위 표시의 3D 모델을 만든다. 노션 DR-09 참고.

```sh
A=~/mc-server-dev/plugins/ItemsAdder/contents/rustport/resourcepack/assets   # 거래 기계는 $A/rustport 를 넘긴다
python3 -I tools/machines/make_vending_machine.py $A/rustport      # 증기 강화석 자판기
python3 -I tools/machines/make_enhancement_machine.py $A/rustport  # 증폭 공작대 (2블록 폭)
python3 -I tools/machines/make_crop_buyer.py $A/rustport           # 종자·작물 거래기
python3 -I tools/machines/make_cooking_station.py $A/rustport   # 조리대 (3x1x2, 개인 요리 기기)
python3 -I tools/machines/make_cooking_tools.py $A              # 보조 요리 도구 6종 (제분기·착즙기·발효조·훈연기·대형 솥·제빵 오븐)
python3 -I tools/machines/make_marker.py $A/rustport               # 기계 위 빨간 역삼각형 표시 (2D 그림, item/generated)
```

`PREVIEW=미리보기.png`를 앞에 붙이면 정면·옆면 합성 미리보기를 그린다. 결과는 `textures/machine/`, `models/machine/`에 저장된다.

| 파일 | 내용 |
|---|---|
| `machine_kit.py` | 공용 재질(매끄러운 철·황동 판재와 원통 명암, 내부·유리·구멍), 큐브 만들기(`cube`, 정면 기준 좌표 `view_cube`), 저장·미리보기 |
| `make_*.py` | 기계별 전용 그림과 큐브 배치 |

- 모델 좌표는 1블록 = 16단위, 앞면 = north. 기계는 1블록 폭 x 2블록 높이(`-16~32` 범위 안). 공작대만 2블록 폭.
- 정면에서 보면 모델 x가 오른쪽→왼쪽으로 커진다. 시안처럼 배치하려면 `view_cube`(정면 기준 좌표)를 쓴다.
- 텍스처는 128x128, 블록당 32px. 검은 외곽선 없이 명암과 형태로 입체감을 낸다.
- 금속 큐브는 두 방향이 얇고 한 방향이 길면 원통(파이프·기둥) 명암, 아니면 판재 명암을 자동으로 쓴다.
- ItemsAdder 가구 설정은 `rustport/configs/machines.yml` (`opposite_direction: true`, `display_transformation.translation.y: 0.5`).

## 요리 기기 (조리대·보조 도구)

- 바닐라 픽셀 크기 그대로 (1 모델 단위 = 텍스처 1픽셀 = 1/16 블록, 키우지 않음). 모든 부품은 정수 단위.
- 바닐라 블록 텍스처는 모델에서 `minecraft:block/...` 로 참조만 하고, 바닐라에 없는 것만 직접 그린다.
- 황동은 Create 모드 황동, 쇠 판은 Create 산업용 철 느낌. 둘 다 부품 면마다 그 면 크기에 맞춰 테두리(쇠는 모서리 볼트)를 그린다 (`furniture_kit.py`의 `framed_face`).
- `furniture_kit.py`: 큐브(`Model.box`, 블록 칸 기준 자동 UV), 바닐라 불·장작, 그림 판, 공용 재질, 저장.

## 미리보기

```sh
python3 -I tools/machines/model_preview.py <모델.json> <리소스팩 assets 폴더> <출력.png>
```

모델 파일을 그대로 읽어 정면·오른쪽·후면·왼쪽과 3D 두 방향을 한 장으로 그린다 (회전 큐브·투명·면 밝기, 바닥 블록 격자).
바닐라 텍스처는 마인크래프트 클라이언트 jar 에서 읽는다. 서버에 넣기 전에 이 그림으로 먼저 확인한다.

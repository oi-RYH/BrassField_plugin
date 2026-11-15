# 거래 기계 모델

마을에 설치하는 스팀펑크 기계(ItemsAdder 가구)와 기계 위 표시의 3D 모델을 만든다. 노션 DR-09 참고.

```sh
A=~/mc-server-dev/plugins/ItemsAdder/contents/rustport/resourcepack/assets/rustport
python3 -I tools/machines/make_vending_machine.py $A      # 증기 강화석 자판기
python3 -I tools/machines/make_enhancement_machine.py $A  # 증폭 공작대 (2블록 폭)
python3 -I tools/machines/make_crop_buyer.py $A           # 종자·작물 거래기
python3 -I tools/machines/make_marker.py $A               # 기계 위 빨간 역삼각형 표시 (2D 그림, item/generated)
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

# CustomCrops 설정 도구

## 계절 조건 지우기 (`strip_season.py`)

BrassField는 계절을 쓰지 않는다 (노션 DR-08). CustomCrops 공식 팩의 작물 설정에는 계절 조건이 들어 있어서,
팩을 새로 받거나 업데이트하면 다시 지워야 한다.

```sh
cp -R ~/mc-server-dev/plugins/CustomCrops/contents/crops ~/mc-server-dev/backups/crops-$(date +%Y%m%d-%H%M%S)
python3 -I tools/customcrops/strip_season.py ~/mc-server-dev/plugins/CustomCrops/contents/crops/*.yml
```

| 조건 | 처리 |
|---|---|
| 심기 조건 `type: season` | 조건 삭제 (비면 `plant: {}`) |
| 성장 조건 `suitable-season` | 조건만 삭제, 물 조건은 유지 |
| 사망 조건 `unsuitable-season` | **사망 항목 전체 삭제** (조건만 지우면 무조건 죽는 항목이 남음) |

함께 `CustomCrops/config.yml`의 월드 `season.enable`을 `false`로 둔다.

CustomCrops 공식 팩과 그 설정 파일은 재배포 금지라 이 저장소에 넣지 않는다.

## 농사 규칙 적용 (`tune_crops.py`)

물이 없으면 자라지 않고, 시들지 않으며, 까마귀가 없다 (노션 DR-08 농사 규칙). 계절 조건을 지운 뒤 이어서 실행한다.

```sh
python3 -I tools/customcrops/tune_crops.py ~/mc-server-dev/plugins/CustomCrops/contents/crops/*.yml
```

| 대상 | 처리 |
|---|---|
| 성장 조건에 물 조건이 없는 작물 | "물 1 이상일 때 1단계씩"으로 교체 (사과·마늘·용과) |
| 사망 조건 `no_water` | 삭제 (물이 없어도 시들지 않음) |
| 사망 조건 `crow_attack` | 삭제 (까마귀 없음) |

품질 등급(일반·은별·금별·거대)은 그대로 둔다.

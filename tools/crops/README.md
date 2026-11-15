# BrassField 자체 작물

CustomCrops 구매자용 팩에 없는 작물(쌀·양파)을 직접 그려 만든다. 우리 팩(`rustport`)에 들어가므로 공개 저장소에 백업해도 된다.

```sh
python3 -I tools/crops/make_crops.py \
  ~/mc-server-dev/plugins/ItemsAdder/contents/rustport \
  ~/mc-server-dev/plugins/CustomCrops/contents/crops
```

만드는 것 (작물마다):

| 종류 | 위치 | 내용 |
|---|---|---|
| 그림 16x16 | `rustport/.../textures/item/crop/<작물>/` | 씨앗, 수확물, 은별·금별(직접 그린 별을 오른쪽 아래에 얹음) |
| 성장 단계 그림·모델 | `textures/block/crop/<작물>/stage_1~4`, `models/block/crop/<작물>/` | 바닐라 X자 모델(`block/cross`) |
| ItemsAdder 정의 | `rustport/configs/crops.yml` | 씨앗·수확물 아이템, 성장 단계 블록(철사 블록 `REAL_WIRE`) |
| CustomCrops 작물 | `CustomCrops/contents/crops/<작물>.yml` | 4단계, 물이 있어야 자람, 시들지 않음, 계절·까마귀 없음, 수확 시 품질 작물 + 씨앗 1~2개 |

새 작물을 넣으면 BrassField `config.yml`의 `crop-shop.crops`에 `"rustport:<작물>"`로 가격을 추가해야 거래기에서 팔고 씨앗을 살 수 있다.

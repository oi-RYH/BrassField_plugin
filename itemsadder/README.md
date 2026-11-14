# ItemsAdder 콘텐츠 백업

서버의 `plugins/ItemsAdder/`에서 BrassField가 쓰는 콘텐츠와 설정을 복사해 둔 곳이다. 원본은 서버 폴더이고, 이 폴더는 백업본이다.

| 경로 | 내용 |
|---|---|
| `contents/rustport/` | 강화 GUI 배경·글자 보드, 강화석 상자·아이콘, 재화 사이드바 그림 |
| `contents/customitem/` | 강화 단계별 검 모델·텍스처 |
| `contents/customfood/` | 요리 아이템 (초기) |
| `config.yml`, `ia_gui.yml`, `lang/` | ItemsAdder 설정 |

## 백업 (서버 → 저장소)

```sh
tools/itemsadder/backup.sh
```

`secret.yml`(비밀값), `storage/`·`output/`·`lib/`(실행 중 생성), `contents/_iainternal/`(ItemsAdder 내장)은 복사하지 않는다.
`contents/customcrops/`(CustomCrops 구매자용 리소스팩)는 약관상 재배포 금지라 이 공개 저장소에 올리지 않는다.
이 저장소는 공개 저장소라 백업 전에 새 설정에 비밀값이 없는지 확인한다.

## 복원 (저장소 → 서버)

서버를 끈 상태에서 필요한 폴더만 되돌린 뒤 `/iazip` 한다.

```sh
rsync -a itemsadder/contents/rustport/ ~/mc-server-dev/plugins/ItemsAdder/contents/rustport/
```

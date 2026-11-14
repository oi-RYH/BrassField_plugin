#!/bin/sh
# 서버의 ItemsAdder 콘텐츠·설정을 이 저장소의 itemsadder/ 로 복사한다. (서버 → 저장소 한 방향)
# 사용: tools/itemsadder/backup.sh [ItemsAdder 폴더]   기본값: ~/mc-server-dev/plugins/ItemsAdder
#
# 비밀값(secret.yml)과 실행 중 생성되는 것(storage, output, lib), ItemsAdder 내장 콘텐츠(_iainternal)는 복사하지 않는다.
# 이 저장소는 공개 저장소이므로, 새 설정 파일을 추가할 때 비밀값이 들어가지 않았는지 확인한다.
set -eu

SRC="${1:-$HOME/mc-server-dev/plugins/ItemsAdder}"
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
DEST="$REPO/itemsadder"

if [ ! -f "$SRC/config.yml" ]; then
    echo "ItemsAdder 폴더를 찾을 수 없습니다: $SRC" >&2
    exit 1
fi

mkdir -p "$DEST"
rsync -a --delete \
    --exclude '.DS_Store' \
    --include 'config.yml' \
    --include 'ia_gui.yml' \
    --include 'lang/***' \
    --include 'contents/' \
    --exclude 'contents/_iainternal/' \
    --include 'contents/***' \
    --exclude '*' \
    "$SRC/" "$DEST/"

echo "백업 완료: $SRC → $DEST"
git -C "$REPO" status --short -- itemsadder | head -20

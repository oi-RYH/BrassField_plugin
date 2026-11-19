package com.brassfield.enhancement;

import com.brassfield.stone.StoneGrade;

/**
 * 강화 한 단계에서 다음 단계로 시도할 때의 확률과 비용. 마지막 단계는 시도할 수 없으므로 확률이 모두 0이다.
 *
 * @param level           현재 단계
 * @param successChance   성공(다음 단계) 확률 %
 * @param downgradeChance 하락(이전 단계) 확률 %
 * @param maintainChance  유지 확률 %
 * @param stoneGrade      필요한 강화석 등급 (END 면 재화가 아님)
 * @param stoneCost       필요한 강화석 개수
 */
public record EnhanceStep(
        int level,
        double successChance,
        double downgradeChance,
        double maintainChance,
        StoneGrade stoneGrade,
        int stoneCost
) {
}

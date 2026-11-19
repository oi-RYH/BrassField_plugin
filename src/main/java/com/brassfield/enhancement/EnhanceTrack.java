package com.brassfield.enhancement;

import org.bukkit.inventory.ItemStack;

/**
 * 강화 종류 하나 (무기 · 방어구 부위 · 장신구 ...). 강화 GUI · 서비스는 이 인터페이스만 보고 동작한다.
 * 아이템이 어떤 종류인지와 단계는 {@link EnhanceTracks} 가 아이템 데이터(PDC)로 판별한다.
 */
public interface EnhanceTrack {

    /** 아이템 데이터에 저장하는 종류 이름 (예: "weapon") — 한 번 정하면 바꾸지 않는다 */
    String key();

    /** 사람에게 보이는 종류 이름 (예: "무기") */
    String displayName();

    int maxLevel();

    /** level 에서 다음 단계로 시도할 때의 확률 · 비용 */
    EnhanceStep step(int level);

    /**
     * 강화 결과를 원래 아이템에 적용한 새 아이템. 단계 외의 데이터(장신구 옵션 등)는 원래 아이템에서 이어받는다.
     */
    ItemStack applyLevel(ItemStack original, int newLevel);

    /**
     * 아직 강화 데이터가 없지만 이 종류의 시작 아이템인지 (예: 커스텀 아이템 막대기). 기본은 아니다
     */
    default boolean isFreshItem(ItemStack item) {
        return false;
    }
}

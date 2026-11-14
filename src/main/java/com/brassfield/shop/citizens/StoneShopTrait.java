package com.brassfield.shop.citizens;

import net.citizensnpcs.api.trait.Trait;
import net.citizensnpcs.api.trait.TraitName;

/**
 * 이 trait이 붙은 Citizens NPC를 우클릭하면 강화석 상점이 열린다.
 * 사용법: /npc create 강화석상인 → /trait stoneshop
 * 표시만 하는 trait이라 저장할 데이터는 없다. 상점 동작은 CitizensShopListener가 처리한다.
 */
@TraitName("stoneshop")
public final class StoneShopTrait extends Trait {

    public StoneShopTrait() {
        super("stoneshop");
    }
}

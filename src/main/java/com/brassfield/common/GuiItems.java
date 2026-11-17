package com.brassfield.common;

import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;

/**
 * 창 아이템 공통 도우미.
 */
public final class GuiItems {

    private GuiItems() {
    }

    /**
     * 작동하지 않는 빈칸 아이템: 마우스를 올려도 설명창(고급 설명의 아이템 ID 줄까지)이 아예 뜨지 않게 한다.
     */
    public static ItemStack hideTooltip(ItemStack item) {
        ItemMeta meta = item.getItemMeta();
        meta.setHideTooltip(true);
        item.setItemMeta(meta);
        return item;
    }
}

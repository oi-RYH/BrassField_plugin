package com.brassfield.enhancement;

import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;

/**
 * 강화 창이 고르는 "칸": 0~40 = 플레이어 가방 칸, EXTRA_FIRST 부터 = 가방 밖에 착용한 장비 (장신구 장착 칸 등).
 * 가방 밖 칸은 플러그인이 {@link #extra(Extra)} 로 연결한다 (enhancement 패키지가 장신구 코드를 몰라도 되게).
 */
public final class EnhanceSlots {

    public static final int EXTRA_FIRST = 100;
    public static final int LAST_INVENTORY_SLOT = 40;

    /** 가방 밖 착용 칸 */
    public interface Extra {
        ItemStack[] items(Player player);

        void set(Player player, int index, ItemStack item);
    }

    private static Extra extra;

    private EnhanceSlots() {
    }

    public static void extra(Extra provider) {
        extra = provider;
    }

    public static boolean isExtra(int slot) {
        return slot >= EXTRA_FIRST;
    }

    public static ItemStack get(Player player, int slot) {
        if (!isExtra(slot)) {
            return player.getInventory().getItem(slot);
        }
        ItemStack[] items = extra == null ? new ItemStack[0] : extra.items(player);
        int index = slot - EXTRA_FIRST;
        return index < items.length ? items[index] : null;
    }

    public static void set(Player player, int slot, ItemStack item) {
        if (!isExtra(slot)) {
            player.getInventory().setItem(slot, item);
        } else if (extra != null) {
            extra.set(player, slot - EXTRA_FIRST, item);
        }
    }

    /** 가방 밖 착용 칸 수 */
    public static int extraCount(Player player) {
        return extra == null ? 0 : extra.items(player).length;
    }
}

package com.rustport.enhancement;

import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;

public final class ItemDelivery {

    private ItemDelivery() {
    }

    public static void giveOrDrop(Player player, ItemStack item) {
        player.getInventory().addItem(item).values().forEach(leftover ->
                player.getWorld().dropItemNaturally(player.getLocation(), leftover)
        );
    }
}

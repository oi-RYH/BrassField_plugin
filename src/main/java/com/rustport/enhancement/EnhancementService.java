package com.rustport.enhancement;

import org.bukkit.inventory.ItemStack;

import java.util.concurrent.ThreadLocalRandom;

public final class EnhancementService {

    private static final double SUCCESS_CHANCE = 0.5;

    public EnhancementResult enhance(ItemStack item) {
        int currentLevel = EnhancementItem.getLevel(item);
        boolean success = ThreadLocalRandom.current().nextDouble() < SUCCESS_CHANCE;
        int newLevel = success ? currentLevel + 1 : Math.max(0, currentLevel - 1);
        return new EnhancementResult(success, newLevel, EnhancementItem.buildItem(item, newLevel));
    }

    public record EnhancementResult(boolean success, int level, ItemStack item) {
    }
}

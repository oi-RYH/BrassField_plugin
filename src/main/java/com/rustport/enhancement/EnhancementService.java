package com.rustport.enhancement;

import org.bukkit.inventory.ItemStack;

import java.util.concurrent.ThreadLocalRandom;

public final class EnhancementService {

    public EnhancementResult enhance(ItemStack item) {
        int currentLevel = EnhancementItem.getLevel(item);
        EnhancementItem.EnhancementTier tier = EnhancementItem.getTier(currentLevel);
        double roll = ThreadLocalRandom.current().nextDouble(100.0);

        Outcome outcome;
        int newLevel;
        if (roll < tier.successChance()) {
            outcome = Outcome.SUCCESS;
            newLevel = currentLevel + 1;
        } else if (roll < tier.successChance() + tier.downgradeChance()) {
            outcome = Outcome.DOWNGRADE;
            newLevel = Math.max(0, currentLevel - 1);
        } else {
            outcome = Outcome.MAINTAIN;
            newLevel = currentLevel;
        }

        return new EnhancementResult(outcome, newLevel, EnhancementItem.buildItem(newLevel));
    }

    public enum Outcome {
        SUCCESS,
        DOWNGRADE,
        MAINTAIN
    }

    public record EnhancementResult(Outcome outcome, int level, ItemStack item) {
    }
}

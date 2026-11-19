package com.brassfield.enhancement;

import org.bukkit.inventory.ItemStack;

import java.util.concurrent.ThreadLocalRandom;

/**
 * 강화 한 번 굴리기. 아이템의 강화 종류({@link EnhanceTrack})에 맞는 확률로 성공 · 하락 · 유지를 정하고 결과 아이템을 만든다.
 */
public final class EnhancementService {

    public EnhancementResult enhance(ItemStack item) {
        EnhanceTrack track = EnhanceTracks.trackOf(item)
                .orElseThrow(() -> new IllegalArgumentException("강화할 수 없는 아이템입니다"));
        int currentLevel = EnhanceTracks.levelOf(item);
        EnhanceStep step = track.step(currentLevel);
        double roll = ThreadLocalRandom.current().nextDouble(100.0);

        Outcome outcome;
        int newLevel;
        if (roll < step.successChance()) {
            outcome = Outcome.SUCCESS;
            newLevel = currentLevel + 1;
        } else if (roll < step.successChance() + step.downgradeChance()) {
            outcome = Outcome.DOWNGRADE;
            newLevel = Math.max(0, currentLevel - 1);
        } else {
            outcome = Outcome.MAINTAIN;
            newLevel = currentLevel;
        }

        return new EnhancementResult(outcome, newLevel, track.applyLevel(item, newLevel));
    }

    public enum Outcome {
        SUCCESS,
        DOWNGRADE,
        MAINTAIN
    }

    public record EnhancementResult(Outcome outcome, int level, ItemStack item) {
    }
}

package com.brassfield.accessory;

import com.brassfield.accessory.AccessoryKind.Grade;
import com.brassfield.enhancement.EnhanceStep;
import com.brassfield.enhancement.EnhanceTrack;
import com.brassfield.enhancement.EnhanceTracks;
import com.brassfield.stone.StoneGrade;
import org.bukkit.inventory.ItemStack;

import java.util.EnumMap;
import java.util.Map;

/**
 * 장신구 강화 (등급마다 하나, 키 "accessory_{등급}"). 노션 "악세사리 시스템" 2026-11-20 확정 — 장신구는 강화가 어렵다.
 * <ul>
 *   <li>등급 안 0 → 3강: 일반 80 · 65 · 50% / 레어 70 · 55 · 40% / 영웅 60 · 45 · 30% / 전설 50 · 35 · 20%</li>
 *   <li>3강 → 다음 등급 0강 (승급): 일반→레어 5% · 레어→영웅 1% · 영웅→전설 0.1%. 전설 3강이 끝</li>
 *   <li>실패하면 단계 유지 (하락 · 파괴 없음)</li>
 * </ul>
 * 승급은 강화 단계 4 로 다룬다: maxLevel = 4 (전설은 3), applyLevel(…, 4) = 다음 등급 0강.
 * 강화석 비용은 잠정 (승급 = 그 등급 2→3강 비용의 2배).
 */
public final class AccessoryTrack implements EnhanceTrack {

    private static final Map<Grade, AccessoryTrack> BY_GRADE = new EnumMap<>(Grade.class);

    private static final double[][] SUCCESS = {{80, 65, 50}, {70, 55, 40}, {60, 45, 30}, {50, 35, 20}};
    private static final double[] PROMOTION = {5, 1, 0.1};
    private static final StoneGrade[] STONE = {StoneGrade.LOW, StoneGrade.MIDDLE, StoneGrade.MIDDLE, StoneGrade.HIGH};
    private static final int[][] COST = {{20, 40, 60}, {10, 20, 30}, {30, 45, 60}, {10, 20, 30}};

    private final Grade grade;

    private AccessoryTrack(Grade grade) {
        this.grade = grade;
    }

    /** 네 등급 강화를 강화 등록부에 올린다 (EnhanceTracks.init 뒤에) */
    public static void registerAll() {
        BY_GRADE.clear();
        for (Grade grade : Grade.values()) {
            AccessoryTrack track = new AccessoryTrack(grade);
            BY_GRADE.put(grade, track);
            EnhanceTracks.register(track);
        }
    }

    static AccessoryTrack of(Grade grade) {
        return BY_GRADE.get(grade);
    }

    private boolean canPromote() {
        return grade.ordinal() < Grade.values().length - 1;
    }

    @Override
    public String key() {
        return "accessory_" + grade.id();
    }

    @Override
    public String displayName() {
        return grade.displayName() + " 장신구";
    }

    @Override
    public int maxLevel() {
        return canPromote() ? AccessoryKind.MAX_LEVEL + 1 : AccessoryKind.MAX_LEVEL;
    }

    @Override
    public boolean isPromotion(int level) {
        return level == AccessoryKind.MAX_LEVEL && canPromote();
    }

    @Override
    public EnhanceStep step(int level) {
        int g = grade.ordinal();
        if (level < AccessoryKind.MAX_LEVEL) {
            double success = SUCCESS[g][level];
            return new EnhanceStep(level, success, 0, 100 - success, STONE[g], COST[g][level]);
        }
        if (isPromotion(level)) {
            double success = PROMOTION[g];
            return new EnhanceStep(level, success, 0, 100 - success, STONE[g], COST[g][AccessoryKind.MAX_LEVEL - 1] * 2);
        }
        return new EnhanceStep(level, 0, 0, 0, StoneGrade.END, 0);
    }

    @Override
    public ItemStack applyLevel(ItemStack original, int newLevel) {
        Accessories.Info info = Accessories.read(original).orElseThrow(() -> new IllegalArgumentException("장신구가 아닙니다"));
        if (newLevel > AccessoryKind.MAX_LEVEL && canPromote()) {      // 승급: 같은 세트 · 종류의 다음 등급 0강
            Grade next = Grade.values()[grade.ordinal() + 1];
            return Accessories.create(new Accessories.Info(info.set(), info.variant(), next, 0));
        }
        int level = Math.max(0, Math.min(AccessoryKind.MAX_LEVEL, newLevel));
        return Accessories.create(new Accessories.Info(info.set(), info.variant(), grade, level));
    }

    @Override
    public int freshLevel(ItemStack item) {
        return Accessories.read(item).map(Accessories.Info::level).orElse(0);
    }

    /** 강화 기록(enhance_track)이 붙기 전에 만든 장신구도 강화 대상으로 본다 */
    @Override
    public boolean isFreshItem(ItemStack item) {
        return Accessories.read(item).map(info -> info.grade() == grade).orElse(false);
    }
}

package com.brassfield.accessory;

import com.brassfield.accessory.AccessoryKind.Grade;
import com.brassfield.accessory.AccessoryKind.Set;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ThreadLocalRandom;

/**
 * 장신구 보조옵션 (노션 "악세사리 시스템" 2026-11-21: 기본옵션 없음, 보조옵션 칸 일반 1 · 레어 2 · 영웅 3 · 전설 4).
 * 세트마다 나오는 옵션이 다르다. 수치는 등급별 [최소, 최대] 에서 굴리고(잠정), 강화 1단계마다 +10% (3강 = +30%).
 * 장착한 장신구끼리는 합산하고 CAP 을 넘지 않는다. 한 장신구 안에서는 같은 옵션이 겹치지 않는다.
 */
public enum AccessoryOption {

    // 전투
    ATTACK("attack", "공격력", "%", Set.COMBAT, 40, new double[][]{{1, 2}, {1.5, 3}, {2.5, 4}, {3.5, 5}}),
    CRIT_CHANCE("crit_chance", "치명타 확률", "%", Set.COMBAT, 50, new double[][]{{1, 3}, {2, 4}, {3, 5}, {4, 6}}),
    CRIT_DAMAGE("crit_damage", "치명타 피해", "%", Set.COMBAT, 200, new double[][]{{5, 10}, {8, 14}, {12, 18}, {16, 24}}),
    BLEED("bleed", "출혈 확률", "%", Set.COMBAT, 40, new double[][]{{2, 4}, {3, 5}, {4, 7}, {6, 9}}),
    ATTACK_SPEED("attack_speed", "공격 속도", "%", Set.COMBAT, 30, new double[][]{{2, 4}, {3, 5}, {4, 6}, {5, 8}}),
    // 요리/농사
    MAX_HEALTH("max_health", "최대 체력", "", Set.FARM, 20, new double[][]{{1, 2}, {2, 3}, {3, 4}, {4, 5}}),
    HEAL_ON_HIT("heal_on_hit", "피격 시 회복 확률", "%", Set.FARM, 30, new double[][]{{2, 4}, {3, 5}, {4, 6}, {5, 8}}),
    FOOD_BUFF("food_buff", "요리 효과 지속", "%", Set.FARM, 100, new double[][]{{5, 10}, {8, 14}, {12, 18}, {16, 24}}),
    HARVEST("harvest", "수확 1개 더 확률", "%", Set.FARM, 50, new double[][]{{3, 6}, {5, 8}, {7, 11}, {10, 14}}),
    // 생활/모험
    SPEED("speed", "이동 속도", "%", Set.ADVENTURE, 30, new double[][]{{2, 4}, {3, 5}, {4, 6}, {5, 8}}),
    FALL_REDUCTION("fall_reduction", "낙하 피해 감소", "%", Set.ADVENTURE, 80, new double[][]{{5, 10}, {8, 14}, {12, 18}, {16, 24}}),
    EXP("exp", "경험치 획득", "%", Set.ADVENTURE, 100, new double[][]{{3, 6}, {5, 8}, {7, 11}, {10, 14}}),
    DAMAGE_REDUCTION("damage_reduction", "받는 피해 감소", "%", Set.ADVENTURE, 20, new double[][]{{1, 2}, {1.5, 2.5}, {2, 3}, {2.5, 4}});

    /** 강화 1단계마다 보조옵션 수치 배율 */
    public static final double PER_LEVEL = 0.10;

    private final String id;
    private final String displayName;
    private final String unit;
    private final Set set;
    private final double cap;
    private final double[][] range;

    AccessoryOption(String id, String displayName, String unit, Set set, double cap, double[][] range) {
        this.id = id;
        this.displayName = displayName;
        this.unit = unit;
        this.set = set;
        this.cap = cap;
        this.range = range;
    }

    public String id() {
        return id;
    }

    public String displayName() {
        return displayName;
    }

    public String unit() {
        return unit;
    }

    public Set set() {
        return set;
    }

    public double cap() {
        return cap;
    }

    public static AccessoryOption byId(String id) {
        for (AccessoryOption option : values()) {
            if (option.id.equals(id)) {
                return option;
            }
        }
        return null;
    }

    /** 등급 칸 수: 일반 1 · 레어 2 · 영웅 3 · 전설 4 */
    public static int slots(Grade grade) {
        return grade.ordinal() + 1;
    }

    /** 이 등급 범위에서 0.1 단위로 굴린 값 */
    public double roll(Grade grade) {
        double[] r = range[grade.ordinal()];
        double value = r[0] + ThreadLocalRandom.current().nextDouble() * (r[1] - r[0]);
        return Math.round(value * 10) / 10.0;
    }

    /** 한 줄: 옵션과 굴린 값 (강화 전 값) */
    public record Roll(AccessoryOption option, double base) {
        public double value(int level) {
            return Math.round(base * (1 + PER_LEVEL * level) * 10) / 10.0;
        }
    }

    /** 세트 · 등급에 맞춰 빈 칸을 채운다 (이미 있는 옵션은 두고, 겹치지 않게) */
    public static List<Roll> fill(Set set, Grade grade, List<Roll> existing) {
        List<Roll> rolls = new ArrayList<>(existing);
        List<AccessoryOption> pool = new ArrayList<>();
        for (AccessoryOption option : values()) {
            if (option.set == set && rolls.stream().noneMatch(r -> r.option() == option)) {
                pool.add(option);
            }
        }
        while (rolls.size() < slots(grade) && !pool.isEmpty()) {
            AccessoryOption pick = pool.remove(ThreadLocalRandom.current().nextInt(pool.size()));
            rolls.add(new Roll(pick, pick.roll(grade)));
        }
        return rolls;
    }
}

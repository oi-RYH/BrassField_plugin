package com.brassfield.stone;

import net.kyori.adventure.text.format.NamedTextColor;

/**
 * 강화석 등급. 필요 개수 = 기본 + 추가 초기값 + 공차 × (등급 안에서의 순번, 0부터).
 * END는 최고 단계 표시용이라 강화석 재화가 아니다.
 */
public enum StoneGrade {
    LOW("하급", NamedTextColor.GRAY, 0, 10, 0, 1),
    MIDDLE("중급", NamedTextColor.AQUA, 9, 30, 5, 3),
    HIGH("상급", NamedTextColor.GOLD, 17, 70, 10, 5),
    END("엔드", NamedTextColor.LIGHT_PURPLE, 25, 0, 0, 0);

    private final String displayName;
    private final NamedTextColor color;
    private final int firstLevel;
    private final int baseCost;
    private final int extraStart;
    private final int extraStep;

    StoneGrade(String displayName, NamedTextColor color, int firstLevel, int baseCost, int extraStart, int extraStep) {
        this.displayName = displayName;
        this.color = color;
        this.firstLevel = firstLevel;
        this.baseCost = baseCost;
        this.extraStart = extraStart;
        this.extraStep = extraStep;
    }

    public String displayName() {
        return displayName;
    }

    public NamedTextColor color() {
        return color;
    }

    public int firstLevel() {
        return firstLevel;
    }

    public boolean isCurrency() {
        return this != END;
    }

    public int costAt(int level) {
        if (!isCurrency()) {
            return 0;
        }
        return baseCost + extraStart + extraStep * (level - firstLevel);
    }

    public static StoneGrade fromDisplayName(String name) {
        for (StoneGrade grade : values()) {
            if (grade.isCurrency() && grade.displayName.equals(name)) {
                return grade;
            }
        }
        return null;
    }
}

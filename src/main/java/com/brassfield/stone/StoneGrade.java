package com.brassfield.stone;

import net.kyori.adventure.text.format.TextColor;

/**
 * 강화석 등급. 필요 개수 = 기본 + 추가 초기값 + 공차 × (등급 안에서의 순번, 0부터).
 * END는 최고 단계 표시용이라 강화석 재화가 아니다.
 */
public enum StoneGrade {
    // 색은 강화석 그림(같은 호박색 결정이 커짐)에 맞춘다: 철 회색 → 호박색 → 불꽃 주황. 엔드는 마스터소드 전용 표시.
    LOW("하급", TextColor.color(190, 180, 166), 0, 10, 0, 1),
    MIDDLE("중급", TextColor.color(255, 200, 90), 9, 30, 5, 3),
    HIGH("상급", TextColor.color(255, 120, 40), 17, 70, 10, 5),
    END("엔드", TextColor.color(255, 85, 255), 25, 0, 0, 0);

    private final String displayName;
    private final TextColor color;
    private final int firstLevel;
    private final int baseCost;
    private final int extraStart;
    private final int extraStep;

    StoneGrade(String displayName, TextColor color, int firstLevel, int baseCost, int extraStart, int extraStep) {
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

    public TextColor color() {
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

    /**
     * GUI에 강화석을 보여줄 때 쓰는 ItemsAdder 표시 전용 아이콘 ID. 재화가 아니면 null.
     */
    public String iconItemId() {
        return switch (this) {
            case LOW -> "rustport:low_stone_icon";
            case MIDDLE -> "rustport:mid_stone_icon";
            case HIGH -> "rustport:high_stone_icon";
            case END -> null;
        };
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

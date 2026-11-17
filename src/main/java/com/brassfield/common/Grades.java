package com.brassfield.common;

/**
 * 작물·요리 등급 (아이템 ID 끝): 일반 0 · 은별 1 ("_silver_star") · 금별 2 ("_golden_star").
 */
public final class Grades {

    public static final String[] SUFFIXES = {"", "_silver_star", "_golden_star"};
    public static final String[] NAMES = {"일반", "은별", "금별"};

    private Grades() {
    }

    public static int of(String id) {
        if (id == null) {
            return 0;
        }
        return id.endsWith(SUFFIXES[2]) ? 2 : id.endsWith(SUFFIXES[1]) ? 1 : 0;
    }

    /** 등급 표시를 뗀 기본 ID */
    public static String base(String id) {
        int grade = of(id);
        return grade == 0 ? id : id.substring(0, id.length() - SUFFIXES[grade].length());
    }

    public static String withGrade(String baseId, int grade) {
        return baseId + SUFFIXES[Math.max(0, Math.min(2, grade))];
    }
}

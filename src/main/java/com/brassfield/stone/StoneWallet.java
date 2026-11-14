package com.brassfield.stone;

import com.brassfield.common.BalanceBook;

import java.util.UUID;

/**
 * 플레이어별 강화석 보유량(재화). 아이템이 아니라 골드처럼 숫자로만 관리한다. (설계 결정 DR-07)
 * 강화석 모듈의 공개 API: 다른 모듈은 이 클래스로만 강화석을 확인·지급·차감한다.
 */
public final class StoneWallet {

    private final BalanceBook book;

    public StoneWallet(BalanceBook book) {
        this.book = book;
    }

    public long get(UUID playerId, StoneGrade grade) {
        return book.get(playerId, key(grade));
    }

    public boolean has(UUID playerId, StoneGrade grade, long amount) {
        return get(playerId, grade) >= amount;
    }

    public void deposit(UUID playerId, StoneGrade grade, long amount) {
        book.deposit(playerId, key(grade), amount);
    }

    /**
     * 보유량이 충분하면 차감하고 true, 부족하면 아무것도 바꾸지 않고 false를 돌려준다.
     */
    public boolean withdraw(UUID playerId, StoneGrade grade, long amount) {
        return book.withdraw(playerId, key(grade), amount);
    }

    public void set(UUID playerId, StoneGrade grade, long amount) {
        book.set(playerId, key(grade), amount);
    }

    private static String key(StoneGrade grade) {
        if (!grade.isCurrency()) {
            throw new IllegalArgumentException("재화가 아닌 강화석 등급입니다: " + grade);
        }
        return grade.name();
    }
}

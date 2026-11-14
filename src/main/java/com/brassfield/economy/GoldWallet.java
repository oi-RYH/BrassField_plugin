package com.brassfield.economy;

import com.brassfield.common.BalanceBook;

import java.util.UUID;

/**
 * 플레이어별 골드 보유량. 경제 모듈의 공개 API: 다른 모듈은 이 클래스로만 골드를 확인·지급·차감한다.
 * 나중에 Vault 연동이 필요해지면 이 클래스를 감싸는 Economy 구현을 추가한다.
 */
public final class GoldWallet {

    private static final String CURRENCY = "GOLD";

    private final BalanceBook book;

    public GoldWallet(BalanceBook book) {
        this.book = book;
    }

    public long get(UUID playerId) {
        return book.get(playerId, CURRENCY);
    }

    public boolean has(UUID playerId, long amount) {
        return get(playerId) >= amount;
    }

    public void deposit(UUID playerId, long amount) {
        book.deposit(playerId, CURRENCY, amount);
    }

    /**
     * 보유량이 충분하면 차감하고 true, 부족하면 아무것도 바꾸지 않고 false를 돌려준다.
     */
    public boolean withdraw(UUID playerId, long amount) {
        return book.withdraw(playerId, CURRENCY, amount);
    }

    public void set(UUID playerId, long amount) {
        book.set(playerId, CURRENCY, amount);
    }
}

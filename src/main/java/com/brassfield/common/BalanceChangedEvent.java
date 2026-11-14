package com.brassfield.common;

import org.bukkit.event.Event;
import org.bukkit.event.HandlerList;
import org.jetbrains.annotations.NotNull;

import java.util.UUID;

/**
 * 재화 보유량이 바뀌었을 때 발행된다. (골드·강화석 공통)
 * 재화를 보여주는 쪽(HUD 등)은 재화 모듈을 직접 부르지 않고 이 이벤트를 구독해 반응한다.
 */
public final class BalanceChangedEvent extends Event {

    private static final HandlerList HANDLERS = new HandlerList();

    private final UUID playerId;
    private final String bookName;
    private final String currency;
    private final long amount;

    public BalanceChangedEvent(UUID playerId, String bookName, String currency, long amount) {
        this.playerId = playerId;
        this.bookName = bookName;
        this.currency = currency;
        this.amount = amount;
    }

    public UUID getPlayerId() {
        return playerId;
    }

    /**
     * 재화 장부 이름 (예: "Gold", "Stone")
     */
    public String getBookName() {
        return bookName;
    }

    /**
     * 장부 안의 재화 키 (예: "GOLD", "LOW")
     */
    public String getCurrency() {
        return currency;
    }

    public long getAmount() {
        return amount;
    }

    @Override
    public @NotNull HandlerList getHandlers() {
        return HANDLERS;
    }

    public static HandlerList getHandlerList() {
        return HANDLERS;
    }
}

package com.brassfield.common;

import org.bukkit.Bukkit;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.logging.Logger;

/**
 * 플레이어별 재화 장부. 강화석·골드처럼 아이템이 아니라 숫자로만 관리하는 재화가 공통으로 쓴다.
 * 보유량은 메인 스레드에서만 읽고 바꾸며, 바뀔 때마다 전용 스레드 하나에서 순서대로 파일에 저장하고
 * BalanceChangedEvent를 발행한다.
 */
public final class BalanceBook {

    private final BalanceStorage storage;
    private final Logger logger;
    private final Map<UUID, Map<String, Long>> balances = new HashMap<>();
    private final ExecutorService saveExecutor;
    private final String name;

    public BalanceBook(BalanceStorage storage, Logger logger, String name) {
        this.storage = storage;
        this.logger = logger;
        this.name = name;
        this.saveExecutor = Executors.newSingleThreadExecutor(runnable -> {
            Thread thread = new Thread(runnable, "BrassField-" + name + "Save");
            thread.setDaemon(true);
            return thread;
        });
        balances.putAll(storage.loadAll());
    }

    public long get(UUID playerId, String currency) {
        Map<String, Long> playerBalances = balances.get(playerId);
        return playerBalances == null ? 0L : playerBalances.getOrDefault(currency, 0L);
    }

    public void deposit(UUID playerId, String currency, long amount) {
        requirePositive(amount);
        set(playerId, currency, Math.addExact(get(playerId, currency), amount));
    }

    /**
     * 보유량이 충분하면 차감하고 true, 부족하면 아무것도 바꾸지 않고 false를 돌려준다.
     */
    public boolean withdraw(UUID playerId, String currency, long amount) {
        requirePositive(amount);
        long current = get(playerId, currency);
        if (current < amount) {
            return false;
        }
        set(playerId, currency, current - amount);
        return true;
    }

    public void set(UUID playerId, String currency, long amount) {
        if (amount < 0) {
            throw new IllegalArgumentException("보유량은 음수가 될 수 없습니다: " + amount);
        }
        balances.computeIfAbsent(playerId, id -> new HashMap<>()).put(currency, amount);
        scheduleSave();
        Bukkit.getPluginManager().callEvent(new BalanceChangedEvent(playerId, name, currency, amount));
    }

    /**
     * 남은 저장 작업을 마치고 마지막 상태를 한 번 더 저장한다. 플러그인 종료 시 호출.
     */
    public void shutdown() {
        saveExecutor.shutdown();
        try {
            if (!saveExecutor.awaitTermination(5, TimeUnit.SECONDS)) {
                logger.warning("재화 저장 작업이 제때 끝나지 않았습니다.");
            }
        } catch (InterruptedException exception) {
            Thread.currentThread().interrupt();
        }
        storage.saveAll(snapshot());
    }

    private void scheduleSave() {
        Map<UUID, Map<String, Long>> snapshot = snapshot();
        saveExecutor.execute(() -> storage.saveAll(snapshot));
    }

    private Map<UUID, Map<String, Long>> snapshot() {
        Map<UUID, Map<String, Long>> copy = new HashMap<>();
        balances.forEach((playerId, playerBalances) -> copy.put(playerId, new HashMap<>(playerBalances)));
        return copy;
    }

    private static void requirePositive(long amount) {
        if (amount <= 0) {
            throw new IllegalArgumentException("수량은 1 이상이어야 합니다: " + amount);
        }
    }
}

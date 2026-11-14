package com.brassfield.stone;

import java.util.EnumMap;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.logging.Logger;

/**
 * 플레이어별 강화석 보유량(재화). 아이템이 아니라 골드처럼 숫자로만 관리한다. (설계 결정 DR-07)
 * 보유량은 메인 스레드에서만 읽고 바꾸며, 바뀔 때마다 전용 스레드 하나에서 순서대로 파일에 저장한다.
 */
public final class StoneWallet {

    private final StoneStorage storage;
    private final Logger logger;
    private final Map<UUID, EnumMap<StoneGrade, Long>> balances = new HashMap<>();
    private final ExecutorService saveExecutor = Executors.newSingleThreadExecutor(runnable -> {
        Thread thread = new Thread(runnable, "BrassField-StoneSave");
        thread.setDaemon(true);
        return thread;
    });

    public StoneWallet(StoneStorage storage, Logger logger) {
        this.storage = storage;
        this.logger = logger;
        balances.putAll(storage.loadAll());
    }

    public long get(UUID playerId, StoneGrade grade) {
        requireCurrency(grade);
        EnumMap<StoneGrade, Long> playerBalances = balances.get(playerId);
        return playerBalances == null ? 0L : playerBalances.getOrDefault(grade, 0L);
    }

    public boolean has(UUID playerId, StoneGrade grade, long amount) {
        return get(playerId, grade) >= amount;
    }

    public void deposit(UUID playerId, StoneGrade grade, long amount) {
        requirePositive(amount);
        set(playerId, grade, Math.addExact(get(playerId, grade), amount));
    }

    /**
     * 보유량이 충분하면 차감하고 true, 부족하면 아무것도 바꾸지 않고 false를 돌려준다.
     */
    public boolean withdraw(UUID playerId, StoneGrade grade, long amount) {
        requirePositive(amount);
        long current = get(playerId, grade);
        if (current < amount) {
            return false;
        }
        set(playerId, grade, current - amount);
        return true;
    }

    public void set(UUID playerId, StoneGrade grade, long amount) {
        requireCurrency(grade);
        if (amount < 0) {
            throw new IllegalArgumentException("강화석 보유량은 음수가 될 수 없습니다: " + amount);
        }
        balances.computeIfAbsent(playerId, id -> new EnumMap<>(StoneGrade.class)).put(grade, amount);
        scheduleSave();
    }

    /**
     * 남은 저장 작업을 마치고 마지막 상태를 한 번 더 저장한다. 플러그인 종료 시 호출.
     */
    public void shutdown() {
        saveExecutor.shutdown();
        try {
            if (!saveExecutor.awaitTermination(5, TimeUnit.SECONDS)) {
                logger.warning("강화석 저장 작업이 제때 끝나지 않았습니다.");
            }
        } catch (InterruptedException exception) {
            Thread.currentThread().interrupt();
        }
        storage.saveAll(snapshot());
    }

    private void scheduleSave() {
        Map<UUID, EnumMap<StoneGrade, Long>> snapshot = snapshot();
        saveExecutor.execute(() -> storage.saveAll(snapshot));
    }

    private Map<UUID, EnumMap<StoneGrade, Long>> snapshot() {
        Map<UUID, EnumMap<StoneGrade, Long>> copy = new HashMap<>();
        balances.forEach((playerId, playerBalances) -> copy.put(playerId, new EnumMap<>(playerBalances)));
        return copy;
    }

    private static void requireCurrency(StoneGrade grade) {
        if (!grade.isCurrency()) {
            throw new IllegalArgumentException("재화가 아닌 강화석 등급입니다: " + grade);
        }
    }

    private static void requirePositive(long amount) {
        if (amount <= 0) {
            throw new IllegalArgumentException("수량은 1 이상이어야 합니다: " + amount);
        }
    }
}

package com.brassfield.common;

import java.util.Map;
import java.util.UUID;

/**
 * 플레이어별 재화 보유량 저장소. 저장 방식(YAML, SQLite 등)을 바꿔도 BalanceBook은 그대로 쓸 수 있게 분리했다.
 * 보유량은 "플레이어 → (재화 키 → 수량)" 형태다.
 */
public interface BalanceStorage {

    Map<UUID, Map<String, Long>> loadAll();

    /**
     * 전체 보유량 스냅샷을 저장한다. 메인 스레드가 아닌 곳에서 호출될 수 있다.
     */
    void saveAll(Map<UUID, Map<String, Long>> snapshot);
}

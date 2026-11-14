package com.rustport.enhancement;

import java.util.EnumMap;
import java.util.Map;
import java.util.UUID;

/**
 * 강화석 보유량 저장소. 저장 방식(YAML, SQLite 등)을 바꿔도 StoneWallet은 그대로 쓸 수 있게 분리했다.
 */
public interface StoneStorage {

    Map<UUID, EnumMap<EnhancementItem.StoneGrade, Long>> loadAll();

    /**
     * 전체 보유량 스냅샷을 저장한다. 메인 스레드가 아닌 곳에서 호출될 수 있다.
     */
    void saveAll(Map<UUID, EnumMap<EnhancementItem.StoneGrade, Long>> snapshot);
}

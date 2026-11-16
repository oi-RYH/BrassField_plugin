package com.brassfield.shop;

import com.brassfield.stone.StoneGrade;
import org.bukkit.configuration.file.FileConfiguration;

import java.util.EnumMap;
import java.util.Map;
import java.util.logging.Logger;

/**
 * config.yml 의 stone-shop.prices: 등급별 강화석 1개 가격(골드).
 */
public final class StoneShopPrices {

    private static final Map<StoneGrade, Long> DEFAULT_PRICES = Map.of(
            StoneGrade.LOW, 1_000L,
            StoneGrade.MIDDLE, 5_000L,
            StoneGrade.HIGH, 10_000L
    );

    private final EnumMap<StoneGrade, Long> prices = new EnumMap<>(StoneGrade.class);

    private StoneShopPrices() {
    }

    public static StoneShopPrices load(FileConfiguration config, Logger logger) {
        StoneShopPrices result = new StoneShopPrices();
        DEFAULT_PRICES.forEach((grade, fallback) -> {
            String path = "stone-shop.prices." + grade.name();
            // getLong(path, def)는 파일에 값이 없으면 플러그인 기본 설정을 보지 않으므로 먼저 확인한다
            long price = config.contains(path) ? config.getLong(path) : fallback;
            if (price <= 0) {
                logger.warning("강화석 가격이 1 미만이라 기본값을 씁니다: " + grade.name() + " = " + price);
                price = fallback;
            }
            result.prices.put(grade, price);
        });
        return result;
    }

    public long priceOf(StoneGrade grade) {
        Long price = prices.get(grade);
        if (price == null) {
            throw new IllegalArgumentException("판매하지 않는 강화석 등급입니다: " + grade);
        }
        return price;
    }
}

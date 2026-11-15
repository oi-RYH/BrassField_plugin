package com.brassfield.market;

import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.configuration.file.FileConfiguration;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.logging.Logger;

/**
 * config.yml 의 crop-shop: 작물 수확물(ItemsAdder ID) → 매입가(골드, 1개).
 * 일반 = 작물 가격, 은별·금별 = 배율, 거대·황금 같은 드문 수확물 = special 배율.
 * 씨앗(customcrops:<ID>_seeds) 판매가는 seed-price.
 */
public final class CropPrices {

    private static final String NAMESPACE = "customcrops:";

    private final Map<String, Long> prices = new HashMap<>();
    private final List<Entry> crops = new ArrayList<>();

    private CropPrices() {
    }

    public static CropPrices load(FileConfiguration config, Logger logger) {
        CropPrices result = new CropPrices();
        ConfigurationSection root = config.getConfigurationSection("crop-shop");
        if (root == null) {
            logger.warning("config.yml에 crop-shop 설정이 없어 작물을 매입할 수 없습니다.");
            return result;
        }
        long silver = root.getLong("quality-multipliers.silver", 2);
        long golden = root.getLong("quality-multipliers.golden", 4);
        long special = root.getLong("quality-multipliers.special", 10);

        ConfigurationSection cropSection = root.getConfigurationSection("crops");
        Map<String, Long> basePrices = new HashMap<>();
        if (cropSection != null) {
            for (String id : cropSection.getKeys(false)) {
                long price = cropSection.getLong(id + ".price");
                if (price <= 0) {
                    logger.warning("작물 가격이 1 미만이라 매입하지 않습니다: " + id);
                    continue;
                }
                String name = cropSection.getString(id + ".name", id);
                long seedPrice = Math.max(1, cropSection.getLong(id + ".seed-price", Math.max(1, price / 2)));
                basePrices.put(id, price);
                result.crops.add(new Entry(id, name, price, price * silver, price * golden, seedPrice));
                result.prices.put(NAMESPACE + id, price);
                result.prices.put(NAMESPACE + id + "_silver_star", price * silver);
                result.prices.put(NAMESPACE + id + "_golden_star", price * golden);
            }
        }

        ConfigurationSection specials = root.getConfigurationSection("special-items");
        if (specials != null) {
            for (String itemId : specials.getKeys(false)) {
                Long base = basePrices.get(specials.getString(itemId, ""));
                if (base == null) {
                    logger.warning("드문 수확물의 작물을 찾을 수 없습니다: " + itemId);
                    continue;
                }
                result.prices.put(itemId, base * special);
            }
        }
        return result;
    }

    /**
     * ItemsAdder ID의 1개 매입가. 매입하지 않는 아이템이면 0.
     */
    public long priceOf(String itemId) {
        return itemId == null ? 0 : prices.getOrDefault(itemId, 0L);
    }

    /**
     * 가격표 표시용 작물 목록 (설정 순서)
     */
    public List<Entry> crops() {
        return Collections.unmodifiableList(crops);
    }

    public record Entry(String id, String name, long normal, long silver, long golden, long seedPrice) {

        public String seedItemId() {
            return NAMESPACE + id + "_seeds";
        }
    }
}

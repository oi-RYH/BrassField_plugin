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
 * 씨앗(<ID>_seeds) 판매가는 seed-price.
 * 작물 ID에 네임스페이스가 없으면 CustomCrops 기본 팩(customcrops:)으로 보고,
 * BrassField 자체 작물은 "rustport:rice" 처럼 네임스페이스까지 적는다.
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
        long silver = longOr(root, "quality-multipliers.silver", 2);
        long golden = longOr(root, "quality-multipliers.golden", 4);
        long special = longOr(root, "quality-multipliers.special", 10);

        ConfigurationSection cropSection = root.getConfigurationSection("crops");
        Map<String, Long> basePrices = new HashMap<>();
        if (cropSection != null) {
            for (String id : cropSection.getKeys(false)) {
                long price = cropSection.getLong(id + ".price");
                if (price <= 0) {
                    logger.warning("작물 가격이 1 미만이라 매입하지 않습니다: " + id);
                    continue;
                }
                String name = cropSection.getString(id + ".name");
                if (name == null) {
                    name = id;
                }
                long seedPrice = Math.max(1, longOr(cropSection, id + ".seed-price", Math.max(1, price / 2)));
                String itemId = id.contains(":") ? id : NAMESPACE + id;
                basePrices.put(id, price);
                result.crops.add(new Entry(itemId, name, price, price * silver, price * golden, seedPrice));
                result.prices.put(itemId, price);
                result.prices.put(itemId + "_silver_star", price * silver);
                result.prices.put(itemId + "_golden_star", price * golden);
            }
        }

        ConfigurationSection specials = root.getConfigurationSection("special-items");
        if (specials != null) {
            for (String itemId : specials.getKeys(false)) {
                String cropId = specials.getString(itemId);
                Long base = cropId == null ? null : basePrices.get(cropId);
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
     * 기본값을 직접 넘기는 getLong(path, def)은 서버 config.yml에 값이 없을 때 플러그인 기본 설정을 보지 않고 def를 돌려준다.
     * (업데이트 직후 새 항목이 아직 파일에 없을 때 틀린 값이 나옴) 그래서 기본 설정까지 포함해 있는지 먼저 확인한다.
     */
    private static long longOr(ConfigurationSection section, String path, long fallback) {
        return section.contains(path) ? section.getLong(path) : fallback;
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

    /**
     * @param itemId 수확물(일반 품질) ItemsAdder ID, 예: customcrops:tomato, rustport:rice
     */
    public record Entry(String itemId, String name, long normal, long silver, long golden, long seedPrice) {

        public String seedItemId() {
            return itemId + "_seeds";
        }
    }
}

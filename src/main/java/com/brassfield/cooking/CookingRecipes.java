package com.brassfield.cooking;

import com.brassfield.common.ItemsAdderItemProvider;
import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.configuration.file.FileConfiguration;
import org.bukkit.inventory.ItemStack;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.logging.Logger;

/**
 * 요리 기기 하나의 레시피 목록 (config.yml 의 cooking.stations.&lt;기기&gt;.recipes) 과 기기들이 함께 쓰는 재료 묶음 (cooking.groups).
 * <ul>
 *   <li>재료는 "namespace:id" (바닐라는 minecraft:carrot 처럼) 또는 "#묶음" (구운 고기 아무거나 등).</li>
 *   <li>작물 품질(은별·금별)은 구분하지 않는다: customcrops:tomato_golden_star 도 customcrops:tomato 로 본다.</li>
 *   <li>재료 칸에 든 재료 종류가 레시피 재료와 정확히 같아야 그 요리가 된다 (모양·위치는 상관없음).</li>
 *   <li>amount: 한 번 만들 때 나오는 개수 (대형 솥 수프는 4그릇 등, 기본 1).</li>
 * </ul>
 */
public final class CookingRecipes {

    private static final String[] QUALITY_SUFFIXES = {"_silver_star", "_golden_star"};

    private final ItemsAdderItemProvider itemProvider;
    private final Map<String, Group> groups;
    private final List<Recipe> recipes = new ArrayList<>();
    private final Set<String> ingredientIds = new HashSet<>();

    private CookingRecipes(ItemsAdderItemProvider itemProvider, Map<String, Group> groups) {
        this.itemProvider = itemProvider;
        this.groups = groups;
    }

    /**
     * cooking.stations 의 모든 기기와 레시피를 읽는다 (설정 순서 유지).
     */
    public static Map<String, CookingStation> loadStations(FileConfiguration config, ItemsAdderItemProvider itemProvider, Logger logger) {
        Map<String, Group> groups = new HashMap<>();
        ConfigurationSection groupSection = config.getConfigurationSection("cooking.groups");
        if (groupSection != null) {
            for (String key : groupSection.getKeys(false)) {
                String name = groupSection.getString(key + ".name", key);
                groups.put(key, new Group(name, Set.copyOf(groupSection.getStringList(key + ".items"))));
            }
        }
        Map<String, CookingStation> stations = new LinkedHashMap<>();
        ConfigurationSection stationSection = config.getConfigurationSection("cooking.stations");
        if (stationSection == null) {
            logger.warning("cooking.stations 설정이 없어 요리 기기를 쓸 수 없습니다.");
            return stations;
        }
        for (String key : stationSection.getKeys(false)) {
            String furniture = stationSection.getString(key + ".furniture");
            if (furniture == null) {
                logger.warning("요리 기기 " + key + "의 furniture(가구 ID)가 없어 건너뜁니다.");
                continue;
            }
            String title = stationSection.getString(key + ".title", key);
            CookingRecipes recipes = new CookingRecipes(itemProvider, groups);
            recipes.read(stationSection.getConfigurationSection(key + ".recipes"), key, logger);
            stations.put(key, new CookingStation(key, furniture, title, recipes));
            logger.info("요리 기기 " + title + ": 레시피 " + recipes.recipes.size() + "개");
        }
        return stations;
    }

    /**
     * 절구 레시피 (config.yml 의 mortar.recipes). 재료 묶음은 cooking.groups 와 mortar.groups 를 함께 쓴다.
     */
    public static CookingRecipes loadMortar(FileConfiguration config, ItemsAdderItemProvider itemProvider, Logger logger) {
        Map<String, Group> groups = new HashMap<>();
        for (String path : new String[]{"cooking.groups", "mortar.groups"}) {
            ConfigurationSection groupSection = config.getConfigurationSection(path);
            if (groupSection == null) {
                continue;
            }
            for (String key : groupSection.getKeys(false)) {
                String name = groupSection.getString(key + ".name", key);
                groups.put(key, new Group(name, Set.copyOf(groupSection.getStringList(key + ".items"))));
            }
        }
        CookingRecipes recipes = new CookingRecipes(itemProvider, groups);
        recipes.read(config.getConfigurationSection("mortar.recipes"), "절구", logger);
        logger.info("절구 레시피 " + recipes.recipes.size() + "개를 불러왔습니다.");
        return recipes;
    }

    private void read(ConfigurationSection recipeSection, String station, Logger logger) {
        if (recipeSection == null) {
            logger.warning("요리 기기 " + station + "에 레시피가 없습니다.");
            return;
        }
        Map<Set<String>, String> seen = new HashMap<>();
        for (String key : recipeSection.getKeys(false)) {
            String resultId = key.contains(":") ? key : "rustport:" + key;
            int seconds = Math.max(1, recipeSection.getInt(key + ".seconds", 5));
            int amount = Math.max(1, recipeSection.getInt(key + ".amount", 1));
            ConfigurationSection ingredientSection = recipeSection.getConfigurationSection(key + ".ingredients");
            if (ingredientSection == null || ingredientSection.getKeys(false).isEmpty()) {
                logger.warning(station + ": 재료가 없는 레시피를 건너뜁니다: " + key);
                continue;
            }
            Map<String, Integer> ingredients = new LinkedHashMap<>();
            boolean valid = true;
            for (String ingredient : ingredientSection.getKeys(false)) {
                if (ingredient.startsWith("#") && !groups.containsKey(ingredient.substring(1))) {
                    logger.warning(station + ": 레시피 " + key + "의 재료 묶음이 없습니다: " + ingredient);
                    valid = false;
                }
                ingredients.put(ingredient, Math.max(1, ingredientSection.getInt(ingredient)));
            }
            if (!valid) {
                continue;
            }
            String duplicate = seen.put(ingredients.keySet(), resultId);
            if (duplicate != null) {
                logger.warning(station + ": 레시피 재료 구성이 같아 구분할 수 없습니다: " + duplicate + " / " + resultId);
            }
            recipes.add(new Recipe(resultId, seconds, amount, ingredients));
            for (String ingredient : ingredients.keySet()) {
                if (ingredient.startsWith("#")) {
                    ingredientIds.addAll(groups.get(ingredient.substring(1)).items());
                } else {
                    ingredientIds.add(ingredient);
                }
            }
        }
    }

    public List<Recipe> recipes() {
        return recipes;
    }

    public String groupName(String groupKey) {
        Group group = groups.get(groupKey);
        return group == null ? groupKey : group.name();
    }

    public Set<String> groupItems(String groupKey) {
        Group group = groups.get(groupKey);
        return group == null ? Set.of() : group.items();
    }

    /**
     * 아이템의 재료 ID. ItemsAdder 아이템은 품질 표시를 뗀 "namespace:id", 바닐라는 "minecraft:id".
     */
    public String keyOf(ItemStack item) {
        if (item == null || item.getType().isAir()) {
            return null;
        }
        String id = itemProvider.idOf(item);
        if (id == null) {
            // 물약 중에서는 물병만 재료로 본다 (다른 물약을 물 대신 넣지 못하게)
            if (item.getType() == org.bukkit.Material.POTION
                    && !(item.getItemMeta() instanceof org.bukkit.inventory.meta.PotionMeta potion
                    && potion.getBasePotionType() == org.bukkit.potion.PotionType.WATER)) {
                return "minecraft:potion#other";
            }
            return item.getType().getKey().toString();
        }
        for (String suffix : QUALITY_SUFFIXES) {
            if (id.endsWith(suffix)) {
                return id.substring(0, id.length() - suffix.length());
            }
        }
        return id;
    }

    public boolean isIngredient(ItemStack item) {
        String key = keyOf(item);
        return key != null && ingredientIds.contains(key);
    }

    /**
     * 재료 칸 아이템으로 만들 수 있는 요리와 몇 번 만들 수 있는지. 없으면 null.
     */
    public Match match(List<ItemStack> items) {
        for (Recipe recipe : recipes) {
            int batches = batches(recipe, items);
            if (batches > 0) {
                return new Match(recipe, batches);
            }
        }
        return null;
    }

    /**
     * 이 레시피로 몇 번 만들 수 있는지. 레시피에 없는 재료가 섞여 있거나 모자라면 0.
     */
    private int batches(Recipe recipe, List<ItemStack> items) {
        Map<String, Integer> counts = new HashMap<>();
        boolean any = false;
        for (ItemStack item : items) {
            String key = keyOf(item);
            if (key == null) {
                continue;
            }
            String ingredient = ingredientFor(recipe, key);
            if (ingredient == null) {
                return 0;
            }
            counts.merge(ingredient, item.getAmount(), Integer::sum);
            any = true;
        }
        if (!any) {
            return 0;
        }
        int batches = Integer.MAX_VALUE;
        for (Map.Entry<String, Integer> entry : recipe.ingredients().entrySet()) {
            batches = Math.min(batches, counts.getOrDefault(entry.getKey(), 0) / entry.getValue());
        }
        return batches;
    }

    /**
     * 재료 ID가 레시피의 어느 재료 칸에 들어가는지 (정확한 ID 우선, 그다음 묶음). 없으면 null.
     */
    String ingredientFor(Recipe recipe, String key) {
        if (recipe.ingredients().containsKey(key)) {
            return key;
        }
        for (String ingredient : recipe.ingredients().keySet()) {
            if (ingredient.startsWith("#") && groupItems(ingredient.substring(1)).contains(key)) {
                return ingredient;
            }
        }
        return null;
    }

    public record Recipe(String resultId, int seconds, int amount, Map<String, Integer> ingredients) {
    }

    public record Match(Recipe recipe, int batches) {
    }

    private record Group(String name, Set<String> items) {
    }
}

package com.brassfield.cooking;

import com.brassfield.common.ItemsAdderGuiBackground;
import com.brassfield.common.ItemsAdderItemProvider;
import net.kyori.adventure.text.Component;
import org.bukkit.Location;
import org.bukkit.World;
import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.entity.Entity;
import org.bukkit.entity.HumanEntity;
import org.bukkit.entity.ItemDisplay;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;
import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.scheduler.BukkitTask;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/**
 * 설치된 요리 기기들(조리대·제분기·착즙기·발효조·훈연기·대형 솥·제빵 오븐)의 조리 상태를 위치별로 들고 있고,
 * cooking_machines.yml 에 저장한다. 기기 종류와 레시피는 config.yml 의 cooking.stations.
 * <ul>
 *   <li>기계를 우클릭하면 그 위치의 조리칸을 연다 (처음이면 빈 조리칸을 만든다).</li>
 *   <li>보고 있는 사람이 있는 기계는 1초마다 진행을 갱신한다. 아무도 안 볼 때는 열 때 한꺼번에 계산한다.</li>
 *   <li>관리자가 기계를 부수면 안에 든 재료·요리·빈 그릇을 그 자리에 떨어뜨린다.</li>
 *   <li>저장: 걸린 요리 · 진행 시작 시각 · 재료(아이템 + 개수) · 완성품(아이템 + 개수) · 빈 그릇 개수.</li>
 * </ul>
 */
public final class CookingMachines {

    private static final String FILE_NAME = "cooking_machines.yml";
    private static final long SAVE_EVERY_TICKS = 20L * 60;

    private final JavaPlugin plugin;
    private final Map<String, CookingStation> stations;
    private final ItemsAdderItemProvider itemProvider;
    private final CookGlyphs glyphs;
    private final File file;
    private final Map<String, CookingMachine> machines = new HashMap<>();
    /**
     * 조리 중이면 가구 모양을 바꾸는 기기: 기기 → 켜짐 모델 아이템 (ItemsAdder 모델 전용 아이템, 설치 불가).
     * 가구 표시 아이템의 item_model 만 그 아이템 것으로 바꾼다 (가구 ID 는 그대로라 부수기·회수·우클릭은 그대로).
     */
    private static final Map<String, String> LIT_MODELS = Map.of("kettle", "rustport:kettle_on", "oven", "rustport:oven_on",
            "fermenter", "rustport:fermenter_on");
    private final Map<String, ItemMeta> modelSources = new HashMap<>();       // 모델을 빌려 올 아이템 (custom model data · item_model)
    private final Map<String, Boolean> shownLit = new HashMap<>();
    private final java.util.Set<String> missingDisplays = new java.util.HashSet<>();             // 기기 → 지금 가구에 보이는 모양 (켜짐?)
    private final Map<String, Component> resultNames = new HashMap<>();
    private BukkitTask tickTask;
    private BukkitTask saveTask;
    private boolean dirty;

    public CookingMachines(JavaPlugin plugin, Map<String, CookingStation> stations, ItemsAdderItemProvider itemProvider,
                           ItemsAdderGuiBackground guiBackground) {
        this.plugin = plugin;
        this.stations = stations;
        this.itemProvider = itemProvider;
        this.glyphs = new CookGlyphs(guiBackground);
        this.file = new File(plugin.getDataFolder(), FILE_NAME);
    }

    public java.util.Collection<CookingStation> stations() {
        return stations.values();
    }

    ItemsAdderItemProvider itemProvider() {
        return itemProvider;
    }

    CookGlyphs glyphs() {
        return glyphs;
    }

    JavaPlugin plugin() {
        return plugin;
    }

    public void start() {
        load();
        tickTask = plugin.getServer().getScheduler().runTaskTimer(plugin, this::tickViewed, 20L, 20L);
        saveTask = plugin.getServer().getScheduler().runTaskTimer(plugin, () -> {
            if (dirty) {
                save();
            }
        }, SAVE_EVERY_TICKS, SAVE_EVERY_TICKS);
    }

    public void stop() {
        if (tickTask != null) {
            tickTask.cancel();
        }
        if (saveTask != null) {
            saveTask.cancel();
        }
        for (CookingMachine machine : machines.values()) {
            for (HumanEntity viewer : new ArrayList<>(machine.getInventory().getViewers())) {
                viewer.closeInventory();
            }
            machine.update(System.currentTimeMillis());
        }
        save();
    }

    /**
     * 요리 기기 가구를 우클릭했을 때.
     */
    public void open(Player player, Entity furniture, CookingStation station) {
        String key = keyOf(furniture.getLocation());
        CookingMachine machine = machines.get(key);
        if (machine == null || !machine.station().key().equals(station.key())) {
            machine = new CookingMachine(this, station, key);
            machines.put(key, machine);
        }
        machine.open(player);
        refreshModel(machine);
        dirty = true;
    }

    /**
     * 요리 기계 가구를 부쉈을 때 (관리자만 가능): 안에 든 것을 그 자리에 떨어뜨린다.
     */
    public void destroy(Entity furniture) {
        Location location = furniture.getLocation();
        CookingMachine machine = machines.remove(keyOf(location));
        shownLit.remove(keyOf(location));
        if (machine == null) {
            return;
        }
        for (HumanEntity viewer : new ArrayList<>(machine.getInventory().getViewers())) {
            viewer.closeInventory();
        }
        machine.update(System.currentTimeMillis());
        for (ItemStack item : machine.contents()) {
            drop(location, item);
        }
        save();
    }

    void markDirty() {
        dirty = true;
    }

    ItemStack createResult(String resultId) {
        return itemProvider.create(resultId);
    }

    private final Map<String, Boolean> gradable = new HashMap<>();

    /**
     * 레시피 재료에 등급(은별·금별)이 있는지: 재료 ID(묶음이면 그 안 아무거나)의 금별 아이템이 있으면 등급 있는 재료.
     * 요리 등급 평균에는 등급 있는 재료만 넣는다 (바닐라 재료는 빼고 센다).
     */
    boolean isGradable(String ingredient, CookingRecipes recipes) {
        return gradable.computeIfAbsent(ingredient, key -> {
            java.util.Collection<String> ids = key.startsWith("#") ? recipes.groupItems(key.substring(1)) : List.of(key);
            for (String id : ids) {
                if (id.startsWith("minecraft:")) {
                    continue;
                }
                try {
                    itemProvider.create(com.brassfield.common.Grades.withGrade(id, 2));
                    return true;
                } catch (IllegalStateException ignored) {
                    // 금별 아이템 없음
                }
            }
            return false;
        });
    }

    /**
     * 아직 넣지 않은 재료 칸에 보일 아이콘: 재료 ID(묶음이면 이름순 첫 아이템)로 만든 아이템, 못 만들면 종이
     */
    ItemStack ingredientIcon(CookingRecipes recipes, String ingredient) {
        String id = ingredient;
        if (ingredient.startsWith("#")) {
            id = recipes.groupItems(ingredient.substring(1)).stream().sorted().findFirst().orElse("minecraft:paper");
        }
        if (id.startsWith("minecraft:")) {
            org.bukkit.Material material = org.bukkit.Material.matchMaterial(id);
            return new ItemStack(material == null || !material.isItem() ? org.bukkit.Material.PAPER : material);
        }
        try {
            return itemProvider.create(id);
        } catch (IllegalStateException exception) {
            return new ItemStack(org.bukkit.Material.PAPER);
        }
    }

    Component resultName(String resultId) {
        return resultNames.computeIfAbsent(resultId, id -> displayName(id));
    }

    /**
     * 재료·요리 ID의 표시 이름: 바닐라는 번역 키(클라이언트 언어), ItemsAdder 아이템은 그 이름.
     */
    Component displayName(String id) {
        if (id.startsWith("#")) {
            return Component.text(groupName(id.substring(1)));
        }
        if (id.startsWith("minecraft:")) {
            org.bukkit.Material material = org.bukkit.Material.matchMaterial(id);
            return material == null ? Component.text(id) : Component.translatable(material.translationKey());
        }
        try {
            ItemStack item = itemProvider.create(id);
            Component name = item.getItemMeta().displayName();
            return name != null ? name : Component.translatable(item.translationKey());
        } catch (IllegalStateException exception) {
            return Component.text(id);
        }
    }

    private String groupName(String group) {
        for (CookingStation station : stations.values()) {
            String name = station.recipes().groupName(group);
            if (!name.equals(group)) {
                return name;
            }
        }
        return group;
    }

    private void tickViewed() {
        long now = System.currentTimeMillis();
        for (CookingMachine machine : machines.values()) {
            boolean viewed = !machine.getInventory().getViewers().isEmpty();
            boolean lit = LIT_MODELS.containsKey(machine.station().key());
            if ((viewed || lit) && machine.update(now)) {                       // 켜짐 모양이 있는 기기는 아무도 안 봐도 진행 (재료가 떨어지면 꺼짐)
                dirty = true;
            }
            if (lit) {
                refreshModel(machine);
            }
        }
    }

    /** 가구 모양을 조리 상태(켜짐 · 꺼짐)에 맞춘다. 청크가 안 불러와졌으면 다음에 다시 */
    void refreshModel(CookingMachine machine) {
        String litModel = LIT_MODELS.get(machine.station().key());
        if (litModel == null) {
            return;
        }
        boolean lit = machine.running();
        if (Objects.equals(shownLit.get(machine.key()), lit)) {
            return;
        }
        ItemDisplay display = displayOf(machine);
        if (display == null) {
            return;
        }
        ItemMeta source = modelSource(lit ? litModel : machine.station().furnitureId());
        ItemStack item = display.getItemStack();
        ItemMeta meta = item.getItemMeta();
        if (source == null || meta == null) {
            return;
        }
        // ItemsAdder 는 가구 모델을 종이 아이템의 custom model data 번호로 고른다 (item_model 이 있으면 그것도 함께)
        meta.setCustomModelDataComponent(source.getCustomModelDataComponent());
        meta.setItemModel(source.hasItemModel() ? source.getItemModel() : null);
        item.setItemMeta(meta);
        display.setItemStack(item);
        shownLit.put(machine.key(), lit);
    }

    /** 기기 자리(블록)의 가구 표시 엔티티 */
    private ItemDisplay displayOf(CookingMachine machine) {
        String[] parts = machine.key().split(";");
        World world = plugin.getServer().getWorld(parts[0]);
        if (world == null) {
            return null;
        }
        int x = Integer.parseInt(parts[1]);
        int y = Integer.parseInt(parts[2]);
        int z = Integer.parseInt(parts[3]);
        if (!world.isChunkLoaded(x >> 4, z >> 4)) {
            return null;
        }
        Location center = new Location(world, x + 0.5, y + 0.5, z + 0.5);
        for (Entity entity : world.getNearbyEntities(center, 0.6, 0.6, 0.6, e -> e instanceof ItemDisplay)) {
            ItemDisplay display = (ItemDisplay) entity;
            if (keyOf(display.getLocation()).equals(machine.key())
                    && machine.station().furnitureId().equals(itemProvider.idOf(display.getItemStack()))) {
                return display;
            }
        }
        if (missingDisplays.add(machine.key())) {                     // 청크는 있는데 가구 표시가 없음: 한 번만 알림
            plugin.getLogger().warning("요리 기기 가구 표시를 찾지 못해 모양을 바꾸지 못했습니다: " + machine.key());
        }
        return null;
    }

    /** 모델을 빌려 올 ItemsAdder 아이템의 정보 (custom model data · item_model) */
    private ItemMeta modelSource(String itemId) {
        return modelSources.computeIfAbsent(itemId, id -> {
            try {
                return itemProvider.create(id).getItemMeta();
            } catch (RuntimeException exception) {
                plugin.getLogger().warning("가구 모양 아이템을 찾지 못했습니다: " + id);
                return null;
            }
        });
    }

    private static void drop(Location location, ItemStack item) {
        if (item != null && !item.getType().isAir()) {
            location.getWorld().dropItemNaturally(location, item);
        }
    }

    private static String keyOf(Location location) {
        return location.getWorld().getName() + ";" + location.getBlockX() + ";" + location.getBlockY() + ";" + location.getBlockZ();
    }

    // ── 저장 ──
    private void load() {
        if (!file.exists()) {
            return;
        }
        YamlConfiguration data = YamlConfiguration.loadConfiguration(file);
        ConfigurationSection root = data.getConfigurationSection("machines");
        if (root == null) {
            return;
        }
        for (String id : root.getKeys(false)) {
            ConfigurationSection section = root.getConfigurationSection(id);
            String key = section.getString("location");
            if (key == null) {
                continue;
            }
            CookingStation station = stations.get(section.getString("station", "counter"));
            if (station == null) {
                plugin.getLogger().warning("요리 기기 종류를 찾을 수 없어 건너뜁니다: " + section.getString("station") + " @ " + key);
                continue;
            }
            CookingMachine machine = new CookingMachine(this, station, key);
            ConfigurationSection items = section.getConfigurationSection("items");
            if (items != null) {
                // 예전 저장 형식(칸마다 아이템): 처음 여는 사람에게 돌려준다
                for (String slot : items.getKeys(false)) {
                    ItemStack item = items.getItemStack(slot);
                    if (item != null && !item.getType().isAir()) {
                        machine.legacy().add(item);
                    }
                }
            }
            for (Object raw : section.getList("legacy", List.of())) {
                if (raw instanceof ItemStack item) {
                    machine.legacy().add(item);
                }
            }
            for (Map<?, ?> raw : section.getMapList("stocks")) {
                if (raw.get("item") instanceof ItemStack item && raw.get("count") instanceof Number count) {
                    machine.addStock(item, count.intValue());
                }
            }
            ConfigurationSection byproducts = section.getConfigurationSection("byproducts");
            if (byproducts != null) {
                for (String material : byproducts.getKeys(false)) {
                    org.bukkit.Material type = org.bukkit.Material.matchMaterial(material);
                    if (type != null && byproducts.getInt(material) > 0) {
                        machine.byproducts().put(type, byproducts.getInt(material));
                    }
                }
            }
            List<Integer> counts = section.getIntegerList("output.counts");
            int[] outputs = counts.size() == 3 ? new int[]{counts.get(0), counts.get(1), counts.get(2)}
                    : new int[]{section.getInt("output.count"), 0, 0};
            machine.restore(section.getString("recipe"), section.getLong("started", -1), section.getLong("paused", 0),
                    section.getItemStack("output.item"), outputs);
            machines.put(key, machine);
        }
        plugin.getLogger().info("요리 기계 " + machines.size() + "대의 조리 상태를 불러왔습니다.");
    }

    void save() {
        YamlConfiguration data = new YamlConfiguration();
        int index = 0;
        for (CookingMachine machine : machines.values()) {
            String path = "machines." + index++;
            data.set(path + ".location", machine.key());
            data.set(path + ".station", machine.station().key());
            data.set(path + ".recipe", machine.pinned() == null ? null : machine.pinned().resultId());
            data.set(path + ".started", machine.startedAt());
            data.set(path + ".paused", machine.pausedProgress());
            List<Map<String, Object>> stocks = new ArrayList<>();
            for (CookingMachine.Stock stock : machine.stocks()) {
                stocks.add(Map.of("item", stock.sample, "count", stock.count));
            }
            data.set(path + ".stocks", stocks);
            if (machine.outputSample() != null && machine.outputCount() > 0) {
                data.set(path + ".output.item", machine.outputSample());
                int[] outputs = machine.outputs();
                data.set(path + ".output.counts", List.of(outputs[0], outputs[1], outputs[2]));
            }
            machine.byproducts().forEach((material, count) -> data.set(path + ".byproducts." + material.name(), count));
            if (!machine.legacy().isEmpty()) {
                data.set(path + ".legacy", machine.legacy());
            }
        }
        try {
            plugin.getDataFolder().mkdirs();
            data.save(file);
            dirty = false;
        } catch (IOException exception) {
            plugin.getLogger().severe("요리 기계 상태를 저장하지 못했습니다: " + exception);
        }
    }
}

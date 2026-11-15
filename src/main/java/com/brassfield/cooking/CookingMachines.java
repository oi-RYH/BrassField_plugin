package com.brassfield.cooking;

import com.brassfield.common.ItemsAdderItemProvider;
import net.kyori.adventure.text.Component;
import org.bukkit.Location;
import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.entity.Entity;
import org.bukkit.entity.HumanEntity;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;
import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.scheduler.BukkitTask;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

/**
 * 설치된 요리 기기들(조리대·제분기·착즙기·발효조·훈연기·대형 솥·제빵 오븐)의 조리 상태를 위치별로 들고 있고,
 * cooking_machines.yml 에 저장한다. 기기 종류와 레시피는 config.yml 의 cooking.stations.
 * <ul>
 *   <li>기계를 우클릭하면 그 위치의 조리칸을 연다 (처음이면 빈 조리칸을 만든다).</li>
 *   <li>보고 있는 사람이 있는 기계는 1초마다 진행을 갱신한다. 아무도 안 볼 때는 열 때 한꺼번에 계산한다.</li>
 *   <li>관리자가 기계를 부수면 안에 든 재료와 요리를 그 자리에 떨어뜨린다.</li>
 * </ul>
 */
public final class CookingMachines {

    private static final String FILE_NAME = "cooking_machines.yml";
    private static final long SAVE_EVERY_TICKS = 20L * 60;

    private final JavaPlugin plugin;
    private final Map<String, CookingStation> stations;
    private final ItemsAdderItemProvider itemProvider;
    private final File file;
    private final Map<String, CookingMachine> machines = new HashMap<>();
    private final Map<String, Component> resultNames = new HashMap<>();
    private BukkitTask tickTask;
    private BukkitTask saveTask;
    private boolean dirty;

    public CookingMachines(JavaPlugin plugin, Map<String, CookingStation> stations, ItemsAdderItemProvider itemProvider) {
        this.plugin = plugin;
        this.stations = stations;
        this.itemProvider = itemProvider;
        this.file = new File(plugin.getDataFolder(), FILE_NAME);
    }

    public java.util.Collection<CookingStation> stations() {
        return stations.values();
    }

    ItemsAdderItemProvider itemProvider() {
        return itemProvider;
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
        dirty = true;
    }

    /**
     * 요리 기계 가구를 부쉈을 때 (관리자만 가능): 안에 든 것을 그 자리에 떨어뜨린다.
     */
    public void destroy(Entity furniture) {
        Location location = furniture.getLocation();
        CookingMachine machine = machines.remove(keyOf(location));
        if (machine == null) {
            return;
        }
        for (HumanEntity viewer : new ArrayList<>(machine.getInventory().getViewers())) {
            viewer.closeInventory();
        }
        machine.update(System.currentTimeMillis());
        for (int slot : CookingMachine.INGREDIENT_SLOTS) {
            drop(location, machine.getInventory().getItem(slot));
        }
        drop(location, machine.getInventory().getItem(CookingMachine.OUTPUT_SLOT));
        for (int slot : CookingMachine.BYPRODUCT_SLOTS) {
            drop(location, machine.getInventory().getItem(slot));
        }
        save();
    }

    void markDirty() {
        dirty = true;
    }

    ItemStack createResult(String resultId) {
        return itemProvider.create(resultId);
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
            if (!machine.getInventory().getViewers().isEmpty() && machine.update(now)) {
                dirty = true;
            }
        }
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
                for (String slot : items.getKeys(false)) {
                    machine.getInventory().setItem(Integer.parseInt(slot), items.getItemStack(slot));
                }
            }
            machine.restore(section.getString("recipe"), section.getLong("started", -1));
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
            data.set(path + ".recipe", machine.recipeId());
            data.set(path + ".started", machine.startedAt());
            for (int slot : CookingMachine.INGREDIENT_SLOTS) {
                saveItem(data, path, slot, machine.getInventory().getItem(slot));
            }
            saveItem(data, path, CookingMachine.OUTPUT_SLOT, machine.getInventory().getItem(CookingMachine.OUTPUT_SLOT));
            for (int slot : CookingMachine.BYPRODUCT_SLOTS) {
                saveItem(data, path, slot, machine.getInventory().getItem(slot));
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

    private static void saveItem(YamlConfiguration data, String path, int slot, ItemStack item) {
        if (item != null && !item.getType().isAir()) {
            data.set(path + ".items." + slot, item);
        }
    }
}

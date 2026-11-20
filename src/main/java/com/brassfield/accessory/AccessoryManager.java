package com.brassfield.accessory;

import com.brassfield.accessory.AccessoryKind.Part;
import org.bukkit.NamespacedKey;
import org.bukkit.attribute.Attribute;
import org.bukkit.attribute.AttributeInstance;
import org.bukkit.attribute.AttributeModifier;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.entity.Player;
import org.bukkit.inventory.EquipmentSlotGroup;
import org.bukkit.inventory.ItemStack;
import org.bukkit.plugin.java.JavaPlugin;

import java.io.File;
import java.io.IOException;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * 플레이어별 장착 장신구 5칸 (목걸이 1 · 귀걸이 2 · 반지 2): 파일 저장 · 불러오기와 능력치 합계 적용.
 * 저장: plugins/BrassField/accessories/{uuid}.yml. 최대 체력은 속성 보정치로, 공격력 · 받는 피해는 AccessoryListener 가 피해 계산 때 쓴다.
 */
public final class AccessoryManager {

    /** 장착 칸 순서 (AccessoryGui 칸과 맞춤) */
    public static final Part[] SLOT_PARTS = {Part.NECKLACE, Part.EARRING, Part.EARRING, Part.RING, Part.RING};

    private final JavaPlugin plugin;
    private final File folder;
    private final NamespacedKey healthKey;
    private final Map<UUID, ItemStack[]> equipped = new HashMap<>();
    private final Map<UUID, Map<Part, Double>> totals = new HashMap<>();

    public AccessoryManager(JavaPlugin plugin) {
        this.plugin = plugin;
        this.folder = new File(plugin.getDataFolder(), "accessories");
        this.healthKey = new NamespacedKey(plugin, "accessory_health");
    }

    public ItemStack[] slots(Player player) {
        return equipped.computeIfAbsent(player.getUniqueId(), id -> load(id));
    }

    public void setSlot(Player player, int index, ItemStack item) {
        slots(player)[index] = item == null || item.getType().isAir() ? null : item;
        save(player);
        apply(player);
    }

    /** 부위별 합계 (목걸이 = 최대 체력, 귀걸이 = 공격력 %, 반지 = 받는 피해 감소 %) */
    public double total(Player player, Part part) {
        return totals.getOrDefault(player.getUniqueId(), Map.of()).getOrDefault(part, 0.0);
    }

    /** 장착한 장신구 중 가장 높은 등급 (없으면 일반) — 장착 창 배경을 고른다 */
    public com.brassfield.accessory.AccessoryKind.Grade highestGrade(Player player) {
        com.brassfield.accessory.AccessoryKind.Grade best = com.brassfield.accessory.AccessoryKind.Grade.COMMON;
        for (ItemStack item : slots(player)) {
            var info = Accessories.read(item).orElse(null);
            if (info != null && info.grade().ordinal() > best.ordinal()) {
                best = info.grade();
            }
        }
        return best;
    }

    public void apply(Player player) {
        Map<Part, Double> sum = new EnumMap<>(Part.class);
        for (ItemStack item : slots(player)) {
            Accessories.read(item).ifPresent(info -> sum.merge(info.part(), info.value(), Double::sum));
        }
        totals.put(player.getUniqueId(), sum);
        AttributeInstance health = player.getAttribute(Attribute.MAX_HEALTH);
        if (health != null) {
            health.removeModifier(healthKey);
            double bonus = sum.getOrDefault(Part.NECKLACE, 0.0);
            if (bonus > 0) {
                health.addModifier(new AttributeModifier(healthKey, bonus, AttributeModifier.Operation.ADD_NUMBER, EquipmentSlotGroup.ANY));
            }
            if (player.getHealth() > health.getValue()) {
                player.setHealth(health.getValue());
            }
        }
    }

    public void unload(Player player) {
        save(player);
        equipped.remove(player.getUniqueId());
        totals.remove(player.getUniqueId());
    }

    private ItemStack[] load(UUID id) {
        ItemStack[] items = new ItemStack[SLOT_PARTS.length];
        File file = new File(folder, id + ".yml");
        if (file.exists()) {
            YamlConfiguration yaml = YamlConfiguration.loadConfiguration(file);
            for (int i = 0; i < items.length; i++) {
                items[i] = yaml.getItemStack("slot" + i);
            }
        }
        return items;
    }

    private void save(Player player) {
        ItemStack[] items = equipped.get(player.getUniqueId());
        if (items == null) {
            return;
        }
        YamlConfiguration yaml = new YamlConfiguration();
        for (int i = 0; i < items.length; i++) {
            yaml.set("slot" + i, items[i]);
        }
        try {
            folder.mkdirs();
            yaml.save(new File(folder, player.getUniqueId() + ".yml"));
        } catch (IOException exception) {
            plugin.getLogger().warning("장신구 저장 실패 (" + player.getName() + "): " + exception.getMessage());
        }
    }
}

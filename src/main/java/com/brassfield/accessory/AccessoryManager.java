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
 * 플레이어별 장착 장신구 5칸 (목걸이 1 · 귀걸이 2 · 반지 2): 파일 저장 · 불러오기와 보조옵션 합계 적용.
 * 저장: plugins/BrassField/accessories/{uuid}.yml. 최대 체력 · 이동 속도 · 공격 속도는 속성 보정치로,
 * 나머지(공격력 · 치명타 · 출혈 · 회복 · 피해 감소 · 낙하 · 경험치 · 요리 · 수확)는 AccessoryListener · SetEffects 가 이벤트에서 쓴다.
 */
public final class AccessoryManager {

    /** 장착 칸 순서 (AccessoryGui 칸과 맞춤) */
    public static final Part[] SLOT_PARTS = {Part.NECKLACE, Part.EARRING, Part.EARRING, Part.RING, Part.RING};

    private final JavaPlugin plugin;
    private final File folder;
    private final NamespacedKey healthKey;
    private final Map<UUID, ItemStack[]> equipped = new HashMap<>();
    private final Map<UUID, Map<AccessoryOption, Double>> totals = new HashMap<>();
    private final NamespacedKey speedKey;
    private final NamespacedKey attackSpeedKey;
    private SetEffects setEffects;

    public AccessoryManager(JavaPlugin plugin) {
        this.plugin = plugin;
        this.folder = new File(plugin.getDataFolder(), "accessories");
        this.healthKey = new NamespacedKey(plugin, "accessory_health");
        this.speedKey = new NamespacedKey(plugin, "accessory_speed");
        this.attackSpeedKey = new NamespacedKey(plugin, "accessory_attack_speed");
    }

    public void setEffects(SetEffects setEffects) {
        this.setEffects = setEffects;
    }

    public SetEffects setEffects() {
        return setEffects;
    }

    public ItemStack[] slots(Player player) {
        return equipped.computeIfAbsent(player.getUniqueId(), id -> load(id));
    }

    public void setSlot(Player player, int index, ItemStack item) {
        slots(player)[index] = item == null || item.getType().isAir() ? null : item;
        save(player);
        apply(player);
    }

    /** 장착한 장신구 보조옵션 합계 (강화 배율 적용, 옵션마다 상한까지) */
    public double total(Player player, AccessoryOption option) {
        return totals.getOrDefault(player.getUniqueId(), Map.of()).getOrDefault(option, 0.0);
    }

    public Map<AccessoryOption, Double> totals(Player player) {
        return totals.getOrDefault(player.getUniqueId(), Map.of());
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
        Map<AccessoryOption, Double> sum = new EnumMap<>(AccessoryOption.class);
        for (ItemStack item : slots(player)) {
            Accessories.read(item).ifPresent(info -> {
                for (AccessoryOption.Roll roll : info.options()) {
                    sum.merge(roll.option(), roll.value(info.level()), Double::sum);
                }
            });
        }
        sum.replaceAll((option, value) -> Math.min(option.cap(), Math.round(value * 10) / 10.0));
        totals.put(player.getUniqueId(), sum);
        modifier(player, Attribute.MAX_HEALTH, healthKey, sum.getOrDefault(AccessoryOption.MAX_HEALTH, 0.0), false);
        modifier(player, Attribute.MOVEMENT_SPEED, speedKey, sum.getOrDefault(AccessoryOption.SPEED, 0.0) / 100, true);
        modifier(player, Attribute.ATTACK_SPEED, attackSpeedKey, sum.getOrDefault(AccessoryOption.ATTACK_SPEED, 0.0) / 100, true);
        AttributeInstance health = player.getAttribute(Attribute.MAX_HEALTH);
        if (health != null && player.getHealth() > health.getValue()) {
            player.setHealth(health.getValue());
        }
        if (setEffects != null) {
            setEffects.update(player, slots(player));
        }
    }

    private static void modifier(Player player, Attribute attribute, NamespacedKey key, double amount, boolean scalar) {
        AttributeInstance instance = player.getAttribute(attribute);
        if (instance == null) {
            return;
        }
        instance.removeModifier(key);
        if (amount > 0) {
            instance.addModifier(new AttributeModifier(key, amount,
                    scalar ? AttributeModifier.Operation.ADD_SCALAR : AttributeModifier.Operation.ADD_NUMBER, EquipmentSlotGroup.ANY));
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

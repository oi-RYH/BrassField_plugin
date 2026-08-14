package com.rustport.enhancement;

import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.Material;
import org.bukkit.NamespacedKey;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.plugin.java.JavaPlugin;

import java.util.List;
import java.util.stream.IntStream;

public final class EnhancementItem {

    private static NamespacedKey enhanceLevelKey;

    private EnhancementItem() {
    }

    // 강화 단계별 무기 종류 (0강=나무검 ~ 3강=다이아검)
    private static final Material[] TIERS = {
            Material.WOODEN_SWORD,
            Material.STONE_SWORD,
            Material.IRON_SWORD,
            Material.DIAMOND_SWORD
    };

    public static void init(JavaPlugin plugin) {
        enhanceLevelKey = new NamespacedKey(plugin, "enhance_level");
    }

    public static int getLevel(ItemStack item) {
        if (item == null) {
            return 0;
        }

        ItemMeta meta = item.getItemMeta();
        Integer storedLevel = meta.getPersistentDataContainer()
                .get(enhanceLevelKey, PersistentDataType.INTEGER);
        if (storedLevel != null) {
            return Math.max(0, Math.min(storedLevel, getMaxLevel()));
        }

        return IntStream.range(0, TIERS.length)
                .filter(index -> TIERS[index] == item.getType())
                .findFirst()
                .orElse(0);
    }

    public static int getMaxLevel() {
        return TIERS.length - 1; // 3
    }

    // 강화 단계에 맞는 새 아이템을 만들어서 반환
    public static boolean isEnhanceable(ItemStack item) {
        if (item == null) {
            return false;
        }
        for (Material material : TIERS) {
            if (item.getType() == material) {
                return true;
            }
        }
        return false;
    }

    public static ItemStack buildItem(ItemStack source, int level) {
        int normalizedLevel = Math.max(0, Math.min(level, getMaxLevel()));

        ItemStack item = source.withType(TIERS[normalizedLevel]);
        item.setAmount(1);
        ItemMeta meta = item.getItemMeta();
        meta.displayName(Component.text("강화 검", NamedTextColor.WHITE));
        meta.lore(List.of(
                Component.text("강화 단계: ", NamedTextColor.GRAY)
                        .append(Component.text("+" + normalizedLevel, NamedTextColor.GREEN))
        ));
        meta.getPersistentDataContainer()
                .set(enhanceLevelKey, PersistentDataType.INTEGER, normalizedLevel);
        item.setItemMeta(meta);

        return item;
    }
}

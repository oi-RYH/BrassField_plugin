package com.rustport.enhancement;

import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.Bukkit;
import org.bukkit.Material;
import org.bukkit.inventory.Inventory;
import org.bukkit.inventory.InventoryHolder;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;
import org.jetbrains.annotations.NotNull;

import java.util.List;

public final class EnhancementGui implements InventoryHolder {

    public static final int TARGET_SLOT = 10;
    public static final int ENHANCE_BUTTON_SLOT = 13;

    private static final int SIZE = 27;
    private static final Component TITLE = Component.text("장비 강화");

    private final Inventory inventory;

    public EnhancementGui(ItemStack targetItem) {
        inventory = Bukkit.createInventory(this, SIZE, TITLE);
        inventory.setItem(TARGET_SLOT, targetItem);
        inventory.setItem(ENHANCE_BUTTON_SLOT, createEnhanceButton());
    }

    @Override
    public @NotNull Inventory getInventory() {
        return inventory;
    }

    public ItemStack getTargetItem() {
        return inventory.getItem(TARGET_SLOT);
    }

    public ItemStack takeTargetItem() {
        ItemStack targetItem = getTargetItem();
        inventory.setItem(TARGET_SLOT, null);
        return targetItem;
    }

    private ItemStack createEnhanceButton() {
        ItemStack button = new ItemStack(Material.ANVIL);
        ItemMeta meta = button.getItemMeta();
        meta.displayName(Component.text("강화하기", NamedTextColor.GREEN));
        meta.lore(List.of(Component.text("클릭하면 강화를 시도합니다.", NamedTextColor.GRAY)));
        button.setItemMeta(meta);
        return button;
    }
}

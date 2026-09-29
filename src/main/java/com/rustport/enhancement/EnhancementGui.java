package com.rustport.enhancement;

import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.Bukkit;
import org.bukkit.Material;
import org.bukkit.entity.Player;
import org.bukkit.inventory.Inventory;
import org.bukkit.inventory.InventoryHolder;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;
import org.jetbrains.annotations.NotNull;

import java.util.List;

public final class EnhancementGui implements InventoryHolder {

    public static final int TARGET_SLOT = 1;
    public static final int ENHANCEMENT_STONE_SLOT = 19;
    public static final int ENHANCE_BUTTON_SLOT = 13;
    public static final int INFO_SLOT = 22;

    private static final int SIZE = 27;
    private static final String TITLE_TEXT = "장비 강화";
    private static final Component TITLE = Component.text(TITLE_TEXT);
    private static final String BACKGROUND_FONT_IMAGE = "rustport:enhance_bg";
    private static final int BACKGROUND_TITLE_OFFSET = 0;
    private static final int BACKGROUND_TEXTURE_OFFSET = -8;

    private final Inventory inventory;
    private final ItemsAdderGuiBackground guiBackground;
    private final ItemsAdderGuiBackground.TexturedGui texturedGui;

    public EnhancementGui(ItemStack targetItem, ItemsAdderGuiBackground guiBackground) {
        this.guiBackground = guiBackground;
        this.texturedGui = guiBackground.build(
                this, SIZE, TITLE_TEXT, BACKGROUND_FONT_IMAGE, BACKGROUND_TITLE_OFFSET, BACKGROUND_TEXTURE_OFFSET
        );

        if (texturedGui != null) {
            inventory = texturedGui.inventory();
        } else {
            inventory = Bukkit.createInventory(this, SIZE, TITLE);
            fillBackground();
        }

        inventory.setItem(TARGET_SLOT, targetItem);
        inventory.setItem(ENHANCEMENT_STONE_SLOT, null);
        inventory.setItem(ENHANCE_BUTTON_SLOT, createEnhanceButton());
        refreshInfo();
    }

    @Override
    public @NotNull Inventory getInventory() {
        return inventory;
    }

    public void open(Player player) {
        if (texturedGui != null) {
            guiBackground.show(texturedGui, player);
        } else {
            player.openInventory(inventory);
        }
    }

    public ItemStack getTargetItem() {
        return inventory.getItem(TARGET_SLOT);
    }

    public ItemStack takeTargetItem() {
        return takeItem(TARGET_SLOT);
    }

    public ItemStack takeEnhancementStone() {
        return takeItem(ENHANCEMENT_STONE_SLOT);
    }

    public void refreshInfo() {
        ItemStack targetItem = getTargetItem();
        if (targetItem == null || targetItem.getType().isAir()) {
            inventory.setItem(INFO_SLOT, createEmptyInfoItem());
            return;
        }
        if (!EnhancementItem.isEnhanceable(targetItem)) {
            inventory.setItem(INFO_SLOT, createInvalidInfoItem());
            return;
        }
        inventory.setItem(INFO_SLOT, createProbabilityInfo(targetItem));
    }

    private ItemStack takeItem(int slot) {
        ItemStack item = inventory.getItem(slot);
        inventory.setItem(slot, null);
        return item;
    }

    private void fillBackground() {
        ItemStack filler = new ItemStack(Material.GRAY_STAINED_GLASS_PANE);
        ItemMeta meta = filler.getItemMeta();
        meta.displayName(Component.empty());
        filler.setItemMeta(meta);

        for (int slot = 0; slot < SIZE; slot++) {
            inventory.setItem(slot, filler);
        }
    }

    private ItemStack createEnhanceButton() {
        ItemStack button = new ItemStack(Material.ANVIL);
        ItemMeta meta = button.getItemMeta();
        meta.displayName(Component.text("강화 시도", NamedTextColor.GREEN));
        meta.lore(List.of(
                Component.text("강화할 아이템을 왼쪽 슬롯에 넣고", NamedTextColor.GRAY),
                Component.text("클릭하세요.", NamedTextColor.GRAY)
        ));
        button.setItemMeta(meta);
        return button;
    }

    private ItemStack createEmptyInfoItem() {
        ItemStack info = new ItemStack(Material.BARRIER);
        ItemMeta meta = info.getItemMeta();
        meta.displayName(Component.text("강화 정보", NamedTextColor.YELLOW));
        meta.lore(List.of(Component.text("강화할 아이템을 넣어주세요.", NamedTextColor.GRAY)));
        info.setItemMeta(meta);
        return info;
    }

    private ItemStack createInvalidInfoItem() {
        ItemStack info = new ItemStack(Material.BARRIER);
        ItemMeta meta = info.getItemMeta();
        meta.displayName(Component.text("강화 불가", NamedTextColor.RED));
        meta.lore(List.of(Component.text("강화할 수 없는 아이템입니다.", NamedTextColor.GRAY)));
        info.setItemMeta(meta);
        return info;
    }

    private ItemStack createProbabilityInfo(ItemStack targetItem) {
        EnhancementItem.EnhancementTier tier = EnhancementItem.getTier(EnhancementItem.getLevel(targetItem));
        ItemStack info = new ItemStack(Material.PAPER);
        ItemMeta meta = info.getItemMeta();
        meta.displayName(Component.text("강화 확률 정보", NamedTextColor.AQUA));
        meta.lore(List.of(
                Component.text("현재 단계: ", NamedTextColor.GRAY)
                        .append(Component.text("+" + tier.level(), NamedTextColor.GREEN)),
                Component.empty(),
                chanceLine("성공: ", tier.successChance(), NamedTextColor.GREEN),
                chanceLine("유지: ", tier.maintainChance(), NamedTextColor.YELLOW),
                chanceLine("하락: ", tier.downgradeChance(), NamedTextColor.RED),
                Component.empty(),
                Component.text("필요 강화석: ", NamedTextColor.GRAY)
                        .append(Component.text(tier.stoneGrade().displayName(), tier.stoneGrade().color()))
        ));
        info.setItemMeta(meta);
        return info;
    }

    private Component chanceLine(String label, double chance, NamedTextColor color) {
        String formattedChance = chance == Math.rint(chance)
                ? String.format("%.0f", chance)
                : String.valueOf(chance);
        return Component.text(label, NamedTextColor.GRAY)
                .append(Component.text(formattedChance + "%", color));
    }
}

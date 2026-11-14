package com.brassfield.shop;

import com.brassfield.common.CommandSupport;
import com.brassfield.stone.StoneGrade;
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

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * 강화석 상점 창 (4줄).
 * 첫 줄 가운데: 보유 골드 / 2~4줄: 하급·중급·상급 강화석 (왼쪽 아이콘, 오른쪽 1개·10개·64개 구매 버튼)
 */
public final class StoneShopGui implements InventoryHolder {

    private static final int SIZE = 36;
    private static final int GOLD_SLOT = 4;
    private static final int ICON_COLUMN = 1;
    private static final int[] BUTTON_COLUMNS = {4, 5, 6};
    private static final int[] QUANTITIES = {1, 10, 64};
    private static final StoneGrade[] GRADES = {StoneGrade.LOW, StoneGrade.MIDDLE, StoneGrade.HIGH};

    private final StoneShop shop;
    private final UUID ownerId;
    private final Inventory inventory;
    private final Map<Integer, Purchase> purchases = new HashMap<>();

    StoneShopGui(StoneShop shop, UUID ownerId) {
        this.shop = shop;
        this.ownerId = ownerId;
        this.inventory = Bukkit.createInventory(this, SIZE, Component.text("강화석 상점"));
        for (int row = 0; row < GRADES.length; row++) {
            for (int i = 0; i < QUANTITIES.length; i++) {
                purchases.put(slot(row + 1, BUTTON_COLUMNS[i]), new Purchase(GRADES[row], QUANTITIES[i]));
            }
        }
        refresh();
    }

    @Override
    public @NotNull Inventory getInventory() {
        return inventory;
    }

    void open(Player player) {
        player.openInventory(inventory);
    }

    Purchase purchaseAt(int slot) {
        return purchases.get(slot);
    }

    void refresh() {
        ItemStack filler = named(new ItemStack(Material.GRAY_STAINED_GLASS_PANE), Component.empty(), List.of());
        for (int slot = 0; slot < SIZE; slot++) {
            inventory.setItem(slot, filler);
        }

        long gold = shop.goldOf(ownerId);
        inventory.setItem(GOLD_SLOT, named(new ItemStack(Material.GOLD_INGOT),
                Component.text("보유 골드", NamedTextColor.GOLD),
                List.of(Component.text(CommandSupport.formatNumber(gold) + "골드", NamedTextColor.YELLOW))));

        for (int row = 0; row < GRADES.length; row++) {
            StoneGrade grade = GRADES[row];
            inventory.setItem(slot(row + 1, ICON_COLUMN), createStoneIcon(grade));
            for (int i = 0; i < QUANTITIES.length; i++) {
                inventory.setItem(slot(row + 1, BUTTON_COLUMNS[i]), createBuyButton(grade, QUANTITIES[i], gold));
            }
        }
    }

    private ItemStack createStoneIcon(StoneGrade grade) {
        ItemStack icon;
        try {
            icon = shop.itemProvider().create(grade.iconItemId());
        } catch (IllegalStateException exception) {
            icon = new ItemStack(Material.AMETHYST_SHARD);
        }
        return named(icon, Component.text(grade.displayName() + " 강화석", grade.color()), List.of(
                Component.text("1개 가격: ", NamedTextColor.GRAY)
                        .append(Component.text(CommandSupport.formatNumber(shop.priceOf(grade)) + "골드", NamedTextColor.YELLOW)),
                Component.text("보유: ", NamedTextColor.GRAY)
                        .append(Component.text(CommandSupport.formatNumber(shop.stonesOf(ownerId, grade)) + "개", NamedTextColor.WHITE))
        ));
    }

    private ItemStack createBuyButton(StoneGrade grade, int quantity, long gold) {
        long total = shop.priceOf(grade) * quantity;
        boolean affordable = gold >= total;
        ItemStack button = new ItemStack(Material.GOLD_NUGGET, quantity);
        return named(button,
                Component.text(grade.displayName() + " 강화석 " + quantity + "개 구매",
                        affordable ? NamedTextColor.GREEN : NamedTextColor.RED),
                List.of(
                        Component.text("가격: ", NamedTextColor.GRAY)
                                .append(Component.text(CommandSupport.formatNumber(total) + "골드", NamedTextColor.YELLOW)),
                        affordable
                                ? Component.text("클릭하면 구매합니다.", NamedTextColor.GRAY)
                                : Component.text(CommandSupport.formatNumber(total - gold) + "골드가 부족합니다.", NamedTextColor.RED)
                ));
    }

    private static ItemStack named(ItemStack item, Component name, List<Component> lore) {
        ItemMeta meta = item.getItemMeta();
        meta.displayName(name);
        meta.lore(lore);
        item.setItemMeta(meta);
        return item;
    }

    private static int slot(int row, int column) {
        return row * 9 + column;
    }

    record Purchase(StoneGrade grade, int quantity) {
    }
}

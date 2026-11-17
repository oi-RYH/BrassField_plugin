package com.brassfield.shop;

import com.brassfield.common.GuiItems;
import com.brassfield.common.CommandSupport;
import com.brassfield.common.ItemsAdderGuiBackground;
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
 * 2~4줄: 하급·중급·상급 강화석 (왼쪽 아이콘, 가운데 +1·+10·+64 구매 버튼) / 3줄 오른쪽 끝: 보유 골드
 * ItemsAdder 배경(rustport:stone_shop_bg)이 있으면 배경 그림에 제목·칸 테두리가 그려져 있어 빈 칸은 비워 둔다.
 * 없으면 바닐라 창 제목과 회색 유리판으로 대신한다.
 */
public final class StoneShopGui implements InventoryHolder {

    private static final int SIZE = 36;
    private static final int GOLD_SLOT = 26;            // 3줄(중급 줄) 오른쪽 끝
    private static final String BACKGROUND_FONT_IMAGE = "rustport:stone_shop_bg";
    private static final int BACKGROUND_TITLE_OFFSET = 0;
    private static final int BACKGROUND_TEXTURE_OFFSET = -8;
    private static final String GOLD_ITEM_ID = "rustport:gold_icon";
    private static final String[] NUMBER_ITEM_IDS = {"rustport:number_1", "rustport:number_10", "rustport:number_64"};
    private static final int ICON_COLUMN = 1;
    private static final int[] BUTTON_COLUMNS = {4, 5, 6};
    private static final int[] QUANTITIES = {1, 10, 64};
    private static final StoneGrade[] GRADES = {StoneGrade.LOW, StoneGrade.MIDDLE, StoneGrade.HIGH};

    private final StoneShop shop;
    private final UUID ownerId;
    private final Inventory inventory;
    private final ItemsAdderGuiBackground.TexturedGui texturedGui;
    private final Map<Integer, Purchase> purchases = new HashMap<>();

    StoneShopGui(StoneShop shop, UUID ownerId) {
        this.shop = shop;
        this.ownerId = ownerId;
        // 배경 그림에 제목이 들어 있으므로 제목 글자 없이 연다
        this.texturedGui = shop.guiBackground().build(
                this, SIZE, "", BACKGROUND_FONT_IMAGE, BACKGROUND_TITLE_OFFSET, BACKGROUND_TEXTURE_OFFSET
        );
        this.inventory = texturedGui != null
                ? texturedGui.inventory()
                : Bukkit.createInventory(this, SIZE, Component.text("강화석 상점"));
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
        if (texturedGui != null) {
            shop.guiBackground().show(texturedGui, player);
        } else {
            player.openInventory(inventory);
        }
    }

    Purchase purchaseAt(int slot) {
        return purchases.get(slot);
    }

    void refresh() {
        ItemStack filler = texturedGui != null
                ? null
                : GuiItems.hideTooltip(named(new ItemStack(Material.GRAY_STAINED_GLASS_PANE), Component.empty(), List.of()));
        for (int slot = 0; slot < SIZE; slot++) {
            inventory.setItem(slot, filler);
        }

        long gold = shop.goldOf(ownerId);
        inventory.setItem(GOLD_SLOT, named(createGoldIcon(),
                Component.text("보유 골드", NamedTextColor.GOLD),
                List.of(Component.text(CommandSupport.formatNumber(gold) + "골드", NamedTextColor.YELLOW))));

        for (int row = 0; row < GRADES.length; row++) {
            StoneGrade grade = GRADES[row];
            inventory.setItem(slot(row + 1, ICON_COLUMN), createStoneIcon(grade));
            for (int i = 0; i < QUANTITIES.length; i++) {
                inventory.setItem(slot(row + 1, BUTTON_COLUMNS[i]), createBuyButton(grade, i, gold));
            }
        }
    }

    private ItemStack createGoldIcon() {
        try {
            return shop.itemProvider().create(GOLD_ITEM_ID);                 // 사이드바와 같은 골드 동전
        } catch (IllegalStateException exception) {
            return new ItemStack(Material.GOLD_INGOT);
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

    private ItemStack createBuyButton(StoneGrade grade, int index, long gold) {
        int quantity = QUANTITIES[index];
        long total = shop.priceOf(grade) * quantity;
        boolean affordable = gold >= total;
        ItemStack button;
        try {
            button = shop.itemProvider().create(NUMBER_ITEM_IDS[index]);      // +1 · +10 · +64 숫자 아이템
        } catch (IllegalStateException exception) {
            button = new ItemStack(Material.GOLD_NUGGET, quantity);
        }
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

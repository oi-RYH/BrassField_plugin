package com.brassfield.market;

import com.brassfield.common.CommandSupport;
import com.brassfield.common.ItemDelivery;
import com.brassfield.common.ItemsAdderGuiBackground;
import com.brassfield.common.TitleCanvas;
import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.Bukkit;
import org.bukkit.Material;
import org.bukkit.entity.HumanEntity;
import org.bukkit.entity.Player;
import org.bukkit.inventory.Inventory;
import org.bukkit.inventory.InventoryHolder;
import org.bukkit.inventory.InventoryView;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;
import org.jetbrains.annotations.NotNull;

import java.util.ArrayList;
import java.util.List;

/**
 * 종자·작물 거래기의 작물 판매 창 (6줄). 배경은 ItemsAdder 그림(rustport:crop_sell_bg, 도마).
 * 2~4줄 1~7열: 팔 작물을 올리는 도마 안쪽 칸 21개
 * 6줄: [씨앗 구매] [가격표] [모두 팔기] · 4~8열 금액 창(판매 예정 금액, 제목 글자로 표시) · [판매]
 * 나머지 칸은 투명 아이템으로 막아 Shift+클릭으로 넣은 작물이 도마 밖으로 가지 않게 한다.
 * ItemsAdder 배경이 없으면 바닐라 창(회색 유리판)으로 같은 배치를 쓴다.
 */
public final class CropSellGui implements InventoryHolder {

    static final int SIZE = 54;
    static final int SEED_TAB_SLOT = 45;
    static final int PRICE_LIST_SLOT = 46;
    static final int SELL_ALL_SLOT = 47;
    static final int SELL_SLOT = 53;
    private static final int[] TOTAL_SLOTS = {48, 49, 50, 51, 52};
    private static final int[] DEPOSIT_SLOTS = {10, 11, 12, 13, 14, 15, 16, 19, 20, 21, 22, 23, 24, 25, 28, 29, 30, 31, 32, 33, 34};
    private static final int TOTAL_RIGHT_X = 146;                  // 금액 숫자 오른쪽 끝 (창 기준 x)
    private static final String BLANK_ID = "rustport:gui_blank";

    private final CropMarket market;
    private final ItemsAdderGuiBackground.TexturedGui texturedGui;
    private final Inventory inventory;
    private long shownTotal = -1;                                   // 제목에 띄운 금액 (바뀔 때만 제목을 다시 보낸다)

    CropSellGui(CropMarket market) {
        this.market = market;
        this.texturedGui = market.guiBackground().build(this, SIZE, "", CropFont.SELL_BACKGROUND, 0, -8);
        this.inventory = texturedGui != null
                ? texturedGui.inventory()
                : Bukkit.createInventory(this, SIZE, Component.text("종자·작물 거래기 - 작물 판매"));
        ItemStack filler = filler();
        for (int slot = 0; slot < SIZE; slot++) {
            if (!isDeposit(slot)) {
                inventory.setItem(slot, filler);
            }
        }
        inventory.setItem(SEED_TAB_SLOT, named(market.icon("rustport:crop_seed_tab", new ItemStack(Material.WHEAT_SEEDS)),
                Component.text("씨앗 구매", NamedTextColor.GREEN),
                List.of(Component.text("씨앗 구매 화면으로 바꿉니다.", NamedTextColor.GRAY),
                        Component.text("올려 둔 작물은 돌려받습니다.", NamedTextColor.GRAY))));
        inventory.setItem(PRICE_LIST_SLOT, createPriceList());
        inventory.setItem(SELL_ALL_SLOT, named(market.icon("rustport:crop_sell_all", new ItemStack(Material.HOPPER)),
                Component.text("가방의 작물 모두 팔기", NamedTextColor.YELLOW),
                List.of(Component.text("가방에 있는 작물을 한 번에 팝니다.", NamedTextColor.GRAY))));
        refresh();
    }

    static boolean isDeposit(int slot) {
        for (int deposit : DEPOSIT_SLOTS) {
            if (deposit == slot) {
                return true;
            }
        }
        return false;
    }

    @Override
    public @NotNull Inventory getInventory() {
        return inventory;
    }

    void open(Player player) {
        if (texturedGui != null) {
            market.guiBackground().show(texturedGui, player);
            shownTotal = -1;
            refresh();
        } else {
            player.openInventory(inventory);
        }
    }

    CropMarket market() {
        return market;
    }

    /**
     * 판매 예정 금액(금액 창 숫자·설명)과 [판매] 버튼을 다시 그린다.
     */
    void refresh() {
        long total = 0;
        int count = 0;
        for (int slot : DEPOSIT_SLOTS) {
            ItemStack item = inventory.getItem(slot);
            long value = market.valueOf(item);
            if (value > 0) {
                total += value;
                count += item.getAmount();
            }
        }
        ItemStack info = named(texturedGui != null ? market.icon(BLANK_ID, new ItemStack(Material.GOLD_INGOT))
                        : new ItemStack(Material.GOLD_INGOT),
                Component.text("판매 예정: " + CommandSupport.formatNumber(total) + "골드", NamedTextColor.GOLD),
                List.of(Component.text("작물 " + count + "개", NamedTextColor.GRAY)));
        for (int slot : TOTAL_SLOTS) {
            inventory.setItem(slot, info);
        }
        inventory.setItem(SELL_SLOT, named(market.icon("rustport:crop_sell_button",
                        new ItemStack(total > 0 ? Material.LIME_STAINED_GLASS_PANE : Material.RED_STAINED_GLASS_PANE)),
                Component.text("판매", total > 0 ? NamedTextColor.GREEN : NamedTextColor.RED),
                List.of(total > 0
                        ? Component.text("올린 작물을 " + CommandSupport.formatNumber(total) + "골드에 팝니다.", NamedTextColor.GRAY)
                        : Component.text("도마에 팔 작물을 올려주세요.", NamedTextColor.GRAY))));
        updateTitle(total);
    }

    /**
     * 금액 창에 판매 예정 금액을 띄운다. ItemsAdder 는 창을 열 때만 배경을 넣으므로 제목 전체를 직접 조립한다.
     */
    private void updateTitle(long total) {
        if (texturedGui == null || total == shownTotal) {
            return;
        }
        shownTotal = total;
        CropFont font = market.font();
        String text = CommandSupport.formatNumber(total);
        TitleCanvas canvas = new TitleCanvas(font.glyph(CropFont.SELL_BACKGROUND), CropFont.BACKGROUND_ADVANCE);
        font.amber(canvas, TOTAL_RIGHT_X - CropFont.amberWidth(text) + 1, text);
        String title = canvas.build();
        for (HumanEntity viewer : new ArrayList<>(inventory.getViewers())) {
            InventoryView view = viewer.getOpenInventory();
            if (view.getTopInventory() == inventory) {
                view.setTitle(title);
            }
        }
    }

    /**
     * 올린 작물을 판다.
     */
    void sellDeposited(Player player) {
        List<ItemStack> items = new ArrayList<>();
        for (int slot : DEPOSIT_SLOTS) {
            ItemStack item = inventory.getItem(slot);
            if (market.isSellable(item)) {
                items.add(item);
            }
        }
        if (market.sell(player, items) > 0) {
            for (int slot : DEPOSIT_SLOTS) {
                if (market.isSellable(inventory.getItem(slot))) {
                    inventory.setItem(slot, null);
                }
            }
        }
        refresh();
    }

    /**
     * 플레이어 가방(손에 든 것·장비 칸 제외 저장 칸)의 작물을 모두 판다.
     */
    void sellFromInventory(Player player) {
        ItemStack[] contents = player.getInventory().getStorageContents();
        List<ItemStack> items = new ArrayList<>();
        for (ItemStack item : contents) {
            if (market.isSellable(item)) {
                items.add(item);
            }
        }
        if (market.sell(player, items) > 0) {
            for (int i = 0; i < contents.length; i++) {
                if (market.isSellable(contents[i])) {
                    contents[i] = null;
                }
            }
            player.getInventory().setStorageContents(contents);
        } else {
            player.sendMessage(Component.text("가방에 팔 수 있는 작물이 없습니다.", NamedTextColor.RED));
        }
    }

    /**
     * 팔지 않고 창을 닫으면 올려 둔 아이템을 돌려준다.
     */
    public void returnItemsTo(Player player) {
        for (int slot : DEPOSIT_SLOTS) {
            ItemStack item = inventory.getItem(slot);
            if (item != null && !item.getType().isAir()) {
                inventory.setItem(slot, null);
                ItemDelivery.giveOrDrop(player, item);
            }
        }
    }

    private ItemStack filler() {
        return texturedGui != null
                ? named(market.icon(BLANK_ID, new ItemStack(Material.GRAY_STAINED_GLASS_PANE)), Component.empty(), List.of())
                : named(new ItemStack(Material.GRAY_STAINED_GLASS_PANE), Component.empty(), List.of());
    }

    private ItemStack createPriceList() {
        List<Component> lore = new ArrayList<>();
        lore.add(Component.text("작물 1개 매입가 (일반 / 은별 / 금별)", NamedTextColor.GRAY));
        for (CropPrices.Entry crop : market.prices().crops()) {
            lore.add(Component.text(crop.name() + ": ", NamedTextColor.WHITE)
                    .append(Component.text(crop.normal() + " / " + crop.silver() + " / " + crop.golden() + "골드",
                            NamedTextColor.YELLOW)));
        }
        lore.add(Component.text("거대·황금 작물은 훨씬 비싸게 삽니다.", NamedTextColor.GRAY));
        return named(market.icon("rustport:crop_price_list", new ItemStack(Material.BOOK)),
                Component.text("매입 가격표", NamedTextColor.AQUA), lore);
    }

    private static ItemStack named(ItemStack item, Component name, List<Component> lore) {
        ItemMeta meta = item.getItemMeta();
        meta.displayName(name);
        meta.lore(lore);
        item.setItemMeta(meta);
        return item;
    }
}

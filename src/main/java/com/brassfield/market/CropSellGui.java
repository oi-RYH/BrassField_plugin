package com.brassfield.market;

import com.brassfield.common.CommandSupport;
import com.brassfield.common.ItemDelivery;
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

import java.util.ArrayList;
import java.util.List;

/**
 * 종자·작물 거래기의 작물 팔기 창 (6줄).
 * 1~4줄: 팔 작물을 넣는 칸 / 5줄: 구분선 / 6줄: 가격표 · [씨앗 사기] · 판매 예정 금액 · [판매] · [가방의 작물 모두 팔기]
 */
public final class CropSellGui implements InventoryHolder {

    static final int SIZE = 54;
    static final int DEPOSIT_SLOTS = 36;
    static final int PRICE_LIST_SLOT = 45;
    static final int SEED_TAB_SLOT = 46;
    static final int TOTAL_SLOT = 48;
    static final int SELL_SLOT = 50;
    static final int SELL_ALL_SLOT = 52;

    private final CropMarket market;
    private final Inventory inventory;

    CropSellGui(CropMarket market) {
        this.market = market;
        this.inventory = Bukkit.createInventory(this, SIZE, Component.text("종자·작물 거래기 - 작물 팔기"));
        ItemStack filler = named(new ItemStack(Material.GRAY_STAINED_GLASS_PANE), Component.empty(), List.of());
        for (int slot = DEPOSIT_SLOTS; slot < SIZE; slot++) {
            inventory.setItem(slot, filler);
        }
        inventory.setItem(PRICE_LIST_SLOT, createPriceList());
        inventory.setItem(SEED_TAB_SLOT, named(new ItemStack(Material.WHEAT_SEEDS),
                Component.text("씨앗 사기", NamedTextColor.GREEN),
                List.of(Component.text("씨앗 구매 화면으로 바꿉니다.", NamedTextColor.GRAY),
                        Component.text("넣어 둔 작물은 돌려받습니다.", NamedTextColor.GRAY))));
        inventory.setItem(SELL_ALL_SLOT, named(new ItemStack(Material.HOPPER),
                Component.text("가방의 작물 모두 팔기", NamedTextColor.YELLOW),
                List.of(Component.text("가방에 있는 작물을 한 번에 팝니다.", NamedTextColor.GRAY))));
        refresh();
    }

    @Override
    public @NotNull Inventory getInventory() {
        return inventory;
    }

    void open(Player player) {
        player.openInventory(inventory);
    }

    CropMarket market() {
        return market;
    }

    /**
     * 판매 예정 금액과 [판매] 버튼을 다시 그린다.
     */
    void refresh() {
        long total = 0;
        int count = 0;
        for (int slot = 0; slot < DEPOSIT_SLOTS; slot++) {
            ItemStack item = inventory.getItem(slot);
            long value = market.valueOf(item);
            if (value > 0) {
                total += value;
                count += item.getAmount();
            }
        }
        inventory.setItem(TOTAL_SLOT, named(new ItemStack(Material.GOLD_INGOT),
                Component.text("판매 예정: " + CommandSupport.formatNumber(total) + "골드", NamedTextColor.GOLD),
                List.of(Component.text("작물 " + count + "개", NamedTextColor.GRAY))));
        inventory.setItem(SELL_SLOT, total > 0
                ? named(new ItemStack(Material.LIME_STAINED_GLASS_PANE), Component.text("판매", NamedTextColor.GREEN),
                List.of(Component.text("넣은 작물을 " + CommandSupport.formatNumber(total) + "골드에 팝니다.", NamedTextColor.GRAY)))
                : named(new ItemStack(Material.RED_STAINED_GLASS_PANE), Component.text("판매", NamedTextColor.RED),
                List.of(Component.text("위 칸에 팔 작물을 넣어주세요.", NamedTextColor.GRAY))));
    }

    /**
     * 넣은 작물을 판다.
     */
    void sellDeposited(Player player) {
        List<ItemStack> items = new ArrayList<>();
        for (int slot = 0; slot < DEPOSIT_SLOTS; slot++) {
            ItemStack item = inventory.getItem(slot);
            if (market.isSellable(item)) {
                items.add(item);
            }
        }
        if (market.sell(player, items) > 0) {
            for (int slot = 0; slot < DEPOSIT_SLOTS; slot++) {
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
     * 팔지 않고 창을 닫으면 넣어 둔 아이템을 돌려준다.
     */
    public void returnItemsTo(Player player) {
        for (int slot = 0; slot < DEPOSIT_SLOTS; slot++) {
            ItemStack item = inventory.getItem(slot);
            if (item != null && !item.getType().isAir()) {
                inventory.setItem(slot, null);
                ItemDelivery.giveOrDrop(player, item);
            }
        }
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
        return named(new ItemStack(Material.BOOK), Component.text("매입 가격표", NamedTextColor.AQUA), lore);
    }

    private static ItemStack named(ItemStack item, Component name, List<Component> lore) {
        ItemMeta meta = item.getItemMeta();
        meta.displayName(name);
        meta.lore(lore);
        item.setItemMeta(meta);
        return item;
    }
}

package com.brassfield.market;

import com.brassfield.common.CommandSupport;
import com.brassfield.common.ItemDelivery;
import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.Bukkit;
import org.bukkit.Material;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Player;
import org.bukkit.inventory.Inventory;
import org.bukkit.inventory.InventoryHolder;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;
import org.jetbrains.annotations.NotNull;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * DL-7 요리 납품 창 (6줄).
 * 1~4줄: 팔 요리를 넣는 칸 / 5줄: 구분선 / 6줄: 가격표 · 판매 예정 금액 · [납품] · [가방의 요리 모두 납품]
 */
public final class FoodSellGui implements InventoryHolder {

    static final int SIZE = 54;
    static final int DEPOSIT_SLOTS = 36;
    static final int PRICE_LIST_SLOT = 45;
    static final int ORDER_SLOT = 46;
    static final int TOTAL_SLOT = 48;
    static final int SELL_SLOT = 50;
    static final int SELL_ALL_SLOT = 52;

    private final FoodMarket market;
    private final Entity robot;
    private final Inventory inventory;

    FoodSellGui(FoodMarket market, Entity robot) {
        this.market = market;
        this.robot = robot;
        this.inventory = Bukkit.createInventory(this, SIZE, Component.text("DL-7 · 납품 수령"));
        ItemStack filler = named(new ItemStack(Material.GRAY_STAINED_GLASS_PANE), Component.empty(), List.of());
        for (int slot = DEPOSIT_SLOTS; slot < SIZE; slot++) {
            inventory.setItem(slot, filler);
        }
        inventory.setItem(PRICE_LIST_SLOT, createPriceList());
        inventory.setItem(ORDER_SLOT, createOrders());
        inventory.setItem(SELL_ALL_SLOT, named(new ItemStack(Material.HOPPER),
                Component.text("가방의 요리 모두 납품", NamedTextColor.YELLOW),
                List.of(Component.text("가방에 있는 요리를 한 번에 팝니다.", NamedTextColor.GRAY))));
        refresh();
    }

    @Override
    public @NotNull Inventory getInventory() {
        return inventory;
    }

    void open(Player player) {
        player.openInventory(inventory);
    }

    FoodMarket market() {
        return market;
    }

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
                Component.text("납품 예정: " + CommandSupport.formatNumber(total) + "골드", NamedTextColor.GOLD),
                List.of(Component.text("요리 " + count + "개", NamedTextColor.GRAY))));
        inventory.setItem(SELL_SLOT, total > 0
                ? named(new ItemStack(Material.LIME_STAINED_GLASS_PANE), Component.text("납품", NamedTextColor.GREEN),
                List.of(Component.text("넣은 요리를 " + CommandSupport.formatNumber(total) + "골드에 팝니다.", NamedTextColor.GRAY)))
                : named(new ItemStack(Material.RED_STAINED_GLASS_PANE), Component.text("납품", NamedTextColor.RED),
                List.of(Component.text("위 칸에 팔 요리를 넣어주세요.", NamedTextColor.GRAY))));
    }

    void sellDeposited(Player player) {
        List<ItemStack> items = new ArrayList<>();
        for (int slot = 0; slot < DEPOSIT_SLOTS; slot++) {
            ItemStack item = inventory.getItem(slot);
            if (market.isSellable(item)) {
                items.add(item);
            }
        }
        if (market.sell(player, items, robot) > 0) {
            for (int slot = 0; slot < DEPOSIT_SLOTS; slot++) {
                if (market.isSellable(inventory.getItem(slot))) {
                    inventory.setItem(slot, null);
                }
            }
        }
        refresh();
    }

    void sellFromInventory(Player player) {
        ItemStack[] contents = player.getInventory().getStorageContents();
        List<ItemStack> items = new ArrayList<>();
        for (ItemStack item : contents) {
            if (market.isSellable(item)) {
                items.add(item);
            }
        }
        if (market.sell(player, items, robot) > 0) {
            for (int i = 0; i < contents.length; i++) {
                if (market.isSellable(contents[i])) {
                    contents[i] = null;
                }
            }
            player.getInventory().setStorageContents(contents);
        } else {
            player.sendMessage(Component.text("가방에 납품할 수 있는 요리가 없습니다.", NamedTextColor.RED));
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
        lore.add(Component.text("요리 1개 매입가 (다음 변동 " + market.nextChangeTime() + ")", NamedTextColor.GRAY));
        for (Map.Entry<String, Long> entry : market.basePrices().entrySet()) {
            String id = entry.getKey();
            double change = market.changeOf(id);
            Component line = Component.text(market.nameOf(id) + ": ", NamedTextColor.WHITE)
                    .append(Component.text(CommandSupport.formatNumber(market.priceOf(id)) + "골드", NamedTextColor.YELLOW));
            if (market.isOrdered(id)) {
                line = line.append(Component.text(" ★주문 +" + Math.round(change * 100) + "%", NamedTextColor.GOLD));
            } else if (change > 1e-9) {
                line = line.append(Component.text(" ▲" + Math.round(change * 100) + "%", NamedTextColor.GREEN));
            } else if (change < -1e-9) {
                line = line.append(Component.text(" ▼" + Math.round(-change * 100) + "%", NamedTextColor.RED));
            }
            lore.add(line);
        }
        lore.add(Component.text("많이 납품된 요리는 내리고, 덜 납품된 요리는 올립니다.", NamedTextColor.GRAY));
        return named(new ItemStack(Material.BOOK), Component.text("납품 단가표", NamedTextColor.AQUA), lore);
    }

    private ItemStack createOrders() {
        List<Component> lore = new ArrayList<>();
        if (market.orders().isEmpty()) {
            lore.add(Component.text("오늘은 주문이 없습니다.", NamedTextColor.GRAY));
        } else {
            lore.add(Component.text("오늘은 아래 요리를 +" + Math.round(market.orderBonus() * 100) + "%에 삽니다.", NamedTextColor.GRAY));
            for (String id : market.orders()) {
                lore.add(Component.text("★ " + market.nameOf(id) + ": ", NamedTextColor.GOLD)
                        .append(Component.text(CommandSupport.formatNumber(market.priceOf(id)) + "골드", NamedTextColor.YELLOW)));
            }
            lore.add(Component.text("매일 오전 6시에 바뀝니다.", NamedTextColor.GRAY));
        }
        return named(new ItemStack(Material.PAPER), Component.text("오늘의 납품 주문", NamedTextColor.GOLD), lore);
    }

    private static ItemStack named(ItemStack item, Component name, List<Component> lore) {
        ItemMeta meta = item.getItemMeta();
        meta.displayName(name);
        meta.lore(lore);
        item.setItemMeta(meta);
        return item;
    }
}

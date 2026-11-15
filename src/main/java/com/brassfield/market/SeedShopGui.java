package com.brassfield.market;

import com.brassfield.common.CommandSupport;
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
 * 종자·작물 거래기의 씨앗 사기 창 (4줄).
 * 2~3줄: 작물별 씨앗 (좌클릭 1개 · 우클릭 8개 · Shift+클릭 64개) / 4줄: [작물 팔기] · 보유 골드
 */
public final class SeedShopGui implements InventoryHolder {

    static final int SIZE = 36;
    static final int SELL_TAB_SLOT = 27;
    private static final int GOLD_SLOT = 31;
    // 씨앗 자리: 2줄 가운데 7칸, 3줄 가운데 7칸 (작물 수만큼 앞에서부터 채움)
    private static final int[] SEED_SLOTS = {10, 11, 12, 13, 14, 15, 16, 19, 20, 21, 22, 23, 24, 25};

    private final CropMarket market;
    private final UUID ownerId;
    private final Inventory inventory;
    private final Map<Integer, CropPrices.Entry> crops = new HashMap<>();

    SeedShopGui(CropMarket market, UUID ownerId) {
        this.market = market;
        this.ownerId = ownerId;
        this.inventory = Bukkit.createInventory(this, SIZE, Component.text("종자·작물 거래기 - 씨앗 사기"));
        List<CropPrices.Entry> entries = market.prices().crops();
        for (int i = 0; i < entries.size() && i < SEED_SLOTS.length; i++) {
            crops.put(SEED_SLOTS[i], entries.get(i));
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

    CropMarket market() {
        return market;
    }

    CropPrices.Entry cropAt(int slot) {
        return crops.get(slot);
    }

    void refresh() {
        ItemStack filler = named(new ItemStack(Material.GRAY_STAINED_GLASS_PANE), Component.empty(), List.of());
        for (int slot = 0; slot < SIZE; slot++) {
            inventory.setItem(slot, filler);
        }
        long gold = market.goldOf(ownerId);
        crops.forEach((slot, crop) -> inventory.setItem(slot, createSeedIcon(crop, gold)));
        inventory.setItem(SELL_TAB_SLOT, named(new ItemStack(Material.HOPPER), Component.text("작물 팔기", NamedTextColor.YELLOW),
                List.of(Component.text("작물 팔기 화면으로 바꿉니다.", NamedTextColor.GRAY))));
        inventory.setItem(GOLD_SLOT, named(new ItemStack(Material.GOLD_INGOT), Component.text("보유 골드", NamedTextColor.GOLD),
                List.of(Component.text(CommandSupport.formatNumber(gold) + "골드", NamedTextColor.YELLOW))));
    }

    private ItemStack createSeedIcon(CropPrices.Entry crop, long gold) {
        ItemStack icon;
        try {
            icon = market.itemProvider().create(crop.seedItemId());
        } catch (IllegalStateException exception) {
            icon = new ItemStack(Material.WHEAT_SEEDS);
        }
        icon.setAmount(1);
        boolean affordable = gold >= crop.seedPrice();
        return named(icon, Component.text(crop.name() + " 씨앗", affordable ? NamedTextColor.GREEN : NamedTextColor.RED), List.of(
                Component.text("1개 가격: ", NamedTextColor.GRAY)
                        .append(Component.text(CommandSupport.formatNumber(crop.seedPrice()) + "골드", NamedTextColor.YELLOW)),
                Component.text("수확물 매입가: ", NamedTextColor.GRAY)
                        .append(Component.text(crop.normal() + " / " + crop.silver() + " / " + crop.golden() + "골드", NamedTextColor.WHITE)),
                Component.empty(),
                Component.text("좌클릭 1개 · 우클릭 8개 · Shift+클릭 64개", NamedTextColor.GRAY)
        ));
    }

    private static ItemStack named(ItemStack item, Component name, List<Component> lore) {
        ItemMeta meta = item.getItemMeta();
        meta.displayName(name);
        meta.lore(lore);
        item.setItemMeta(meta);
        return item;
    }
}

package com.brassfield.market;

import com.brassfield.common.CommandSupport;
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
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * 종자·작물 거래기의 씨앗 구매 창 (6줄). 배경은 ItemsAdder 그림(rustport:seed_shop_bg, 선반).
 * 2~5줄: 한 페이지에 씨앗 봉투 12개 (1·4·7열 x 4줄, 좌클릭 1개 · 우클릭 8개 · Shift+클릭 64개).
 *        봉투 오른쪽 옆에 가격표 (제목 글자로 표시)
 * 6줄: [작물 판매] · [이전] 페이지 번호 창 [다음] · 보유 골드. 이전·다음은 넘길 페이지가 있을 때만 보인다.
 * ItemsAdder 배경이 없으면 바닐라 창(회색 유리판)으로 같은 배치를 쓴다.
 */
public final class SeedShopGui implements InventoryHolder {

    static final int SIZE = 54;
    static final int SELL_TAB_SLOT = 45;
    static final int PREV_SLOT = 48;
    static final int NEXT_SLOT = 50;
    private static final int PAGE_SLOT = 49;
    private static final int GOLD_SLOT = 53;
    // 한 페이지의 씨앗 자리: 2~5줄의 1·4·7열 (설정 순서대로 채움)
    private static final int[] SEED_SLOTS = {10, 13, 16, 19, 22, 25, 28, 31, 34, 37, 40, 43};
    private static final int PAGE_CENTER_X = 88;                    // 페이지 번호 창 가운데 (창 기준 x)
    private static final String BLANK_ID = "rustport:gui_blank";

    private final CropMarket market;
    private final UUID ownerId;
    private final ItemsAdderGuiBackground.TexturedGui texturedGui;
    private final Inventory inventory;
    private final List<CropPrices.Entry> entries;
    private final Map<Integer, CropPrices.Entry> crops = new HashMap<>();
    private int page;

    SeedShopGui(CropMarket market, UUID ownerId) {
        this.market = market;
        this.ownerId = ownerId;
        this.texturedGui = market.guiBackground().build(this, SIZE, "", CropFont.SEED_BACKGROUND, 0, -8);
        this.inventory = texturedGui != null
                ? texturedGui.inventory()
                : Bukkit.createInventory(this, SIZE, Component.text("종자·작물 거래기 - 씨앗 구매"));
        this.entries = market.prices().crops();
        refresh();
    }

    int pageCount() {
        return Math.max(1, (entries.size() + SEED_SLOTS.length - 1) / SEED_SLOTS.length);
    }

    /**
     * 페이지를 delta 만큼 넘긴다 (처음·마지막 페이지를 넘어가면 그대로).
     */
    void turnPage(int delta) {
        int next = Math.max(0, Math.min(pageCount() - 1, page + delta));
        if (next != page) {
            page = next;
            refresh();
            updateTitle();
        }
    }

    @Override
    public @NotNull Inventory getInventory() {
        return inventory;
    }

    void open(Player player) {
        if (texturedGui != null) {
            market.guiBackground().show(texturedGui, player);
            updateTitle();
        } else {
            player.openInventory(inventory);
        }
    }

    CropMarket market() {
        return market;
    }

    CropPrices.Entry cropAt(int slot) {
        return crops.get(slot);
    }

    void refresh() {
        ItemStack filler = named(texturedGui != null ? market.icon(BLANK_ID, new ItemStack(Material.GRAY_STAINED_GLASS_PANE))
                : new ItemStack(Material.GRAY_STAINED_GLASS_PANE), Component.empty(), List.of());
        for (int slot = 0; slot < SIZE; slot++) {
            inventory.setItem(slot, filler);
        }
        crops.clear();
        int first = page * SEED_SLOTS.length;
        for (int i = 0; i < SEED_SLOTS.length && first + i < entries.size(); i++) {
            crops.put(SEED_SLOTS[i], entries.get(first + i));
        }
        long gold = market.goldOf(ownerId);
        crops.forEach((slot, crop) -> inventory.setItem(slot, createSeedIcon(crop, gold)));
        int pages = pageCount();
        if (page > 0) {
            inventory.setItem(PREV_SLOT, named(market.icon("rustport:crop_page_prev", new ItemStack(Material.ARROW)),
                    Component.text("이전 페이지", NamedTextColor.YELLOW),
                    List.of(Component.text((page) + " / " + pages + " 페이지로", NamedTextColor.GRAY))));
        }
        if (page < pages - 1) {
            inventory.setItem(NEXT_SLOT, named(market.icon("rustport:crop_page_next", new ItemStack(Material.ARROW)),
                    Component.text("다음 페이지", NamedTextColor.YELLOW),
                    List.of(Component.text((page + 2) + " / " + pages + " 페이지로", NamedTextColor.GRAY))));
        }
        inventory.setItem(PAGE_SLOT, named(texturedGui != null ? market.icon(BLANK_ID, new ItemStack(Material.PAPER))
                        : new ItemStack(Material.PAPER),
                Component.text((page + 1) + " / " + pages + " 페이지", NamedTextColor.WHITE), List.of()));
        inventory.setItem(SELL_TAB_SLOT, named(market.icon("rustport:crop_sell_tab", new ItemStack(Material.HOPPER)),
                Component.text("작물 판매", NamedTextColor.YELLOW),
                List.of(Component.text("작물 판매 화면으로 바꿉니다.", NamedTextColor.GRAY))));
        inventory.setItem(GOLD_SLOT, named(market.icon("rustport:gold_icon", new ItemStack(Material.GOLD_INGOT)),
                Component.text("보유 골드", NamedTextColor.GOLD),
                List.of(Component.text(CommandSupport.formatNumber(gold) + "골드", NamedTextColor.YELLOW))));
    }

    /**
     * 페이지 번호 창 숫자와 봉투 옆 가격표를 띄운다. ItemsAdder 는 창을 열 때만 배경을 넣으므로 제목 전체를 직접 조립한다.
     */
    private void updateTitle() {
        if (texturedGui == null) {
            return;
        }
        CropFont font = market.font();
        TitleCanvas canvas = new TitleCanvas(font.glyph(CropFont.SEED_BACKGROUND), CropFont.BACKGROUND_ADVANCE);
        crops.forEach((slot, crop) -> font.priceTag(canvas, slot / 9, 7 + (slot % 9) * 18 + 18, crop.seedPrice()));
        String text = (page + 1) + "/" + pageCount();
        int width = CropFont.amberWidth(text);
        font.amber(canvas, PAGE_CENTER_X + 1 + width / 2 - width, text);
        String title = canvas.build();
        for (HumanEntity viewer : new ArrayList<>(inventory.getViewers())) {
            InventoryView view = viewer.getOpenInventory();
            if (view.getTopInventory() == inventory) {
                view.setTitle(title);
            }
        }
    }

    private ItemStack createSeedIcon(CropPrices.Entry crop, long gold) {
        String name = crop.itemId().substring(crop.itemId().indexOf(':') + 1);
        ItemStack icon = market.icon("rustport:seed_packet_" + name, market.icon(crop.seedItemId(), new ItemStack(Material.WHEAT_SEEDS)));
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

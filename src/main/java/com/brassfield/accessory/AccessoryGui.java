package com.brassfield.accessory;

import com.brassfield.accessory.AccessoryKind.Part;
import com.brassfield.common.GuiItems;
import com.brassfield.common.ItemsAdderGuiBackground;
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
 * 장신구 장착 창 (3줄). 배경 rustport:accessory_bg_{등급} (tools/gui/make_accessory_gui.py): 장착한 장신구의 최고 등급 그림.
 * 장신구 5칸:
 * 귀걸이 (0,2) · (0,6) / 목걸이 (1,4) / 반지 (2,2) · (2,6). 효과 단추: 왼쪽 기둥 (1,0) 세트 효과(왕관) · 오른쪽 기둥 (1,8) 종합 효과(크리스탈).
 * 가방의 장신구를 클릭하면 맞는 부위 빈칸에 끼우고(없으면 첫 칸과 바꿈), 끼운 칸을 클릭하면 가방으로 뺀다.
 */
public final class AccessoryGui implements InventoryHolder {

    static final int SIZE = 27;
    /** AccessoryManager.SLOT_PARTS 순서: 목걸이 · 귀걸이 왼 · 귀걸이 오 · 반지 왼 · 반지 오 */
    static final int[] SLOTS = {13, 2, 6, 20, 24};
    static final int SET_SLOT = 9;
    static final int TOTAL_SLOT = 17;
    private static final String BACKGROUND = "rustport:accessory_bg_";

    private final AccessoryManager manager;
    private final Player player;
    private final Inventory inventory;
    private final ItemsAdderGuiBackground.TexturedGui textured;
    private final AccessoryKind.Grade backgroundGrade;

    AccessoryGui(AccessoryManager manager, ItemsAdderGuiBackground background, Player player) {
        this.manager = manager;
        this.player = player;
        this.backgroundGrade = manager.highestGrade(player);
        this.textured = background.build(this, SIZE, "", BACKGROUND + backgroundGrade.id(), 0, -8);
        this.inventory = textured != null ? textured.inventory() : Bukkit.createInventory(this, SIZE, Component.text("장신구"));
        refresh();
    }

    void open(ItemsAdderGuiBackground background) {
        if (textured != null) {
            background.show(textured, player);
        } else {
            player.openInventory(inventory);
        }
    }

    /** 장착이 바뀌어 최고 등급이 달라졌으면 true → 창을 다시 열어 배경을 바꾼다 */
    boolean backgroundOutdated() {
        return textured != null && manager.highestGrade(player) != backgroundGrade;
    }

    @Override
    public @NotNull Inventory getInventory() {
        return inventory;
    }

    /** 창 칸 번호 → 장착 칸 번호 (아니면 -1) */
    static int indexOf(int rawSlot) {
        for (int i = 0; i < SLOTS.length; i++) {
            if (SLOTS[i] == rawSlot) {
                return i;
            }
        }
        return -1;
    }

    void refresh() {
        ItemStack filler = textured != null ? null
                : GuiItems.hideTooltip(new ItemStack(Material.GRAY_STAINED_GLASS_PANE));
        for (int slot = 0; slot < SIZE; slot++) {
            inventory.setItem(slot, filler);
        }
        ItemStack[] equipped = manager.slots(player);
        for (int i = 0; i < SLOTS.length; i++) {
            inventory.setItem(SLOTS[i], equipped[i] == null ? null : equipped[i].clone());
        }
        inventory.setItem(SET_SLOT, setItem());
        inventory.setItem(TOTAL_SLOT, totalItem());
    }

    private static ItemStack button(String model) {
        ItemStack item = new ItemStack(Material.PAPER);
        item.setData(io.papermc.paper.datacomponent.DataComponentTypes.ITEM_MODEL, new org.bukkit.NamespacedKey("rustport", model));
        return item;
    }

    /** 세트 효과(왕관): 세트별 장착 개수. 2세트 · 5세트 효과 내용은 아직 정하지 않았다 (노션 Q12) */
    private ItemStack setItem() {
        ItemStack item = button("accessory_set");
        ItemMeta meta = item.getItemMeta();
        meta.displayName(Accessories.plain("세트 효과", NamedTextColor.GOLD));
        java.util.Map<AccessoryKind.Set, Integer> counts = new java.util.EnumMap<>(AccessoryKind.Set.class);
        for (ItemStack equipped : manager.slots(player)) {
            Accessories.read(equipped).ifPresent(info -> counts.merge(info.set(), 1, Integer::sum));
        }
        List<Component> lore = new ArrayList<>();
        for (AccessoryKind.Set set : AccessoryKind.Set.values()) {
            int n = counts.getOrDefault(set, 0);
            lore.add(Accessories.plain(set.displayName() + " 세트 ", NamedTextColor.GRAY)
                    .append(Accessories.plain(n + " / 5", n >= 5 ? NamedTextColor.GOLD : n >= 2 ? NamedTextColor.GREEN : NamedTextColor.DARK_GRAY)));
        }
        lore.add(Component.empty());
        lore.add(Accessories.plain("같은 세트 2개 · 5개를 끼면 세트 효과 (준비 중)", NamedTextColor.DARK_GRAY));
        meta.lore(lore);
        item.setItemMeta(meta);
        return item;
    }

    /** 종합 효과(크리스탈): 장착한 장신구 기본옵션 합계 */
    private ItemStack totalItem() {
        ItemStack book = button("accessory_total");
        ItemMeta meta = book.getItemMeta();
        meta.displayName(Accessories.plain("종합 효과", NamedTextColor.GOLD));
        List<Component> lore = new ArrayList<>();
        for (Part part : Part.values()) {
            double value = manager.total(player, part);
            lore.add(value > 0 ? Accessories.optionLine(part, value)
                    : Accessories.plain(part.optionName() + " 없음", NamedTextColor.DARK_GRAY));
        }
        lore.add(Component.empty());
        lore.add(Accessories.plain("가방의 장신구를 클릭하면 장착", NamedTextColor.GRAY));
        lore.add(Accessories.plain("장착한 장신구를 클릭하면 해제", NamedTextColor.GRAY));
        meta.lore(lore);
        book.setItemMeta(meta);
        return book;
    }
}

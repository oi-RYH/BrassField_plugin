package com.brassfield.shop;

import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.inventory.InventoryClickEvent;
import org.bukkit.event.inventory.InventoryDragEvent;

/**
 * 강화석 상점 창: 아이템을 넣거나 빼는 조작은 모두 막고, 구매 버튼 클릭만 처리한다.
 */
public final class StoneShopListener implements Listener {

    private final StoneShop shop;

    public StoneShopListener(StoneShop shop) {
        this.shop = shop;
    }

    @EventHandler
    public void onInventoryClick(InventoryClickEvent event) {
        if (!(event.getInventory().getHolder() instanceof StoneShopGui gui)) {
            return;
        }
        event.setCancelled(true);

        if (event.getClickedInventory() != event.getView().getTopInventory()
                || !(event.getWhoClicked() instanceof Player player)) {
            return;
        }
        StoneShopGui.Purchase purchase = gui.purchaseAt(event.getRawSlot());
        if (purchase == null) {
            return;
        }

        shop.purchase(player, purchase.grade(), purchase.quantity());
        gui.refresh();
    }

    @EventHandler
    public void onInventoryDrag(InventoryDragEvent event) {
        if (event.getInventory().getHolder() instanceof StoneShopGui) {
            event.setCancelled(true);
        }
    }
}

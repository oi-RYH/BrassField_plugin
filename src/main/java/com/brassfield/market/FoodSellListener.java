package com.brassfield.market;

import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.inventory.ClickType;
import org.bukkit.event.inventory.InventoryAction;
import org.bukkit.event.inventory.InventoryClickEvent;
import org.bukkit.event.inventory.InventoryCloseEvent;
import org.bukkit.event.inventory.InventoryDragEvent;
import org.bukkit.inventory.ItemStack;
import org.bukkit.plugin.java.JavaPlugin;

/**
 * DL-7 납품 창: 위 4줄에는 매입하는 요리만 넣고 뺄 수 있고, 아래 줄은 버튼만 동작한다.
 */
public final class FoodSellListener implements Listener {

    private final JavaPlugin plugin;

    public FoodSellListener(JavaPlugin plugin) {
        this.plugin = plugin;
    }

    @EventHandler
    public void onInventoryClick(InventoryClickEvent event) {
        if (!(event.getInventory().getHolder() instanceof FoodSellGui gui)
                || !(event.getWhoClicked() instanceof Player player)) {
            return;
        }
        FoodMarket market = gui.market();
        if (event.getAction() == InventoryAction.COLLECT_TO_CURSOR) {
            event.setCancelled(true);
            return;
        }
        boolean clickedTop = event.getClickedInventory() == event.getView().getTopInventory();
        int slot = event.getRawSlot();

        if (clickedTop && slot >= FoodSellGui.DEPOSIT_SLOTS) {
            event.setCancelled(true);
            if (slot == FoodSellGui.SELL_SLOT) {
                gui.sellDeposited(player);
            } else if (slot == FoodSellGui.SELL_ALL_SLOT) {
                gui.sellFromInventory(player);
            }
            return;
        }

        if (clickedTop) {
            ItemStack incoming = event.getClick() == ClickType.NUMBER_KEY
                    ? player.getInventory().getItem(event.getHotbarButton())
                    : event.getCursor();
            if (incoming != null && !incoming.getType().isAir() && !market.isSellable(incoming)) {
                event.setCancelled(true);
                player.sendMessage(Component.text("DL-7이 받는 요리만 넣을 수 있습니다.", NamedTextColor.RED));
                return;
            }
        } else if (event.isShiftClick() && !market.isSellable(event.getCurrentItem())) {
            event.setCancelled(true);
            return;
        }
        plugin.getServer().getScheduler().runTask(plugin, gui::refresh);
    }

    @EventHandler
    public void onInventoryDrag(InventoryDragEvent event) {
        if (!(event.getInventory().getHolder() instanceof FoodSellGui gui)) {
            return;
        }
        boolean touchesTop = false;
        for (int slot : event.getRawSlots()) {
            if (slot >= FoodSellGui.SIZE) {
                continue;
            }
            touchesTop = true;
            if (slot >= FoodSellGui.DEPOSIT_SLOTS) {
                event.setCancelled(true);
                return;
            }
        }
        if (touchesTop && !gui.market().isSellable(event.getOldCursor())) {
            event.setCancelled(true);
            return;
        }
        plugin.getServer().getScheduler().runTask(plugin, gui::refresh);
    }

    @EventHandler
    public void onInventoryClose(InventoryCloseEvent event) {
        if (event.getInventory().getHolder() instanceof FoodSellGui gui && event.getPlayer() instanceof Player player) {
            gui.returnItemsTo(player);
        }
    }
}

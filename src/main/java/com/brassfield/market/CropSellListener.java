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
 * 작물 매입 창: 위 4줄에는 작물만 넣고 뺄 수 있고, 아래 줄은 버튼만 동작한다.
 */
public final class CropSellListener implements Listener {

    private final JavaPlugin plugin;

    public CropSellListener(JavaPlugin plugin) {
        this.plugin = plugin;
    }

    @EventHandler
    public void onInventoryClick(InventoryClickEvent event) {
        if (!(event.getInventory().getHolder() instanceof CropSellGui gui)
                || !(event.getWhoClicked() instanceof Player player)) {
            return;
        }
        CropMarket market = gui.market();
        if (event.getAction() == InventoryAction.COLLECT_TO_CURSOR) {
            // 더블클릭 모으기는 창의 버튼까지 끌어올 수 있어 막는다
            event.setCancelled(true);
            return;
        }
        boolean clickedTop = event.getClickedInventory() == event.getView().getTopInventory();
        int slot = event.getRawSlot();

        if (clickedTop && slot >= CropSellGui.DEPOSIT_SLOTS) {
            event.setCancelled(true);
            if (slot == CropSellGui.SELL_SLOT) {
                gui.sellDeposited(player);
            } else if (slot == CropSellGui.SELL_ALL_SLOT) {
                gui.sellFromInventory(player);
            } else if (slot == CropSellGui.SEED_TAB_SLOT) {
                // 창을 바꾸면 닫기 이벤트로 넣어 둔 작물이 돌아온다
                plugin.getServer().getScheduler().runTask(plugin, () -> market.openSeeds(player));
            }
            return;
        }

        if (clickedTop) {
            // 작물 칸: 손에 든(또는 숫자 키로 바꾸는) 아이템이 작물이 아니면 넣지 못하게 한다
            ItemStack incoming = event.getClick() == ClickType.NUMBER_KEY
                    ? player.getInventory().getItem(event.getHotbarButton())
                    : event.getCursor();
            if (incoming != null && !incoming.getType().isAir() && !market.isSellable(incoming)) {
                event.setCancelled(true);
                player.sendMessage(Component.text("작물만 넣을 수 있습니다.", NamedTextColor.RED));
                return;
            }
        } else if (event.isShiftClick()) {
            // 가방에서 Shift+클릭: 작물만 창으로 옮긴다
            if (!market.isSellable(event.getCurrentItem())) {
                event.setCancelled(true);
                return;
            }
        }
        scheduleRefresh(gui);
    }

    @EventHandler
    public void onSeedShopClick(InventoryClickEvent event) {
        if (!(event.getInventory().getHolder() instanceof SeedShopGui gui)
                || !(event.getWhoClicked() instanceof Player player)) {
            return;
        }
        event.setCancelled(true);
        if (event.getClickedInventory() != event.getView().getTopInventory()) {
            return;
        }
        int slot = event.getRawSlot();
        if (slot == SeedShopGui.SELL_TAB_SLOT) {
            plugin.getServer().getScheduler().runTask(plugin, () -> gui.market().open(player));
            return;
        }
        CropPrices.Entry crop = gui.cropAt(slot);
        if (crop == null) {
            return;
        }
        int amount = event.isShiftClick() ? 64 : (event.isRightClick() ? 8 : 1);
        gui.market().buySeeds(player, crop, amount);
        gui.refresh();
    }

    @EventHandler
    public void onSeedShopDrag(InventoryDragEvent event) {
        if (event.getInventory().getHolder() instanceof SeedShopGui) {
            event.setCancelled(true);
        }
    }

    @EventHandler
    public void onInventoryDrag(InventoryDragEvent event) {
        if (!(event.getInventory().getHolder() instanceof CropSellGui gui)) {
            return;
        }
        boolean touchesTop = false;
        for (int slot : event.getRawSlots()) {
            if (slot >= CropSellGui.SIZE) {
                continue;
            }
            touchesTop = true;
            if (slot >= CropSellGui.DEPOSIT_SLOTS) {
                event.setCancelled(true);
                return;
            }
        }
        if (touchesTop && !gui.market().isSellable(event.getOldCursor())) {
            event.setCancelled(true);
            return;
        }
        scheduleRefresh(gui);
    }

    @EventHandler
    public void onInventoryClose(InventoryCloseEvent event) {
        if (event.getInventory().getHolder() instanceof CropSellGui gui && event.getPlayer() instanceof Player player) {
            gui.returnItemsTo(player);
        }
    }

    private void scheduleRefresh(CropSellGui gui) {
        plugin.getServer().getScheduler().runTask(plugin, gui::refresh);
    }
}

package com.brassfield.cooking;

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
import org.bukkit.inventory.Inventory;
import org.bukkit.inventory.ItemStack;
import org.bukkit.plugin.java.JavaPlugin;

import java.util.Set;

/**
 * 요리 기계 창의 클릭 규칙.
 * <ul>
 *   <li>재료 칸(3x3): 레시피에 쓰이는 재료만 넣고 뺄 수 있다.</li>
 *   <li>완성품 칸·부산물(빈 그릇) 칸: 꺼내기만 할 수 있다.</li>
 *   <li>가방에서 Shift+클릭하면 재료만 재료 칸으로 옮긴다.</li>
 * </ul>
 * 재료가 바뀌면 바뀌기 전까지 익은 것을 먼저 정산하고, 바뀐 뒤 다음 틱에 다시 계산한다.
 */
public final class CookingListener implements Listener {

    private static final Set<InventoryAction> TAKE_ACTIONS = Set.of(
            InventoryAction.PICKUP_ALL, InventoryAction.PICKUP_HALF, InventoryAction.PICKUP_ONE,
            InventoryAction.PICKUP_SOME, InventoryAction.MOVE_TO_OTHER_INVENTORY, InventoryAction.DROP_ONE_SLOT,
            InventoryAction.DROP_ALL_SLOT);

    private final JavaPlugin plugin;

    public CookingListener(JavaPlugin plugin) {
        this.plugin = plugin;
    }

    @EventHandler
    public void onMachineClick(InventoryClickEvent event) {
        if (!(event.getInventory().getHolder() instanceof CookingMachine machine)
                || !(event.getWhoClicked() instanceof Player player)) {
            return;
        }
        if (event.getAction() == InventoryAction.COLLECT_TO_CURSOR) {
            // 더블클릭 모으기는 완성품·재료 칸에서 끌어올 수 있어 막는다
            event.setCancelled(true);
            return;
        }
        CookingRecipes recipes = machine.recipes();
        boolean clickedTop = event.getClickedInventory() == event.getView().getTopInventory();
        int slot = event.getRawSlot();
        long now = System.currentTimeMillis();

        if (!clickedTop) {
            if (event.isShiftClick()) {
                event.setCancelled(true);
                ItemStack item = event.getCurrentItem();
                if (item == null || item.getType().isAir()) {
                    return;
                }
                if (!recipes.isIngredient(item)) {
                    player.sendMessage(Component.text("요리 재료만 넣을 수 있습니다.", NamedTextColor.RED));
                    return;
                }
                machine.update(now);
                ItemStack rest = moveIntoIngredients(machine.getInventory(), item);
                event.setCurrentItem(rest);
                changed(machine);
            }
            return;
        }

        if (slot == CookingMachine.BOOK_SLOT) {
            event.setCancelled(true);
            plugin.getServer().getScheduler().runTask(plugin, () -> new RecipeBookGui(machine).open(player));
            return;
        }
        if (slot == CookingMachine.OUTPUT_SLOT || CookingMachine.isByproductSlot(slot)) {
            if (!TAKE_ACTIONS.contains(event.getAction())) {
                event.setCancelled(true);
                return;
            }
            machine.update(now);
            changed(machine);
            return;
        }
        if (!CookingMachine.isIngredientSlot(slot)) {
            event.setCancelled(true);
            return;
        }
        ItemStack incoming = event.getClick() == ClickType.NUMBER_KEY
                ? player.getInventory().getItem(event.getHotbarButton())
                : event.getClick() == ClickType.SWAP_OFFHAND ? player.getInventory().getItemInOffHand() : event.getCursor();
        if (incoming != null && !incoming.getType().isAir() && !recipes.isIngredient(incoming)) {
            event.setCancelled(true);
            player.sendMessage(Component.text("요리 재료만 넣을 수 있습니다.", NamedTextColor.RED));
            return;
        }
        // 바뀌기 전까지 익은 만큼 먼저 정산
        machine.update(now);
        changed(machine);
    }

    @EventHandler
    public void onMachineDrag(InventoryDragEvent event) {
        if (!(event.getInventory().getHolder() instanceof CookingMachine machine)) {
            return;
        }
        int topSize = event.getView().getTopInventory().getSize();
        for (int slot : event.getRawSlots()) {
            if (slot < topSize && !CookingMachine.isIngredientSlot(slot)) {
                event.setCancelled(true);
                return;
            }
        }
        if (event.getRawSlots().stream().anyMatch(slot -> slot < topSize)
                && !machine.recipes().isIngredient(event.getOldCursor())) {
            event.setCancelled(true);
            return;
        }
        machine.update(System.currentTimeMillis());
        changed(machine);
    }

    @EventHandler
    public void onMachineClose(InventoryCloseEvent event) {
        if (event.getInventory().getHolder() instanceof CookingMachine machine) {
            machine.update(System.currentTimeMillis());
            machine.machines().save();
        }
    }

    @EventHandler
    public void onRecipeBookClick(InventoryClickEvent event) {
        if (!(event.getInventory().getHolder() instanceof RecipeBookGui gui)
                || !(event.getWhoClicked() instanceof Player player)) {
            return;
        }
        event.setCancelled(true);
        if (event.getRawSlot() == RecipeBookGui.BACK_SLOT) {
            plugin.getServer().getScheduler().runTask(plugin, () -> gui.machine().open(player));
        }
    }

    @EventHandler
    public void onRecipeBookDrag(InventoryDragEvent event) {
        if (event.getInventory().getHolder() instanceof RecipeBookGui) {
            event.setCancelled(true);
        }
    }

    /**
     * 클릭으로 칸이 바뀐 뒤(다음 틱) 레시피를 다시 맞춰 보고 진행을 새로 그린다.
     */
    private void changed(CookingMachine machine) {
        machine.machines().markDirty();
        plugin.getServer().getScheduler().runTask(plugin, () -> machine.update(System.currentTimeMillis()));
    }

    /**
     * 아이템을 재료 칸으로 옮긴다: 같은 아이템이 든 칸부터 채우고, 남으면 빈 칸에. 다 못 넣은 나머지를 돌려준다.
     */
    private static ItemStack moveIntoIngredients(Inventory inventory, ItemStack item) {
        ItemStack rest = item.clone();
        for (int pass = 0; pass < 2 && rest.getAmount() > 0; pass++) {
            for (int slot : CookingMachine.INGREDIENT_SLOTS) {
                ItemStack current = inventory.getItem(slot);
                boolean empty = current == null || current.getType().isAir();
                if (pass == 0 && !empty && current.isSimilar(rest)) {
                    int move = Math.min(rest.getAmount(), current.getMaxStackSize() - current.getAmount());
                    current.setAmount(current.getAmount() + move);
                    rest.setAmount(rest.getAmount() - move);
                } else if (pass == 1 && empty) {
                    inventory.setItem(slot, rest.clone());
                    rest.setAmount(0);
                }
                if (rest.getAmount() == 0) {
                    break;
                }
            }
        }
        return rest.getAmount() == 0 ? null : rest;
    }
}

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
import org.bukkit.inventory.ItemStack;
import org.bukkit.plugin.java.JavaPlugin;

/**
 * 요리 기계 창의 클릭 규칙. 위 창의 칸은 진짜 아이템 칸이 아니라 보관 개수를 보여 주는 그림이라 모든 클릭을 막고 직접 처리한다.
 * <ul>
 *   <li>가방에서 Shift+클릭: 걸린 요리의 재료면 그 묶음을 통째로 넣는다.</li>
 *   <li>재료 칸: 아이템을 들고 클릭하면 넣기, 빈손 클릭은 한 묶음 꺼내기, Shift+클릭은 가방에 들어가는 만큼 꺼내기.</li>
 *   <li>접시: 클릭 한 묶음, Shift+클릭 모두 꺼내기. 빈 그릇 칸: 클릭하면 가방에 들어가는 만큼.</li>
 *   <li>레시피 책 칸: 레시피 책을 연다 (요리 고르기).</li>
 *   <li>화덕 문 불 버튼: 조리 시작·멈춤.</li>
 * </ul>
 * 바꾸기 전에 그때까지 익은 것을 먼저 정산한다.
 */
public final class CookingListener implements Listener {

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
        boolean clickedTop = event.getClickedInventory() == event.getView().getTopInventory();
        if (!clickedTop) {
            if (event.getAction() == InventoryAction.COLLECT_TO_CURSOR) {
                event.setCancelled(true);                   // 더블클릭 모으기가 위 창 그림 아이템을 끌어오지 않게
                return;
            }
            if (!event.isShiftClick()) {
                return;                                     // 가방 안 정리는 자유롭게
            }
            event.setCancelled(true);
            ItemStack item = event.getCurrentItem();
            if (item == null || item.getType().isAir()) {
                return;
            }
            long now = System.currentTimeMillis();
            machine.update(now);
            ItemStack rest = deposit(player, machine, item);
            if (rest != item) {
                event.setCurrentItem(rest);
                changed(machine);
            }
            return;
        }

        event.setCancelled(true);
        int slot = event.getRawSlot();
        long now = System.currentTimeMillis();
        if (machine.layout().isBook(slot)) {
            plugin.getServer().getScheduler().runTask(plugin, () -> new RecipeBookGui(machine).open(player));
            return;
        }
        machine.update(now);
        if (slot == machine.layout().fireSlot()) {
            machine.toggleFire(player);
        } else if (machine.layout().isIngredient(slot)) {
            ItemStack cursor = event.getCursor();
            if (cursor != null && !cursor.getType().isAir()) {
                ItemStack rest = deposit(player, machine, cursor);
                if (rest != cursor) {
                    player.setItemOnCursor(rest);
                }
            } else if (event.getClick() == ClickType.LEFT || event.getClick() == ClickType.RIGHT || event.isShiftClick()) {
                int index = CookLayout.indexOf(machine.layout().ingredientSlots(), slot);
                machine.withdrawIngredient(player, index, event.isShiftClick());
            }
        } else if (machine.layout().isOutput(slot)) {
            if (event.getClick() == ClickType.LEFT || event.getClick() == ClickType.RIGHT || event.isShiftClick()) {
                machine.withdrawOutput(player, event.isShiftClick());
            }
        } else if (machine.layout().isByproduct(slot)) {
            machine.withdrawByproduct(player, CookLayout.indexOf(machine.layout().byproductSlots(), slot));
        } else {
            return;
        }
        changed(machine);
    }

    /**
     * 재료 넣기. 걸린 요리가 없거나 그 재료가 아니면 알려 주고 그대로 돌려준다.
     */
    private static ItemStack deposit(Player player, CookingMachine machine, ItemStack item) {
        if (machine.pinned() == null) {
            player.sendMessage(Component.text("먼저 레시피 책에서 만들 요리를 거세요.", NamedTextColor.RED));
            return item;
        }
        if (machine.ingredientOf(item) == null) {
            player.sendMessage(Component.text("걸린 요리의 재료만 넣을 수 있습니다.", NamedTextColor.RED));
            return item;
        }
        ItemStack rest = machine.deposit(item);
        if (rest != null && rest.getAmount() == item.getAmount()) {
            player.sendMessage(Component.text("이 재료는 더 넣을 수 없습니다 (최대 " + String.format("%,d", CookingMachine.STOCK_LIMIT) + "개).",
                    NamedTextColor.RED));
            return item;
        }
        return rest;
    }

    @EventHandler
    public void onMachineDrag(InventoryDragEvent event) {
        if (!(event.getInventory().getHolder() instanceof CookingMachine)) {
            return;
        }
        int topSize = event.getView().getTopInventory().getSize();
        if (event.getRawSlots().stream().anyMatch(slot -> slot < topSize)) {
            event.setCancelled(true);
        }
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
        if (event.getClickedInventory() == event.getView().getTopInventory()) {
            gui.click(player, event.getRawSlot());
        }
    }

    @EventHandler
    public void onRecipeBookDrag(InventoryDragEvent event) {
        if (event.getInventory().getHolder() instanceof RecipeBookGui) {
            event.setCancelled(true);
        }
    }

    /**
     * 바뀐 내용을 저장 대상으로 표시하고 창을 새로 그린다.
     */
    private void changed(CookingMachine machine) {
        machine.machines().markDirty();
        machine.update(System.currentTimeMillis());
    }
}

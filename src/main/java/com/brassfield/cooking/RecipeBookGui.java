package com.brassfield.cooking;

import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.Bukkit;
import org.bukkit.Material;
import org.bukkit.entity.Player;
import org.bukkit.inventory.Inventory;
import org.bukkit.inventory.InventoryHolder;
import org.bukkit.inventory.ItemStack;
import org.jetbrains.annotations.NotNull;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * 요리 기계의 레시피 보기 창 (읽기 전용). 요리마다 재료·조리 시간을 보여 주고, [돌아가기]로 조리칸에 돌아간다.
 */
public final class RecipeBookGui implements InventoryHolder {

    static final int SIZE = 54;
    static final int BACK_SLOT = 49;

    private final CookingMachine machine;
    private final Inventory inventory;

    RecipeBookGui(CookingMachine machine) {
        this.machine = machine;
        this.inventory = Bukkit.createInventory(this, SIZE, Component.text(machine.station().title() + " - 레시피"));
        CookingMachines machines = machine.machines();
        List<CookingRecipes.Recipe> recipes = machine.recipes().recipes();
        for (int i = 0; i < recipes.size() && i < 45; i++) {
            inventory.setItem(i, icon(machines, recipes.get(i)));
        }
        ItemStack filler = CookingMachine.named(new ItemStack(Material.GRAY_STAINED_GLASS_PANE), Component.empty(), List.of());
        for (int slot = 45; slot < SIZE; slot++) {
            inventory.setItem(slot, filler);
        }
        inventory.setItem(BACK_SLOT, CookingMachine.named(new ItemStack(Material.ARROW), Component.text("돌아가기", NamedTextColor.YELLOW),
                List.of(Component.text("조리칸으로 돌아갑니다.", NamedTextColor.GRAY))));
    }

    @Override
    public @NotNull Inventory getInventory() {
        return inventory;
    }

    CookingMachine machine() {
        return machine;
    }

    void open(Player player) {
        player.openInventory(inventory);
    }

    private static ItemStack icon(CookingMachines machines, CookingRecipes.Recipe recipe) {
        ItemStack icon;
        try {
            icon = machines.createResult(recipe.resultId());
        } catch (IllegalStateException exception) {
            icon = new ItemStack(Material.BOWL);
        }
        List<Component> lore = new ArrayList<>();
        lore.add(Component.text("재료", NamedTextColor.GOLD));
        for (Map.Entry<String, Integer> entry : recipe.ingredients().entrySet()) {
            lore.add(Component.text(" · ", NamedTextColor.DARK_GRAY)
                    .append(machines.displayName(entry.getKey()).color(NamedTextColor.WHITE))
                    .append(Component.text(" x" + entry.getValue(), NamedTextColor.GRAY)));
        }
        lore.add(Component.empty());
        lore.add(Component.text("조리 시간 ", NamedTextColor.GRAY).append(Component.text(recipe.seconds() + "초", NamedTextColor.YELLOW)));
        if (recipe.amount() > 1) {
            lore.add(Component.text("한 번에 ", NamedTextColor.GRAY).append(Component.text(recipe.amount() + "개", NamedTextColor.YELLOW)));
        }
        return CookingMachine.named(icon, machines.resultName(recipe.resultId()), lore);
    }
}

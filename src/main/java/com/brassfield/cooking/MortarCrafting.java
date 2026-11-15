package com.brassfield.cooking;

import com.brassfield.common.ItemsAdderItemProvider;
import org.bukkit.Material;
import org.bukkit.entity.HumanEntity;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.inventory.InventoryClickEvent;
import org.bukkit.event.inventory.InventoryType;
import org.bukkit.event.inventory.PrepareItemCraftEvent;
import org.bukkit.inventory.CraftingInventory;
import org.bukkit.inventory.ItemStack;
import org.bukkit.plugin.java.JavaPlugin;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * 절구 (HarvestCraft 도구처럼 들고 다니며 제작 칸에서 쓰는 도구).
 * <ul>
 *   <li>제작대·인벤토리 제작 칸에 절구 하나와 절구 레시피 재료를 넣으면 결과 칸에 결과가 보인다.</li>
 *   <li>결과를 꺼내면 재료만 줄고 절구는 그대로 남는다. Shift+클릭은 재료가 다할 때까지 한 번에 만든다.</li>
 *   <li>물병·물 양동이·우유 양동이는 빈 병·빈 양동이로 돌려준다.</li>
 * </ul>
 * 바닐라 제작법에는 "도구가 남는" 방식이 없어 결과 칸 클릭을 직접 처리한다.
 */
public final class MortarCrafting implements Listener {

    public static final String MORTAR_ID = "rustport:mortar";
    private static final Map<String, Material> CONTAINERS = Map.of(
            "minecraft:milk_bucket", Material.BUCKET,
            "minecraft:water_bucket", Material.BUCKET,
            "minecraft:honey_bottle", Material.GLASS_BOTTLE,
            "minecraft:potion", Material.GLASS_BOTTLE);

    private final JavaPlugin plugin;
    private final CookingRecipes recipes;
    private final ItemsAdderItemProvider itemProvider;

    public MortarCrafting(JavaPlugin plugin, CookingRecipes recipes, ItemsAdderItemProvider itemProvider) {
        this.plugin = plugin;
        this.recipes = recipes;
        this.itemProvider = itemProvider;
    }

    /**
     * 제작 칸의 절구 레시피: 절구가 정확히 하나 있고 나머지 재료가 레시피와 맞을 때만.
     */
    private CookingRecipes.Match match(CraftingInventory inventory) {
        int mortars = 0;
        List<ItemStack> ingredients = new ArrayList<>();
        for (ItemStack item : inventory.getMatrix()) {
            if (item == null || item.getType().isAir()) {
                continue;
            }
            if (MORTAR_ID.equals(itemProvider.idOf(item))) {
                mortars += item.getAmount();
            } else {
                ingredients.add(item);
            }
        }
        return mortars == 1 ? recipes.match(ingredients) : null;
    }

    @EventHandler(priority = EventPriority.HIGH)
    public void onPrepare(PrepareItemCraftEvent event) {
        CookingRecipes.Match match = match(event.getInventory());
        if (match == null) {
            return;
        }
        ItemStack result = itemProvider.create(match.recipe().resultId());
        result.setAmount(match.recipe().amount());
        event.getInventory().setResult(result);
    }

    @EventHandler(priority = EventPriority.HIGH)
    public void onTakeResult(InventoryClickEvent event) {
        if (!(event.getInventory() instanceof CraftingInventory inventory)
                || event.getSlotType() != InventoryType.SlotType.RESULT
                || !(event.getWhoClicked() instanceof Player player)) {
            return;
        }
        CookingRecipes.Match match = match(inventory);
        if (match == null) {
            return;
        }
        event.setCancelled(true);
        CookingRecipes.Recipe recipe = match.recipe();
        ItemStack result = itemProvider.create(recipe.resultId());
        int perCraft = recipe.amount();

        int crafts;
        if (event.isShiftClick()) {
            crafts = match.batches();
        } else {
            // 커서로 집기: 커서가 비었거나 같은 결과이고 자리가 있을 때 한 번
            ItemStack cursor = event.getCursor();
            boolean empty = cursor == null || cursor.getType().isAir();
            if (!empty && (!cursor.isSimilar(result) || cursor.getAmount() + perCraft > cursor.getMaxStackSize())) {
                return;
            }
            crafts = 1;
        }
        if (crafts <= 0) {
            return;
        }

        consume(inventory, recipe, crafts);
        List<ItemStack> returns = new ArrayList<>();
        recipe.ingredients().forEach((ingredient, count) -> {
            // "#묶음" 재료는 실제로 쓴 아이템이 무엇인지에 따라 그릇이 다르다 → consume 에서 따로 모은다
            Material container = CONTAINERS.get(ingredient);
            if (container != null) {
                returns.add(new ItemStack(container, count * crafts));
            }
        });
        returns.addAll(lastContainers);
        lastContainers.clear();

        if (event.isShiftClick()) {
            give(player, result, perCraft * crafts);
        } else {
            ItemStack cursor = event.getCursor();
            if (cursor == null || cursor.getType().isAir()) {
                result.setAmount(perCraft);
                player.setItemOnCursor(result);
            } else {
                cursor.setAmount(cursor.getAmount() + perCraft);
                player.setItemOnCursor(cursor);
            }
        }
        for (ItemStack container : returns) {
            give(player, container, container.getAmount());
        }
        // 남은 재료로 결과 칸을 다시 계산
        plugin.getServer().getScheduler().runTask(plugin, () -> {
            CookingRecipes.Match next = match(inventory);
            if (next == null) {
                inventory.setResult(null);
            } else {
                ItemStack again = itemProvider.create(next.recipe().resultId());
                again.setAmount(next.recipe().amount());
                inventory.setResult(again);
            }
            player.updateInventory();
        });
    }

    private final List<ItemStack> lastContainers = new ArrayList<>();

    /**
     * 제작 칸에서 재료를 crafts 번 분량만큼 뺀다 (절구는 빼지 않는다). "#묶음"으로 쓴 그릇 재료의 빈 그릇은 lastContainers 에 모은다.
     */
    private void consume(CraftingInventory inventory, CookingRecipes.Recipe recipe, int crafts) {
        ItemStack[] matrix = inventory.getMatrix();
        for (Map.Entry<String, Integer> entry : recipe.ingredients().entrySet()) {
            int need = entry.getValue() * crafts;
            for (int i = 0; i < matrix.length && need > 0; i++) {
                ItemStack item = matrix[i];
                if (item == null || item.getType().isAir() || MORTAR_ID.equals(itemProvider.idOf(item))) {
                    continue;
                }
                String key = recipes.keyOf(item);
                if (key == null || !entry.getKey().equals(recipes.ingredientFor(recipe, key))) {
                    continue;
                }
                int take = Math.min(need, item.getAmount());
                if (entry.getKey().startsWith("#") && CONTAINERS.containsKey(key)) {
                    lastContainers.add(new ItemStack(CONTAINERS.get(key), take));
                }
                item.setAmount(item.getAmount() - take);
                matrix[i] = item.getAmount() == 0 ? null : item;
                need -= take;
            }
        }
        inventory.setMatrix(matrix);
    }

    private static void give(HumanEntity player, ItemStack item, int amount) {
        while (amount > 0) {
            ItemStack stack = item.clone();
            int put = Math.min(amount, stack.getMaxStackSize());
            stack.setAmount(put);
            player.getInventory().addItem(stack).values()
                    .forEach(left -> player.getWorld().dropItemNaturally(player.getLocation(), left));
            amount -= put;
        }
    }
}

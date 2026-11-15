package com.brassfield.cooking;

import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import net.kyori.adventure.text.format.TextDecoration;
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
import java.util.Map;

/**
 * 마을에 설치한 요리 기계 한 대 (조리칸 하나, 누구나 같이 씀).
 * <ul>
 *   <li>재료 칸(3x3)에 넣은 재료가 레시피와 맞으면 바로 조리를 시작하고, 재료가 남아 있는 만큼 이어서 만든다.</li>
 *   <li>진행은 실제 시간 기준이라 창을 닫거나 자리를 떠도(청크가 내려가도, 서버를 다시 켜도) 계속 익는다.
 *       창을 열거나 보고 있을 때 그동안 익은 만큼을 한꺼번에 완성품 칸으로 옮긴다.</li>
 *   <li>완성품 칸이 가득 차면 조리를 멈춘다 (꺼내면 그 묶음부터 다시 익는다).</li>
 *   <li>우유 양동이·꿀병처럼 그릇이 남는 재료를 쓰면 빈 양동이·빈 병을 부산물 칸(완성품 아래)에 돌려준다.</li>
 *   <li>기기 종류(조리대·제분기·착즙기 …)마다 창 제목과 레시피가 다르다 ({@link CookingStation}).</li>
 * </ul>
 */
public final class CookingMachine implements InventoryHolder {

    static final int SIZE = 54;
    static final int[] INGREDIENT_SLOTS = {10, 11, 12, 19, 20, 21, 28, 29, 30};
    static final int PROGRESS_SLOT = 23;
    static final int OUTPUT_SLOT = 25;
    static final int BOOK_SLOT = 49;
    static final int[] BYPRODUCT_SLOTS = {34, 35};
    /** 다 쓰고 그릇이 남는 재료 → 남는 그릇 */
    private static final Map<String, Material> CONTAINERS = Map.of(
            "minecraft:milk_bucket", Material.BUCKET,
            "minecraft:water_bucket", Material.BUCKET,
            "minecraft:honey_bottle", Material.GLASS_BOTTLE,
            "minecraft:potion", Material.GLASS_BOTTLE);

    private final CookingMachines machines;
    private final CookingStation station;
    private final String key;
    private final Inventory inventory;
    private String recipeId;
    private long startedAt = -1;
    private boolean blocked;

    CookingMachine(CookingMachines machines, CookingStation station, String key) {
        this.machines = machines;
        this.station = station;
        this.key = key;
        this.inventory = Bukkit.createInventory(this, SIZE, Component.text(station.title()));
        ItemStack filler = named(new ItemStack(Material.GRAY_STAINED_GLASS_PANE), Component.empty(), List.of());
        for (int slot = 0; slot < SIZE; slot++) {
            if (!isIngredientSlot(slot) && slot != OUTPUT_SLOT && !isByproductSlot(slot)) {
                inventory.setItem(slot, filler);
            }
        }
        inventory.setItem(BOOK_SLOT, named(new ItemStack(Material.KNOWLEDGE_BOOK), Component.text("레시피 보기", NamedTextColor.YELLOW),
                List.of(Component.text("만들 수 있는 요리와 재료를 봅니다.", NamedTextColor.GRAY))));
    }

    @Override
    public @NotNull Inventory getInventory() {
        return inventory;
    }

    String key() {
        return key;
    }

    CookingMachines machines() {
        return machines;
    }

    CookingStation station() {
        return station;
    }

    CookingRecipes recipes() {
        return station.recipes();
    }

    static boolean isByproductSlot(int slot) {
        return slot == BYPRODUCT_SLOTS[0] || slot == BYPRODUCT_SLOTS[1];
    }

    String recipeId() {
        return recipeId;
    }

    long startedAt() {
        return startedAt;
    }

    void restore(String recipeId, long startedAt) {
        this.recipeId = recipeId;
        this.startedAt = startedAt;
    }

    void open(Player player) {
        update(System.currentTimeMillis());
        player.openInventory(inventory);
    }

    static boolean isIngredientSlot(int slot) {
        for (int ingredientSlot : INGREDIENT_SLOTS) {
            if (ingredientSlot == slot) {
                return true;
            }
        }
        return false;
    }

    List<ItemStack> ingredientItems() {
        List<ItemStack> items = new ArrayList<>();
        for (int slot : INGREDIENT_SLOTS) {
            ItemStack item = inventory.getItem(slot);
            if (item != null && !item.getType().isAir()) {
                items.add(item);
            }
        }
        return items;
    }

    /**
     * 지금까지 익은 만큼 완성품 칸으로 옮기고 진행 표시를 새로 그린다. 무언가 바뀌었으면 true.
     */
    boolean update(long now) {
        boolean changed = settle(now);
        drawProgress(now);
        return changed;
    }

    private boolean settle(long now) {
        CookingRecipes.Match match = recipes().match(ingredientItems());
        blocked = false;
        if (match == null) {
            boolean changed = recipeId != null;
            recipeId = null;
            startedAt = -1;
            return changed;
        }
        CookingRecipes.Recipe recipe = match.recipe();
        if (!recipe.resultId().equals(recipeId) || startedAt < 0) {
            // 새 요리 시작 (재료를 바꿔 다른 요리가 되면 진행도 처음부터)
            recipeId = recipe.resultId();
            startedAt = now;
            return true;
        }
        long perBatch = recipe.seconds() * 1000L;
        long elapsedBatches = Math.max(0, (now - startedAt) / perBatch);
        ItemStack result = machines.createResult(recipe.resultId());
        int capacity = outputCapacity(result) / recipe.amount();
        int done = (int) Math.min(Math.min(elapsedBatches, match.batches()), capacity);
        Map<Material, Integer> containers = containersPerBatch(recipe);
        while (done > 0 && !byproductsFit(containers, done)) {
            done--;                                          // 부산물 칸이 가득 차면 그만큼만
        }
        if (done > 0) {
            consume(recipe, done);
            ItemStack output = inventory.getItem(OUTPUT_SLOT);
            if (output == null || output.getType().isAir()) {
                result.setAmount(done * recipe.amount());
                inventory.setItem(OUTPUT_SLOT, result);
            } else {
                output.setAmount(output.getAmount() + done * recipe.amount());
            }
            for (Map.Entry<Material, Integer> entry : containers.entrySet()) {
                addByproduct(entry.getKey(), entry.getValue() * done);
            }
            startedAt += done * perBatch;
        }
        if (done == match.batches()) {
            // 재료를 다 썼다
            recipeId = null;
            startedAt = -1;
        } else if (elapsedBatches > done) {
            // 완성품 칸이 가득 차 더 만들지 못함: 꺼낼 때까지 멈춘다
            blocked = true;
            startedAt = now;
        }
        return done > 0;
    }

    private int outputCapacity(ItemStack result) {
        ItemStack output = inventory.getItem(OUTPUT_SLOT);
        if (output == null || output.getType().isAir()) {
            return result.getMaxStackSize();
        }
        return output.isSimilar(result) ? Math.max(0, output.getMaxStackSize() - output.getAmount()) : 0;
    }

    /**
     * 한 번 만들 때 남는 그릇 (우유 양동이 → 빈 양동이 등)
     */
    private static Map<Material, Integer> containersPerBatch(CookingRecipes.Recipe recipe) {
        Map<Material, Integer> out = new java.util.EnumMap<>(Material.class);
        recipe.ingredients().forEach((ingredient, count) -> {
            Material container = CONTAINERS.get(ingredient);
            if (container != null) {
                out.merge(container, count, Integer::sum);
            }
        });
        return out;
    }

    /**
     * 부산물 칸 두 개에 batches 번 만든 만큼의 그릇이 들어가는지
     */
    private boolean byproductsFit(Map<Material, Integer> perBatch, int batches) {
        ItemStack[] slots = {copy(inventory.getItem(BYPRODUCT_SLOTS[0])), copy(inventory.getItem(BYPRODUCT_SLOTS[1]))};
        for (Map.Entry<Material, Integer> entry : perBatch.entrySet()) {
            int left = entry.getValue() * batches;
            for (int i = 0; i < slots.length && left > 0; i++) {
                ItemStack slot = slots[i];
                int max = entry.getKey().getMaxStackSize();
                if (slot == null) {
                    int put = Math.min(left, max);
                    slots[i] = new ItemStack(entry.getKey(), put);
                    left -= put;
                } else if (slot.getType() == entry.getKey()) {
                    int put = Math.min(left, max - slot.getAmount());
                    slot.setAmount(slot.getAmount() + put);
                    left -= put;
                }
            }
            if (left > 0) {
                return false;
            }
        }
        return true;
    }

    private void addByproduct(Material material, int count) {
        for (int slot : BYPRODUCT_SLOTS) {
            if (count <= 0) {
                return;
            }
            ItemStack item = inventory.getItem(slot);
            if (item == null || item.getType().isAir()) {
                int put = Math.min(count, material.getMaxStackSize());
                inventory.setItem(slot, new ItemStack(material, put));
                count -= put;
            } else if (item.getType() == material) {
                int put = Math.min(count, material.getMaxStackSize() - item.getAmount());
                item.setAmount(item.getAmount() + put);
                count -= put;
            }
        }
    }

    private static ItemStack copy(ItemStack item) {
        return item == null || item.getType().isAir() ? null : item.clone();
    }

    private void consume(CookingRecipes.Recipe recipe, int batches) {
        CookingRecipes recipes = recipes();
        for (Map.Entry<String, Integer> entry : recipe.ingredients().entrySet()) {
            int need = entry.getValue() * batches;
            for (int slot : INGREDIENT_SLOTS) {
                if (need == 0) {
                    break;
                }
                ItemStack item = inventory.getItem(slot);
                String itemKey = recipes.keyOf(item);
                if (itemKey == null || !entry.getKey().equals(recipes.ingredientFor(recipe, itemKey))) {
                    continue;
                }
                int take = Math.min(need, item.getAmount());
                item.setAmount(item.getAmount() - take);
                inventory.setItem(slot, item.getAmount() == 0 ? null : item);
                need -= take;
            }
        }
    }

    private void drawProgress(long now) {
        CookingRecipes.Match match = recipes().match(ingredientItems());
        if (match == null || recipeId == null) {
            inventory.setItem(PROGRESS_SLOT, named(new ItemStack(Material.CAMPFIRE), Component.text("조리 대기", NamedTextColor.GRAY), List.of(
                    Component.text("왼쪽 칸에 레시피 재료를 넣으면", NamedTextColor.GRAY),
                    Component.text("바로 조리를 시작합니다.", NamedTextColor.GRAY))));
            return;
        }
        Component dish = machines.resultName(recipeId);
        if (blocked) {
            inventory.setItem(PROGRESS_SLOT, named(new ItemStack(Material.BARRIER), Component.text("완성품 칸이 가득 찼습니다", NamedTextColor.RED), List.of(
                    Component.text("완성품이나 빈 그릇(아래 칸)을 꺼내면 다시 조리합니다.", NamedTextColor.GRAY))));
            return;
        }
        long perBatch = match.recipe().seconds() * 1000L;
        long remaining = Math.max(0, perBatch - (now - startedAt));
        long seconds = (remaining + 999) / 1000;
        inventory.setItem(PROGRESS_SLOT, named(new ItemStack(Material.CLOCK), Component.text("조리 중: ", NamedTextColor.GOLD).append(dish), List.of(
                Component.text("다음 완성까지 ", NamedTextColor.GRAY).append(Component.text(seconds + "초", NamedTextColor.YELLOW)),
                Component.text("남은 재료로 ", NamedTextColor.GRAY)
                        .append(Component.text(match.batches() * match.recipe().amount() + "개", NamedTextColor.YELLOW))
                        .append(Component.text(" 더 만듭니다.", NamedTextColor.GRAY)),
                Component.empty(),
                Component.text("창을 닫아도 계속 익습니다.", NamedTextColor.DARK_GRAY))));
    }

    static ItemStack named(ItemStack item, Component name, List<Component> lore) {
        ItemMeta meta = item.getItemMeta();
        meta.displayName(name.decoration(TextDecoration.ITALIC, false));
        meta.lore(lore.stream().map(line -> line.decoration(TextDecoration.ITALIC, false)).toList());
        item.setItemMeta(meta);
        return item;
    }
}

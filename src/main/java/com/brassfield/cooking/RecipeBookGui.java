package com.brassfield.cooking;

import com.brassfield.common.GuiItems;
import com.brassfield.common.ItemsAdderGuiBackground;
import com.brassfield.common.TitleCanvas;
import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.Bukkit;
import org.bukkit.Material;
import org.bukkit.entity.Player;
import org.bukkit.inventory.Inventory;
import org.bukkit.inventory.InventoryHolder;
import org.bukkit.inventory.InventoryView;
import org.bukkit.inventory.ItemStack;
import org.jetbrains.annotations.NotNull;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * 요리 기계의 레시피 책 (펼친 요리책 그림, 한 사람이 하나씩 연다).
 * <ul>
 *   <li>왼쪽 페이지: 이 기기 요리 3x3 (한 쪽 9개, 위 화살표로 쪽 넘김). 누르면 오른쪽 페이지에 자세히 보인다.
 *       보고 있는 요리는 금색 테, 지금 걸린 요리는 빨간 핀 (제목 글꼴 그림).</li>
 *   <li>오른쪽 페이지: 고른 요리를 2배 크기로 + 한 번에 나오는 개수, 아래에 필요한 재료와 개수.
 *       큰 요리를 누르면 그 요리를 걸고 솥 화면으로 돌아간다. 남은 재료가 있으면 한 번 더 눌러야 바뀐다.</li>
 *   <li>아래 책갈피: 바꾸지 않고 돌아가기.</li>
 * </ul>
 */
public final class RecipeBookGui implements InventoryHolder {

    static final int SIZE = 54;
    static final int[] LIST_SLOTS = {19, 20, 21, 28, 29, 30, 37, 38, 39};
    static final int PREV_SLOT = 10;
    static final int NEXT_SLOT = 12;
    static final int DISH_SLOT = 15;
    static final int[] NEED_SLOTS = {32, 33, 34, 41, 42};
    static final int BACK_SLOT = 48;
    private static final long CONFIRM_MILLIS = 5000;

    private final CookingMachine machine;
    private final ItemsAdderGuiBackground.TexturedGui texturedGui;
    private final Inventory inventory;
    private final List<CookingRecipes.Recipe> recipes;
    private int page;
    private int selected;
    private long confirmUntil;
    private String shownTitle;

    RecipeBookGui(CookingMachine machine) {
        this.machine = machine;
        this.recipes = machine.recipes().recipes();
        this.texturedGui = machine.machines().glyphs().background().build(this, SIZE, "", CookGlyphs.BOOK_BACKGROUND, 0, -8);
        this.inventory = texturedGui != null ? texturedGui.inventory()
                : Bukkit.createInventory(this, SIZE, Component.text(machine.station().title() + " - 레시피"));
        int pinned = machine.pinned() == null ? -1 : recipes.indexOf(machine.pinned());
        selected = Math.max(0, pinned);
        page = selected / LIST_SLOTS.length;
        draw();
    }

    @Override
    public @NotNull Inventory getInventory() {
        return inventory;
    }

    CookingMachine machine() {
        return machine;
    }

    void open(Player player) {
        if (texturedGui != null) {
            machine.machines().glyphs().background().show(texturedGui, player);
            shownTitle = null;
            draw();
        } else {
            player.openInventory(inventory);
        }
    }

    private int pages() {
        return Math.max(1, (recipes.size() + LIST_SLOTS.length - 1) / LIST_SLOTS.length);
    }

    // ── 클릭 ──

    void click(Player player, int slot) {
        for (int i = 0; i < LIST_SLOTS.length; i++) {
            int index = page * LIST_SLOTS.length + i;
            if (LIST_SLOTS[i] == slot && index < recipes.size()) {
                selected = index;
                confirmUntil = 0;
                draw();
                return;
            }
        }
        if (slot == PREV_SLOT && page > 0) {
            page--;
            draw();
        } else if (slot == NEXT_SLOT && page < pages() - 1) {
            page++;
            draw();
        } else if (slot == DISH_SLOT && selected < recipes.size()) {
            choose(player);
        } else if (slot == BACK_SLOT) {
            reopenMachine(player);
        }
    }

    private void choose(Player player) {
        CookingRecipes.Recipe recipe = recipes.get(selected);
        boolean same = machine.pinned() != null && machine.pinned().resultId().equals(recipe.resultId());
        if (!same && !machine.isEmpty() && System.currentTimeMillis() > confirmUntil) {
            confirmUntil = System.currentTimeMillis() + CONFIRM_MILLIS;
            player.sendMessage(Component.text("남은 재료와 접시 위 요리를 돌려받고 바꿉니다. 한 번 더 누르면 바뀝니다.", NamedTextColor.YELLOW));
            draw();
            return;
        }
        machine.pin(player, recipe);
        player.sendMessage(Component.text("만들 요리: ", NamedTextColor.GRAY)
                .append(machine.machines().resultName(recipe.resultId()).colorIfAbsent(NamedTextColor.WHITE)));
        reopenMachine(player);
    }

    private void reopenMachine(Player player) {
        CookingMachines machines = machine.machines();
        machines.plugin().getServer().getScheduler().runTask(machines.plugin(), () -> machine.open(player));
    }

    // ── 그리기 ──

    private void draw() {
        CookingMachines machines = machine.machines();
        ItemStack blank = blank();
        for (int slot = 0; slot < SIZE; slot++) {
            inventory.setItem(slot, blank);
        }
        for (int i = 0; i < LIST_SLOTS.length; i++) {
            int index = page * LIST_SLOTS.length + i;
            if (index < recipes.size()) {
                inventory.setItem(LIST_SLOTS[i], listIcon(recipes.get(index)));
            }
        }
        if (page > 0) {
            inventory.setItem(PREV_SLOT, pageIcon("rustport:crop_page_prev", "이전 쪽"));
        }
        if (page < pages() - 1) {
            inventory.setItem(NEXT_SLOT, pageIcon("rustport:crop_page_next", "다음 쪽"));
        }
        if (selected < recipes.size()) {
            CookingRecipes.Recipe recipe = recipes.get(selected);
            inventory.setItem(DISH_SLOT, dishIcon(recipe));
            List<String> keys = new ArrayList<>(recipe.ingredients().keySet());
            for (int i = 0; i < keys.size() && i < NEED_SLOTS.length; i++) {
                String key = keys.get(i);
                inventory.setItem(NEED_SLOTS[i], CookingMachine.named(machines.ingredientIcon(machine.recipes(), key),
                        machines.displayName(key).colorIfAbsent(NamedTextColor.WHITE),
                        List.of(Component.text("한 번에 " + recipe.ingredients().get(key) + "개", NamedTextColor.GRAY))));
            }
        }
        ItemStack back = CookingMachine.named(blank(), Component.text("돌아가기", NamedTextColor.YELLOW),
                List.of(Component.text("바꾸지 않고 솥 화면으로 돌아갑니다.", NamedTextColor.GRAY)));
        back.editMeta(meta -> meta.setHideTooltip(false));
        inventory.setItem(BACK_SLOT, back);
        updateTitle();
    }

    private ItemStack listIcon(CookingRecipes.Recipe recipe) {
        CookingMachines machines = machine.machines();
        ItemStack icon;
        try {
            icon = machines.createResult(recipe.resultId());
        } catch (IllegalStateException exception) {
            icon = new ItemStack(Material.BOWL);
        }
        return CookingMachine.named(icon, machines.resultName(recipe.resultId()).colorIfAbsent(NamedTextColor.WHITE), recipeLore(recipe,
                Component.text("클릭: 오른쪽 페이지에서 보기", NamedTextColor.DARK_GRAY)));
    }

    private ItemStack dishIcon(CookingRecipes.Recipe recipe) {
        CookingMachines machines = machine.machines();
        String name = recipe.resultId().substring(recipe.resultId().indexOf(':') + 1);
        ItemStack icon;
        try {
            icon = machines.itemProvider().create("rustport:cook_big_" + name);
        } catch (IllegalStateException exception) {
            try {
                icon = machines.createResult(recipe.resultId());
            } catch (IllegalStateException missing) {
                icon = new ItemStack(Material.BOWL);
            }
        }
        boolean same = machine.pinned() != null && machine.pinned().resultId().equals(recipe.resultId());
        Component action;
        if (same) {
            action = Component.text("지금 걸려 있는 요리입니다.", NamedTextColor.GREEN);
        } else if (System.currentTimeMillis() <= confirmUntil) {
            action = Component.text("한 번 더 누르면 바꿉니다 (남은 재료·요리는 돌려받음)", NamedTextColor.RED);
        } else {
            action = Component.text("클릭: 이 요리 걸기", NamedTextColor.YELLOW);
        }
        return CookingMachine.named(icon, machines.resultName(recipe.resultId()).colorIfAbsent(NamedTextColor.WHITE), recipeLore(recipe, action));
    }

    private List<Component> recipeLore(CookingRecipes.Recipe recipe, Component last) {
        CookingMachines machines = machine.machines();
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
        lore.add(last);
        return lore;
    }

    private ItemStack pageIcon(String id, String name) {
        ItemStack icon;
        try {
            icon = machine.machines().itemProvider().create(id);
        } catch (IllegalStateException exception) {
            icon = new ItemStack(Material.ARROW);
        }
        return CookingMachine.named(icon, Component.text(name + " (" + (page + 1) + "/" + pages() + ")", NamedTextColor.YELLOW), List.of());
    }

    private ItemStack blank() {
        ItemStack item;
        try {
            item = machine.machines().itemProvider().create("rustport:gui_blank");
        } catch (IllegalStateException exception) {
            item = new ItemStack(Material.GRAY_STAINED_GLASS_PANE);
        }
        return GuiItems.hideTooltip(CookingMachine.named(item, Component.empty(), List.of()));
    }

    private void updateTitle() {
        if (texturedGui == null) {
            return;
        }
        CookGlyphs glyphs = machine.machines().glyphs();
        TitleCanvas canvas = new TitleCanvas(glyphs.glyph(CookGlyphs.BOOK_BACKGROUND), CookGlyphs.BACKGROUND_ADVANCE);
        StringBuilder state = new StringBuilder().append(page).append('|').append(selected);
        int pinned = machine.pinned() == null ? -1 : recipes.indexOf(machine.pinned());
        for (int i = 0; i < LIST_SLOTS.length; i++) {
            int index = page * LIST_SLOTS.length + i;
            if (index == selected) {
                glyphs.pick(canvas, LIST_SLOTS[i]);
            }
            if (index == pinned) {
                glyphs.pin(canvas, LIST_SLOTS[i]);
                state.append("|p").append(i);
            }
        }
        if (selected < recipes.size()) {
            CookingRecipes.Recipe recipe = recipes.get(selected);
            glyphs.times(canvas, recipe.amount());
            int i = 0;
            for (int count : recipe.ingredients().values()) {
                if (i < NEED_SLOTS.length) {
                    glyphs.slotCount(canvas, "need", NEED_SLOTS[i++], String.valueOf(count));
                }
            }
        }
        String key = state.toString();
        if (key.equals(shownTitle)) {
            return;
        }
        shownTitle = key;
        String title = canvas.build();
        for (var viewer : new ArrayList<>(inventory.getViewers())) {
            InventoryView view = viewer.getOpenInventory();
            if (view.getTopInventory() == inventory) {
                view.setTitle(title);
            }
        }
    }
}

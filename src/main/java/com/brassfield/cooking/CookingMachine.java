package com.brassfield.cooking;

import com.brassfield.common.GuiItems;
import com.brassfield.common.Grades;
import com.brassfield.common.ItemsAdderGuiBackground;
import com.brassfield.common.TitleCanvas;
import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import net.kyori.adventure.text.format.TextDecoration;
import org.bukkit.Bukkit;
import org.bukkit.Material;
import org.bukkit.entity.HumanEntity;
import org.bukkit.entity.Player;
import org.bukkit.inventory.Inventory;
import org.bukkit.inventory.InventoryHolder;
import org.bukkit.inventory.InventoryView;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;
import org.jetbrains.annotations.NotNull;

import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;

/**
 * 마을에 설치한 요리 기계 한 대 (누구나 같이 씀).
 * <ul>
 *   <li>레시피 책에서 만들 요리를 하나 걸어 두면, 그 요리의 재료만 받아 개수로 쌓아 둔다 (칸 수 제한 없음, 재료당 최대 {@link #STOCK_LIMIT}개).
 *       재료는 구름 위 칸에 걸린 요리의 재료 순서대로 아이콘과 개수로 보인다.</li>
 *   <li>요리 등급 = 한 번 만들 때 쓴 재료 중 등급 있는 재료(작물·등급 요리)의 등급 평균 (일반 0 · 은별 1 · 금별 2, 소수점 버림).
 *       재료는 싼 것부터 쓴다 (일반 → 은별 → 금별). 은별·금별 요리는 &lt;요리&gt;_silver_star · _golden_star.</li>
 *   <li>화덕 문 자리 불 버튼으로 조리를 시작·멈춘다. 멈추면 만들던 1개의 진행이 남아 다시 시작하면 이어서 익는다.
 *       재료가 떨어지거나 요리를 바꾸면 꺼진다 (다시 눌러야 시작).</li>
 *   <li>켜져 있고 재료가 한 번 만들 만큼 있으면 계속 익힌다. 진행은 실제 시간 기준이라 창을 닫거나 자리를 떠도 익는다.
 *       창을 열거나 보고 있을 때 그동안 익은 만큼을 한꺼번에 접시(완성품)로 옮긴다. 완성품도 개수로 쌓인다.</li>
 *   <li>우유 양동이·꿀병처럼 그릇이 남는 재료를 쓰면 빈 양동이·빈 병을 부산물 칸에 개수로 쌓는다.</li>
 *   <li>걸린 요리를 바꾸면 남은 재료와 접시 위 요리를 바꾼 사람에게 돌려준다.</li>
 *   <li>창 그림은 기기마다 rustport:cook_&lt;기기&gt;_bg (없으면 공통 그림). 진행 게이지·개수는 제목 글꼴 그림 ({@link CookGlyphs}).</li>
 * </ul>
 */
public final class CookingMachine implements InventoryHolder {

    static final int SIZE = 54;
    static final int STOCK_LIMIT = 1728;                          // 재료 하나당 최대 보관 (27묶음)
    private static final String BLANK_ID = "rustport:gui_blank";
    /** 다 쓰고 그릇이 남는 재료 → 남는 그릇 */
    private static final Map<String, Material> CONTAINERS = Map.of(
            "minecraft:milk_bucket", Material.BUCKET,
            "minecraft:water_bucket", Material.BUCKET,
            "minecraft:honey_bottle", Material.GLASS_BOTTLE,
            "minecraft:potion", Material.GLASS_BOTTLE);

    /** 보관 중인 재료 한 종류 (같은 아이템끼리 묶음, 품질이 다르면 따로) */
    static final class Stock {
        final ItemStack sample;
        int count;

        Stock(ItemStack sample, int count) {
            this.sample = sample.asOne();
            this.count = count;
        }
    }

    private final CookingMachines machines;
    private final CookingStation station;
    private final String key;
    private final ItemsAdderGuiBackground.TexturedGui texturedGui;
    private final CookLayout layout;                               // 칸 배치 (기기 그림마다 다름, 공통 그림이면 솥 배치)
    private final Inventory inventory;
    private final List<Stock> stocks = new ArrayList<>();
    private final Map<Material, Integer> byproducts = new EnumMap<>(Material.class);
    private final List<ItemStack> legacy = new ArrayList<>();      // 예전(칸 방식) 저장에서 넘어온 아이템: 처음 연 사람에게 돌려준다
    private CookingRecipes.Recipe pinned;
    private ItemStack outputSample;                                // 접시 위 요리 (일반 등급 아이템)
    private final int[] outputs = new int[3];                      // 접시 위 요리 개수: 일반 · 은별 · 금별
    private long startedAt = -1;                                  // 켜져서 익는 중인 1개의 시작 시각 (-1 = 꺼짐)
    private long pausedProgress;                                   // 꺼질 때 만들던 1개가 익은 시간 (다시 켜면 이어서)
    private String background;
    private String shownTitle;

    CookingMachine(CookingMachines machines, CookingStation station, String key) {
        this.machines = machines;
        this.station = station;
        this.key = key;
        ItemsAdderGuiBackground gui = machines.glyphs().background();
        String wanted = CookGlyphs.machineBackground(station.key());
        background = machines.glyphs().hasBackground(wanted) ? wanted : CookGlyphs.GENERIC_BACKGROUND;   // 그림 없는 기기는 공통 그림
        layout = background.equals(wanted) ? CookLayout.of(station.key()) : CookLayout.KETTLE;
        ItemsAdderGuiBackground.TexturedGui built = gui.build(this, SIZE, "", machines.glyphs().openingBackground(background), 0, -8);
        this.texturedGui = built;
        this.inventory = built != null ? built.inventory() : Bukkit.createInventory(this, SIZE, Component.text(station.title()));
        ItemStack filler = blank(Component.empty(), List.of());
        for (int slot = 0; slot < SIZE; slot++) {
            inventory.setItem(slot, filler);
        }
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

    CookingRecipes.Recipe pinned() {
        return pinned;
    }

    long startedAt() {
        return startedAt;
    }

    long pausedProgress() {
        return pausedProgress;
    }

    boolean running() {
        return startedAt >= 0;
    }

    List<Stock> stocks() {
        return stocks;
    }

    ItemStack outputSample() {
        return outputSample;
    }

    int outputCount() {
        return outputs[0] + outputs[1] + outputs[2];
    }

    int[] outputs() {
        return outputs;
    }

    Map<Material, Integer> byproducts() {
        return byproducts;
    }

    List<ItemStack> legacy() {
        return legacy;
    }

    boolean isEmpty() {
        return stocks.isEmpty() && outputCount() == 0;
    }

    void restore(String recipeId, long startedAt, long pausedProgress, ItemStack outputSample, int[] counts) {
        this.pinned = recipeId == null ? null : recipes().byResult(recipeId);
        this.startedAt = pinned == null ? -1 : startedAt;
        this.pausedProgress = pinned == null ? 0 : Math.max(0, pausedProgress);
        this.outputSample = outputSample == null ? null : outputSample.asOne();
        for (int g = 0; g < 3; g++) {
            outputs[g] = this.outputSample == null ? 0 : counts[g];
        }
    }

    void open(Player player) {
        update(System.currentTimeMillis());
        if (!legacy.isEmpty()) {
            give(player, legacy);
            legacy.clear();
            player.sendMessage(Component.text("예전 조리칸에 남아 있던 아이템을 돌려받았습니다.", NamedTextColor.YELLOW));
            machines.markDirty();
        }
        if (texturedGui != null) {
            machines.glyphs().background().show(texturedGui, player);
            shownTitle = null;
            redraw(System.currentTimeMillis());
        } else {
            player.openInventory(inventory);
        }
    }

    CookLayout layout() {
        return layout;
    }

    // ── 조리 ──

    /**
     * 지금까지 익은 만큼 접시로 옮기고 창을 새로 그린다. 무언가 바뀌었으면 true.
     */
    boolean update(long now) {
        boolean changed = settle(now);
        redraw(now);
        return changed;
    }

    private boolean settle(long now) {
        if (pinned == null || startedAt < 0) {
            startedAt = -1;
            return false;
        }
        int batches = batchesAvailable();
        if (batches == 0) {
            startedAt = -1;                                        // 재료가 떨어지면 꺼진다
            pausedProgress = 0;
            return true;
        }
        long perBatch = pinned.seconds() * 1000L;
        int done = (int) Math.min(batches, Math.max(0, (now - startedAt) / perBatch));
        if (done == 0) {
            return false;
        }
        ItemStack result = machines.createResult(pinned.resultId());
        if (outputSample == null || !outputSample.isSimilar(result)) {
            outputSample = result.asOne();
            java.util.Arrays.fill(outputs, 0);
        }
        for (int batch = 0; batch < done; batch++) {
            int gradeSum = 0;
            int graded = 0;
            for (Map.Entry<String, Integer> entry : pinned.ingredients().entrySet()) {
                boolean gradable = machines.isGradable(entry.getKey(), recipes());
                for (ItemStack used : take(entry.getKey(), entry.getValue())) {
                    if (gradable) {
                        gradeSum += grade(used) * used.getAmount();
                        graded += used.getAmount();
                    }
                }
            }
            outputs[graded == 0 ? 0 : gradeSum / graded] += pinned.amount();
        }
        for (Map.Entry<String, Integer> entry : pinned.ingredients().entrySet()) {
            Material container = CONTAINERS.get(entry.getKey());
            if (container != null) {
                byproducts.merge(container, entry.getValue() * done, Integer::sum);
            }
        }
        if (done == batches) {
            startedAt = -1;                                        // 재료를 다 썼다: 꺼진다
            pausedProgress = 0;
        } else {
            startedAt += done * perBatch;
        }
        return true;
    }

    /** 걸린 요리를 지금 재료로 몇 번 만들 수 있는지 */
    int batchesAvailable() {
        if (pinned == null) {
            return 0;
        }
        int batches = Integer.MAX_VALUE;
        for (Map.Entry<String, Integer> entry : pinned.ingredients().entrySet()) {
            batches = Math.min(batches, stored(entry.getKey()) / entry.getValue());
        }
        return batches;
    }

    /** 레시피 재료(정확한 ID 또는 #묶음)에 맞는 보관 개수 */
    int stored(String ingredient) {
        int total = 0;
        for (Stock stock : stocks) {
            if (matches(ingredient, stock.sample)) {
                total += stock.count;
            }
        }
        return total;
    }

    private boolean matches(String ingredient, ItemStack item) {
        String itemKey = recipes().keyOf(item);
        return itemKey != null && pinned != null && ingredient.equals(recipes().ingredientFor(pinned, itemKey));
    }

    /** 레시피 재료 하나를 count 개 덜어 낸다 (싼 것부터: 일반 → 은별 → 금별). 덜어 낸 아이템 묶음을 돌려준다 */
    private List<ItemStack> take(String ingredient, int count) {
        List<ItemStack> out = new ArrayList<>();
        List<Stock> matching = new ArrayList<>(stocks.stream().filter(s -> matches(ingredient, s.sample)).toList());
        matching.sort((a, b) -> Integer.compare(grade(a.sample), grade(b.sample)));
        for (Stock stock : matching) {
            if (count == 0) {
                break;
            }
            int n = Math.min(count, stock.count);
            stock.count -= n;
            count -= n;
            out.addAll(stacks(stock.sample, n));
            if (stock.count == 0) {
                stocks.remove(stock);
            }
        }
        return out;
    }

    /**
     * 가방이나 커서의 아이템을 재료로 넣는다. 걸린 요리의 재료가 아니면 그대로, 한도를 넘는 만큼은 남겨 돌려준다.
     */
    ItemStack deposit(ItemStack item) {
        if (pinned == null || item == null || item.getType().isAir()) {
            return item;
        }
        String ingredient = ingredientOf(item);
        if (ingredient == null) {
            return item;
        }
        int room = STOCK_LIMIT - stored(ingredient);
        int put = Math.min(room, item.getAmount());
        if (put <= 0) {
            return item;
        }
        Stock target = null;
        for (Stock stock : stocks) {
            if (stock.sample.isSimilar(item)) {
                target = stock;
                break;
            }
        }
        if (target == null) {
            stocks.add(new Stock(item, put));
        } else {
            target.count += put;
        }
        ItemStack rest = item.clone();
        rest.setAmount(item.getAmount() - put);
        return rest.getAmount() == 0 ? null : rest;
    }

    /** 작물·요리 등급: 0 일반 · 1 은별 · 2 금별 */
    private int grade(ItemStack item) {
        return Grades.of(machines.itemProvider().idOf(item));
    }

    /** 걸린 요리의 어느 재료인지 (아니면 null) */
    String ingredientOf(ItemStack item) {
        String itemKey = recipes().keyOf(item);
        return itemKey == null || pinned == null ? null : recipes().ingredientFor(pinned, itemKey);
    }

    /** 재료 칸 index 의 재료를 꺼낸다: all 이면 가방에 들어가는 만큼, 아니면 한 묶음 */
    void withdrawIngredient(Player player, int index, boolean all) {
        String ingredient = ingredientAt(index);
        if (ingredient == null) {
            return;
        }
        int available = stored(ingredient);
        if (available == 0) {
            return;
        }
        ItemStack sample = stocks.stream().filter(s -> matches(ingredient, s.sample)).max((a, b) -> Integer.compare(a.count, b.count))
                .map(s -> s.sample).orElseThrow();
        int want = all ? Math.min(available, room(player, sample)) : Math.min(available, sample.getMaxStackSize());
        if (want <= 0) {
            player.sendMessage(Component.text("가방에 빈자리가 없습니다.", NamedTextColor.RED));
            return;
        }
        give(player, take(ingredient, want));
    }

    /** 접시 위 요리 꺼내기: 높은 등급부터. all 이면 가방에 들어가는 만큼, 아니면 한 묶음 */
    void withdrawOutput(Player player, boolean all) {
        if (outputSample == null || outputCount() == 0) {
            return;
        }
        boolean any = false;
        for (int g = 2; g >= 0; g--) {
            if (outputs[g] == 0) {
                continue;
            }
            ItemStack sample = graded(g);
            int want = Math.min(outputs[g], all ? room(player, sample) : sample.getMaxStackSize());
            if (want <= 0) {
                continue;
            }
            outputs[g] -= want;
            give(player, stacks(sample, want));
            any = true;
            if (!all) {
                break;
            }
        }
        if (!any) {
            player.sendMessage(Component.text("가방에 빈자리가 없습니다.", NamedTextColor.RED));
        }
        if (outputCount() == 0) {
            outputSample = null;
        }
    }

    /**
     * 불 버튼: 꺼져 있으면 켜고(만들던 1개는 이어서), 켜져 있으면 끈다.
     */
    void toggleFire(Player player) {
        long now = System.currentTimeMillis();
        settle(now);
        if (startedAt >= 0) {
            pausedProgress = now - startedAt;
            startedAt = -1;
            player.sendMessage(Component.text("조리를 멈췄습니다.", NamedTextColor.GRAY));
        } else if (pinned == null) {
            player.sendMessage(Component.text("먼저 레시피 책에서 만들 요리를 거세요.", NamedTextColor.RED));
        } else if (batchesAvailable() == 0) {
            player.sendMessage(Component.text("재료가 모자랍니다.", NamedTextColor.RED));
        } else {
            startedAt = now - pausedProgress;
            pausedProgress = 0;
            player.sendMessage(Component.text("조리를 시작했습니다.", NamedTextColor.GOLD));
        }
        machines.markDirty();
        machines.refreshModel(this);                                   // 가구 모양 (켜짐 · 꺼짐) 바로 바꾸기
    }

    /** 접시 위 요리의 등급 g 아이템 (은별·금별 아이템이 없으면 일반) */
    private ItemStack graded(int g) {
        if (g == 0) {
            return outputSample.clone();
        }
        String id = machines.itemProvider().idOf(outputSample);
        try {
            return machines.createResult(Grades.withGrade(Grades.base(id), g)).asOne();
        } catch (IllegalStateException | NullPointerException exception) {
            return outputSample.clone();
        }
    }

    /** 접시 위 요리 전부 (등급별 아이템 묶음) */
    private List<ItemStack> outputItems() {
        List<ItemStack> all = new ArrayList<>();
        if (outputSample != null) {
            for (int g = 0; g < 3; g++) {
                all.addAll(stacks(graded(g), outputs[g]));
            }
        }
        return all;
    }

    /** 빈 그릇 칸 index 를 꺼낸다. 빈 그릇 칸이 하나뿐인 배치면 모든 그릇을 꺼낸다 */
    void withdrawByproduct(Player player, int index) {
        List<Material> kinds = new ArrayList<>(byproducts.keySet());
        if (layout.byproductSlots().length == 1) {
            for (int i = 0; i < kinds.size(); i++) {
                withdrawKind(player, kinds.get(i));
            }
        } else if (index < kinds.size()) {
            withdrawKind(player, kinds.get(index));
        }
    }

    private void withdrawKind(Player player, Material material) {
        ItemStack sample = new ItemStack(material);
        int want = Math.min(byproducts.get(material), room(player, sample));
        if (want <= 0) {
            player.sendMessage(Component.text("가방에 빈자리가 없습니다.", NamedTextColor.RED));
            return;
        }
        byproducts.merge(material, -want, Integer::sum);
        byproducts.remove(material, 0);
        give(player, stacks(sample, want));
    }

    /**
     * 만들 요리를 건다. 다른 요리로 바꾸면 남은 재료와 접시 위 요리를 player 에게 돌려준다.
     */
    void pin(Player player, CookingRecipes.Recipe recipe) {
        long now = System.currentTimeMillis();
        settle(now);
        if (pinned != null && pinned.resultId().equals(recipe.resultId())) {
            return;
        }
        List<ItemStack> back = new ArrayList<>();
        for (Stock stock : stocks) {
            back.addAll(stacks(stock.sample, stock.count));
        }
        stocks.clear();
        back.addAll(outputItems());
        outputSample = null;
        java.util.Arrays.fill(outputs, 0);
        give(player, back);
        pinned = recipe;
        startedAt = -1;
        pausedProgress = 0;
        machines.markDirty();
    }

    /** 부순 기계 자리에 떨어뜨릴 아이템 전부 */
    List<ItemStack> contents() {
        List<ItemStack> all = new ArrayList<>(legacy);
        for (Stock stock : stocks) {
            all.addAll(stacks(stock.sample, stock.count));
        }
        all.addAll(outputItems());
        byproducts.forEach((material, count) -> all.addAll(stacks(new ItemStack(material), count)));
        return all;
    }

    void addStock(ItemStack sample, int count) {
        if (sample != null && count > 0) {
            stocks.add(new Stock(sample, count));
        }
    }

    // ── 그리기 ──

    /** 재료 칸 index 에 놓이는 레시피 재료 (걸린 요리 재료 순서) */
    String ingredientAt(int index) {
        if (pinned == null) {
            return null;
        }
        List<String> keys = new ArrayList<>(pinned.ingredients().keySet());
        return index < keys.size() ? keys.get(index) : null;
    }

    void redraw(long now) {
        List<String> keys = pinned == null ? List.of() : new ArrayList<>(pinned.ingredients().keySet());
        int[] ingredientSlots = layout.ingredientSlots();
        for (int i = 0; i < ingredientSlots.length; i++) {
            inventory.setItem(ingredientSlots[i], i < keys.size() ? ingredientIcon(keys.get(i)) : blank(Component.empty(), List.of()));
        }
        ItemStack plate = plateIcon(now);
        ItemMeta plateMeta = plate.getItemMeta();                      // 2x2 나머지 칸도 같은 이름·설명 (그림은 안 보임)
        ItemStack plateCover = blank(plateMeta.hasDisplayName() ? plateMeta.displayName() : Component.empty(),
                plateMeta.hasLore() ? plateMeta.lore() : List.of());
        int[] outputSlots = layout.outputSlots();
        for (int i = 0; i < outputSlots.length; i++) {
            inventory.setItem(outputSlots[i], i == 0 ? plate : plateCover);
        }
        inventory.setItem(layout.fireSlot(), fireIcon(now));
        ItemStack gauge = blank(Component.text("조리 진행", NamedTextColor.GOLD), gaugeLore(now));
        for (int slot : layout.gaugeSlots()) {
            inventory.setItem(slot, gauge);
        }
        ItemStack book = bookIcon();
        for (int slot : layout.bookSlots()) {
            inventory.setItem(slot, book);
        }
        List<Material> kinds = new ArrayList<>(byproducts.keySet());
        int[] byproductSlots = layout.byproductSlots();
        for (int i = 0; i < byproductSlots.length; i++) {
            if (byproductSlots.length == 1 && !kinds.isEmpty()) {
                inventory.setItem(byproductSlots[i], allByproductsIcon(kinds));
            } else if (i < kinds.size()) {
                int count = byproducts.get(kinds.get(i));
                ItemStack item = new ItemStack(kinds.get(i), Math.max(1, Math.min(count, kinds.get(i).getMaxStackSize())));
                inventory.setItem(byproductSlots[i], named(item, Component.text("남은 빈 그릇 " + count + "개", NamedTextColor.WHITE),
                        List.of(Component.text("클릭: 가방으로 꺼내기", NamedTextColor.GRAY))));
            } else {
                inventory.setItem(byproductSlots[i], blank(Component.empty(), List.of()));
            }
        }
        updateTitle(now, keys);
    }

    private ItemStack ingredientIcon(String ingredient) {
        int count = stored(ingredient);
        ItemStack icon = stocks.stream().filter(s -> matches(ingredient, s.sample)).max((a, b) -> Integer.compare(a.count, b.count))
                .map(s -> s.sample.clone()).orElseGet(() -> machines.ingredientIcon(recipes(), ingredient));
        if (texturedGui == null) {
            icon.setAmount(Math.max(1, Math.min(count, icon.getMaxStackSize())));
        }
        int need = pinned.ingredients().get(ingredient);
        List<Component> lore = new ArrayList<>();
        lore.add(Component.text("보관 ", NamedTextColor.GRAY).append(Component.text(String.format("%,d개", count),
                count >= need ? NamedTextColor.YELLOW : NamedTextColor.RED))
                .append(Component.text(" · 한 번에 " + need + "개", NamedTextColor.GRAY)));
        int[] grades = new int[3];
        for (Stock stock : stocks) {
            if (matches(ingredient, stock.sample)) {
                grades[grade(stock.sample)] += stock.count;
            }
        }
        if (grades[1] + grades[2] > 0) {
            lore.add(Component.text(String.format("일반 %,d · 은별 %,d · 금별 %,d", grades[0], grades[1], grades[2]), NamedTextColor.GRAY));
            lore.add(Component.text("싼 것부터 씁니다 (일반 → 은별 → 금별)", NamedTextColor.DARK_GRAY));
        }
        lore.add(Component.empty());
        lore.add(Component.text("가방에서 Shift+클릭, 또는 들고 클릭: 넣기", NamedTextColor.DARK_GRAY));
        lore.add(Component.text("클릭: 한 묶음 꺼내기 · Shift+클릭: 모두 꺼내기", NamedTextColor.DARK_GRAY));
        return named(icon, machines.displayName(ingredient).colorIfAbsent(NamedTextColor.WHITE), lore);
    }

    private ItemStack plateIcon(long now) {
        if (outputSample == null || outputCount() == 0) {
            if (pinned == null) {
                return blank(Component.text("접시", NamedTextColor.WHITE),
                        List.of(Component.text("오른쪽 위 레시피 책에서 만들 요리를 거세요.", NamedTextColor.GRAY)));
            }
            return blank(Component.text("접시", NamedTextColor.WHITE), progressLore(now));
        }
        ItemMeta resultMeta = outputSample.getItemMeta();
        ItemStack icon = texturedGui == null || !layout.bigOutput() ? null : plateIcon();   // 접시 2x2 가운데에 2배 크기 그림 아이템
        if (icon == null) {
            icon = outputSample.clone();
            icon.setAmount(texturedGui == null ? Math.max(1, Math.min(outputCount(), icon.getMaxStackSize())) : 1);
        }
        ItemMeta meta = icon.getItemMeta();
        meta.displayName(resultMeta.hasDisplayName() ? resultMeta.displayName()
                : Component.translatable(outputSample.translationKey()).decoration(TextDecoration.ITALIC, false));
        List<Component> lore = new ArrayList<>(resultMeta.hasLore() ? resultMeta.lore() : List.of());
        lore.add(Component.empty());
        lore.add(Component.text("완성 " + String.format("%,d개", outputCount()), NamedTextColor.YELLOW).decoration(TextDecoration.ITALIC, false));
        if (outputs[1] + outputs[2] > 0) {
            lore.add(Component.text(String.format("일반 %,d · 은별 %,d · 금별 %,d", outputs[0], outputs[1], outputs[2]), NamedTextColor.GRAY)
                    .decoration(TextDecoration.ITALIC, false));
        }
        for (Component line : progressLore(now)) {
            lore.add(line.decoration(TextDecoration.ITALIC, false));
        }
        lore.add(Component.text("클릭: 한 묶음 꺼내기 · Shift+클릭: 모두 꺼내기 (높은 등급부터)", NamedTextColor.DARK_GRAY).decoration(TextDecoration.ITALIC, false));
        meta.lore(lore);
        icon.setItemMeta(meta);
        return icon;
    }

    private List<Component> progressLore(long now) {
        if (pinned == null) {
            return List.of();
        }
        if (startedAt < 0) {
            return List.of(Component.text(batchesAvailable() == 0 ? "재료가 모자랍니다" : "불이 꺼져 있습니다", NamedTextColor.GRAY));
        }
        long remaining = Math.max(0, pinned.seconds() * 1000L - (now - startedAt));
        return List.of(Component.text("다음 완성까지 ", NamedTextColor.GRAY).append(Component.text((remaining + 999) / 1000 + "초", NamedTextColor.YELLOW)),
                Component.text("남은 재료로 ", NamedTextColor.GRAY)
                        .append(Component.text(batchesAvailable() * pinned.amount() + "개", NamedTextColor.YELLOW))
                        .append(Component.text(" 더 만듭니다.", NamedTextColor.GRAY)));
    }

    /** 접시 위 요리의 2배 크기 그림 아이템 (rustport:cook_plate_<요리>), 없으면 null */
    private ItemStack plateIcon() {
        String id = machines.itemProvider().idOf(outputSample);
        if (id == null) {
            return null;
        }
        try {
            return machines.itemProvider().create("rustport:cook_plate_" + id.substring(id.indexOf(':') + 1));
        } catch (IllegalStateException exception) {
            return null;
        }
    }

    /** 빈 그릇 한 칸에 모든 그릇: 가장 많은 그릇 아이콘 + 설명에 그릇마다 개수 */
    private ItemStack allByproductsIcon(List<Material> kinds) {
        Material most = kinds.stream().max((a, b) -> Integer.compare(byproducts.get(a), byproducts.get(b))).orElseThrow();
        List<Component> lore = new ArrayList<>();
        for (Material kind : kinds) {
            lore.add(Component.translatable(kind.translationKey()).color(NamedTextColor.WHITE)
                    .append(Component.text(" " + String.format("%,d개", byproducts.get(kind)), NamedTextColor.GRAY)));
        }
        lore.add(Component.text("클릭: 모두 가방으로 꺼내기", NamedTextColor.GRAY));
        ItemStack item = new ItemStack(most, Math.max(1, Math.min(byproducts.get(most), most.getMaxStackSize())));
        return named(item, Component.text("남은 빈 그릇", NamedTextColor.WHITE), lore);
    }

    /** 시작 버튼: 불(화덕 문 — 켜짐 타오르는 불 · 꺼짐 회색 불) 또는 톱니(착즙기 — 작동 황동 · 멈춤 회색) */
    private ItemStack fireIcon(long now) {
        boolean on = startedAt >= 0;
        boolean fire = "fire".equals(layout.startIcon());
        ItemStack icon;
        try {
            icon = machines.itemProvider().create("rustport:cook_" + layout.startIcon() + (on ? "_on" : "_off"));
        } catch (IllegalStateException exception) {
            icon = new ItemStack(on ? Material.CAMPFIRE : Material.SOUL_CAMPFIRE);
        }
        List<Component> lore = new ArrayList<>(gaugeLore(now));
        lore.add(Component.empty());
        lore.add(Component.text(on ? "클릭: 조리 멈추기" : "클릭: 조리 시작", NamedTextColor.YELLOW));
        String name = fire ? (on ? "불 켜짐 · 조리 중" : "불 꺼짐") : (on ? "작동 중" : "멈춤");
        return named(icon, Component.text(name, on ? NamedTextColor.GOLD : NamedTextColor.GRAY), lore);
    }

    /** 게이지 설명: 다음 1개 완성까지 · 전부 완성까지 남은 시간 */
    private List<Component> gaugeLore(long now) {
        if (pinned == null) {
            return List.of(Component.text("걸린 요리가 없습니다.", NamedTextColor.GRAY));
        }
        int batches = batchesAvailable();
        if (batches == 0) {
            return List.of(Component.text("재료가 모자랍니다.", NamedTextColor.GRAY));
        }
        long perBatch = pinned.seconds() * 1000L;
        if (startedAt < 0) {
            long all = perBatch - pausedProgress + (batches - 1) * perBatch;
            return List.of(Component.text("불이 꺼져 있습니다. 화덕의 불 버튼을 눌러 시작하세요.", NamedTextColor.GRAY),
                    Component.text("켜면 전부 완성까지 ", NamedTextColor.GRAY).append(Component.text(duration(all), NamedTextColor.YELLOW))
                            .append(Component.text(" (" + String.format("%,d", batches * pinned.amount()) + "개)", NamedTextColor.GRAY)));
        }
        long next = Math.max(0, perBatch - (now - startedAt));
        long all = next + (batches - 1) * perBatch;
        return List.of(
                Component.text("1개 완성까지 ", NamedTextColor.GRAY).append(Component.text(duration(next), NamedTextColor.YELLOW)),
                Component.text("전부 완성까지 ", NamedTextColor.GRAY).append(Component.text(duration(all), NamedTextColor.YELLOW))
                        .append(Component.text(" (" + String.format("%,d", batches * pinned.amount()) + "개)", NamedTextColor.GRAY)));
    }

    /** 남은 시간 글: 1시간 2분 3초 / 2분 3초 / 3초 (초는 올림) */
    static String duration(long millis) {
        long seconds = (millis + 999) / 1000;
        long h = seconds / 3600;
        long m = seconds % 3600 / 60;
        long sec = seconds % 60;
        StringBuilder out = new StringBuilder();
        if (h > 0) {
            out.append(h).append("시간 ");
        }
        if (h > 0 || m > 0) {
            out.append(m).append("분 ");
        }
        return out.append(sec).append("초").toString();
    }

    private ItemStack bookIcon() {
        List<Component> lore = new ArrayList<>();
        if (pinned == null) {
            lore.add(Component.text("걸린 요리 없음", NamedTextColor.GRAY));
        } else {
            lore.add(Component.text("걸린 요리: ", NamedTextColor.GRAY).append(machines.resultName(pinned.resultId()).colorIfAbsent(NamedTextColor.WHITE)));
        }
        lore.add(Component.text("클릭: 만들 요리 고르기", NamedTextColor.DARK_GRAY));
        return blank(Component.text("레시피 책", NamedTextColor.YELLOW), lore);
    }

    private int gaugeLevel(long now) {
        if (pinned == null) {
            return 0;
        }
        long perBatch = pinned.seconds() * 1000L;
        long progress = startedAt >= 0 ? now - startedAt : pausedProgress;
        return (int) Math.min(CookGlyphs.GAUGE_STEPS, progress * CookGlyphs.GAUGE_STEPS / perBatch);
    }

    private void updateTitle(long now, List<String> keys) {
        if (texturedGui == null) {
            return;
        }
        CookGlyphs glyphs = machines.glyphs();
        TitleCanvas canvas = glyphs.backgroundCanvas(background);
        glyphs.gauge(canvas, layout, gaugeLevel(now));
        StringBuilder state = new StringBuilder().append(gaugeLevel(now));
        int[] ingredientSlots = layout.ingredientSlots();
        for (int i = 0; i < keys.size() && i < ingredientSlots.length; i++) {
            String text = CookGlyphs.compact(stored(keys.get(i)));
            glyphs.slotCount(canvas, "cnt", ingredientSlots[i], text);
            state.append('|').append(text);
        }
        if (outputCount() > 0) {
            String text;
            if (layout.countRow() < 0) {                           // 솥: 접시 아래 명찰
                text = CookGlyphs.plate(outputCount());
                glyphs.plateCount(canvas, text);
            } else {
                text = CookGlyphs.compact(outputCount());
                glyphs.count(canvas, "cnt", layout.countRow(), layout.countRight(), text);
            }
            state.append('|').append(text);
        }
        String key = state.toString();
        if (key.equals(shownTitle)) {
            return;
        }
        shownTitle = key;
        String title = canvas.build();
        for (HumanEntity viewer : new ArrayList<>(inventory.getViewers())) {
            InventoryView view = viewer.getOpenInventory();
            if (view.getTopInventory() == inventory) {
                view.setTitle(title);
            }
        }
    }

    // ── 도우미 ──

    /** sample 을 count 개, 최대 묶음 크기로 나눈 아이템들 */
    static List<ItemStack> stacks(ItemStack sample, int count) {
        List<ItemStack> out = new ArrayList<>();
        int max = sample.getMaxStackSize();
        while (count > 0) {
            ItemStack stack = sample.clone();
            stack.setAmount(Math.min(max, count));
            count -= stack.getAmount();
            out.add(stack);
        }
        return out;
    }

    /** 가방에 sample 이 몇 개 더 들어가는지 */
    private static int room(Player player, ItemStack sample) {
        int room = 0;
        for (ItemStack item : player.getInventory().getStorageContents()) {
            if (item == null || item.getType().isAir()) {
                room += sample.getMaxStackSize();
            } else if (item.isSimilar(sample)) {
                room += Math.max(0, item.getMaxStackSize() - item.getAmount());
            }
        }
        return room;
    }

    /** 가방에 넣고, 못 넣은 것은 발밑에 떨어뜨린다 */
    static void give(Player player, List<ItemStack> items) {
        for (ItemStack item : items) {
            for (ItemStack rest : player.getInventory().addItem(item).values()) {
                player.getWorld().dropItemNaturally(player.getLocation(), rest);
            }
        }
    }

    private ItemStack blank(Component name, List<Component> lore) {
        ItemStack item;
        try {
            item = machines.itemProvider().create(BLANK_ID);
        } catch (IllegalStateException exception) {
            item = new ItemStack(Material.GRAY_STAINED_GLASS_PANE);
        }
        ItemStack out = named(item, name, lore);
        return name.equals(Component.empty()) && lore.isEmpty() ? GuiItems.hideTooltip(out) : out;
    }

    static ItemStack named(ItemStack item, Component name, List<Component> lore) {
        ItemMeta meta = item.getItemMeta();
        meta.displayName(name.decoration(TextDecoration.ITALIC, false));
        meta.lore(lore.stream().map(line -> line.decoration(TextDecoration.ITALIC, false)).toList());
        item.setItemMeta(meta);
        return item;
    }
}

package com.brassfield.enhancement;

import com.brassfield.common.FontSpace;
import com.brassfield.common.ItemsAdderGuiBackground;
import com.brassfield.stone.StoneGrade;
import com.brassfield.stone.StoneWallet;
import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.Bukkit;
import io.papermc.paper.datacomponent.DataComponentTypes;
import org.bukkit.Material;
import org.bukkit.NamespacedKey;
import org.bukkit.entity.HumanEntity;
import org.bukkit.entity.Player;
import org.bukkit.inventory.Inventory;
import org.bukkit.inventory.InventoryHolder;
import org.bukkit.inventory.InventoryView;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.PlayerInventory;
import org.bukkit.inventory.meta.ItemMeta;
import org.jetbrains.annotations.NotNull;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

public final class EnhancementGui implements InventoryHolder {

    public static final int TARGET_SLOT = 1;
    public static final int ENHANCE_BUTTON_SLOT = 13;
    public static final int INFO_SLOT = 7;
    public static final int STONE_SLOT = 19;

    private static final int SIZE = 54;
    private static final String TITLE_TEXT = "장비 강화";
    private static final Component TITLE = Component.text(TITLE_TEXT);
    private static final String BACKGROUND_FONT_IMAGE = "rustport:enhance_bg";
    private static final int BACKGROUND_TITLE_OFFSET = 0;
    private static final int BACKGROUND_TEXTURE_OFFSET = -8;
    // enhance_bg 글자 폭: 글자 폭은 이미지에서 실제로 그려진 부분(왼쪽 176px) 기준이고,
    // ItemsAdder가 글자 뒤에 붙이는 -1px이 글자 간격 1px을 상쇄한다.
    private static final int BACKGROUND_GLYPH_ADVANCE = 176;
    // 제목 글자 시작 x, 글자 보드 가운데 x (enhance_bg의 보드: x=102, 폭 55)
    private static final int TITLE_ORIGIN_X = 8;
    private static final int BOARD_CENTER_X = 129;
    private static final Map<String, String> BOARD_GLYPH_CACHE = new ConcurrentHashMap<>();
    private static final String BLANK_ICON_ID = "rustport:gui_blank";
    private static final Map<String, String> LIST_GLYPH_CACHE = new ConcurrentHashMap<>();

    private final Inventory inventory;
    private final ItemsAdderGuiBackground guiBackground;
    private final ItemsAdderGuiBackground.TexturedGui texturedGui;
    private final StoneWallet wallet;
    private final UUID ownerId;

    // 아래 장비 목록
    private List<EnhanceList.Entry> entries = List.of();
    private int page;
    // 목록에서 고른 장비: 플레이어 가방 칸 번호 + 그때의 아이템. 장비는 그 자리(착용 칸 포함)에 그대로 두고
    // 강화 칸에는 보기용 복사본만 띄운다. 강화 결과도 그 자리에 바로 쓴다. 안 골랐으면 -1
    private int selectedSlot = -1;
    private ItemStack selectedItem;

    public EnhancementGui(ItemsAdderGuiBackground guiBackground, StoneWallet wallet, UUID ownerId) {
        this(-1, guiBackground, wallet, ownerId);
    }

    /** selectedSlot = 처음부터 골라 둘 가방 칸 (강화 후 다시 열 때), 없으면 -1 */
    public EnhancementGui(int selectedSlot, ItemsAdderGuiBackground guiBackground, StoneWallet wallet, UUID ownerId) {
        this.guiBackground = guiBackground;
        this.wallet = wallet;
        this.ownerId = ownerId;
        // 배경 GUI는 제목 글자 없이 연다. (TITLE_TEXT는 ItemsAdder가 없을 때의 바닐라 창 제목)
        this.texturedGui = guiBackground.build(
                this, SIZE, "", BACKGROUND_FONT_IMAGE, BACKGROUND_TITLE_OFFSET, BACKGROUND_TEXTURE_OFFSET
        );

        if (texturedGui != null) {
            inventory = texturedGui.inventory();
        } else {
            inventory = Bukkit.createInventory(this, SIZE, TITLE);
            fillBackground();
        }

        Player owner = Bukkit.getPlayer(ownerId);
        if (owner != null && selectedSlot >= 0) {
            ItemStack item = owner.getInventory().getItem(selectedSlot);
            if (EnhanceTracks.isEnhanceable(item)) {
                this.selectedSlot = selectedSlot;
                this.selectedItem = item.clone();
            }
        }
        inventory.setItem(ENHANCE_BUTTON_SLOT, createEnhanceButton());
        refresh();
    }

    @Override
    public @NotNull Inventory getInventory() {
        return inventory;
    }

    public void open(Player player) {
        if (texturedGui != null) {
            guiBackground.show(texturedGui, player);
            refresh();
        } else {
            player.openInventory(inventory);
        }
    }

    /** 강화 칸 정보 + 장비 목록을 다시 그린다 (가방이 바뀌었을 때) */
    public void refresh() {
        followSelection();
        refreshList();
        refreshInfo();
    }

    /** 고른 장비가 있는 가방 칸, 안 골랐으면 -1 */
    public int selectedSlot() {
        return selectedSlot;
    }

    /** 고를 때의 장비 (강화 직전에 그 칸에 아직 같은 장비가 있는지 확인용) */
    public ItemStack selectedItem() {
        return selectedItem == null ? null : selectedItem.clone();
    }

    public void clearSelection() {
        selectedSlot = -1;
        selectedItem = null;
        refresh();
    }

    /** 강화 칸 보기용 복사본 (설명 · 확률 표시용) */
    public ItemStack getTargetItem() {
        return selectedItem;
    }

    /** 장비는 플레이어 가방에 그대로 있으므로 돌려줄 것이 없다 (다른 창들과 같은 닫기 처리용) */
    public void returnItemsTo(Player player) {
    }

    /** 가방 안에서 고른 장비를 옮겼으면 따라가고, 없어졌으면 선택을 푼다 */
    private void followSelection() {
        if (selectedSlot < 0) {
            return;
        }
        Player owner = Bukkit.getPlayer(ownerId);
        if (owner == null) {
            return;
        }
        PlayerInventory playerInventory = owner.getInventory();
        if (selectedItem.equals(playerInventory.getItem(selectedSlot))) {
            return;
        }
        for (int slot = 0; slot <= 40; slot++) {
            if (selectedItem.equals(playerInventory.getItem(slot))) {
                selectedSlot = slot;
                return;
            }
        }
        selectedSlot = -1;
        selectedItem = null;
    }

    /** 아래 가방에서 강화할 수 있는 장비를 눌렀을 때: 집어 들지 않고 바로 고른다. 골랐으면 true */
    public boolean selectFromInventory(Player player, int inventorySlot) {
        ItemStack item = player.getInventory().getItem(inventorySlot);
        if (!EnhanceTracks.isEnhanceable(item)) {
            return false;
        }
        selectedSlot = inventorySlot;
        selectedItem = item.clone();
        refresh();
        return true;
    }

    /**
     * 장비 목록 칸 · 쪽 넘기기 칸을 눌렀을 때. 목록 칸이면 그 장비를 고른다 (장비는 제자리에 둔다). 처리했으면 true
     */
    public boolean handleListClick(Player player, int rawSlot) {
        if (rawSlot == EnhanceList.PREV_SLOT || rawSlot == EnhanceList.NEXT_SLOT) {
            int pages = EnhanceList.pageCount(entries.size());
            int next = page + (rawSlot == EnhanceList.NEXT_SLOT ? 1 : -1);
            if (next >= 0 && next < pages) {
                page = next;
                refresh();
            }
            return true;
        }
        int card = EnhanceList.cardOf(rawSlot);
        if (card < 0) {
            return rawSlot == EnhanceList.PAGE_SLOT;
        }
        int index = page * EnhanceList.PAGE_SIZE + card;
        if (index >= entries.size()) {
            return true;
        }
        EnhanceList.Entry entry = entries.get(index);
        ItemStack current = player.getInventory().getItem(entry.slot());
        if (current != null && current.equals(entry.snapshot())) {
            selectedSlot = entry.slot();
            selectedItem = current.clone();
        }
        refresh();
        return true;
    }

    private void refreshList() {
        Player owner = Bukkit.getPlayer(ownerId);
        entries = owner == null ? List.of() : EnhanceList.scan(owner);
        int pages = EnhanceList.pageCount(entries.size());
        page = Math.min(page, pages - 1);
        for (int card = 0; card < EnhanceList.PAGE_SIZE; card++) {
            int index = page * EnhanceList.PAGE_SIZE + card;
            int slot = EnhanceList.iconSlot(card);
            if (index >= entries.size()) {
                inventory.setItem(slot, null);
                inventory.setItem(slot + 1, null);
                continue;
            }
            EnhanceList.Entry entry = entries.get(index);
            ItemStack shown = cardItem(entry);
            inventory.setItem(slot, shown);
            inventory.setItem(slot + 1, cardFiller(shown));
        }
        inventory.setItem(EnhanceList.PREV_SLOT, page > 0 ? navButton("이전 쪽", Material.ARROW) : null);
        inventory.setItem(EnhanceList.NEXT_SLOT, page < pages - 1 ? navButton("다음 쪽", Material.ARROW) : null);
        inventory.setItem(EnhanceList.PAGE_SLOT, pages > 1 ? navButton((page + 1) + " / " + pages + " 쪽", Material.PAPER) : null);
    }

    /** 카드에 띄울 장비 복사본: 카드용 작은 모델(rustport:card/아이템이름) + "착용 중" · 안내 줄 */
    private ItemStack cardItem(EnhanceList.Entry entry) {
        ItemStack shown = entry.snapshot().clone();
        shown.setAmount(1);
        String id = EnhanceTracks.itemProvider().idOf(shown);
        if (texturedGui != null && id != null && id.startsWith("customitem:")) {
            shown.setData(DataComponentTypes.ITEM_MODEL, new NamespacedKey("rustport", "card/" + id.substring("customitem:".length())));
        }
        ItemMeta meta = shown.getItemMeta();
        List<Component> lore = meta.hasLore() ? new ArrayList<>(meta.lore()) : new ArrayList<>();
        lore.add(Component.empty());
        if (entry.worn()) {
            lore.add(Component.text("착용 중", NamedTextColor.RED));
        }
        lore.add(entry.slot() == selectedSlot
                ? Component.text("강화 칸에 올라가 있습니다.", NamedTextColor.GREEN)
                : Component.text("클릭하면 강화 칸에 올립니다.", NamedTextColor.YELLOW));
        meta.lore(lore);
        shown.setItemMeta(meta);
        return shown;
    }

    /** 카드 오른쪽 칸: 투명 아이콘에 같은 설명 */
    private ItemStack cardFiller(ItemStack shown) {
        ItemStack filler = createIcon(Material.LIGHT_GRAY_STAINED_GLASS_PANE);
        ItemMeta source = shown.getItemMeta();
        ItemMeta meta = filler.getItemMeta();
        meta.displayName(source.displayName());
        meta.lore(source.lore());
        filler.setItemMeta(meta);
        return filler;
    }

    private ItemStack navButton(String name, Material fallback) {
        ItemStack button = createIcon(fallback);
        ItemMeta meta = button.getItemMeta();
        meta.displayName(Component.text(name, NamedTextColor.YELLOW));
        button.setItemMeta(meta);
        return button;
    }

    public void refreshInfo() {
        ItemStack targetItem = getTargetItem();
        inventory.setItem(TARGET_SLOT, targetItem == null ? null : selectedDisplay(targetItem));
        if (targetItem == null || targetItem.getType().isAir()) {
            inventory.setItem(INFO_SLOT, createEmptyInfoItem());
            inventory.setItem(STONE_SLOT, createStoneHint("아래 목록에서 장비를 고르면 필요한 강화석이 표시됩니다."));
            updateBoard(List.of("§7장비를", "§7넣어주세요"));          // 정보판 글꼴에 있는 글자만 쓸 수 있다
            return;
        }
        EnhanceTrack track = EnhanceTracks.trackOf(targetItem).orElse(null);
        if (track == null) {
            inventory.setItem(INFO_SLOT, createInvalidInfoItem());
            inventory.setItem(STONE_SLOT, createStoneHint("강화할 수 없는 아이템입니다."));
            updateBoard(List.of("", "", "§c강화 불가"));
            return;
        }
        int level = EnhanceTracks.levelOf(targetItem);
        EnhanceStep step = track.step(level);
        inventory.setItem(INFO_SLOT, createProbabilityInfo(step));
        if (level >= track.maxLevel()) {
            inventory.setItem(STONE_SLOT, createStoneHint("최고 단계라 더 이상 강화석이 필요하지 않습니다."));
            updateBoard(List.of("", "", "§6최고 단계"));
            return;
        }
        inventory.setItem(STONE_SLOT, createStoneInfo(step));
        updateBoard(List.of(
                "§a+" + level + " → +" + (level + 1),
                "§f성공 " + formatChance(step.successChance()) + "%"
        ));
    }

    /**
     * 오른쪽 아래 글자 보드를 갱신한다.
     * ItemsAdder는 창을 열 때만 제목 표식(IA_CUST_GUI)을 배경으로 바꿔치기하므로, 제목 전체를 직접 조립해 바꾼다.
     */
    private void updateBoard(List<String> lines) {
        if (texturedGui == null) {
            return;
        }
        String title = buildTexturedTitle(buildListText() + buildBoardText(lines));
        for (HumanEntity viewer : new ArrayList<>(inventory.getViewers())) {
            InventoryView view = viewer.getOpenInventory();
            if (view.getTopInventory() != inventory) {
                continue;
            }
            view.setTitle(title);
        }
    }

    private String buildTexturedTitle(String boardText) {
        // 제목 시작점(x=8)에서 왼쪽으로 8px → 배경을 GUI 왼쪽 끝(x=0)에 그림 → 다시 제목 시작점으로 복귀
        return "§f" + FontSpace.of(BACKGROUND_TEXTURE_OFFSET)
                + guiBackground.glyph(BACKGROUND_FONT_IMAGE)
                + FontSpace.of(-BACKGROUND_GLYPH_ADVANCE - BACKGROUND_TEXTURE_OFFSET)
                + boardText;
    }

    /**
     * 장비 목록 위 글자: 카드마다 오른쪽 끝 맞춤 강화 단계(+N), 착용 중이면 검붉은 테두리, 쪽 번호.
     * 끝나면 커서를 제목 시작점으로 되돌린다.
     */
    private String buildListText() {
        StringBuilder builder = new StringBuilder("§f");
        int[] cursor = {0};
        for (int card = 0; card < EnhanceList.PAGE_SIZE; card++) {
            int index = page * EnhanceList.PAGE_SIZE + card;
            if (index >= entries.size()) {
                break;
            }
            EnhanceList.Entry entry = entries.get(index);
            int x = EnhanceList.cardX(card);
            int row = EnhanceList.cardRow(card);
            if (entry.worn()) {
                placeGlyph(builder, cursor, x + 1, "rustport:enh_worn_r" + row, EnhanceList.WORN_FRAME_ADVANCE);
            }
            String text = "+" + entry.level();
            int width = text.length() * EnhanceList.DIGIT_ADVANCE - 1;
            int start = x + EnhanceList.CARD_W - 3 - width;
            for (int i = 0; i < text.length(); i++) {
                placeGlyph(builder, cursor, start + i * EnhanceList.DIGIT_ADVANCE,
                        "rustport:enh_lv_r" + row + "_" + glyphKey(text.charAt(i)), EnhanceList.DIGIT_ADVANCE);
            }
        }
        int pages = EnhanceList.pageCount(entries.size());
        if (pages > 1) {
            String text = (page + 1) + "/" + pages;
            int width = text.length() * EnhanceList.DIGIT_ADVANCE - 1;
            int start = EnhanceList.NAV_X + 9 - width / 2;
            for (int i = 0; i < text.length(); i++) {
                placeGlyph(builder, cursor, start + i * EnhanceList.DIGIT_ADVANCE,
                        "rustport:enh_pg_r1_" + glyphKey(text.charAt(i)), EnhanceList.DIGIT_ADVANCE);
            }
        }
        return builder.append(FontSpace.of(-cursor[0])).toString();
    }

    private static String glyphKey(char ch) {
        return switch (ch) {
            case '+' -> "plus";
            case '/' -> "slash";
            default -> String.valueOf(ch);
        };
    }

    /** 창 기준 x 에 글꼴 그림 하나 (cursor = 제목 시작점 기준 현재 위치) */
    private void placeGlyph(StringBuilder builder, int[] cursor, int windowX, String fontImageId, int advance) {
        String glyph = LIST_GLYPH_CACHE.computeIfAbsent(fontImageId, id -> {
            String raw = guiBackground.glyph(id);
            return raw.endsWith("\uF801") ? raw.substring(0, raw.length() - 1) : raw;
        });
        if (glyph.isEmpty()) {
            return;
        }
        int target = windowX - TITLE_ORIGIN_X;
        builder.append(FontSpace.of(target - cursor[0])).append(glyph);
        cursor[0] = target + advance;
    }

    /**
     * 줄마다 가운데 정렬한 보드 글자를 만든다. 각 줄은 "§색코드 + 글자" 형식이고, 빈 문자열이면 비워 둔다.
     * 1·2번째는 위·아래 줄, 3번째는 한 줄짜리 문구용 가운데 줄이다.
     * 끝나면 커서를 제목 시작점으로 되돌린다.
     */
    private String buildBoardText(List<String> lines) {
        StringBuilder builder = new StringBuilder();
        int cursor = 0;
        for (int i = 0; i < lines.size() && i < BoardFont.LINE_COUNT; i++) {
            String line = lines.get(i);
            String color = line.startsWith("§") ? line.substring(0, 2) : "§f";
            String text = line.startsWith("§") ? line.substring(2) : line;
            if (text.isEmpty()) {
                continue;
            }
            int start = BOARD_CENTER_X - TITLE_ORIGIN_X - boardWidth(text) / 2;
            builder.append(FontSpace.of(start - cursor)).append(color);
            cursor = start;
            for (char ch : text.toCharArray()) {
                if (ch == ' ') {
                    builder.append(FontSpace.of(BoardFont.SPACE_ADVANCE));
                    cursor += BoardFont.SPACE_ADVANCE;
                    continue;
                }
                Integer advance = BoardFont.ADVANCES.get(ch);
                if (advance == null) {
                    continue;
                }
                builder.append(boardGlyph(i + 1, ch));
                cursor += advance;
            }
        }
        return builder.append(FontSpace.of(-cursor)).toString();
    }

    private static int boardWidth(String text) {
        int width = 0;
        for (char ch : text.toCharArray()) {
            width += ch == ' ' ? BoardFont.SPACE_ADVANCE : BoardFont.ADVANCES.getOrDefault(ch, 0);
        }
        return width;
    }

    private String boardGlyph(int line, char ch) {
        return BOARD_GLYPH_CACHE.computeIfAbsent(BoardFont.fontImageId(line, ch), id -> {
            String glyph = guiBackground.glyph(id);
            // ItemsAdder가 글자 뒤에 붙이는 -1px 보정을 떼어 바닐라 글자 간격을 그대로 쓴다.
            return glyph.endsWith("\uF801") ? glyph.substring(0, glyph.length() - 1) : glyph;
        });
    }

    /** 강화 칸에 띄우는 고른 장비의 보기용 복사본 */
    private ItemStack selectedDisplay(ItemStack item) {
        ItemStack shown = item.clone();
        shown.setAmount(1);
        ItemMeta meta = shown.getItemMeta();
        List<Component> lore = meta.hasLore() ? new ArrayList<>(meta.lore()) : new ArrayList<>();
        lore.add(Component.empty());
        lore.add(Component.text("장비는 제자리(착용 칸 포함)에 둔 채 강화합니다.", NamedTextColor.GRAY));
        lore.add(Component.text("클릭하면 선택을 풉니다.", NamedTextColor.YELLOW));
        meta.lore(lore);
        shown.setItemMeta(meta);
        return shown;
    }

    private void fillBackground() {
        ItemStack filler = new ItemStack(Material.GRAY_STAINED_GLASS_PANE);
        ItemMeta meta = filler.getItemMeta();
        meta.displayName(Component.empty());
        meta.setHideTooltip(true);
        filler.setItemMeta(meta);

        for (int slot = 0; slot < SIZE; slot++) {
            inventory.setItem(slot, filler);
        }
    }

    private ItemStack createIcon(Material fallback) {
        if (texturedGui == null) {
            return new ItemStack(fallback);
        }
        return EnhanceTracks.createCustomOrFallback(BLANK_ICON_ID, fallback);
    }

    private ItemStack createEnhanceButton() {
        ItemStack button = createIcon(Material.ANVIL);
        ItemMeta meta = button.getItemMeta();
        meta.displayName(Component.text("강화 시도", NamedTextColor.GREEN));
        meta.lore(List.of(
                Component.text("아래 목록에서 장비를 고르고", NamedTextColor.GRAY),
                Component.text("클릭하세요.", NamedTextColor.GRAY)
        ));
        button.setItemMeta(meta);
        return button;
    }

    private ItemStack createEmptyInfoItem() {
        ItemStack info = createIcon(Material.BARRIER);
        ItemMeta meta = info.getItemMeta();
        meta.displayName(Component.text("강화 정보", NamedTextColor.YELLOW));
        meta.lore(List.of(Component.text("아래 목록에서 장비를 골라주세요.", NamedTextColor.GRAY)));
        info.setItemMeta(meta);
        return info;
    }

    private ItemStack createInvalidInfoItem() {
        ItemStack info = createIcon(Material.BARRIER);
        ItemMeta meta = info.getItemMeta();
        meta.displayName(Component.text("강화 불가", NamedTextColor.RED));
        meta.lore(List.of(Component.text("강화할 수 없는 아이템입니다.", NamedTextColor.GRAY)));
        info.setItemMeta(meta);
        return info;
    }

    private ItemStack createProbabilityInfo(EnhanceStep tier) {
        ItemStack info = createIcon(Material.PAPER);
        ItemMeta meta = info.getItemMeta();
        meta.displayName(Component.text("강화 확률 정보", NamedTextColor.AQUA));
        meta.lore(List.of(
                Component.text("현재 단계: ", NamedTextColor.GRAY)
                        .append(Component.text("+" + tier.level(), NamedTextColor.GREEN)),
                Component.empty(),
                chanceLine("성공: ", tier.successChance(), NamedTextColor.GREEN),
                chanceLine("유지: ", tier.maintainChance(), NamedTextColor.YELLOW),
                chanceLine("하락: ", tier.downgradeChance(), NamedTextColor.RED)
        ));
        info.setItemMeta(meta);
        return info;
    }

    /**
     * 강화석 칸: 이번 강화에 필요한 등급의 강화석 아이콘과 필요/보유 수량. (강화석은 재화라 칸에 넣지 않는다)
     */
    private ItemStack createStoneInfo(EnhanceStep tier) {
        StoneGrade grade = tier.stoneGrade();
        long balance = wallet.get(ownerId, grade);
        boolean enough = balance >= tier.stoneCost();

        ItemStack icon = texturedGui == null
                ? new ItemStack(Material.AMETHYST_SHARD)
                : EnhanceTracks.createCustomOrFallback(grade.iconItemId(), Material.AMETHYST_SHARD);
        ItemMeta meta = icon.getItemMeta();
        meta.displayName(Component.text(grade.displayName() + " 강화석", grade.color()));
        meta.lore(List.of(
                Component.text("필요: ", NamedTextColor.GRAY)
                        .append(Component.text(tier.stoneCost() + "개", NamedTextColor.WHITE)),
                Component.text("보유: ", NamedTextColor.GRAY)
                        .append(Component.text(balance + "개", enough ? NamedTextColor.GREEN : NamedTextColor.RED)),
                Component.empty(),
                enough
                        ? Component.text("강화할 때마다 " + tier.stoneCost() + "개가 소모됩니다.", NamedTextColor.GRAY)
                        : Component.text((tier.stoneCost() - balance) + "개가 부족합니다.", NamedTextColor.RED)
        ));
        icon.setItemMeta(meta);
        return icon;
    }

    private ItemStack createStoneHint(String message) {
        ItemStack hint = createIcon(Material.LIGHT_GRAY_STAINED_GLASS_PANE);
        ItemMeta meta = hint.getItemMeta();
        meta.displayName(Component.text("강화석", NamedTextColor.YELLOW));
        meta.lore(List.of(Component.text(message, NamedTextColor.GRAY)));
        hint.setItemMeta(meta);
        return hint;
    }

    private Component chanceLine(String label, double chance, NamedTextColor color) {
        return Component.text(label, NamedTextColor.GRAY)
                .append(Component.text(formatChance(chance) + "%", color));
    }

    private static String formatChance(double chance) {
        return chance == Math.rint(chance)
                ? String.format("%.0f", chance)
                : String.valueOf(chance);
    }
}

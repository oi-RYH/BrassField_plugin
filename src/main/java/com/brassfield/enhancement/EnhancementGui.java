package com.brassfield.enhancement;

import com.brassfield.common.FontSpace;
import com.brassfield.common.ItemDelivery;
import com.brassfield.common.ItemsAdderGuiBackground;
import com.brassfield.stone.StoneGrade;
import com.brassfield.stone.StoneWallet;
import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
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
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

public final class EnhancementGui implements InventoryHolder {

    public static final int TARGET_SLOT = 1;
    public static final int ENHANCE_BUTTON_SLOT = 13;
    public static final int INFO_SLOT = 7;
    public static final int STONE_SLOT = 19;

    private static final int SIZE = 27;
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

    private final Inventory inventory;
    private final ItemsAdderGuiBackground guiBackground;
    private final ItemsAdderGuiBackground.TexturedGui texturedGui;
    private final StoneWallet wallet;
    private final UUID ownerId;

    public EnhancementGui(ItemStack targetItem, ItemsAdderGuiBackground guiBackground, StoneWallet wallet, UUID ownerId) {
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

        inventory.setItem(TARGET_SLOT, targetItem);
        inventory.setItem(ENHANCE_BUTTON_SLOT, createEnhanceButton());
        refreshInfo();
    }

    @Override
    public @NotNull Inventory getInventory() {
        return inventory;
    }

    public void open(Player player) {
        if (texturedGui != null) {
            guiBackground.show(texturedGui, player);
            refreshInfo();
        } else {
            player.openInventory(inventory);
        }
    }

    public ItemStack getTargetItem() {
        return inventory.getItem(TARGET_SLOT);
    }

    public ItemStack takeTargetItem() {
        return takeItem(TARGET_SLOT);
    }

    /**
     * 장비 칸에 올려 둔 아이템을 플레이어에게 돌려준다. (인벤토리가 가득 차면 바닥에 떨어뜨림)
     */
    public void returnItemsTo(Player player) {
        ItemStack item = takeTargetItem();
        if (item != null && !item.getType().isAir()) {
            ItemDelivery.giveOrDrop(player, item);
        }
    }

    public void refreshInfo() {
        ItemStack targetItem = getTargetItem();
        if (targetItem == null || targetItem.getType().isAir()) {
            inventory.setItem(INFO_SLOT, createEmptyInfoItem());
            inventory.setItem(STONE_SLOT, createStoneHint("장비를 넣으면 필요한 강화석이 표시됩니다."));
            updateBoard(List.of("§7장비를", "§7넣어주세요"));
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
        String title = buildTexturedTitle(buildBoardText(lines));
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

    private ItemStack takeItem(int slot) {
        ItemStack item = inventory.getItem(slot);
        inventory.setItem(slot, null);
        return item;
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
                Component.text("강화할 아이템을 왼쪽 슬롯에 넣고", NamedTextColor.GRAY),
                Component.text("클릭하세요.", NamedTextColor.GRAY)
        ));
        button.setItemMeta(meta);
        return button;
    }

    private ItemStack createEmptyInfoItem() {
        ItemStack info = createIcon(Material.BARRIER);
        ItemMeta meta = info.getItemMeta();
        meta.displayName(Component.text("강화 정보", NamedTextColor.YELLOW));
        meta.lore(List.of(Component.text("강화할 아이템을 넣어주세요.", NamedTextColor.GRAY)));
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

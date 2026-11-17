package com.brassfield.market;

import com.brassfield.common.GuiItems;
import com.brassfield.common.CommandSupport;
import com.brassfield.common.ItemDelivery;
import com.brassfield.common.ItemsAdderGuiBackground;
import com.brassfield.common.TitleCanvas;
import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import net.kyori.adventure.text.format.TextDecoration;
import org.bukkit.Bukkit;
import org.bukkit.Material;
import org.bukkit.Sound;
import org.bukkit.entity.Entity;
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
import java.util.concurrent.ConcurrentHashMap;

/**
 * DL-7 요리 납품 창 (6줄). 배경은 ItemsAdder 그림(rustport:dl7_bg — BrassField tools/gui/make_dl7_bg.py).
 * 1줄 0·1열: DL-7 얼굴 (마우스를 올리면 오늘의 주문)
 * 2~5줄 1~5열: 화물 상자 안, 납품할 요리를 넣는 칸 20개
 * 6줄 3열: 상자 앞 포크·나이프 판 = [가방의 요리 모두 납품]
 * 5~6줄 7~8열: [납품] 버튼 (네 칸 어디를 눌러도)
 * 영수증: 올린 요리 개수와 총 금액을 제목 글자(글꼴 그림 dl7_ink1_*, dl7_ink2_*)로 띄운다.
 * 납품 연출: 영수증 쪽 칸(3줄 9열)에 3D 도장 모델 장면(dl7_stamp3d_high·mid·press·lift)을 0.1초 간격으로 넣어
 *          도장이 영수증 위로 내려와 찍히고 들어 올려진다. 찍히는 순간 납품하면서 영수증에 붉은 도장 자국
 *          (dl7_stamp_mark, 요리사 모자)을 남긴다. 자국은 다음에 상자에 요리를 넣을 때 사라진다. 연출 중에는 클릭을 막는다.
 * 나머지 칸은 투명 아이템으로 막아 Shift+클릭으로 넣은 요리가 상자 밖으로 가지 않게 한다.
 * ItemsAdder 배경이 없으면 바닐라 창(회색 유리판)으로 같은 배치를 쓴다.
 */
public final class FoodSellGui implements InventoryHolder {

    static final int SIZE = 54;
    static final int SELL_ALL_SLOT = 48;
    private static final int[] ORDER_SLOTS = {0, 1};
    private static final int[] SELL_SLOTS = {43, 44, 52, 53};
    private static final int[] DEPOSIT_SLOTS = {10, 11, 12, 13, 14, 19, 20, 21, 22, 23, 28, 29, 30, 31, 32, 37, 38, 39, 40, 41};
    private static final String BACKGROUND = "rustport:dl7_bg";
    private static final int BACKGROUND_ADVANCE = 176;
    private static final String BLANK_ID = "rustport:gui_blank";
    private static final int RECEIPT_RIGHT_X = 162;                 // 영수증 숫자 오른쪽 끝 (창 기준 x)
    private static final int DIGIT_ADVANCE = 4;
    private static final int COMMA_ADVANCE = 2;
    private static final Map<String, String> GLYPHS = new ConcurrentHashMap<>();
    private static final int STAMP_SLOT = 26;                        // 영수증 오른쪽 아래 칸 (3줄 9열) — 모델이 자국 자리로 옮겨 그려짐
    private static final String[] STAMP_FRAMES = {"high", "mid", "press", "lift"};
    private static final int PRESS_FRAME = 2;                        // 이 장면에서 납품하고 자국을 남긴다
    private static final long[] STAMP_TICKS = {0, 2, 4, 9};          // 장면별 시작 시각 (찍힌 채로 잠깐 멈춤)
    private static final long STAMP_END_TICKS = 12;
    private static final int MARK_X = 148;                           // 영수증 위 도장 자국 왼쪽 (창 기준 x)

    private final FoodMarket market;
    private final Entity robot;
    private final ItemsAdderGuiBackground.TexturedGui texturedGui;
    private final Inventory inventory;
    private String shownReceipt;                                    // 제목에 띄운 영수증 (바뀔 때만 제목을 다시 보낸다)
    private boolean stamping;                                       // 도장 연출 중 (클릭 막음)
    private boolean stampMark;                                      // 영수증에 도장 자국 표시

    FoodSellGui(FoodMarket market, Entity robot) {
        this.market = market;
        this.robot = robot;
        this.texturedGui = market.guiBackground().build(this, SIZE, "", BACKGROUND, 0, -8);
        this.inventory = texturedGui != null
                ? texturedGui.inventory()
                : Bukkit.createInventory(this, SIZE, Component.text("DL-7 · 납품 수령"));
        ItemStack filler = GuiItems.hideTooltip(icon(BLANK_ID, Material.GRAY_STAINED_GLASS_PANE, Component.empty(), List.of()));
        for (int slot = 0; slot < SIZE; slot++) {
            if (!isDeposit(slot)) {
                inventory.setItem(slot, filler);
            }
        }
        ItemStack orders = createOrders();
        for (int slot : ORDER_SLOTS) {
            inventory.setItem(slot, orders);
        }
        inventory.setItem(SELL_ALL_SLOT, icon(BLANK_ID, Material.HOPPER,
                Component.text("가방의 요리 모두 납품", NamedTextColor.YELLOW),
                List.of(Component.text("가방에 있는 요리를 한 번에 DL-7에게 넘깁니다.", NamedTextColor.GRAY))));
        refresh();
    }

    static boolean isDeposit(int slot) {
        return contains(DEPOSIT_SLOTS, slot);
    }

    static boolean isSell(int slot) {
        return contains(SELL_SLOTS, slot);
    }

    private static boolean contains(int[] slots, int slot) {
        for (int s : slots) {
            if (s == slot) {
                return true;
            }
        }
        return false;
    }

    @Override
    public @NotNull Inventory getInventory() {
        return inventory;
    }

    void open(Player player) {
        if (texturedGui != null) {
            market.guiBackground().show(texturedGui, player);
            shownReceipt = null;
            refresh();
        } else {
            player.openInventory(inventory);
        }
    }

    FoodMarket market() {
        return market;
    }

    /**
     * 영수증(개수·총 금액)과 [납품] 버튼 설명을 다시 그린다.
     */
    void refresh() {
        long total = 0;
        int count = 0;
        for (int slot : DEPOSIT_SLOTS) {
            ItemStack item = inventory.getItem(slot);
            long value = market.valueOf(item);
            if (value > 0) {
                total += value;
                count += item.getAmount();
            }
        }
        ItemStack sell = icon(BLANK_ID, total > 0 ? Material.LIME_STAINED_GLASS_PANE : Material.RED_STAINED_GLASS_PANE,
                Component.text("납품", total > 0 ? NamedTextColor.GREEN : NamedTextColor.RED),
                List.of(Component.text("요리 " + count + "개 · " + CommandSupport.formatNumber(total) + "골드", NamedTextColor.GOLD),
                        total > 0
                                ? Component.text("상자에 넣은 요리를 넘깁니다.", NamedTextColor.GRAY)
                                : Component.text("상자에 납품할 요리를 넣어주세요.", NamedTextColor.GRAY)));
        if (!stamping) {
            for (int slot : SELL_SLOTS) {
                inventory.setItem(slot, sell);
            }
        }
        if (count > 0) {
            stampMark = false;                                      // 새 요리를 넣으면 지난 납품 자국은 지운다
        }
        updateTitle(count, total);
    }

    boolean isStamping() {
        return stamping;
    }

    /**
     * [납품]: 도장이 내려와 찍히는 연출 후 납품한다. 상자에 납품할 요리가 없거나 배경 그림이 없으면 바로 처리한다.
     */
    void stampAndSell(Player player) {
        if (stamping) {
            return;
        }
        boolean any = false;
        for (int slot : DEPOSIT_SLOTS) {
            any |= market.isSellable(inventory.getItem(slot));
        }
        if (!any || texturedGui == null) {
            sellDeposited(player);
            return;
        }
        stamping = true;
        player.playSound(player.getLocation(), Sound.BLOCK_PISTON_EXTEND, 0.4f, 0.7f);
        for (int frame = 0; frame < STAMP_FRAMES.length; frame++) {
            int f = frame;
            market.plugin().getServer().getScheduler().runTaskLater(market.plugin(), () -> {
                showStamp(f);
                if (f == PRESS_FRAME) {
                    player.playSound(player.getLocation(), Sound.BLOCK_ANVIL_LAND, 0.3f, 1.6f);
                    sellDeposited(player);
                }
            }, STAMP_TICKS[frame]);
        }
        market.plugin().getServer().getScheduler().runTaskLater(market.plugin(), () -> {
            stamping = false;
            inventory.setItem(STAMP_SLOT, icon(BLANK_ID, Material.GRAY_STAINED_GLASS_PANE, Component.empty(), List.of()));
            refresh();
        }, STAMP_END_TICKS);
    }

    private void showStamp(int frame) {
        ItemStack item = market.icon("rustport:dl7_stamp3d_" + STAMP_FRAMES[frame], new ItemStack(Material.PAPER));
        ItemMeta meta = item.getItemMeta();
        meta.displayName(Component.text("수령 도장", NamedTextColor.RED).decoration(TextDecoration.ITALIC, false));
        item.setItemMeta(meta);
        inventory.setItem(STAMP_SLOT, item);
    }

    /**
     * 영수증 숫자를 띄운다. ItemsAdder 는 창을 열 때만 배경을 넣으므로 제목 전체를 직접 조립한다.
     */
    private void updateTitle(int count, long total) {
        if (texturedGui == null) {
            return;
        }
        String countText = CommandSupport.formatNumber(count);
        String totalText = CommandSupport.formatNumber(total);
        String receipt = countText + "|" + totalText + "|" + stampMark;
        if (receipt.equals(shownReceipt)) {
            return;
        }
        shownReceipt = receipt;
        TitleCanvas canvas = new TitleCanvas(glyph(BACKGROUND), BACKGROUND_ADVANCE);
        ink(canvas, 1, countText);
        ink(canvas, 2, totalText);
        if (stampMark) {
            canvas.place(MARK_X, glyph("rustport:dl7_stamp_mark"), 14);
        }
        String title = canvas.build();
        for (HumanEntity viewer : new ArrayList<>(inventory.getViewers())) {
            InventoryView view = viewer.getOpenInventory();
            if (view.getTopInventory() == inventory) {
                view.setTitle(title);
            }
        }
    }

    /**
     * 영수증 line(1 = 개수, 2 = 총 금액) 줄에 오른쪽 맞춤으로 잉크색 숫자
     */
    private void ink(TitleCanvas canvas, int line, String text) {
        int width = -1;
        for (char ch : text.toCharArray()) {
            width += ch == ',' ? COMMA_ADVANCE : DIGIT_ADVANCE;
        }
        int x = RECEIPT_RIGHT_X - width + 1;
        for (char ch : text.toCharArray()) {
            int advance = ch == ',' ? COMMA_ADVANCE : DIGIT_ADVANCE;
            canvas.place(x, glyph("rustport:dl7_ink" + line + "_" + (ch == ',' ? "comma" : String.valueOf(ch))), advance);
            x += advance;
        }
    }

    private String glyph(String id) {
        return GLYPHS.computeIfAbsent(id, market.guiBackground()::glyph);
    }

    void sellDeposited(Player player) {
        List<ItemStack> items = new ArrayList<>();
        for (int slot : DEPOSIT_SLOTS) {
            ItemStack item = inventory.getItem(slot);
            if (market.isSellable(item)) {
                items.add(item);
            }
        }
        if (market.sell(player, items, robot) > 0) {
            for (int slot : DEPOSIT_SLOTS) {
                if (market.isSellable(inventory.getItem(slot))) {
                    inventory.setItem(slot, null);
                }
            }
            stampMark = texturedGui != null;
        }
        refresh();
    }

    void sellFromInventory(Player player) {
        ItemStack[] contents = player.getInventory().getStorageContents();
        List<ItemStack> items = new ArrayList<>();
        for (ItemStack item : contents) {
            if (market.isSellable(item)) {
                items.add(item);
            }
        }
        if (market.sell(player, items, robot) > 0) {
            for (int i = 0; i < contents.length; i++) {
                if (market.isSellable(contents[i])) {
                    contents[i] = null;
                }
            }
            player.getInventory().setStorageContents(contents);
        } else {
            player.sendMessage(Component.text("가방에 납품할 수 있는 요리가 없습니다.", NamedTextColor.RED));
        }
    }

    /**
     * 팔지 않고 창을 닫으면 넣어 둔 아이템을 돌려준다.
     */
    public void returnItemsTo(Player player) {
        for (int slot : DEPOSIT_SLOTS) {
            ItemStack item = inventory.getItem(slot);
            if (item != null && !item.getType().isAir()) {
                inventory.setItem(slot, null);
                ItemDelivery.giveOrDrop(player, item);
            }
        }
    }

    private ItemStack createOrders() {
        List<Component> lore = new ArrayList<>();
        if (market.orders().isEmpty()) {
            lore.add(line("오늘은 주문이 없습니다.", NamedTextColor.GRAY));
        } else {
            lore.add(line("오늘은 아래 요리를 +" + Math.round(market.orderBonus() * 100) + "%에 삽니다.", NamedTextColor.GRAY));
            for (String id : market.orders()) {
                lore.add(line("★ " + market.nameOf(id) + ": ", NamedTextColor.GOLD)
                        .append(Component.text(CommandSupport.formatNumber(market.priceOf(id)) + "골드", NamedTextColor.YELLOW)));
            }
            lore.add(line("매일 오전 6시에 바뀝니다.", NamedTextColor.GRAY));
        }
        lore.add(line("요리 단가는 /요리가격 으로 볼 수 있습니다.", NamedTextColor.DARK_GRAY));
        return icon(BLANK_ID, Material.PAPER, Component.text("오늘의 납품 주문", NamedTextColor.GOLD), lore);
    }

    /**
     * ItemsAdder 배경이 있으면 투명 아이템(itemId), 없으면 바닐라 fallback 아이템에 이름·설명을 붙인다.
     */
    private ItemStack icon(String itemId, Material fallback, Component name, List<Component> lore) {
        ItemStack item = texturedGui != null ? market.icon(itemId, new ItemStack(fallback)) : new ItemStack(fallback);
        ItemMeta meta = item.getItemMeta();
        meta.displayName(name.decoration(TextDecoration.ITALIC, false));
        meta.lore(lore);
        item.setItemMeta(meta);
        return item;
    }

    private static Component line(String text, NamedTextColor color) {
        return Component.text(text, color).decoration(TextDecoration.ITALIC, false);
    }
}

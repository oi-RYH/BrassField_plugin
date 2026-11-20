package com.brassfield.enhancement;

import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.PlayerInventory;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

/**
 * 강화 창 아래 3줄의 장비 목록: 가방 · 착용 칸에서 강화할 수 있는 장비를 모아 가로 2칸 카드로 보여 준다.
 * 배치 · 글꼴 그림 위치는 tools/gui/make_enhance_assets.py 와 맞춘다.
 *
 * <p>정렬: 착용 중 먼저 → 강화 단계 오름차순 → 무기 · 방어구(투구 · 상의 · 하의 · 신발) · 장신구 순.
 * 착용 = 방어구 칸 · 보조손 (손에 든 무기는 단축바를 바꿀 때마다 달라져 착용으로 보지 않는다).
 */
final class EnhanceList {

    static final int FIRST_ROW = 3;
    static final int ROWS = 3;
    static final int COLS = 4;
    static final int PAGE_SIZE = ROWS * COLS;
    static final int PREV_SLOT = FIRST_ROW * 9 + 8;
    static final int PAGE_SLOT = (FIRST_ROW + 1) * 9 + 8;
    static final int NEXT_SLOT = (FIRST_ROW + 2) * 9 + 8;

    // 창 기준 픽셀 위치 (make_enhance_assets.py)
    static final int LIST_TOP = 71;
    static final int CARD_X0 = 7;
    static final int CARD_W = 36;
    static final int CARD_H = 18;
    static final int NAV_X = CARD_X0 + 8 * 18;
    static final int DIGIT_ADVANCE = 4;            // 3px 숫자 + 글자 간격 1px
    static final int WORN_FRAME_ADVANCE = CARD_W - 1;

    private static final int FIRST_WORN_SLOT = 36; // 36~39 방어구 칸, 40 보조손
    private static final int LAST_SLOT = 40;

    /** 목록 한 줄: 플레이어 가방 칸 번호 · 그때의 아이템 (고를 때 바뀌지 않았는지 확인) */
    record Entry(int slot, ItemStack snapshot, boolean worn, int level, int kindOrder) {
    }

    private EnhanceList() {
    }

    static List<Entry> scan(Player player) {
        PlayerInventory inventory = player.getInventory();
        List<Entry> entries = new ArrayList<>();
        for (int slot = 0; slot <= LAST_SLOT; slot++) {
            ItemStack item = inventory.getItem(slot);
            EnhanceTrack track = EnhanceTracks.trackOf(item).orElse(null);
            if (track == null) {
                continue;
            }
            entries.add(new Entry(slot, item.clone(), slot >= FIRST_WORN_SLOT, EnhanceTracks.levelOf(item), kindOrder(track)));
        }
        for (int i = 0; i < EnhanceSlots.extraCount(player); i++) {          // 가방 밖 착용 칸 (장신구)
            int slot = EnhanceSlots.EXTRA_FIRST + i;
            ItemStack item = EnhanceSlots.get(player, slot);
            EnhanceTrack track = EnhanceTracks.trackOf(item).orElse(null);
            if (track != null) {
                entries.add(new Entry(slot, item.clone(), true, EnhanceTracks.levelOf(item), kindOrder(track)));
            }
        }
        entries.sort(Comparator.comparing((Entry e) -> !e.worn())
                .thenComparingInt(Entry::level)
                .thenComparingInt(Entry::kindOrder)
                .thenComparingInt(Entry::slot));
        return entries;
    }

    private static int kindOrder(EnhanceTrack track) {
        if (track instanceof WeaponTrack) {
            return 0;
        }
        if (track instanceof ArmorTrack armor) {
            return 1 + armor.part().ordinal();
        }
        return 10;                                    // 장신구 등
    }

    /** 창 칸 번호 → 이 쪽의 카드 번호 (0~11), 카드가 아니면 -1 */
    static int cardOf(int rawSlot) {
        int row = rawSlot / 9 - FIRST_ROW;
        int col = rawSlot % 9;
        if (row < 0 || row >= ROWS || col >= COLS * 2) {
            return -1;
        }
        return row * COLS + col / 2;
    }

    /** 카드의 아이콘 칸 (오른쪽 칸 = +1) */
    static int iconSlot(int card) {
        return (FIRST_ROW + card / COLS) * 9 + (card % COLS) * 2;
    }

    static int cardX(int card) {
        return CARD_X0 + (card % COLS) * CARD_W;
    }

    static int cardRow(int card) {
        return card / COLS;
    }

    static int pageCount(int entries) {
        return Math.max(1, (entries + PAGE_SIZE - 1) / PAGE_SIZE);
    }
}

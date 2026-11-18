package com.brassfield.cooking;

import com.brassfield.common.CommandSupport;
import com.brassfield.common.ItemsAdderGuiBackground;
import com.brassfield.common.TitleCanvas;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 요리 기기 창 제목에 얹는 글꼴 그림 (tools/gui/make_cook_assets.py 가 만든 rustport:cook_* 와 이름·위치를 맞춘다).
 * <ul>
 *   <li>숫자 글꼴: 0~9 · 쉼표 · 점 · k. 테 두른 숫자(재료 개수)는 그림 폭 5(쉼표·점 3)에 왼쪽 테 1px,
 *       테 없는 숫자(접시 명찰·×N)는 그림 폭 4(쉼표·점 2).</li>
 *   <li>높이(y)는 글꼴 그림마다 정해져 있어 줄마다 따로 만든다 (재료 칸 줄 0·1, 책 필요 재료 줄 3·4).</li>
 * </ul>
 */
final class CookGlyphs {

    static final String BOOK_BACKGROUND = "rustport:cook_book_bg";
    static final String GENERIC_BACKGROUND = "rustport:cook_generic_bg";
    static final int BACKGROUND_ADVANCE = 176;
    static final int GAUGE_STEPS = 8;
    private static final int PLATE_RIGHT_X = 141;                  // 접시 아래 명찰 숫자 오른쪽 끝
    private static final int TIMES_X = 142;                        // 책 큰 요리 오른쪽 "×"
    private static final int PICK_ADVANCE = 20;
    private static final int PIN_ADVANCE = 4;
    private static final int CNT_SHIFT = 1;                        // 재료·완성품 개수는 칸 오른쪽 위로 1px 더 (글꼴 그림 높이도 1px 위, make_cook_assets.py)

    private final ItemsAdderGuiBackground background;
    private final Map<String, String> glyphs = new ConcurrentHashMap<>();

    CookGlyphs(ItemsAdderGuiBackground background) {
        this.background = background;
    }

    ItemsAdderGuiBackground background() {
        return background;
    }

    String glyph(String id) {
        return glyphs.computeIfAbsent(id, background::glyph);
    }

    static String machineBackground(String stationKey) {
        return "rustport:cook_" + stationKey + "_bg";
    }

    /*
     * 2배 해상도 배경은 조각 4장 (<이름>_0 왼쪽 위 · _1 오른쪽 위 · _2 왼쪽 아래 · _3 오른쪽 아래, 창 128px 에서 나눔).
     * 마인크래프트 글꼴 판이 256x256 이라 그보다 큰 글꼴 그림은 네모(□)로 나오기 때문.
     */
    private static final int TILE = 128;
    private static final int TILE_RIGHT_ADVANCE = BACKGROUND_ADVANCE - TILE;

    private boolean tiled(String background) {
        return glyph(background).isEmpty() && !glyph(background + "_0").isEmpty();
    }

    boolean hasBackground(String background) {
        return !glyph(background).isEmpty() || tiled(background);
    }

    /** 창을 처음 열 때 ItemsAdder 에 넘기는 배경 (조각 배경이면 왼쪽 위 조각 — 열자마자 제목을 다시 그려 나머지를 채운다) */
    String openingBackground(String background) {
        return tiled(background) ? background + "_0" : background;
    }

    TitleCanvas backgroundCanvas(String background) {
        if (!tiled(background)) {
            return new TitleCanvas(glyph(background), BACKGROUND_ADVANCE);
        }
        TitleCanvas canvas = new TitleCanvas("", 0);
        canvas.place(0, glyph(background + "_0"), TILE);
        canvas.place(TILE, glyph(background + "_1"), TILE_RIGHT_ADVANCE);
        canvas.place(0, glyph(background + "_2"), TILE);
        canvas.place(TILE, glyph(background + "_3"), TILE_RIGHT_ADVANCE);
        return canvas;
    }

    void gauge(TitleCanvas canvas, CookLayout layout, int level) {
        canvas.place(layout.gaugeX(), glyph("rustport:cook_gauge_" + layout.gaugeGlyph() + "_" + Math.max(0, Math.min(GAUGE_STEPS, level))),
                layout.gaugeAdvance());
    }

    /**
     * 칸 오른쪽에 테 두른 개수 (재료 칸 줄 0·1 = "cnt" 은 위쪽, 책 필요 재료 줄 3·4 = "need" 는 아래쪽 — 높이는 글꼴 그림에 정해져 있다)
     */
    void slotCount(TitleCanvas canvas, String kind, int slot, String text) {
        count(canvas, kind, slot / 9, 7 + (slot % 9) * 18 + 16, text);
    }

    /** 테 두른 개수를 줄 row 높이에 오른쪽 끝 right 에 맞춰 (칸 밖 자리에도) */
    void count(TitleCanvas canvas, String kind, int row, int right, String text) {
        // 재료·완성품 개수(cnt)는 한 자리 숫자 자리에서 오른쪽으로 늘어난다 (왼쪽으로 늘면 같은 칸 아이템 뒤로 숨는다)
        int x = "cnt".equals(kind) ? right - inkWidth("0") + 1 + CNT_SHIFT : right - inkWidth(text) + 1;
        for (char ch : text.toCharArray()) {
            canvas.place(x - 1, glyph("rustport:cook_" + kind + "_r" + row + "_" + key(ch)), narrow(ch) ? 3 : 5);
            x += narrow(ch) ? 2 : 4;
        }
    }

    void plateCount(TitleCanvas canvas, String text) {
        plain(canvas, "rustport:cook_plate_", PLATE_RIGHT_X - inkWidth(text) + 1, text);
    }

    void times(TitleCanvas canvas, int amount) {
        canvas.place(TIMES_X, glyph("rustport:cook_times_x"), 4);
        plain(canvas, "rustport:cook_times_", TIMES_X + 5, String.valueOf(amount));
    }

    /**
     * 책 목록 칸(slot) 둘레 금색 테 / 왼쪽 위 빨간 핀
     */
    void pick(TitleCanvas canvas, int slot) {
        canvas.place(7 + (slot % 9) * 18 - 1, glyph("rustport:cook_pick_r" + slot / 9), PICK_ADVANCE);
    }

    void pin(TitleCanvas canvas, int slot) {
        canvas.place(7 + (slot % 9) * 18 - 1, glyph("rustport:cook_pin_r" + slot / 9), PIN_ADVANCE);
    }

    private void plain(TitleCanvas canvas, String prefix, int x, String text) {
        for (char ch : text.toCharArray()) {
            int advance = narrow(ch) ? 2 : 4;
            canvas.place(x, glyph(prefix + key(ch)), advance);
            x += advance;
        }
    }

    /**
     * 재료 개수: 1,000 미만은 그대로, 넘으면 "1.2k" (소수 한 자리 버림)
     */
    static String compact(long count) {
        if (count < 1000) {
            return String.valueOf(count);
        }
        long tenths = count / 100;
        return tenths % 10 == 0 || count >= 10000 ? count / 1000 + "k" : tenths / 10 + "." + tenths % 10 + "k";
    }

    /**
     * 접시 명찰: 99,999 까지 쉼표, 넘으면 "123k"
     */
    static String plate(long count) {
        return count < 100000 ? CommandSupport.formatNumber(count) : count / 1000 + "k";
    }

    private static boolean narrow(char ch) {
        return ch == ',' || ch == '.';
    }

    private static String key(char ch) {
        return switch (ch) {
            case ',' -> "comma";
            case '.' -> "dot";
            default -> String.valueOf(ch);
        };
    }

    private static int inkWidth(String text) {
        int width = -1;
        for (char ch : text.toCharArray()) {
            width += narrow(ch) ? 2 : 4;
        }
        return width;
    }
}

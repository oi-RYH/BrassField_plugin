package com.brassfield.market;

import com.brassfield.common.ItemsAdderGuiBackground;
import com.brassfield.common.TitleCanvas;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 종자·작물 거래기 창 제목으로 띄우는 숫자 글꼴 그림 (BrassField tools/gui/make_crop_assets.py 가 만든 ItemsAdder font_images).
 * amber : 금액 창·페이지 번호 창 숫자 (숫자·'/' 이동량 4, ',' 2)
 * tag<줄> : 씨앗 가격표 조각 — 왼쪽 끝(테두리+금화, 8) · 숫자(4) · 오른쪽 끝(2). 봉투 줄(1~4)마다 높이가 달라 따로 있다.
 */
final class CropFont {

    static final String SELL_BACKGROUND = "rustport:crop_sell_bg";
    static final String SEED_BACKGROUND = "rustport:seed_shop_bg";
    static final int BACKGROUND_ADVANCE = 176;

    private static final int DIGIT_ADVANCE = 4;
    private static final int COMMA_ADVANCE = 2;
    private static final int TAG_LEFT_ADVANCE = 8;
    private static final int TAG_RIGHT_ADVANCE = 2;

    private final ItemsAdderGuiBackground fontImages;
    private final Map<String, String> glyphs = new ConcurrentHashMap<>();

    CropFont(ItemsAdderGuiBackground fontImages) {
        this.fontImages = fontImages;
    }

    String glyph(String id) {
        return glyphs.computeIfAbsent(id, fontImages::glyph);
    }

    /**
     * 호박색 숫자 글자들의 폭 (마지막 글자 뒤 틈 1px 제외)
     */
    static int amberWidth(String text) {
        int width = 0;
        for (char ch : text.toCharArray()) {
            width += ch == ',' ? COMMA_ADVANCE : DIGIT_ADVANCE;
        }
        return Math.max(0, width - 1);
    }

    /**
     * 호박색 숫자를 x 부터 그린다 (숫자·',' · '/' 만)
     */
    void amber(TitleCanvas canvas, int x, String text) {
        for (char ch : text.toCharArray()) {
            String key = ch == ',' ? "comma" : ch == '/' ? "slash" : String.valueOf(ch);
            int advance = ch == ',' ? COMMA_ADVANCE : DIGIT_ADVANCE;
            canvas.place(x, glyph("rustport:crop_amber_" + key), advance);
            x += advance;
        }
    }

    /**
     * 씨앗 가격표: 봉투 줄 row(1~4)의 x 에 금화 + 가격 숫자
     */
    void priceTag(TitleCanvas canvas, int row, int x, long price) {
        String prefix = "rustport:crop_tag" + row + "_";
        canvas.place(x, glyph(prefix + "left"), TAG_LEFT_ADVANCE);
        x += TAG_LEFT_ADVANCE;
        for (char ch : Long.toString(price).toCharArray()) {
            canvas.place(x, glyph(prefix + ch), DIGIT_ADVANCE);
            x += DIGIT_ADVANCE;
        }
        canvas.place(x, glyph(prefix + "right"), TAG_RIGHT_ADVANCE);
    }
}

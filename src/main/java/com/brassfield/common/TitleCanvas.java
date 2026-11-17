package com.brassfield.common;

/**
 * 상자 창 제목 글자로 배경 그림과 글꼴 그림(숫자 등)을 원하는 x 위치에 그리는 문자열을 만든다.
 * 제목 글자는 창 왼쪽에서 8px(ORIGIN_X)부터 시작하고, 글꼴 그림의 이동량은 그려진 폭과 같다
 * (ItemsAdder가 글자 뒤에 붙이는 -1px이 글자 간격 1px을 상쇄한다 — 강화 창과 같은 규칙).
 * 높이(y)는 글꼴 그림마다 ItemsAdder font_images의 y_position으로 정해져 있다.
 */
public final class TitleCanvas {

    private static final int ORIGIN_X = 8;

    private final StringBuilder builder = new StringBuilder("§f");
    private int cursor;

    /**
     * 창 왼쪽 끝(x=0)에 배경 그림을 깔고 시작한다. backgroundAdvance = 배경 그림의 그려진 폭
     */
    public TitleCanvas(String backgroundGlyph, int backgroundAdvance) {
        builder.append(FontSpace.of(-ORIGIN_X)).append(backgroundGlyph).append(FontSpace.of(ORIGIN_X - backgroundAdvance));
    }

    /**
     * 창 기준 x 에 글꼴 그림 하나를 놓는다. advance = 그 그림의 폭
     */
    public TitleCanvas place(int x, String glyph, int advance) {
        if (glyph.isEmpty()) {
            return this;
        }
        int target = x - ORIGIN_X;
        builder.append(FontSpace.of(target - cursor)).append(glyph);
        cursor = target + advance;
        return this;
    }

    public String build() {
        return builder + FontSpace.of(-cursor);
    }
}

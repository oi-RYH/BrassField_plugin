package com.brassfield.common;

/**
 * ItemsAdder 리소스팩에 들어 있는 공백 이동 글자(Negative Space Font 규격)로 가로 이동 문자열을 만든다.
 * 음수: U+F801~F808 = -1~-8, U+F809/F80A/F80B/F80C = -16/-32/-64/-128
 * 양수: U+F822~F828 = +2~+8, U+F829/F82A/F82B/F82C = +16/+32/+64/+128 (+1 글자는 없어 +2 -1로 만든다)
 */
public final class FontSpace {

    private static final int[] STEPS = {128, 64, 32, 16};
    private static final char[] NEGATIVE_STEPS = {'', '', '', ''};
    private static final char[] POSITIVE_STEPS = {'', '', '', ''};

    private FontSpace() {
    }

    public static String of(int pixels) {
        StringBuilder builder = new StringBuilder();
        int remaining = Math.abs(pixels);
        boolean negative = pixels < 0;
        for (int i = 0; i < STEPS.length; i++) {
            while (remaining >= STEPS[i]) {
                builder.append(negative ? NEGATIVE_STEPS[i] : POSITIVE_STEPS[i]);
                remaining -= STEPS[i];
            }
        }
        if (remaining > 8) {
            builder.append(negative ? '' : '');
            remaining -= 8;
        }
        if (remaining > 0) {
            if (negative) {
                builder.append((char) (0xF800 + remaining));
            } else if (remaining == 1) {
                builder.append('').append('');
            } else {
                builder.append((char) (0xF820 + remaining));
            }
        }
        return builder.toString();
    }
}

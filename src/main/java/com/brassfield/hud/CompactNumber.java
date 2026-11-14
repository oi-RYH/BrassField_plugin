package com.brassfield.hud;

/**
 * 큰 수를 K·M·B·T·Q·E 단위로 줄여 최대 5글자로 만든다. 반올림하면 999,999가 "1000K"가 되므로 내림한다.
 * <pre>
 * 999 → 999      8,654 → 8.6K      125,400 → 125K      10,000,000,000,003 → 10T
 * </pre>
 */
final class CompactNumber {

    private static final String[] UNITS = {"K", "M", "B", "T", "Q", "E"};

    private CompactNumber() {
    }

    static String format(long value) {
        if (value < 1000) {
            return Long.toString(value);
        }
        int unit = -1;
        long scaled = value;
        long remainder = 0;
        while (scaled >= 1000 && unit < UNITS.length - 1) {
            remainder = scaled % 1000;
            scaled /= 1000;
            unit++;
        }
        // 100 미만이면 소수 첫째 자리까지 (12.5K), 100 이상이면 정수만 (125K)
        if (scaled < 100) {
            long tenth = remainder / 100;
            return tenth == 0 ? scaled + UNITS[unit] : scaled + "." + tenth + UNITS[unit];
        }
        return scaled + UNITS[unit];
    }
}

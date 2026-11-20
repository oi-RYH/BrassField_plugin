package com.brassfield.enhancement;

import java.util.Map;

/**
 * 자동 생성 파일 (gen_board_font.py) — 강화 GUI 글자 보드에서 쓸 수 있는 글자와 각 글자의 이동량(px).
 * 글자 그림은 ItemsAdder font_images "rustport:bf<줄번호>_<유니코드 16진수>"로 등록되어 있다.
 */
final class BoardFont {

    static final int LINE_COUNT = 3;
    static final int SPACE_ADVANCE = 4;

    static final Map<Character, Integer> ADVANCES = Map.ofEntries(
            Map.entry('%', 6),
            Map.entry('+', 6),
            Map.entry('.', 2),
            Map.entry('0', 6),
            Map.entry('1', 6),
            Map.entry('2', 6),
            Map.entry('3', 6),
            Map.entry('4', 6),
            Map.entry('5', 6),
            Map.entry('6', 6),
            Map.entry('7', 6),
            Map.entry('8', 6),
            Map.entry('9', 6),
            Map.entry('→', 8),
            Map.entry('가', 8),
            Map.entry('급', 8),
            Map.entry('강', 8),
            Map.entry('계', 8),
            Map.entry('고', 9),
            Map.entry('공', 9),
            Map.entry('넣', 7),
            Map.entry('단', 8),
            Map.entry('를', 9),
            Map.entry('불', 9),
            Map.entry('비', 7),
            Map.entry('성', 7),
            Map.entry('세', 8),
            Map.entry('승', 8),
            Map.entry('어', 7),
            Map.entry('요', 9),
            Map.entry('장', 8),
            Map.entry('주', 9),
            Map.entry('최', 8),
            Map.entry('화', 9)
    );

    private BoardFont() {
    }

    static String fontImageId(int line, char ch) {
        return String.format("rustport:bf%d_%04x", line, (int) ch);
    }
}

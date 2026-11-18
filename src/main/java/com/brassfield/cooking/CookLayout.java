package com.brassfield.cooking;

/**
 * 요리 기기 창의 칸 배치. 기기마다 그림이 달라 칸 위치도 다르다 (tools/gui/make_cook_bg.py 의 LAYOUTS 와 맞춘다).
 *
 * @param ingredientSlots 걸린 요리 재료 칸 (재료 순서대로, 최대 5)
 * @param outputSlots     완성품 칸 (첫 칸에 요리 그림, 나머지는 같은 설명의 빈칸)
 * @param bigOutput       완성품을 2배 크기 접시 모델(rustport:cook_plate_*)로 그리고 접시 명찰에 개수 — 아니면 1배 아이콘 + 칸 오른쪽 위 개수
 * @param bookSlots       레시피 책 그림 칸 (누르면 책)
 * @param byproductSlots  빈 그릇 칸 (한 칸이면 모든 그릇을 한 칸에)
 * @param fireSlot        조리 시작·멈춤 불 버튼
 * @param gaugeSlots      게이지가 걸친 칸 (마우스를 올리면 남은 시간)
 * @param gaugeGlyph      게이지 글꼴 그림 이름 앞부분 (rustport:cook_gauge_&lt;이름&gt;_&lt;단계&gt;)
 * @param gaugeX          게이지 글꼴 그림 왼쪽 x (창 기준)
 * @param gaugeAdvance    게이지 글꼴 그림 폭
 * @param startIcon       시작 버튼 아이콘 이름 (rustport:cook_&lt;이름&gt;_on · _off): fire = 불, gear = 톱니
 */
record CookLayout(int[] ingredientSlots, int[] outputSlots, boolean bigOutput, int[] bookSlots, int[] byproductSlots,
                  int fireSlot, int[] gaugeSlots, String gaugeGlyph, int gaugeX, int gaugeAdvance, String startIcon) {

    /** 대형 솥 (그림이 없는 기기도 같은 배치): 주문서 위 재료 (0줄 1~3열, 1줄 1~2열) · 오른쪽 접시 2x2 · 책 2x2 · 화덕 문 불 버튼 · 솥 게이지 */
    static final CookLayout KETTLE = new CookLayout(new int[]{1, 2, 3, 10, 11}, new int[]{24, 25, 33, 34}, true,
            new int[]{6, 7, 15, 16}, new int[]{52, 53}, 38, new int[]{30, 31}, "kettle", 71, 13, "fire");

    /** 조리대: 재료는 들보에 물린 주문서 위 (2줄 0~2열 + 3줄 0~1열), 완성품·빈 그릇은 오른쪽 도마, 책은 오른쪽 벽에 걸린 프라이팬 자리 (흰 테두리),
     *  게이지는 냄비, 불 버튼은 화덕 창 */
    static final CookLayout COUNTER = new CookLayout(new int[]{18, 19, 20, 27, 28}, new int[]{33}, false,
            new int[]{16, 25}, new int[]{34}, 49, new int[]{31}, "counter", 80, 13, "fire");

    /** 착즙기:재료는 작은 주문서 위 (1줄 1열), 책은 그 아래 (3·4줄 1열), 완성품은 꼭지 아래 유리병 (4줄 3열에 아이콘,
     *  3줄 3열은 같은 설명), 톱니 시작 버튼은 나무 받침대 앞면 (4줄 5열), 빈 그릇 칸 없음.
     *  게이지는 맨 아래 진행 막대 + 압착기 유리통 주스 (한 그림): 막대 칸 (5줄 1~7열) · 유리통 칸 (1·2줄 5열) */
    static final CookLayout JUICER = new CookLayout(new int[]{10}, new int[]{39, 30}, false,
            new int[]{28, 37}, new int[]{}, 41, new int[]{46, 47, 48, 49, 50, 51, 52, 14, 23}, "juicer", 28, 123, "gear");

    /** 제빵 오븐: 재료는 가로로 긴 주문서 위 (1줄 1·2열), 그 아래 나무 탁자 위에 완성품 (3줄 1열) · 빈 병 (3줄 2열),
     *  책은 탁자 아래 (4·5줄 1열), 불 버튼은 오른쪽 오븐 화실 문 (4줄 6열).
     *  게이지는 굽는 칸 창 (파이가 노릇해지고 불빛이 밝아짐) + 솥과 같은 계기판 (한 그림): 1·2줄 5~8열 */
    static final CookLayout OVEN = new CookLayout(new int[]{10, 11}, new int[]{28}, false,
            new int[]{37, 46}, new int[]{29}, 42, new int[]{14, 15, 16, 17, 23, 24, 25, 26}, "oven", 96, 65, "fire");

    static CookLayout of(String stationKey) {
        return switch (stationKey) {
            case "counter" -> COUNTER;
            case "juicer" -> JUICER;
            case "oven" -> OVEN;
            default -> KETTLE;
        };
    }

    boolean isIngredient(int slot) {
        return indexOf(ingredientSlots, slot) >= 0;
    }

    boolean isOutput(int slot) {
        return indexOf(outputSlots, slot) >= 0;
    }

    boolean isBook(int slot) {
        return indexOf(bookSlots, slot) >= 0;
    }

    boolean isByproduct(int slot) {
        return indexOf(byproductSlots, slot) >= 0;
    }

    static int indexOf(int[] slots, int slot) {
        for (int i = 0; i < slots.length; i++) {
            if (slots[i] == slot) {
                return i;
            }
        }
        return -1;
    }
}

package com.brassfield.accessory;

import net.kyori.adventure.text.format.NamedTextColor;
import net.kyori.adventure.text.format.TextColor;

/**
 * 장신구 분류: 세트(전투 · 요리/농사 · 생활/모험) × 종류(목걸이 · 귀걸이 2 · 반지 2) × 등급(일반 · 레어 · 영웅 · 전설).
 * 아이콘 이름 = {세트}_{종류}_{등급}_{강화} (tools/gui/art/accessory_*), 아이템 모델 = rustport:accessory/{아이콘 이름}.
 */
public final class AccessoryKind {

    private AccessoryKind() {
    }

    /** 부위: 장착 칸을 정한다 (기본옵션은 2026-11-21 없앰 — 능력치는 보조옵션 AccessoryOption) */
    public enum Part {
        NECKLACE("목걸이"),
        EARRING("귀걸이"),
        RING("반지");

        private final String displayName;

        Part(String displayName) {
            this.displayName = displayName;
        }

        public String displayName() {
            return displayName;
        }
    }

    /** 종류: 세트마다 5개 (아이콘 · 이름 순서) */
    public enum Variant {
        NECKLACE("necklace", Part.NECKLACE),
        EARRING_A("earring_a", Part.EARRING),
        EARRING_B("earring_b", Part.EARRING),
        RING_A("ring_a", Part.RING),
        RING_B("ring_b", Part.RING);

        private final String id;
        private final Part part;

        Variant(String id, Part part) {
            this.id = id;
            this.part = part;
        }

        public String id() {
            return id;
        }

        public Part part() {
            return part;
        }
    }

    public enum Set {
        COMBAT("combat", "전투", "전사의 목걸이", "투사의 귀걸이", "수호의 귀걸이", "격노의 반지", "철벽의 반지"),
        FARM("farm", "요리/농사", "풍작의 목걸이", "농부의 귀걸이", "셰프의 귀걸이", "재료의 반지", "빵꾼의 반지"),
        ADVENTURE("adventure", "생활/모험", "탐험가의 목걸이", "여행자의 귀걸이", "기록자의 귀걸이", "나침반의 반지", "생명의 반지");

        private final String id;
        private final String displayName;
        private final String[] itemNames;

        Set(String id, String displayName, String... itemNames) {
            this.id = id;
            this.displayName = displayName;
            this.itemNames = itemNames;
        }

        public String id() {
            return id;
        }

        public String displayName() {
            return displayName;
        }

        public String itemName(Variant variant) {
            return itemNames[variant.ordinal()];
        }
    }

    public enum Grade {
        COMMON("common", "일반", TextColor.color(0xC8C8D2)),
        RARE("rare", "레어", TextColor.color(0x55A0FF)),
        EPIC("epic", "영웅", TextColor.color(0xB05FFF)),
        LEGENDARY("legendary", "전설", TextColor.color(0xFF5544));

        private final String id;
        private final String displayName;
        private final TextColor color;

        Grade(String id, String displayName, TextColor color) {
            this.id = id;
            this.displayName = displayName;
            this.color = color;
        }

        public String id() {
            return id;
        }

        public String displayName() {
            return displayName;
        }

        public TextColor color() {
            return color;
        }
    }

    /** 등급 안 강화 단계 0~3 */
    public static final int MAX_LEVEL = 3;

    static final TextColor LABEL = NamedTextColor.GRAY;

    static <E extends Enum<E>> E parse(Class<E> type, String text) {
        for (E value : type.getEnumConstants()) {
            String id = value instanceof Set s ? s.id() : value instanceof Variant v ? v.id() : value instanceof Grade g ? g.id() : value.name();
            String name = value instanceof Set s ? s.displayName() : value instanceof Grade g ? g.displayName() : "";
            if (id.equalsIgnoreCase(text) || name.equals(text) || value.name().equalsIgnoreCase(text)) {
                return value;
            }
        }
        return null;
    }
}

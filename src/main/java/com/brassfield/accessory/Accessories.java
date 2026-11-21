package com.brassfield.accessory;

import com.brassfield.accessory.AccessoryKind.Grade;
import com.brassfield.accessory.AccessoryKind.Part;
import com.brassfield.accessory.AccessoryKind.Set;
import com.brassfield.accessory.AccessoryKind.Variant;
import io.papermc.paper.datacomponent.DataComponentTypes;
import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import net.kyori.adventure.text.format.TextDecoration;
import org.bukkit.Material;
import org.bukkit.NamespacedKey;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;
import org.bukkit.persistence.PersistentDataContainer;
import org.bukkit.persistence.PersistentDataType;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/**
 * 장신구 아이템 만들기 · 읽기. 그림은 리소스팩 rustport:accessory/{세트}_{종류}_{등급}_{강화} (32x32 아이콘, 3D 없음),
 * 정보는 아이템 PDC 에 (세트 · 종류 · 등급 · 강화) 로 저장한다. 바탕 아이템(종이)은 조합에 쓰이지 않도록 AccessoryListener 가 막는다.
 */
public final class Accessories {

    private static final String NS = "brassfield";
    static final NamespacedKey SET = new NamespacedKey(NS, "acc_set");
    static final NamespacedKey VARIANT = new NamespacedKey(NS, "acc_variant");
    static final NamespacedKey GRADE = new NamespacedKey(NS, "acc_grade");
    static final NamespacedKey LEVEL = new NamespacedKey(NS, "acc_level");
    static final NamespacedKey OPTIONS = new NamespacedKey(NS, "acc_options");   // "id=값;id=값" (강화 전 값)

    /** 아이템 하나의 장신구 정보. options = 보조옵션 (등급 칸 수만큼) */
    public record Info(Set set, Variant variant, Grade grade, int level, List<AccessoryOption.Roll> options) {
        /** 보조옵션 없이 (create 가 칸을 새로 굴린다) */
        public Info(Set set, Variant variant, Grade grade, int level) {
            this(set, variant, grade, level, List.of());
        }

        public Part part() {
            return variant.part();
        }

        public Info withLevel(int newLevel) {
            return new Info(set, variant, grade, newLevel, options);
        }

        public String iconName() {
            return set.id() + "_" + variant.id() + "_" + grade.id() + "_" + level;
        }
    }

    private Accessories() {
    }

    /** 장신구 아이템. 보조옵션 칸이 비어 있으면 세트 · 등급에 맞게 새로 굴려 채운다 */
    public static ItemStack create(Info info) {
        if (info.options().size() < AccessoryOption.slots(info.grade())) {
            info = new Info(info.set(), info.variant(), info.grade(), info.level(),
                    AccessoryOption.fill(info.set(), info.grade(), info.options()));
        }
        ItemStack item = new ItemStack(Material.PAPER);
        item.setData(DataComponentTypes.ITEM_MODEL, new NamespacedKey("rustport", "accessory/" + info.iconName()));
        item.setData(DataComponentTypes.MAX_STACK_SIZE, 1);
        ItemMeta meta = item.getItemMeta();
        PersistentDataContainer pdc = meta.getPersistentDataContainer();
        pdc.set(SET, PersistentDataType.STRING, info.set().id());
        pdc.set(VARIANT, PersistentDataType.STRING, info.variant().id());
        pdc.set(GRADE, PersistentDataType.STRING, info.grade().id());
        pdc.set(LEVEL, PersistentDataType.INTEGER, info.level());
        StringBuilder encoded = new StringBuilder();
        for (AccessoryOption.Roll roll : info.options()) {
            encoded.append(encoded.isEmpty() ? "" : ";").append(roll.option().id()).append('=').append(roll.base());
        }
        pdc.set(OPTIONS, PersistentDataType.STRING, encoded.toString());
        AccessoryTrack track = AccessoryTrack.of(info.grade());
        if (track != null) {
            com.brassfield.enhancement.EnhanceTracks.writeIdentity(meta, track, info.level());   // 강화 창에서 고를 수 있게
        }
        String name = info.set().itemName(info.variant()) + (info.level() > 0 ? " +" + info.level() : "");
        meta.displayName(plain(name, info.grade().color()));
        List<Component> lore = new ArrayList<>();
        lore.add(plain(info.grade().displayName() + " · " + info.part().displayName() + " · " + info.set().displayName() + " 세트",
                NamedTextColor.GRAY));
        lore.add(plain("강화 " + info.level() + " / " + AccessoryKind.MAX_LEVEL, NamedTextColor.DARK_GRAY));
        lore.add(Component.empty());
        lore.add(plain("보조옵션 " + info.options().size() + " / " + AccessoryOption.slots(info.grade())
                + (info.level() > 0 ? "  (강화 +" + Math.round(AccessoryOption.PER_LEVEL * info.level() * 100) + "%)" : ""), NamedTextColor.GRAY));
        for (AccessoryOption.Roll roll : info.options()) {
            lore.add(optionLine(roll.option(), roll.value(info.level())));
        }
        meta.lore(lore);
        item.setItemMeta(meta);
        return item;
    }

    public static Optional<Info> read(ItemStack item) {
        if (item == null || item.getType().isAir() || !item.hasItemMeta()) {
            return Optional.empty();
        }
        PersistentDataContainer pdc = item.getItemMeta().getPersistentDataContainer();
        String set = pdc.get(SET, PersistentDataType.STRING);
        String variant = pdc.get(VARIANT, PersistentDataType.STRING);
        String grade = pdc.get(GRADE, PersistentDataType.STRING);
        Integer level = pdc.get(LEVEL, PersistentDataType.INTEGER);
        if (set == null || variant == null || grade == null) {
            return Optional.empty();
        }
        Set s = AccessoryKind.parse(Set.class, set);
        Variant v = AccessoryKind.parse(Variant.class, variant);
        Grade g = AccessoryKind.parse(Grade.class, grade);
        if (s == null || v == null || g == null) {
            return Optional.empty();
        }
        List<AccessoryOption.Roll> options = new ArrayList<>();
        String encoded = pdc.get(OPTIONS, PersistentDataType.STRING);
        if (encoded != null && !encoded.isEmpty()) {
            for (String part : encoded.split(";")) {
                String[] kv = part.split("=");
                AccessoryOption option = kv.length == 2 ? AccessoryOption.byId(kv[0]) : null;
                if (option != null) {
                    try {
                        options.add(new AccessoryOption.Roll(option, Double.parseDouble(kv[1])));
                    } catch (NumberFormatException ignored) {
                        // 깨진 값은 건너뛴다
                    }
                }
            }
        }
        return Optional.of(new Info(s, v, g, Math.max(0, Math.min(AccessoryKind.MAX_LEVEL, level == null ? 0 : level)), options));
    }

    public static boolean isAccessory(ItemStack item) {
        return read(item).isPresent();
    }

    static Component optionLine(AccessoryOption option, double value) {
        return plain(" " + option.displayName() + " ", NamedTextColor.GRAY)
                .append(plain("+" + format(value) + option.unit(), NamedTextColor.GREEN));
    }

    static String format(double value) {
        return value == Math.rint(value) ? String.valueOf((long) value) : String.valueOf(Math.round(value * 10) / 10.0);
    }

    static Component plain(String text, net.kyori.adventure.text.format.TextColor color) {
        return Component.text(text, color).decoration(TextDecoration.ITALIC, false);
    }
}

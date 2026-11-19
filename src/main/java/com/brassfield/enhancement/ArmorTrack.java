package com.brassfield.enhancement;

import com.brassfield.stone.StoneGrade;
import io.papermc.paper.datacomponent.DataComponentTypes;
import io.papermc.paper.datacomponent.item.Equippable;
import io.papermc.paper.datacomponent.item.ItemAttributeModifiers;
import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import net.kyori.adventure.text.format.TextColor;
import org.bukkit.Material;
import org.bukkit.NamespacedKey;
import org.bukkit.attribute.Attribute;
import org.bukkit.attribute.AttributeModifier;
import org.bukkit.inventory.EquipmentSlot;
import org.bukkit.inventory.EquipmentSlotGroup;
import org.bukkit.inventory.ItemFlag;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;
import org.bukkit.plugin.java.JavaPlugin;

import java.util.ArrayList;
import java.util.List;

/**
 * 방어구 강화 (0~17강, 투구 · 상의 · 하의 · 신발 부위별로 따로). 노션 "전투·성장 시스템 · 축 1-B · 방어구 강화" 표와 같다.
 * 하락 없음 · 내구도 없음. 강화 수치(방어력 · 강인함 보너스, 체력, 피해 감소)는 네 부위에 똑같이 붙는다.
 * 외형은 ItemsAdder customitem 방어구 (contents/customitem/configs/armor.yml): 찢어진 옷 · 천 · 가죽 · 기사 · 영웅 · 마스터.
 * 투구는 3D 모델이라 재질이 종이 — 머리 칸에 쓸 수 있게 장착 정보(EQUIPPABLE)를 붙인다. 찢어진 옷 투구는 머리에선 안 보인다.
 * ItemsAdder 아이템이 없으면 바닐라 방어구로 대신한다.
 */
public final class ArmorTrack implements EnhanceTrack {

    public static final int MAX_LEVEL = 17;

    /** 부위: 바닐라 방어력 (가죽 · 철 · 다이아 · 네더라이트 · 영웅 고정값) */
    public enum Part {
        HEAD("투구", "helmet", EquipmentSlotGroup.HEAD, new double[]{1, 2, 3, 3, 4},
                Material.LEATHER_HELMET, Material.CHAINMAIL_HELMET, Material.IRON_HELMET, Material.DIAMOND_HELMET, Material.NETHERITE_HELMET),
        CHEST("상의", "chestplate", EquipmentSlotGroup.CHEST, new double[]{3, 6, 8, 8, 9},
                Material.LEATHER_CHESTPLATE, Material.CHAINMAIL_CHESTPLATE, Material.IRON_CHESTPLATE, Material.DIAMOND_CHESTPLATE, Material.NETHERITE_CHESTPLATE),
        LEGS("하의", "leggings", EquipmentSlotGroup.LEGS, new double[]{2, 5, 6, 6, 7},
                Material.LEATHER_LEGGINGS, Material.CHAINMAIL_LEGGINGS, Material.IRON_LEGGINGS, Material.DIAMOND_LEGGINGS, Material.NETHERITE_LEGGINGS),
        FEET("신발", "boots", EquipmentSlotGroup.FEET, new double[]{1, 2, 3, 3, 4},
                Material.LEATHER_BOOTS, Material.CHAINMAIL_BOOTS, Material.IRON_BOOTS, Material.DIAMOND_BOOTS, Material.NETHERITE_BOOTS);

        private final String displayName;
        private final String itemSuffix;
        private final EquipmentSlotGroup slot;
        private final double[] specArmor;          // 스펙 순서: 가죽 · 철 · 다이아 · 네더라이트 · 영웅
        private final Material[] looks;            // ItemsAdder 가 없을 때 대신할 바닐라: 가죽 · 사슬 · 철 · 다이아 · 네더라이트

        Part(String displayName, String itemSuffix, EquipmentSlotGroup slot, double[] specArmor, Material... looks) {
            this.displayName = displayName;
            this.itemSuffix = itemSuffix;
            this.slot = slot;
            this.specArmor = specArmor;
            this.looks = looks;
        }

        public String displayName() {
            return displayName;
        }

        String key() {
            return "armor_" + name().toLowerCase();
        }
    }

    // 스펙 (노션 "스펙" 열): 0 = 가죽, 1~4 = 철, 5~8 = 다이아, 9~12 = 네더라이트, 13~ = 영웅 고정
    private static final double[] SPEC_TOUGHNESS = {0, 0, 2, 3, 3.5};

    // 단계 순서대로 0~17. 같은 외형 구간 안에서 누적되는 보너스 (노션 "+0.2" 등의 누적합)
    private static final double[] ARMOR_BONUS = {0, 0, 0.2, 0.4, 0.6, 0, 0, 0, 0, 0, 0.3, 0.6, 1.0, 0, 0, 0, 0, 0};
    private static final double[] TOUGHNESS_BONUS = {0, 0, 0, 0, 0, 0, 0.1, 0.2, 0.4, 0, 0.1, 0.3, 0.5, 0, 0, 0, 0, 0};
    // 영웅 구간 체력 (+2.5 누적, 17강은 16강과 같음) · 피해 감소 %
    private static final double[] HEALTH = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2.5, 5.0, 7.5, 10.0, 10.0};
    private static final double[] DAMAGE_REDUCTION = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 8, 12, 16};

    // 임시 성공 확률 (노션엔 "무기보다 낮게"만 있음). 실패하면 유지 — 하락 없음
    private static final double[] SUCCESS = {95, 85, 80, 75, 70, 60, 52, 45, 40, 32, 25, 20, 15, 10, 7, 5, 3};

    // 외형 구간별 ItemsAdder 방어구 세트 이름 (customitem:<세트>_<helmet|chestplate|leggings|boots>)
    private static final String[] LOOK_SETS = {"torn_clothes", "cloth_armor", "leather_armor", "knight_armor", "hero_armor", "master_armor"};

    private final Part part;
    private final NamespacedKey armorKey;
    private final NamespacedKey toughnessKey;
    private final NamespacedKey healthKey;

    ArmorTrack(JavaPlugin plugin, Part part) {
        this.part = part;
        String prefix = "enhance_" + part.key() + "_";
        armorKey = new NamespacedKey(plugin, prefix + "armor");
        toughnessKey = new NamespacedKey(plugin, prefix + "toughness");
        healthKey = new NamespacedKey(plugin, prefix + "health");
    }

    public Part part() {
        return part;
    }

    @Override
    public String key() {
        return part.key();
    }

    @Override
    public String displayName() {
        return "방어구 (" + part.displayName() + ")";
    }

    @Override
    public int maxLevel() {
        return MAX_LEVEL;
    }

    private static int clamp(int level) {
        return Math.max(0, Math.min(level, MAX_LEVEL));
    }

    /** 외형 구간: 0 찢어진 옷 · 1 천 · 2 가죽 · 3 기사 · 4 영웅 · 5 마스터 */
    private static int lookTier(int level) {
        if (level == 0) return 0;
        if (level <= 4) return 1;
        if (level <= 8) return 2;
        if (level <= 12) return 3;
        if (level <= 16) return 4;
        return 5;
    }

    private static int specIndex(int level) {
        return Math.min(lookTier(level), 4);
    }

    private static String tierName(int level) {
        return switch (lookTier(level)) {
            case 0 -> "찢어진 옷";
            case 1 -> "천 갑옷";
            case 2 -> "가죽 갑옷";
            case 3 -> "기사 갑옷";
            case 4 -> "영웅 갑옷";
            default -> "마스터 아머";
        };
    }

    private static TextColor tierColor(int level) {
        return switch (lookTier(level)) {
            case 0, 1 -> NamedTextColor.GRAY;
            case 2, 3 -> NamedTextColor.WHITE;
            case 4 -> NamedTextColor.GOLD;
            default -> NamedTextColor.LIGHT_PURPLE;
        };
    }

    private static StoneGrade gradeAt(int level) {
        if (level >= MAX_LEVEL) return StoneGrade.END;
        if (level <= 4) return StoneGrade.LOW;
        if (level <= 12) return StoneGrade.MIDDLE;
        return StoneGrade.HIGH;
    }

    private static int gradeFirstLevel(StoneGrade grade) {
        return switch (grade) {
            case LOW -> 0;
            case MIDDLE -> 5;
            case HIGH -> 13;
            case END -> MAX_LEVEL;
        };
    }

    public double armor(int level) {
        level = clamp(level);
        return part.specArmor[specIndex(level)] + ARMOR_BONUS[level];
    }

    public static double toughness(int level) {
        level = clamp(level);
        return SPEC_TOUGHNESS[specIndex(level)] + TOUGHNESS_BONUS[level];
    }

    public static double health(int level) {
        return HEALTH[clamp(level)];
    }

    /** 이 부위 하나가 주는 피해 감소 % (착용한 부위끼리 더한다 — {@link ArmorDamageListener}) */
    public static double damageReduction(int level) {
        return DAMAGE_REDUCTION[clamp(level)];
    }

    @Override
    public EnhanceStep step(int level) {
        level = clamp(level);
        StoneGrade grade = gradeAt(level);
        if (level >= MAX_LEVEL) {
            return new EnhanceStep(level, 0, 0, 0, grade, 0);
        }
        double success = SUCCESS[level];
        return new EnhanceStep(level, success, 0, 100.0 - success, grade,
                grade.costAtStep(level - gradeFirstLevel(grade)));
    }

    @Override
    public ItemStack applyLevel(ItemStack original, int newLevel) {
        return buildItem(newLevel);
    }

    /** level 단계 방어구를 새로 만든다 (처음 지급 · 관리자 지급) */
    public ItemStack buildItem(int level) {
        level = clamp(level);
        int look = lookTier(level);
        ItemStack item = EnhanceTracks.createCustomOrFallback(
                "customitem:" + LOOK_SETS[look] + "_" + part.itemSuffix, part.looks[Math.max(0, look - 1)]);
        item.setAmount(1);

        ItemMeta meta = item.getItemMeta();
        meta.displayName(Component.text("+" + level + " ", NamedTextColor.GREEN)
                .append(Component.text(tierName(level) + " " + part.displayName(), tierColor(level))));
        meta.lore(createLore(level));
        EnhanceTracks.writeIdentity(meta, this, level);
        meta.setUnbreakable(true);
        meta.addItemFlags(ItemFlag.HIDE_UNBREAKABLE);
        meta.setEnchantmentGlintOverride(level == MAX_LEVEL);
        item.setItemMeta(meta);
        applyAttributes(item, level);
        if (!item.hasData(DataComponentTypes.EQUIPPABLE)) {                 // 3D 투구(종이): 머리 칸에 쓸 수 있게
            item.setData(DataComponentTypes.EQUIPPABLE, Equippable.equippable(EquipmentSlot.HEAD).build());
        }
        return item;
    }

    private List<Component> createLore(int level) {
        List<Component> lore = new ArrayList<>();
        lore.add(loreLine("강화 단계: ", "+" + level, level == MAX_LEVEL ? NamedTextColor.LIGHT_PURPLE : NamedTextColor.GREEN));
        lore.add(loreLine("방어력: ", WeaponTrack.format(round(armor(level))), NamedTextColor.AQUA));
        lore.add(loreLine("방어 강도: ", WeaponTrack.format(round(toughness(level))), NamedTextColor.AQUA));
        if (health(level) > 0) {
            lore.add(loreLine("최대 체력: ", "+" + WeaponTrack.format(health(level)), NamedTextColor.RED));
        }
        if (damageReduction(level) > 0) {
            lore.add(loreLine("받는 피해 감소: ", WeaponTrack.format(damageReduction(level)) + "%", NamedTextColor.GOLD));
        }
        if (level == MAX_LEVEL) {
            lore.add(Component.text("최고 강화 단계", NamedTextColor.GOLD));
            return lore;
        }
        EnhanceStep step = step(level);
        lore.add(loreLine("필요 강화석: ", step.stoneGrade().displayName() + " " + step.stoneCost() + "개", step.stoneGrade().color()));
        lore.add(Component.empty());
        lore.add(loreLine("성공: ", WeaponTrack.format(step.successChance()) + "%", NamedTextColor.GREEN));
        lore.add(loreLine("유지: ", WeaponTrack.format(step.maintainChance()) + "%", NamedTextColor.YELLOW));
        return lore;
    }

    private static double round(double value) {
        return Math.round(value * 10.0) / 10.0;
    }

    private static Component loreLine(String label, String value, TextColor valueColor) {
        return Component.text(label, NamedTextColor.GRAY).append(Component.text(value, valueColor));
    }

    private void applyAttributes(ItemStack item, int level) {
        ItemAttributeModifiers.Builder builder = ItemAttributeModifiers.itemAttributes()
                .addModifier(Attribute.ARMOR,
                        new AttributeModifier(armorKey, round(armor(level)), AttributeModifier.Operation.ADD_NUMBER), part.slot);
        double toughness = round(toughness(level));
        if (toughness > 0) {
            builder.addModifier(Attribute.ARMOR_TOUGHNESS,
                    new AttributeModifier(toughnessKey, toughness, AttributeModifier.Operation.ADD_NUMBER), part.slot);
        }
        if (health(level) > 0) {
            builder.addModifier(Attribute.MAX_HEALTH,
                    new AttributeModifier(healthKey, health(level), AttributeModifier.Operation.ADD_NUMBER), part.slot);
        }
        item.setData(DataComponentTypes.ATTRIBUTE_MODIFIERS, builder.build());
    }
}

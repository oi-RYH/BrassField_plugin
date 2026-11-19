package com.brassfield.enhancement;

import com.brassfield.stone.StoneGrade;
import io.papermc.paper.datacomponent.DataComponentTypes;
import io.papermc.paper.datacomponent.item.ItemAttributeModifiers;
import io.papermc.paper.datacomponent.item.attribute.AttributeModifierDisplay;
import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import net.kyori.adventure.text.format.TextColor;
import org.bukkit.Material;
import org.bukkit.NamespacedKey;
import org.bukkit.attribute.Attribute;
import org.bukkit.attribute.AttributeModifier;
import org.bukkit.inventory.EquipmentSlotGroup;
import org.bukkit.inventory.ItemFlag;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;
import org.bukkit.plugin.java.JavaPlugin;

import java.util.List;

/**
 * 무기 강화 (0~25강, 단일 무기 · 외형 진화). 노션 "전투·성장 시스템 · 축 1 · 무기 강화" 표와 같다.
 * 결과 아이템은 단계만으로 새로 만든다 (무기에는 단계 외의 데이터가 없다).
 */
public final class WeaponTrack implements EnhanceTrack {

    private static final WeaponTier[] TIERS = {
            tier(0, Material.STICK, "막대기", "customitem:stick", 98, 0, 2, StoneGrade.LOW, 1.0, NamedTextColor.WHITE),
            tier(1, Material.WOODEN_SWORD, "부서진 목검", "customitem:broken_wooden_sword", 90, 0, 10, StoneGrade.LOW, 2.0, NamedTextColor.GRAY),
            tier(2, Material.WOODEN_SWORD, "부서진 목검", "customitem:broken_wooden_sword", 87, 0, 13, StoneGrade.LOW, 2.5, NamedTextColor.GRAY),
            tier(3, Material.WOODEN_SWORD, "부서진 목검", "customitem:broken_wooden_sword", 85, 0, 15, StoneGrade.LOW, 3.0, NamedTextColor.GRAY),
            tier(4, Material.WOODEN_SWORD, "부서진 목검", "customitem:broken_wooden_sword", 82, 0, 18, StoneGrade.LOW, 3.5, NamedTextColor.GRAY),
            tier(5, Material.WOODEN_SWORD, "목검", "customitem:wooden_sword", 80, 0, 20, StoneGrade.LOW, 4.0, NamedTextColor.WHITE),
            tier(6, Material.WOODEN_SWORD, "목검", "customitem:wooden_sword", 72, 0, 28, StoneGrade.LOW, 4.5, NamedTextColor.WHITE),
            tier(7, Material.WOODEN_SWORD, "목검", "customitem:wooden_sword", 67, 0, 33, StoneGrade.LOW, 5.0, NamedTextColor.WHITE),
            tier(8, Material.WOODEN_SWORD, "목검", "customitem:wooden_sword", 63, 0, 37, StoneGrade.LOW, 5.5, NamedTextColor.WHITE),
            tier(9, Material.STONE_SWORD, "돌검", "customitem:stone_sword", 60, 0, 40, StoneGrade.MIDDLE, 6.0, NamedTextColor.WHITE),
            tier(10, Material.STONE_SWORD, "돌검", "customitem:stone_sword", 40, 0.2, 59.8, StoneGrade.MIDDLE, 6.5, NamedTextColor.WHITE),
            tier(11, Material.STONE_SWORD, "돌검", "customitem:stone_sword", 30, 0.4, 69.6, StoneGrade.MIDDLE, 7.0, NamedTextColor.WHITE),
            tier(12, Material.STONE_SWORD, "돌검", "customitem:stone_sword", 20, 1.0, 79, StoneGrade.MIDDLE, 7.5, NamedTextColor.WHITE),
            tier(13, Material.IRON_SWORD, "철검", "customitem:iron_sword", 15, 0, 85, StoneGrade.MIDDLE, 8.0, NamedTextColor.WHITE),
            tier(14, Material.IRON_SWORD, "철검", "customitem:iron_sword", 13, 0.2, 86.8, StoneGrade.MIDDLE, 8.5, NamedTextColor.WHITE),
            tier(15, Material.IRON_SWORD, "철검", "customitem:iron_sword", 12, 0.4, 87.6, StoneGrade.MIDDLE, 9.0, NamedTextColor.WHITE),
            tier(16, Material.IRON_SWORD, "철검", "customitem:iron_sword", 11, 1.0, 88, StoneGrade.MIDDLE, 10.0, NamedTextColor.WHITE),
            tier(17, Material.DIAMOND_SWORD, "기사의 검", "customitem:knight_sword", 10, 0, 90, StoneGrade.HIGH, 12.0, NamedTextColor.AQUA),
            tier(18, Material.DIAMOND_SWORD, "기사의 검", "customitem:knight_sword", 8, 0.4, 91.6, StoneGrade.HIGH, 14.0, NamedTextColor.AQUA),
            tier(19, Material.DIAMOND_SWORD, "기사의 검", "customitem:knight_sword", 7, 0.9, 92.1, StoneGrade.HIGH, 16.0, NamedTextColor.AQUA),
            tier(20, Material.DIAMOND_SWORD, "기사의 검", "customitem:knight_sword", 6, 2.0, 92, StoneGrade.HIGH, 18.0, NamedTextColor.AQUA),
            tier(21, Material.NETHERITE_SWORD, "영웅의 검", "customitem:hero_sword", 5, 0, 95, StoneGrade.HIGH, 28.0, NamedTextColor.GOLD),
            tier(22, Material.NETHERITE_SWORD, "영웅의 검", "customitem:hero_sword", 4, 0.2, 95.8, StoneGrade.HIGH, 32.0, NamedTextColor.GOLD),
            tier(23, Material.NETHERITE_SWORD, "영웅의 검", "customitem:hero_sword", 3, 1.2, 95.8, StoneGrade.HIGH, 40.0, NamedTextColor.GOLD),
            tier(24, Material.NETHERITE_SWORD, "영웅의 검", "customitem:hero_sword", 1, 3.0, 96, StoneGrade.HIGH, 50.0, NamedTextColor.GOLD),
            tier(25, Material.NETHERITE_SWORD, "마스터소드", "customitem:master_sword", 0, 0, 0, StoneGrade.END, 65.0, NamedTextColor.LIGHT_PURPLE)
    };

    private final NamespacedKey attackDamageKey;
    private final NamespacedKey attackSpeedKey;

    WeaponTrack(JavaPlugin plugin) {
        attackDamageKey = new NamespacedKey(plugin, "enhance_attack_damage");
        attackSpeedKey = new NamespacedKey(plugin, "enhance_attack_speed");
        validateTierTable();
    }

    @Override
    public String key() {
        return "weapon";
    }

    @Override
    public String displayName() {
        return "무기";
    }

    @Override
    public int maxLevel() {
        return TIERS.length - 1;
    }

    public WeaponTier tier(int level) {
        return TIERS[Math.max(0, Math.min(level, maxLevel()))];
    }

    @Override
    public EnhanceStep step(int level) {
        WeaponTier tier = tier(level);
        return new EnhanceStep(tier.level(), tier.successChance(), tier.downgradeChance(), tier.maintainChance(),
                tier.stoneGrade(), tier.stoneGrade().costAt(tier.level()));
    }

    @Override
    public boolean isFreshItem(ItemStack item) {
        return EnhanceTracks.itemProvider().matches(item, TIERS[0].customItemId());
    }

    @Override
    public ItemStack applyLevel(ItemStack original, int newLevel) {
        return buildItem(newLevel);
    }

    /** level 단계 무기를 새로 만든다 (처음 지급 · 관리자 지급) */
    public ItemStack buildItem(int level) {
        WeaponTier tier = tier(level);
        ItemStack item = tier.customItemId() == null
                ? ItemStack.of(tier.material())
                : EnhanceTracks.itemProvider().create(tier.customItemId());
        item.setAmount(1);

        ItemMeta meta = item.getItemMeta();
        meta.displayName(
                Component.text("+" + tier.level() + " ", NamedTextColor.GREEN)
                        .append(Component.text(tier.displayName(), tier.nameColor()))
        );
        meta.lore(createLore(tier));
        EnhanceTracks.writeIdentity(meta, this, tier.level());
        meta.setUnbreakable(true);
        meta.addItemFlags(ItemFlag.HIDE_UNBREAKABLE);
        meta.setEnchantmentGlintOverride(tier.level() == maxLevel());
        item.setItemMeta(meta);
        applyCombatAttributes(item, tier.damage());
        return item;
    }

    private List<Component> createLore(WeaponTier tier) {
        if (tier.level() == maxLevel()) {
            return List.of(
                    loreLine("강화 단계: ", "+" + tier.level(), NamedTextColor.LIGHT_PURPLE),
                    loreLine("공격 데미지: ", format(tier.damage()), NamedTextColor.RED),
                    Component.text("최고 강화 단계", NamedTextColor.GOLD)
            );
        }
        EnhanceStep step = step(tier.level());
        return List.of(
                loreLine("강화 단계: ", "+" + tier.level(), NamedTextColor.GREEN),
                loreLine("공격 데미지: ", format(tier.damage()), NamedTextColor.RED),
                loreLine("필요 강화석: ", step.stoneGrade().displayName() + " " + step.stoneCost() + "개", step.stoneGrade().color()),
                Component.empty(),
                loreLine("성공: ", format(step.successChance()) + "%", NamedTextColor.GREEN),
                loreLine("하락: ", format(step.downgradeChance()) + "%", NamedTextColor.RED),
                loreLine("유지: ", format(step.maintainChance()) + "%", NamedTextColor.YELLOW)
        );
    }

    private static Component loreLine(String label, String value, TextColor valueColor) {
        return Component.text(label, NamedTextColor.GRAY).append(Component.text(value, valueColor));
    }

    private void applyCombatAttributes(ItemStack item, double damage) {
        AttributeModifier damageModifier = new AttributeModifier(
                attackDamageKey,
                damage - 1.0,
                AttributeModifier.Operation.ADD_NUMBER
        );
        AttributeModifier speedModifier = new AttributeModifier(
                attackSpeedKey,
                -2.4,
                AttributeModifier.Operation.ADD_NUMBER
        );

        item.setData(
                DataComponentTypes.ATTRIBUTE_MODIFIERS,
                ItemAttributeModifiers.itemAttributes()
                        .addModifier(
                                Attribute.ATTACK_DAMAGE,
                                damageModifier,
                                EquipmentSlotGroup.MAINHAND,
                                AttributeModifierDisplay.override(
                                        Component.text(format(damage) + " 공격 피해", NamedTextColor.DARK_GREEN)
                                )
                        )
                        .addModifier(
                                Attribute.ATTACK_SPEED,
                                speedModifier,
                                EquipmentSlotGroup.MAINHAND,
                                AttributeModifierDisplay.override(
                                        Component.text("1.6 공격 속도", NamedTextColor.DARK_GREEN)
                                )
                        )
        );
    }

    static String format(double value) {
        return value == Math.rint(value) ? String.format("%.0f", value) : String.valueOf(value);
    }

    private static WeaponTier tier(
            int level,
            Material material,
            String displayName,
            String customItemId,
            double successChance,
            double downgradeChance,
            double maintainChance,
            StoneGrade stoneGrade,
            double damage,
            NamedTextColor nameColor
    ) {
        return new WeaponTier(level, material, displayName, customItemId, successChance, downgradeChance,
                maintainChance, stoneGrade, damage, nameColor);
    }

    private void validateTierTable() {
        for (int index = 0; index < TIERS.length; index++) {
            WeaponTier tier = TIERS[index];
            if (tier.level() != index) {
                throw new IllegalStateException("강화 단계 인덱스가 일치하지 않습니다: " + index);
            }
            boolean gradeStarts = index == 0 || TIERS[index - 1].stoneGrade() != tier.stoneGrade();
            if (gradeStarts && tier.stoneGrade().firstLevel() != index) {
                throw new IllegalStateException("강화석 등급 시작 단계가 일치하지 않습니다: +" + index);
            }
            if (index < maxLevel()) {
                double totalChance = tier.successChance() + tier.downgradeChance() + tier.maintainChance();
                if (Math.abs(totalChance - 100.0) > 0.0001) {
                    throw new IllegalStateException("강화 확률의 합이 100이 아닙니다: +" + index + " = " + totalChance);
                }
            }
        }
    }

    /** 무기 한 단계: 확률 · 강화석 등급 + 외형 (재질 · 이름 · 커스텀 모델) · 데미지 */
    public record WeaponTier(
            int level,
            Material material,
            String displayName,
            String customItemId,
            double successChance,
            double downgradeChance,
            double maintainChance,
            StoneGrade stoneGrade,
            double damage,
            NamedTextColor nameColor
    ) {
    }
}

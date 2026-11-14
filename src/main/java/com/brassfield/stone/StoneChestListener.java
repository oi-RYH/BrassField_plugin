package com.brassfield.stone;

import com.brassfield.common.ItemsAdderItemProvider;
import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.Sound;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.block.Action;
import org.bukkit.event.player.PlayerInteractEvent;
import org.bukkit.inventory.EquipmentSlot;
import org.bukkit.inventory.ItemStack;

import java.util.Map;
import java.util.concurrent.ThreadLocalRandom;

/**
 * 강화석 상자: 우클릭하면 상자 1개가 사라지고 해당 등급 강화석 재화가 3~5개 채워진다.
 */
public final class StoneChestListener implements Listener {

    public static final int MIN_STONES = 3;
    public static final int MAX_STONES = 5;

    private static final Map<String, StoneGrade> CHEST_GRADES = Map.of(
            "rustport:low_enhancement_chest", StoneGrade.LOW,
            "rustport:mid_enhancement_chest", StoneGrade.MIDDLE,
            "rustport:high_enhancement_chest", StoneGrade.HIGH
    );

    private final ItemsAdderItemProvider itemProvider;
    private final StoneWallet wallet;

    public StoneChestListener(ItemsAdderItemProvider itemProvider, StoneWallet wallet) {
        this.itemProvider = itemProvider;
        this.wallet = wallet;
    }

    public static String chestIdOf(StoneGrade grade) {
        return CHEST_GRADES.entrySet().stream()
                .filter(entry -> entry.getValue() == grade)
                .map(Map.Entry::getKey)
                .findFirst()
                .orElseThrow(() -> new IllegalArgumentException("강화석 상자가 없는 등급입니다: " + grade));
    }

    @EventHandler(priority = EventPriority.HIGH)
    public void onInteract(PlayerInteractEvent event) {
        if (event.getAction() != Action.RIGHT_CLICK_AIR && event.getAction() != Action.RIGHT_CLICK_BLOCK) {
            return;
        }
        // 한 번의 우클릭에 주손·보조손 이벤트가 각각 올 수 있어, 상자는 주손에 들었을 때만 연다.
        ItemStack item = event.getItem();
        if (event.getHand() != EquipmentSlot.HAND || item == null || item.getType().isAir()) {
            return;
        }

        StoneGrade grade = CHEST_GRADES.get(itemProvider.idOf(item));
        if (grade == null) {
            return;
        }

        event.setCancelled(true);
        Player player = event.getPlayer();
        int amount = ThreadLocalRandom.current().nextInt(MIN_STONES, MAX_STONES + 1);

        ItemStack remaining = item.clone();
        remaining.setAmount(item.getAmount() - 1);
        player.getInventory().setItemInMainHand(remaining.getAmount() > 0 ? remaining : ItemStack.empty());

        wallet.deposit(player.getUniqueId(), grade, amount);
        player.playSound(player.getLocation(), Sound.BLOCK_CHEST_OPEN, 0.8f, 1.2f);
        player.sendMessage(Component.text(grade.displayName() + " 강화석 " + amount + "개를 얻었습니다! ", NamedTextColor.GREEN)
                .append(Component.text("(보유: " + wallet.get(player.getUniqueId(), grade) + "개)", NamedTextColor.GRAY)));
    }
}

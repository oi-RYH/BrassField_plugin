package com.brassfield.enhancement;

import com.brassfield.common.ItemDelivery;
import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.player.PlayerJoinEvent;
import org.bukkit.inventory.EquipmentSlot;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.PlayerInventory;

/**
 * 처음 접속한 플레이어에게 +0 강화 무기(막대기)와 +0 방어구 4부위(찢어진 옷)를 지급해, 별도 파밍 없이 바로 강화를 시작할 수 있게 한다.
 */
public final class StarterKitListener implements Listener {

    @EventHandler
    public void onPlayerJoin(PlayerJoinEvent event) {
        Player player = event.getPlayer();
        if (player.hasPlayedBefore()) {
            return;
        }

        ItemDelivery.giveOrDrop(player, EnhanceTracks.weapon().buildItem(0));
        giveStarterArmor(player);
        player.sendMessage(Component.text("길에서 주운 나뭇가지를 와 낡은 옷 한 벌을 받았습니다. 마을의 ", NamedTextColor.GREEN)
                .append(Component.text("증폭 공작대", NamedTextColor.YELLOW))
                .append(Component.text("에서 강화를 시작해보세요!", NamedTextColor.GREEN)));
    }

    /** +0 방어구 4부위: 빈 방어구 칸에는 바로 입히고, 차 있으면 가방으로 */
    static void giveStarterArmor(Player player) {
        PlayerInventory inventory = player.getInventory();
        for (ArmorTrack.Part part : ArmorTrack.Part.values()) {
            ItemStack piece = EnhanceTracks.armor(part).buildItem(0);
            EquipmentSlot slot = switch (part) {
                case HEAD -> EquipmentSlot.HEAD;
                case CHEST -> EquipmentSlot.CHEST;
                case LEGS -> EquipmentSlot.LEGS;
                case FEET -> EquipmentSlot.FEET;
            };
            ItemStack worn = inventory.getItem(slot);
            if (worn == null || worn.getType().isAir()) {
                inventory.setItem(slot, piece);
            } else {
                ItemDelivery.giveOrDrop(player, piece);
            }
        }
    }
}

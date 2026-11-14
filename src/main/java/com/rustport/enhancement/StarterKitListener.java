package com.rustport.enhancement;

import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.player.PlayerJoinEvent;

/**
 * 처음 접속한 플레이어에게 +0 강화 무기(막대기)를 지급해, 별도 파밍 없이 바로 강화를 시작할 수 있게 한다.
 * 방어구는 방어구 강화를 구현할 때 함께 지급한다.
 */
public final class StarterKitListener implements Listener {

    @EventHandler
    public void onPlayerJoin(PlayerJoinEvent event) {
        Player player = event.getPlayer();
        if (player.hasPlayedBefore()) {
            return;
        }

        ItemDelivery.giveOrDrop(player, EnhancementItem.buildItem(0));
        player.sendMessage(Component.text("길에서 주운 나뭇가지를 받았습니다. ", NamedTextColor.GREEN)
                .append(Component.text("/강화", NamedTextColor.YELLOW))
                .append(Component.text(" 로 강화를 시작해보세요!", NamedTextColor.GREEN)));
    }
}

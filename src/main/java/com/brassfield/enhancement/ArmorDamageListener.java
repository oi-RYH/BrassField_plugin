package com.brassfield.enhancement;

import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.entity.EntityDamageEvent;
import org.bukkit.inventory.ItemStack;

/**
 * 영웅 갑옷 이상(14강~)의 "받는 피해 감소 %". 바닐라 속성에 없는 효과라 피해 이벤트에서 직접 줄인다.
 * 착용한 강화 방어구 부위의 감소율을 더해서 적용한다 (방어력 계산 전 피해에 곱함).
 */
public final class ArmorDamageListener implements Listener {

    @EventHandler(priority = EventPriority.HIGH, ignoreCancelled = true)
    public void onDamage(EntityDamageEvent event) {
        if (!(event.getEntity() instanceof Player player)) {
            return;
        }
        EntityDamageEvent.DamageCause cause = event.getCause();
        if (cause == EntityDamageEvent.DamageCause.VOID || cause == EntityDamageEvent.DamageCause.KILL
                || cause == EntityDamageEvent.DamageCause.SUICIDE || cause == EntityDamageEvent.DamageCause.WORLD_BORDER) {
            return;
        }
        double percent = 0;
        for (ItemStack piece : player.getInventory().getArmorContents()) {
            if (EnhanceTracks.trackOf(piece).orElse(null) instanceof ArmorTrack) {
                percent += ArmorTrack.damageReduction(EnhanceTracks.levelOf(piece));
            }
        }
        if (percent > 0) {
            event.setDamage(event.getDamage() * Math.max(0, 1 - percent / 100.0));
        }
    }
}

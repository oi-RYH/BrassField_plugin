package com.rustport.enhancement;

import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.inventory.InventoryClickEvent;
import org.bukkit.event.inventory.InventoryCloseEvent;
import org.bukkit.event.player.PlayerJoinEvent;
import org.bukkit.event.player.PlayerQuitEvent;
import org.bukkit.inventory.ItemStack;

public final class EnhancementGuiListener implements Listener {

    private final EnhancementPlugin plugin;
    private final EnhancementService enhancementService;
    private final EnhancementAnimation animation;

    public EnhancementGuiListener(
            EnhancementPlugin plugin,
            EnhancementService enhancementService,
            EnhancementAnimation animation
    ) {
        this.plugin = plugin;
        this.enhancementService = enhancementService;
        this.animation = animation;
    }

    @EventHandler
    public void onInventoryClick(InventoryClickEvent event) {
        if (!(event.getInventory().getHolder() instanceof EnhancementGui gui)) {
            return;
        }

        event.setCancelled(true);
        if (event.getRawSlot() != EnhancementGui.ENHANCE_BUTTON_SLOT
                || !(event.getWhoClicked() instanceof Player player)
                || animation.isPlaying(player)) {
            return;
        }

        ItemStack targetItem = gui.getTargetItem();
        if (targetItem == null || targetItem.getType().isAir()) {
            return;
        }

        int currentLevel = EnhancementItem.getLevel(targetItem);
        if (currentLevel >= EnhancementItem.getMaxLevel()) {
            player.sendMessage(Component.text("이미 최고 강화 단계입니다!", NamedTextColor.YELLOW));
            return;
        }

        EnhancementService.EnhancementResult result = enhancementService.enhance(targetItem);
        ItemStack originalItem = gui.takeTargetItem();
        player.closeInventory();
        animation.play(
                player,
                originalItem,
                result,
                resultItem -> plugin.openEnhancementGui(player, resultItem)
        );
    }

    @EventHandler
    public void onInventoryClose(InventoryCloseEvent event) {
        if (!(event.getInventory().getHolder() instanceof EnhancementGui gui)
                || !(event.getPlayer() instanceof Player player)) {
            return;
        }

        ItemStack targetItem = gui.takeTargetItem();
        if (targetItem != null && !targetItem.getType().isAir()) {
            ItemDelivery.giveOrDrop(player, targetItem);
        }
    }

    @EventHandler
    public void onPlayerQuit(PlayerQuitEvent event) {
        animation.stop(event.getPlayer(), true);
    }

    @EventHandler
    public void onPlayerJoin(PlayerJoinEvent event) {
        animation.hideActiveDisplaysFrom(event.getPlayer());
    }
}

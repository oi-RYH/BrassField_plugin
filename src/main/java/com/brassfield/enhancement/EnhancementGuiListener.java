package com.brassfield.enhancement;

import com.brassfield.stone.StoneGrade;
import com.brassfield.stone.StoneWallet;
import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.inventory.InventoryClickEvent;
import org.bukkit.event.inventory.InventoryCloseEvent;
import org.bukkit.event.inventory.InventoryDragEvent;
import org.bukkit.event.inventory.InventoryType;
import org.bukkit.event.player.PlayerJoinEvent;
import org.bukkit.event.player.PlayerQuitEvent;
import org.bukkit.inventory.ItemStack;
import org.bukkit.plugin.java.JavaPlugin;

public final class EnhancementGuiListener implements Listener {

    private final JavaPlugin plugin;
    private final EnhancementCommand enhancementCommand;
    private final EnhancementService enhancementService;
    private final EnhancementAnimation animation;
    private final StoneWallet wallet;

    public EnhancementGuiListener(
            JavaPlugin plugin,
            EnhancementCommand enhancementCommand,
            EnhancementService enhancementService,
            EnhancementAnimation animation,
            StoneWallet wallet
    ) {
        this.plugin = plugin;
        this.enhancementCommand = enhancementCommand;
        this.enhancementService = enhancementService;
        this.animation = animation;
        this.wallet = wallet;
    }

    @EventHandler
    public void onInventoryClick(InventoryClickEvent event) {
        if (!(event.getInventory().getHolder() instanceof EnhancementGui gui)) {
            return;
        }

        event.setCancelled(true);
        int rawSlot = event.getRawSlot();

        if (rawSlot == EnhancementGui.TARGET_SLOT) {
            event.setCancelled(false);
            scheduleInfoRefresh(gui);
            return;
        }

        if (event.getClickedInventory() != null
                && event.getClickedInventory().getType() == InventoryType.PLAYER) {
            event.setCancelled(event.isShiftClick());
            return;
        }

        if (rawSlot != EnhancementGui.ENHANCE_BUTTON_SLOT
                || !(event.getWhoClicked() instanceof Player player)
                || animation.isPlaying(player)) {
            return;
        }

        ItemStack targetItem = gui.getTargetItem();
        if (targetItem == null || targetItem.getType().isAir()) {
            player.sendMessage(Component.text("강화할 아이템을 넣어주세요.", NamedTextColor.RED));
            return;
        }
        EnhanceTrack track = EnhanceTracks.trackOf(targetItem).orElse(null);
        if (track == null) {
            player.sendMessage(Component.text("강화할 수 없는 아이템입니다.", NamedTextColor.RED));
            return;
        }

        int currentLevel = EnhanceTracks.levelOf(targetItem);
        if (currentLevel >= track.maxLevel()) {
            player.sendMessage(Component.text("이미 최고 강화 단계입니다!", NamedTextColor.YELLOW));
            return;
        }

        EnhanceStep tier = track.step(currentLevel);
        StoneGrade grade = tier.stoneGrade();
        if (!wallet.withdraw(player.getUniqueId(), grade, tier.stoneCost())) {
            player.sendMessage(Component.text(grade.displayName() + " 강화석이 부족합니다. (필요: " + tier.stoneCost()
                    + "개, 보유: " + wallet.get(player.getUniqueId(), grade) + "개)", NamedTextColor.RED));
            return;
        }

        EnhancementService.EnhancementResult result = enhancementService.enhance(targetItem);
        ItemStack originalItem = gui.takeTargetItem();
        player.closeInventory();
        animation.play(
                player,
                originalItem,
                result,
                resultItem -> enhancementCommand.openGui(player, resultItem)
        );
    }

    @EventHandler
    public void onInventoryDrag(InventoryDragEvent event) {
        if (!(event.getInventory().getHolder() instanceof EnhancementGui gui)) {
            return;
        }

        boolean touchesProtectedSlot = event.getRawSlots().stream()
                .filter(slot -> slot < event.getView().getTopInventory().getSize())
                .anyMatch(slot -> slot != EnhancementGui.TARGET_SLOT);
        if (touchesProtectedSlot) {
            event.setCancelled(true);
            return;
        }

        if (event.getRawSlots().contains(EnhancementGui.TARGET_SLOT)) {
            scheduleInfoRefresh(gui);
        }
    }

    @EventHandler
    public void onInventoryClose(InventoryCloseEvent event) {
        if (!(event.getInventory().getHolder() instanceof EnhancementGui gui)
                || !(event.getPlayer() instanceof Player player)) {
            return;
        }

        gui.returnItemsTo(player);
    }

    @EventHandler
    public void onPlayerQuit(PlayerQuitEvent event) {
        animation.stop(event.getPlayer(), true);
    }

    @EventHandler
    public void onPlayerJoin(PlayerJoinEvent event) {
        animation.hideActiveDisplaysFrom(event.getPlayer());
    }

    private void scheduleInfoRefresh(EnhancementGui gui) {
        plugin.getServer().getScheduler().runTask(plugin, gui::refreshInfo);
    }
}

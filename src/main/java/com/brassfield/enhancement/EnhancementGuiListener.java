package com.brassfield.enhancement;

import com.brassfield.stone.StoneGrade;
import com.brassfield.stone.StoneWallet;
import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.Location;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.inventory.ClickType;
import org.bukkit.event.inventory.InventoryAction;
import org.bukkit.event.inventory.InventoryClickEvent;
import org.bukkit.event.inventory.InventoryCloseEvent;
import org.bukkit.event.inventory.InventoryDragEvent;
import org.bukkit.event.inventory.InventoryType;
import org.bukkit.event.player.PlayerJoinEvent;
import org.bukkit.event.player.PlayerQuitEvent;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.PlayerInventory;
import com.brassfield.common.ItemDelivery;
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

        if (rawSlot == EnhancementGui.TARGET_SLOT) {                    // 강화 칸 = 고른 장비 보기용 → 누르면 선택 해제
            if (gui.selectedSlot() >= 0) {
                gui.clearSelection();
            }
            return;
        }

        if (event.getClickedInventory() != null
                && event.getClickedInventory().getType() == InventoryType.PLAYER) {
            // 강화할 수 있는 장비를 그냥 누르면(손에 든 것 없이) 집어 들지 않고 바로 강화 칸에 올린다
            boolean plainClick = (event.getClick() == ClickType.LEFT || event.getClick() == ClickType.RIGHT)
                    && (event.getCursor() == null || event.getCursor().getType().isAir());
            if (plainClick && event.getWhoClicked() instanceof Player clicker && !animation.isPlaying(clicker)
                    && gui.selectFromInventory(clicker, event.getSlot())) {
                return;                                                // 클릭은 취소된 채로
            }
            // 쉬프트 이동 · 더블클릭 모으기는 막는다 (목록 카드 복사본이 가방으로 들어오지 않게)
            event.setCancelled(event.isShiftClick() || event.getAction() == InventoryAction.COLLECT_TO_CURSOR);
            scheduleInfoRefresh(gui);                                  // 가방이 바뀌면 장비 목록도 다시
            return;
        }

        if (event.getWhoClicked() instanceof Player clicker && !animation.isPlaying(clicker)
                && gui.handleListClick(clicker, rawSlot)) {
            return;
        }

        if (rawSlot != EnhancementGui.ENHANCE_BUTTON_SLOT
                || !(event.getWhoClicked() instanceof Player player)
                || animation.isPlaying(player)) {
            return;
        }

        int slot = gui.selectedSlot();
        if (slot < 0) {
            player.sendMessage(Component.text("아래 목록에서 강화할 장비를 골라주세요.", NamedTextColor.RED));
            return;
        }
        PlayerInventory playerInventory = player.getInventory();
        ItemStack targetItem = playerInventory.getItem(slot);
        if (targetItem == null || !targetItem.equals(gui.selectedItem())) {   // 고른 뒤 가방이 바뀜
            gui.refresh();
            player.sendMessage(Component.text("장비 위치가 바뀌었습니다. 다시 골라주세요.", NamedTextColor.RED));
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
        if (wallet.get(player.getUniqueId(), grade) < tier.stoneCost()) {
            player.sendMessage(Component.text(grade.displayName() + " 강화석이 부족합니다. (필요: " + tier.stoneCost()
                    + "개, 보유: " + wallet.get(player.getUniqueId(), grade) + "개)", NamedTextColor.RED));
            return;
        }
        // 결과 아이템을 먼저 만들고(실패하면 강화석을 쓰지 않음) 그다음 강화석을 뺀다
        EnhancementService.EnhancementResult result = enhancementService.enhance(targetItem);
        if (!wallet.withdraw(player.getUniqueId(), grade, tier.stoneCost())) {
            return;
        }

        // 장비는 제자리(착용 칸 포함)에서 바로 바뀐다. 겹쳐 있던 나머지는 가방으로
        ItemStack original = targetItem.clone();
        playerInventory.setItem(slot, result.item());
        if (original.getAmount() > 1) {
            ItemStack rest = original.clone();
            rest.setAmount(original.getAmount() - 1);
            ItemDelivery.giveOrDrop(player, rest);
        }
        original.setAmount(1);
        player.closeInventory();
        Location anvil = enhancementCommand.anvilOf(player);
        if (anvil != null) {                                           // 모루 위에 올려 망치질
            animation.playOnAnvil(player, anvil, original, result, resultItem -> enhancementCommand.openGui(player, slot));
        } else {                                                       // /강화 로 연 경우: 눈앞에 띄우는 연출
            animation.play(player, original, result, false, resultItem -> enhancementCommand.openGui(player, slot));
        }
    }

    @EventHandler
    public void onInventoryDrag(InventoryDragEvent event) {
        if (!(event.getInventory().getHolder() instanceof EnhancementGui gui)) {
            return;
        }

        boolean touchesGui = event.getRawSlots().stream()
                .anyMatch(slot -> slot < event.getView().getTopInventory().getSize());
        if (touchesGui) {
            event.setCancelled(true);
            return;
        }
        scheduleInfoRefresh(gui);
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
        enhancementCommand.forget(event.getPlayer());
    }

    @EventHandler
    public void onPlayerJoin(PlayerJoinEvent event) {
        animation.hideActiveDisplaysFrom(event.getPlayer());
    }

    private void scheduleInfoRefresh(EnhancementGui gui) {
        plugin.getServer().getScheduler().runTask(plugin, gui::refresh);
    }
}

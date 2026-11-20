package com.brassfield.accessory;

import com.brassfield.accessory.AccessoryKind.Part;
import io.papermc.paper.connection.PlayerGameConnection;
import io.papermc.paper.event.player.PlayerCustomClickEvent;
import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.Sound;
import org.bukkit.entity.Player;
import org.bukkit.entity.Projectile;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.entity.EntityDamageByEntityEvent;
import org.bukkit.event.entity.EntityDamageEvent;
import org.bukkit.event.inventory.InventoryClickEvent;
import org.bukkit.event.inventory.InventoryDragEvent;
import org.bukkit.event.inventory.PrepareItemCraftEvent;
import org.bukkit.event.player.PlayerJoinEvent;
import org.bukkit.event.player.PlayerQuitEvent;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.PlayerInventory;
import org.bukkit.plugin.java.JavaPlugin;

/**
 * 장신구: 장착 창 클릭 · 접속/퇴장 저장 · 능력치(공격력 %, 받는 피해 감소 %) · 조합 막기 · G 키 메뉴(데이터팩 다이얼로그) 단추.
 */
public final class AccessoryListener implements Listener {

    private final JavaPlugin plugin;
    private final AccessoryManager manager;
    private final AccessoryCommand command;

    public AccessoryListener(JavaPlugin plugin, AccessoryManager manager, AccessoryCommand command) {
        this.plugin = plugin;
        this.manager = manager;
        this.command = command;
    }

    @EventHandler
    public void onClick(InventoryClickEvent event) {
        if (!(event.getInventory().getHolder() instanceof AccessoryGui gui) || !(event.getWhoClicked() instanceof Player player)) {
            return;
        }
        event.setCancelled(true);
        if (event.getClickedInventory() == null || !event.getCursor().getType().isAir()) {
            return;
        }
        if (event.getClickedInventory() == event.getView().getTopInventory()) {
            int index = AccessoryGui.indexOf(event.getRawSlot());
            ItemStack[] slots = manager.slots(player);
            if (index < 0 || slots[index] == null) {
                return;
            }
            if (!player.getInventory().addItem(slots[index].clone()).isEmpty()) {
                player.sendMessage(Component.text("가방에 빈 칸이 없어 뺄 수 없습니다.", NamedTextColor.RED));
                return;
            }
            manager.setSlot(player, index, null);
            player.playSound(player, Sound.ITEM_ARMOR_EQUIP_CHAIN, 0.6f, 0.8f);
        } else {
            equipFromInventory(player, event.getSlot());
        }
        if (gui.backgroundOutdated()) {
            plugin.getServer().getScheduler().runTask(plugin, () -> command.open(player));   // 최고 등급이 바뀌면 배경째 다시 연다
        } else {
            gui.refresh();
        }
    }

    private void equipFromInventory(Player player, int invSlot) {
        PlayerInventory inventory = player.getInventory();
        ItemStack item = inventory.getItem(invSlot);
        Accessories.Info info = Accessories.read(item).orElse(null);
        if (info == null) {
            return;
        }
        ItemStack[] slots = manager.slots(player);
        int target = -1;
        for (int i = 0; i < slots.length; i++) {
            if (AccessoryManager.SLOT_PARTS[i] == info.part() && (slots[i] == null || target < 0)) {
                if (slots[i] == null) {
                    target = i;
                    break;
                }
                target = i;                                   // 빈칸이 없으면 같은 부위 첫 칸과 바꾼다
            }
        }
        if (target < 0) {
            return;
        }
        ItemStack previous = slots[target];
        ItemStack one = item.clone();
        one.setAmount(1);
        item.setAmount(item.getAmount() - 1);
        inventory.setItem(invSlot, item.getAmount() > 0 ? item : previous);
        if (item.getAmount() > 0 && previous != null) {
            inventory.addItem(previous).values().forEach(left -> player.getWorld().dropItem(player.getLocation(), left));
        }
        manager.setSlot(player, target, one);
        player.playSound(player, Sound.ITEM_ARMOR_EQUIP_GOLD, 0.8f, 1.2f);
    }

    @EventHandler
    public void onDrag(InventoryDragEvent event) {
        if (event.getInventory().getHolder() instanceof AccessoryGui) {
            event.setCancelled(true);
        }
    }

    @EventHandler
    public void onJoin(PlayerJoinEvent event) {
        manager.apply(event.getPlayer());
    }

    @EventHandler
    public void onQuit(PlayerQuitEvent event) {
        manager.unload(event.getPlayer());
    }

    /** 귀걸이: 플레이어가 주는 피해 + 공격력 % */
    @EventHandler(priority = EventPriority.HIGH, ignoreCancelled = true)
    public void onAttack(EntityDamageByEntityEvent event) {
        Player attacker = event.getDamager() instanceof Player p ? p
                : event.getDamager() instanceof Projectile projectile && projectile.getShooter() instanceof Player p ? p : null;
        if (attacker == null) {
            return;
        }
        double bonus = manager.total(attacker, Part.EARRING);
        if (bonus > 0) {
            event.setDamage(event.getDamage() * (1 + bonus / 100));
        }
    }

    /** 반지: 받는 피해 감소 % (방어구 피해 감소와 같은 예외: 공허 · 명령어 · 세계 경계) */
    @EventHandler(priority = EventPriority.HIGH, ignoreCancelled = true)
    public void onHurt(EntityDamageEvent event) {
        if (!(event.getEntity() instanceof Player player)) {
            return;
        }
        switch (event.getCause()) {
            case VOID, KILL, SUICIDE, WORLD_BORDER -> {
                return;
            }
            default -> {
            }
        }
        double reduction = Math.min(80, manager.total(player, Part.RING));
        if (reduction > 0) {
            event.setDamage(event.getDamage() * (1 - reduction / 100));
        }
    }

    /** 장신구(바탕 종이)는 조합 재료로 쓰지 못하게 */
    @EventHandler
    public void onCraft(PrepareItemCraftEvent event) {
        for (ItemStack item : event.getInventory().getMatrix()) {
            if (Accessories.isAccessory(item)) {
                event.getInventory().setResult(null);
                return;
            }
        }
    }

    /** G 키(빠른 동작) 메뉴의 단추 → 장신구 창 */
    @EventHandler
    public void onMenuClick(PlayerCustomClickEvent event) {
        if (!MenuDialogPack.ACCESSORY.equals(event.getIdentifier())
                || !(event.getCommonConnection() instanceof PlayerGameConnection connection)) {
            return;
        }
        Player player = connection.getPlayer();
        plugin.getServer().getScheduler().runTask(plugin, () -> command.open(player));
    }
}

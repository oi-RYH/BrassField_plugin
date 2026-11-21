package com.brassfield.accessory;

import io.papermc.paper.connection.PlayerGameConnection;
import io.papermc.paper.event.player.PlayerCustomClickEvent;
import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.attribute.AttributeInstance;
import org.bukkit.entity.LivingEntity;
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
import org.bukkit.event.player.PlayerExpChangeEvent;
import org.bukkit.event.player.PlayerJoinEvent;
import org.bukkit.event.player.PlayerQuitEvent;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.PlayerInventory;
import org.bukkit.plugin.java.JavaPlugin;

import java.util.concurrent.ThreadLocalRandom;

/**
 * 장신구: 장착 창 클릭 · 접속/퇴장 저장 · 보조옵션(공격 · 치명타 · 출혈 · 피해 감소 · 낙하 · 회복 · 경험치 · 요리) · 조합 막기 · G 키 메뉴 단추.
 */
public final class AccessoryListener implements Listener {

    private final JavaPlugin plugin;
    private final AccessoryManager manager;
    private final AccessoryCommand command;

    private static AccessoryListener instance;
    private final java.util.Map<java.util.UUID, Long> healReady = new java.util.HashMap<>();

    public AccessoryListener(JavaPlugin plugin, AccessoryManager manager, AccessoryCommand command) {
        instance = this;
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
        if (event.getClickedInventory() == event.getView().getTopInventory() && RerollTicket.is(event.getCursor())) {
            int index = AccessoryGui.indexOf(event.getRawSlot());               // 장착한 장신구에 보조옵션권
            ItemStack[] slots = manager.slots(player);
            if (index >= 0 && slots[index] != null) {
                manager.setSlot(player, index, RerollTicket.reroll(slots[index]));
                RerollTicket.consume(event);
                RerollTicket.feedback(player);
                gui.refresh();
            }
            return;
        }
        if (event.getClickedInventory() == null || !event.getCursor().getType().isAir()) {
            return;                                                    // 가방 쪽 보조옵션권 사용은 RerollTicket 이 처리
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

    /** 공격: 공격력 % → 치명타(확률 · 피해) → 출혈 (3초 동안 매초 이번 피해의 10%) */
    @EventHandler(priority = EventPriority.HIGH, ignoreCancelled = true)
    public void onAttack(EntityDamageByEntityEvent event) {
        Player attacker = event.getDamager() instanceof Player p ? p
                : event.getDamager() instanceof Projectile projectile && projectile.getShooter() instanceof Player p ? p : null;
        if (attacker == null || event.getCause() == EntityDamageEvent.DamageCause.CUSTOM) {
            return;                                                    // 출혈 피해(CUSTOM)에는 다시 붙지 않게
        }
        ThreadLocalRandom random = ThreadLocalRandom.current();
        double damage = event.getDamage() * (1 + manager.total(attacker, AccessoryOption.ATTACK) / 100);
        if (random.nextDouble(100) < manager.total(attacker, AccessoryOption.CRIT_CHANCE)) {
            damage *= 1.5 + manager.total(attacker, AccessoryOption.CRIT_DAMAGE) / 100;
            event.getEntity().getWorld().spawnParticle(Particle.CRIT, event.getEntity().getLocation().add(0, 1, 0), 12, 0.3, 0.4, 0.3, 0.2);
            attacker.playSound(attacker, Sound.ENTITY_PLAYER_ATTACK_CRIT, 0.8f, 1.2f);
        }
        event.setDamage(damage);
        if (event.getEntity() instanceof LivingEntity victim && random.nextDouble(100) < manager.total(attacker, AccessoryOption.BLEED)) {
            double tick = damage * 0.10;
            for (int second = 1; second <= 3; second++) {
                plugin.getServer().getScheduler().runTaskLater(plugin, () -> {
                    if (victim.isValid() && !victim.isDead()) {
                        victim.damage(tick);
                        victim.getWorld().spawnParticle(Particle.DAMAGE_INDICATOR, victim.getLocation().add(0, 1, 0), 3, 0.2, 0.3, 0.2, 0);
                    }
                }, second * 20L);
            }
        }
    }

    /** 맞을 때: 받는 피해 감소 %, 낙하 피해 감소 %, 확률로 체력 1 회복 (쿨타임 2초). 공허 · 명령어 · 세계 경계는 그대로 */
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
        double damage = event.getDamage() * (1 - manager.total(player, AccessoryOption.DAMAGE_REDUCTION) / 100);
        if (event.getCause() == EntityDamageEvent.DamageCause.FALL) {
            damage *= 1 - manager.total(player, AccessoryOption.FALL_REDUCTION) / 100;
        }
        event.setDamage(damage);
        long now = System.currentTimeMillis();
        if (now >= healReady.getOrDefault(player.getUniqueId(), 0L)
                && ThreadLocalRandom.current().nextDouble(100) < manager.total(player, AccessoryOption.HEAL_ON_HIT)) {
            healReady.put(player.getUniqueId(), now + 2000);
            plugin.getServer().getScheduler().runTask(plugin, () -> {
                AttributeInstance max = player.getAttribute(Attribute.MAX_HEALTH);
                if (!player.isDead()) {
                    player.setHealth(Math.min(max == null ? 20 : max.getValue(), player.getHealth() + 1));
                    player.getWorld().spawnParticle(Particle.HEART, player.getLocation().add(0, 2, 0), 1);
                }
            });
        }
    }

    /** 경험치 획득 % (남는 소수는 확률로) */
    @EventHandler(ignoreCancelled = true)
    public void onExp(PlayerExpChangeEvent event) {
        double bonus = manager.total(event.getPlayer(), AccessoryOption.EXP);
        if (bonus > 0 && event.getAmount() > 0) {
            double amount = event.getAmount() * (1 + bonus / 100);
            int whole = (int) amount;
            event.setAmount(whole + (ThreadLocalRandom.current().nextDouble() < amount - whole ? 1 : 0));
        }
    }

    /** 요리 버프 지속 시간 배율 (FoodBuffs 가 부른다) */
    public static double foodBuffMultiplier(Player player) {
        return instance == null ? 1 : 1 + instance.manager.total(player, AccessoryOption.FOOD_BUFF) / 100;
    }

    /** 장신구(바탕 종이)는 조합 재료로 쓰지 못하게 */
    @EventHandler
    public void onCraft(PrepareItemCraftEvent event) {
        for (ItemStack item : event.getInventory().getMatrix()) {
            if (Accessories.isAccessory(item) || RerollTicket.is(item)) {
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

package com.brassfield.accessory;

import com.brassfield.accessory.AccessoryKind.Set;
import org.bukkit.GameMode;
import org.bukkit.NamespacedKey;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.attribute.Attribute;
import org.bukkit.attribute.AttributeInstance;
import org.bukkit.attribute.AttributeModifier;
import org.bukkit.entity.Player;
import org.bukkit.entity.Projectile;
import org.bukkit.event.Event;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.entity.EntityDamageByEntityEvent;
import org.bukkit.event.entity.EntityDamageEvent;
import org.bukkit.event.entity.EntityDeathEvent;
import org.bukkit.event.entity.FoodLevelChangeEvent;
import org.bukkit.event.player.PlayerMoveEvent;
import org.bukkit.event.player.PlayerQuitEvent;
import org.bukkit.event.player.PlayerToggleFlightEvent;
import org.bukkit.inventory.EquipmentSlotGroup;
import org.bukkit.inventory.ItemStack;
import org.bukkit.plugin.EventExecutor;
import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.potion.PotionEffect;
import org.bukkit.potion.PotionEffectType;
import org.bukkit.scheduler.BukkitTask;
import org.bukkit.util.Vector;

import java.lang.reflect.Method;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ThreadLocalRandom;

/**
 * 장신구 세트 효과 (노션 "악세사리 시스템" Q12, 2026-11-20 확정). 5세트는 2세트 효과도 함께 받는다.
 * <ul>
 *   <li>전투 2: 공격 속도 +10% / 5: 몹 처치 시 5초 동안 공격력 +10%, 체력 1칸(2) 회복</li>
 *   <li>요리/농사 2: 음식을 먹을 때 숨은 포만감(포화도) +10 / 5: 1분마다 포화 효과 10초, 작물 수확 시 50% 확률로 1개 더</li>
 *   <li>생활/모험 2: 이동 속도 +10%, 2단 점프 / 5: 낙하 피해 면역, 이동 속도 +20% (합계 +30%)</li>
 * </ul>
 * 작물 수확은 CustomCrops 의 DropItemActionEvent 를 이름으로 찾아 받는다 (CustomCrops 가 없어도 플러그인은 켜진다).
 */
public final class SetEffects implements Listener {

    public static final int TWO = 2;
    public static final int FIVE = 5;
    private static final long RAGE_MILLIS = 5000;
    private static SetEffects instance;

    private final JavaPlugin plugin;
    private final NamespacedKey attackSpeedKey;
    private final NamespacedKey speedKey;
    private final Map<UUID, Map<Set, Integer>> counts = new HashMap<>();
    private final Map<UUID, Long> rageUntil = new HashMap<>();
    private final java.util.Set<UUID> jumpGranted = new HashSet<>();
    private BukkitTask saturationTask;

    public SetEffects(JavaPlugin plugin) {
        this.plugin = plugin;
        this.attackSpeedKey = new NamespacedKey(plugin, "accessory_set_attack_speed");
        this.speedKey = new NamespacedKey(plugin, "accessory_set_speed");
        instance = this;
    }

    public void start() {
        saturationTask = plugin.getServer().getScheduler().runTaskTimer(plugin, () -> {
            for (Player player : plugin.getServer().getOnlinePlayers()) {
                if (has(player, Set.FARM, FIVE)) {
                    player.addPotionEffect(new PotionEffect(PotionEffectType.SATURATION, 200, 0, true, false, true));
                }
            }
        }, 1200, 1200);
        hookCustomCrops();
    }

    public void stop() {
        if (saturationTask != null) {
            saturationTask.cancel();
        }
        for (Player player : plugin.getServer().getOnlinePlayers()) {
            revokeJump(player);
        }
    }

    /** 세트별 장착 개수 (AccessoryManager.apply 가 장착이 바뀔 때마다 부른다) */
    void update(Player player, ItemStack[] equipped) {
        Map<Set, Integer> map = new EnumMap<>(Set.class);
        for (ItemStack item : equipped) {
            Accessories.read(item).ifPresent(info -> map.merge(info.set(), 1, Integer::sum));
        }
        counts.put(player.getUniqueId(), map);
        modifier(player, Attribute.ATTACK_SPEED, attackSpeedKey, has(player, Set.COMBAT, TWO) ? 0.10 : 0);
        double speed = (has(player, Set.ADVENTURE, TWO) ? 0.10 : 0) + (has(player, Set.ADVENTURE, FIVE) ? 0.20 : 0);
        modifier(player, Attribute.MOVEMENT_SPEED, speedKey, speed);
        if (!has(player, Set.ADVENTURE, TWO)) {
            revokeJump(player);
        }
    }

    public int count(Player player, Set set) {
        return counts.getOrDefault(player.getUniqueId(), Map.of()).getOrDefault(set, 0);
    }

    public boolean has(Player player, Set set, int pieces) {
        return count(player, set) >= pieces;
    }

    private static void modifier(Player player, Attribute attribute, NamespacedKey key, double amount) {
        AttributeInstance instance = player.getAttribute(attribute);
        if (instance == null) {
            return;
        }
        instance.removeModifier(key);
        if (amount > 0) {
            instance.addModifier(new AttributeModifier(key, amount, AttributeModifier.Operation.ADD_SCALAR, EquipmentSlotGroup.ANY));
        }
    }

    // ── 전투 5: 처치 시 5초 공격력 +10%, 체력 1칸 회복 ──

    @EventHandler
    public void onKill(EntityDeathEvent event) {
        Player killer = event.getEntity().getKiller();
        if (killer == null || !has(killer, Set.COMBAT, FIVE)) {
            return;
        }
        rageUntil.put(killer.getUniqueId(), System.currentTimeMillis() + RAGE_MILLIS);
        AttributeInstance max = killer.getAttribute(Attribute.MAX_HEALTH);
        killer.setHealth(Math.min(max == null ? 20 : max.getValue(), killer.getHealth() + 2));
        killer.getWorld().spawnParticle(Particle.ANGRY_VILLAGER, killer.getLocation().add(0, 2.1, 0), 1);
        killer.playSound(killer, Sound.ENTITY_PLAYER_ATTACK_STRONG, 0.6f, 1.4f);
    }

    @EventHandler(priority = EventPriority.HIGH, ignoreCancelled = true)
    public void onAttack(EntityDamageByEntityEvent event) {
        Player attacker = event.getDamager() instanceof Player p ? p
                : event.getDamager() instanceof Projectile projectile && projectile.getShooter() instanceof Player p ? p : null;
        if (attacker != null && rageUntil.getOrDefault(attacker.getUniqueId(), 0L) > System.currentTimeMillis()) {
            event.setDamage(event.getDamage() * 1.10);
        }
    }

    // ── 요리/농사 2: 먹을 때 포화도 +10 ──

    @EventHandler(ignoreCancelled = true)
    public void onEat(FoodLevelChangeEvent event) {
        if (event.getItem() != null && event.getEntity() instanceof Player player) {
            plugin.getServer().getScheduler().runTask(plugin, () -> ate(player));
        }
    }

    /** 음식을 먹은 뒤 (손으로 먹기 · 놓인 요리 PlacedFood 둘 다) */
    public static void ate(Player player) {
        if (instance != null && instance.has(player, Set.FARM, TWO)) {
            player.setSaturation(Math.min(player.getFoodLevel(), player.getSaturation() + 10));
        }
    }

    // ── 요리/농사 5: 작물 수확 시 50% 확률로 1개 더 (CustomCrops) ──

    private void hookCustomCrops() {
        try {
            @SuppressWarnings("unchecked")
            Class<? extends Event> type = (Class<? extends Event>) Class.forName("net.momirealms.customcrops.api.event.DropItemActionEvent");
            Method context = type.getMethod("context");
            Method getItem = type.getMethod("item");
            Method setItem = type.getMethod("item", ItemStack.class);
            Method holder = Class.forName("net.momirealms.customcrops.api.context.Context").getMethod("holder");
            EventExecutor executor = (listener, event) -> {
                if (!type.isInstance(event)) {
                    return;
                }
                try {
                    Object who = holder.invoke(context.invoke(event));
                    if (who instanceof Player player && has(player, Set.FARM, FIVE) && ThreadLocalRandom.current().nextBoolean()) {
                        ItemStack item = (ItemStack) getItem.invoke(event);
                        if (item != null && !item.getType().isAir()) {
                            ItemStack more = item.clone();
                            more.setAmount(Math.min(more.getMaxStackSize(), item.getAmount() + 1));
                            setItem.invoke(event, more);
                        }
                    }
                } catch (ReflectiveOperationException exception) {
                    plugin.getLogger().fine("CustomCrops 수확 보너스 실패: " + exception);
                }
            };
            plugin.getServer().getPluginManager().registerEvent(type, this, EventPriority.HIGH, executor, plugin, true);
        } catch (ClassNotFoundException | NoSuchMethodException exception) {
            plugin.getLogger().warning("CustomCrops 수확 이벤트를 찾지 못해 농사 5세트 수확 보너스를 끕니다: " + exception.getMessage());
        }
    }

    // ── 생활/모험 2: 2단 점프 (땅에 닿으면 비행 허용 → 비행 시도를 막고 위로 튕김) ──

    private static boolean jumpMode(Player player) {
        return player.getGameMode() == GameMode.SURVIVAL || player.getGameMode() == GameMode.ADVENTURE;
    }

    @EventHandler(ignoreCancelled = true)
    public void onMove(PlayerMoveEvent event) {
        Player player = event.getPlayer();
        if (!has(player, Set.ADVENTURE, TWO) || !jumpMode(player)) {
            return;
        }
        if (((org.bukkit.entity.Entity) player).isOnGround() && !player.getAllowFlight()) {
            player.setAllowFlight(true);
            jumpGranted.add(player.getUniqueId());
        }
    }

    @EventHandler(ignoreCancelled = true)
    public void onDoubleJump(PlayerToggleFlightEvent event) {
        Player player = event.getPlayer();
        if (!event.isFlying() || !jumpGranted.contains(player.getUniqueId()) || !jumpMode(player)) {
            return;
        }
        event.setCancelled(true);
        player.setFlying(false);
        player.setAllowFlight(false);                       // 땅에 닿으면 onMove 가 다시 켠다
        Vector look = player.getLocation().getDirection().setY(0);
        Vector push = (look.lengthSquared() > 0 ? look.normalize().multiply(0.35) : new Vector()).setY(0.62);
        player.setVelocity(player.getVelocity().setY(0).add(push));
        player.setFallDistance(0);
        player.getWorld().spawnParticle(Particle.CLOUD, player.getLocation(), 8, 0.25, 0.05, 0.25, 0.02);
        player.playSound(player, Sound.ENTITY_BREEZE_JUMP, 0.5f, 1.3f);
    }

    private void revokeJump(Player player) {
        if (jumpGranted.remove(player.getUniqueId()) && jumpMode(player)) {
            player.setAllowFlight(false);
            player.setFlying(false);
        }
    }

    // ── 생활/모험 5: 낙하 피해 면역 ──

    @EventHandler(priority = EventPriority.HIGH, ignoreCancelled = true)
    public void onFall(EntityDamageEvent event) {
        if (event.getCause() == EntityDamageEvent.DamageCause.FALL && event.getEntity() instanceof Player player
                && has(player, Set.ADVENTURE, FIVE)) {
            event.setCancelled(true);
        }
    }

    @EventHandler
    public void onQuit(PlayerQuitEvent event) {
        revokeJump(event.getPlayer());
        counts.remove(event.getPlayer().getUniqueId());
        rageUntil.remove(event.getPlayer().getUniqueId());
    }

    /** 장착 창 설명: 세트마다 [2세트 효과, 5세트 효과] */
    static List<String> describe(Set set) {
        return switch (set) {
            case COMBAT -> List.of("공격 속도 +10%", "처치 시 5초간 공격력 +10%, 체력 1칸 회복");
            case FARM -> List.of("음식을 먹을 때 포만감 +10", "1분마다 포화 10초, 작물 수확 시 50% 확률로 1개 더");
            case ADVENTURE -> List.of("이동 속도 +10%, 2단 점프", "낙하 피해 면역, 이동 속도 +20%");
        };
    }
}

package com.brassfield.enhancement;

import com.brassfield.common.ItemDelivery;
import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.World;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.entity.Display;
import org.bukkit.entity.ItemDisplay;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;
import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.scheduler.BukkitRunnable;
import org.bukkit.scheduler.BukkitTask;
import org.bukkit.util.Transformation;
import org.bukkit.util.Vector;
import org.joml.AxisAngle4f;
import org.joml.Quaternionf;
import org.joml.Vector3f;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.function.Consumer;

public final class EnhancementAnimation {

    private static final int CHARGE_DURATION_TICKS = 20;
    private static final int RESULT_DURATION_TICKS = 20;
    private static final int UPDATE_INTERVAL_TICKS = 2;
    private static final double DISPLAY_DISTANCE = 1.3;

    // 모루 위 연출 (rustport:machine/enhance_anvil · enhance_hammer 모델 치수 기준)
    private static final String HAMMER_ID = "rustport:enhance_hammer";
    private static final double ANVIL_TOP = 16.8 / 16.0;       // 모루 윗면 높이 (2x1 모루, 모델 바닥 = 가구 엔티티 높이)
    private static final double HAMMER_REACH = 13 / 16.0;      // 자루 끝 → 망치 머리 가운데
    private static final double HAMMER_LIFT = 5.5 / 16.0;      // 망치 머리 타격면이 장비에 닿는 높이
    private static final float ITEM_SCALE = 0.7f;
    private static final float RAISED = -0.5f;                 // 치켜든 각도 (뒤로 젖힘)
    private static final float DOWN = (float) Math.PI / 2;     // 내려친 각도 (자루가 수평)
    private static final int STRIKES = 3;
    private static final int FIRST_STRIKE = 10;
    private static final int STRIKE_EVERY = 12;
    private static final int DOWN_TICKS = 3;
    private static final int UP_TICKS = 6;
    private static final int REVEAL = FIRST_STRIKE + STRIKES * STRIKE_EVERY + 4;
    private static final int RISE_TICKS = 12;
    private static final float RISE = 0.45f;
    private static final int FINISH = REVEAL + 30;

    private final JavaPlugin plugin;
    private final Map<UUID, ActiveAnimation> activeAnimations = new HashMap<>();

    public EnhancementAnimation(JavaPlugin plugin) {
        this.plugin = plugin;
    }

    public boolean isPlaying(Player player) {
        return activeAnimations.containsKey(player.getUniqueId());
    }

    public void play(
            Player player,
            ItemStack originalItem,
            EnhancementService.EnhancementResult result,
            Consumer<ItemStack> onComplete
    ) {
        play(player, originalItem, result, true, onComplete);
    }

    /**
     * giveOnStop = 연출이 중간에 끊기면(접속 종료 등) 결과 아이템을 플레이어에게 줄지.
     * 장비를 제자리에서 바로 바꾼 경우(통합 강화 창)는 false — 이미 가방에 있으므로 또 주면 복사된다.
     */
    public void play(
            Player player,
            ItemStack originalItem,
            EnhancementService.EnhancementResult result,
            boolean giveOnStop,
            Consumer<ItemStack> onComplete
    ) {
        ItemDisplay display = createDisplay(player, originalItem);
        player.playSound(player.getLocation(), Sound.BLOCK_ENCHANTMENT_TABLE_USE, 1.0f, 1.0f);

        BukkitRunnable animation = new BukkitRunnable() {
            private int elapsedTicks;
            private boolean resultRevealed;

            @Override
            public void run() {
                if (!player.isOnline()) {
                    stop(player, true);
                    return;
                }

                display.teleport(getDisplayLocation(player));

                if (elapsedTicks < CHARGE_DURATION_TICKS) {
                    animateCharging(player, display, elapsedTicks);
                    elapsedTicks += UPDATE_INTERVAL_TICKS;
                    return;
                }

                if (!resultRevealed) {
                    display.setItemStack(result.item());
                    revealResult(player, result);
                    resultRevealed = true;
                }

                int resultTicks = elapsedTicks - CHARGE_DURATION_TICKS;
                if (resultTicks < RESULT_DURATION_TICKS) {
                    animateResult(display, resultTicks);
                    elapsedTicks += UPDATE_INTERVAL_TICKS;
                    return;
                }

                finish(player, onComplete);
            }
        };

        BukkitTask task = animation.runTaskTimer(plugin, 0L, UPDATE_INTERVAL_TICKS);
        activeAnimations.put(player.getUniqueId(), new ActiveAnimation(List.of(display), task, result.item(), giveOnStop));
    }

    /**
     * 모루 위 연출: 장비를 모루 윗면에 눕혀 올리고, 망치가 세 번 내려친 뒤 결과 장비가 떠오르며 결과를 알린다.
     * 장비는 이미 플레이어 가방(제자리)에서 바뀌어 있으므로 연출이 끊겨도 아이템을 주지 않는다.
     *
     * @param anvil 모루 가구 엔티티 위치 (모델 바닥 = 엔티티 높이)
     */
    public void playOnAnvil(
            Player player,
            Location anvil,
            ItemStack originalItem,
            EnhancementService.EnhancementResult result,
            Consumer<ItemStack> onComplete
    ) {
        // 앞 = 모루에서 플레이어 쪽 (동서남북으로 맞춤). 장비는 모루 긴 쪽(앞과 직각)으로 눕고, 망치는 뒤에서 앞으로 내려친다
        Vector toPlayer = player.getLocation().toVector().subtract(anvil.toVector()).setY(0);
        Vector front = Math.abs(toPlayer.getX()) > Math.abs(toPlayer.getZ())
                ? new Vector(Math.signum(toPlayer.getX()), 0, 0)
                : new Vector(0, 0, toPlayer.getZ() < 0 ? -1 : 1);
        float yaw = (float) Math.atan2(front.getX(), front.getZ());
        Vector3f swingAxis = new Vector3f((float) front.getZ(), 0, (float) -front.getX());   // 위 × 앞: 자루가 위 → 앞으로 넘어감

        Location itemSpot = anvil.clone().add(0, ANVIL_TOP, 0);
        itemSpot.setYaw(0);
        itemSpot.setPitch(0);
        Quaternionf flat = new Quaternionf().rotateY(yaw + (float) Math.PI / 2).rotateX((float) Math.PI / 2);
        ItemDisplay item = spawnDisplay(itemSpot, originalItem, ItemDisplay.ItemDisplayTransform.FIXED);
        item.setTransformation(new Transformation(new Vector3f(), flat, new Vector3f(ITEM_SCALE), new Quaternionf()));

        Location pivot = itemSpot.clone().add(front.clone().multiply(-HAMMER_REACH)).add(0, HAMMER_LIFT, 0);
        ItemDisplay hammer = spawnDisplay(pivot, EnhanceTracks.createCustomOrFallback(HAMMER_ID, Material.IRON_AXE),
                ItemDisplay.ItemDisplayTransform.NONE);
        Quaternionf align = new Quaternionf().rotateY(yaw);
        swing(hammer, swingAxis, align, RAISED, 0);
        player.playSound(anvil, Sound.BLOCK_ANVIL_PLACE, 0.5f, 1.4f);

        BukkitRunnable animation = new BukkitRunnable() {
            private int tick;

            @Override
            public void run() {
                if (!player.isOnline()) {
                    stop(player, true);
                    return;
                }
                for (int strike = 0; strike < STRIKES; strike++) {
                    int start = FIRST_STRIKE + strike * STRIKE_EVERY;
                    if (tick == start) {
                        swing(hammer, swingAxis, align, DOWN, DOWN_TICKS);
                    } else if (tick == start + DOWN_TICKS) {
                        impact(itemSpot, strike);
                    } else if (tick == start + DOWN_TICKS + 2) {
                        swing(hammer, swingAxis, align, RAISED, UP_TICKS);
                    }
                }
                if (tick == REVEAL) {
                    item.setItemStack(result.item());
                    item.setInterpolationDelay(0);
                    item.setInterpolationDuration(RISE_TICKS);
                    item.setTransformation(new Transformation(new Vector3f(0, RISE, 0),
                            new Quaternionf().rotateY(yaw + (float) Math.PI * 1.5f).rotateX((float) Math.PI / 2),
                            new Vector3f(ITEM_SCALE * 1.2f), new Quaternionf()));
                    revealResult(player, result, itemSpot.clone().add(0, RISE, 0));
                }
                if (tick >= FINISH) {
                    finish(player, onComplete);
                    return;
                }
                tick++;
            }
        };
        BukkitTask task = animation.runTaskTimer(plugin, 0L, 1L);
        activeAnimations.put(player.getUniqueId(), new ActiveAnimation(List.of(item, hammer), task, result.item(), false));
    }

    private void swing(ItemDisplay hammer, Vector3f axis, Quaternionf align, float angle, int ticks) {
        hammer.setInterpolationDelay(0);
        hammer.setInterpolationDuration(ticks);
        Quaternionf rotation = new Quaternionf().rotateAxis(angle, axis).mul(align);
        hammer.setTransformation(new Transformation(new Vector3f(), rotation, new Vector3f(1f), new Quaternionf()));
    }

    /** 망치가 닿는 순간: 쇠 부딪는 소리 (내려칠수록 높게) · 불꽃 */
    private void impact(Location spot, int strike) {
        World world = spot.getWorld();
        world.playSound(spot, Sound.BLOCK_ANVIL_USE, 0.7f, 0.9f + strike * 0.15f);
        world.spawnParticle(Particle.CRIT, spot.clone().add(0, 0.1, 0), 14, 0.15, 0.05, 0.15, 0.25);
        world.spawnParticle(Particle.LAVA, spot.clone().add(0, 0.1, 0), 2, 0.1, 0.0, 0.1, 0.0);
        world.spawnParticle(Particle.SMALL_FLAME, spot.clone().add(0, 0.1, 0), 4, 0.12, 0.05, 0.12, 0.02);
    }

    private ItemDisplay spawnDisplay(Location at, ItemStack stack, ItemDisplay.ItemDisplayTransform transform) {
        return at.getWorld().spawn(at, ItemDisplay.class, entity -> {
            entity.setItemStack(stack);
            entity.setItemDisplayTransform(transform);
            entity.setInvulnerable(true);
            entity.setPersistent(false);
            entity.setTeleportDuration(0);
        });
    }

    public void hideActiveDisplaysFrom(Player viewer) {
        activeAnimations.forEach((ownerId, animation) -> {
            if (!ownerId.equals(viewer.getUniqueId()) && animation.displays().size() == 1) {   // 앞에 띄우는 연출만 본인 전용
                animation.displays().forEach(display -> viewer.hideEntity(plugin, display));
            }
        });
    }

    public void stop(Player player, boolean returnItem) {
        ActiveAnimation animation = activeAnimations.remove(player.getUniqueId());
        if (animation == null) {
            return;
        }

        animation.task().cancel();
        animation.displays().forEach(Display::remove);
        if (returnItem && animation.giveOnStop()) {
            ItemDelivery.giveOrDrop(player, animation.resultItem());
        }
    }

    public void shutdown() {
        for (Player player : plugin.getServer().getOnlinePlayers()) {
            stop(player, true);
        }
        activeAnimations.values().forEach(animation -> {
            animation.task().cancel();
            animation.displays().forEach(Display::remove);
        });
        activeAnimations.clear();
    }

    private ItemDisplay createDisplay(Player owner, ItemStack item) {
        ItemDisplay display = owner.getWorld().spawn(
                getDisplayLocation(owner),
                ItemDisplay.class,
                entity -> {
                    entity.setItemStack(item);
                    entity.setItemDisplayTransform(ItemDisplay.ItemDisplayTransform.GUI);
                    entity.setBillboard(Display.Billboard.CENTER);
                    entity.setInvulnerable(true);
                    entity.setPersistent(false);
                }
        );

        for (Player viewer : plugin.getServer().getOnlinePlayers()) {
            if (!viewer.equals(owner)) {
                viewer.hideEntity(plugin, display);
            }
        }
        return display;
    }

    private void animateCharging(Player player, ItemDisplay display, int elapsedTicks) {
        float progress = elapsedTicks / (float) CHARGE_DURATION_TICKS;
        float shakeX = (float) Math.sin(elapsedTicks * 2.4f) * (0.04f + progress * 0.08f);
        float shakeY = (float) Math.cos(elapsedTicks * 1.7f) * (0.03f + progress * 0.05f);
        float pulseScale = 1.15f + (float) Math.sin(elapsedTicks * 1.2f) * 0.08f;
        updateTransformation(display, pulseScale, shakeX, shakeY);
        player.getWorld().spawnParticle(
                Particle.ENCHANT,
                player.getLocation().add(0, 1.0, 0),
                8,
                0.6, 0.8, 0.6,
                0.1
        );
    }

    private void revealResult(Player player, EnhancementService.EnhancementResult result) {
        revealResult(player, result, player.getLocation().add(0, 1.0, 0));
    }

    private void revealResult(Player player, EnhancementService.EnhancementResult result, Location at) {
        switch (result.outcome()) {
            case SUCCESS -> {
                player.getWorld().spawnParticle(
                        Particle.TOTEM_OF_UNDYING,
                        at,
                        80,
                        0.7, 1.0, 0.7,
                        0.25
                );
                player.playSound(at, Sound.ITEM_TOTEM_USE, 1.0f, 1.1f);
                player.sendMessage(Component.text("강화 성공! 현재 단계: +" + result.level(), NamedTextColor.GREEN));
            }
            case DOWNGRADE -> {
                playFailureParticles(at);
                player.playSound(at, Sound.BLOCK_ANVIL_BREAK, 1.0f, 0.8f);
                player.sendMessage(Component.text("강화 실패! 강화 단계가 +" + result.level() + "(으)로 하락했습니다.", NamedTextColor.RED));
            }
            case MAINTAIN -> {
                playFailureParticles(at);
                player.playSound(at, Sound.ENTITY_VILLAGER_NO, 0.8f, 1.0f);
                player.sendMessage(Component.text("강화 실패! +" + result.level() + " 단계가 유지됩니다.", NamedTextColor.YELLOW));
            }
        }
    }

    private void playFailureParticles(Location at) {
        at.getWorld().spawnParticle(
                Particle.LARGE_SMOKE,
                at,
                45,
                0.6, 0.8, 0.6,
                0.08
        );
    }

    private void animateResult(ItemDisplay display, int elapsedTicks) {
        float progress = elapsedTicks / (float) RESULT_DURATION_TICKS;
        updateTransformation(display, 1.5f - progress * 0.5f, 0.0f, progress * 0.35f);
    }

    private void finish(Player player, Consumer<ItemStack> onComplete) {
        ActiveAnimation animation = activeAnimations.remove(player.getUniqueId());
        if (animation == null) {
            return;
        }

        animation.displays().forEach(Display::remove);
        animation.task().cancel();
        onComplete.accept(animation.resultItem());
    }

    private Location getDisplayLocation(Player player) {
        Location eyeLocation = player.getEyeLocation();
        return eyeLocation.add(eyeLocation.getDirection().multiply(DISPLAY_DISTANCE));
    }

    private void updateTransformation(ItemDisplay display, float scale, float horizontalOffset, float verticalOffset) {
        display.setTransformation(new Transformation(
                new Vector3f(horizontalOffset, verticalOffset, 0.0f),
                new AxisAngle4f(),
                new Vector3f(scale, scale, scale),
                new AxisAngle4f()
        ));
    }

    private record ActiveAnimation(List<? extends Display> displays, BukkitTask task, ItemStack resultItem, boolean giveOnStop) {
    }
}

package com.rustport.enhancement;

import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.Location;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.entity.Display;
import org.bukkit.entity.ItemDisplay;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;
import org.bukkit.scheduler.BukkitRunnable;
import org.bukkit.scheduler.BukkitTask;
import org.bukkit.util.Transformation;
import org.joml.AxisAngle4f;
import org.joml.Vector3f;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.function.Consumer;

public final class EnhancementAnimation {

    private static final int CHARGE_DURATION_TICKS = 20;
    private static final int RESULT_DURATION_TICKS = 20;
    private static final int UPDATE_INTERVAL_TICKS = 2;
    private static final double DISPLAY_DISTANCE = 1.3;

    private final EnhancementPlugin plugin;
    private final Map<UUID, ActiveAnimation> activeAnimations = new HashMap<>();

    public EnhancementAnimation(EnhancementPlugin plugin) {
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
        activeAnimations.put(player.getUniqueId(), new ActiveAnimation(display, task, result.item()));
    }

    public void hideActiveDisplaysFrom(Player viewer) {
        activeAnimations.forEach((ownerId, animation) -> {
            if (!ownerId.equals(viewer.getUniqueId())) {
                viewer.hideEntity(plugin, animation.display());
            }
        });
    }

    public void stop(Player player, boolean returnItem) {
        ActiveAnimation animation = activeAnimations.remove(player.getUniqueId());
        if (animation == null) {
            return;
        }

        animation.task().cancel();
        animation.display().remove();
        if (returnItem) {
            ItemDelivery.giveOrDrop(player, animation.resultItem());
        }
    }

    public void shutdown() {
        for (Player player : plugin.getServer().getOnlinePlayers()) {
            stop(player, true);
        }
        activeAnimations.values().forEach(animation -> {
            animation.task().cancel();
            animation.display().remove();
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
        switch (result.outcome()) {
            case SUCCESS -> {
                player.getWorld().spawnParticle(
                        Particle.TOTEM_OF_UNDYING,
                        player.getLocation().add(0, 1.0, 0),
                        80,
                        0.7, 1.0, 0.7,
                        0.25
                );
                player.playSound(player.getLocation(), Sound.ITEM_TOTEM_USE, 1.0f, 1.1f);
                player.sendMessage(Component.text("강화 성공! 현재 단계: +" + result.level(), NamedTextColor.GREEN));
            }
            case DOWNGRADE -> {
                playFailureParticles(player);
                player.playSound(player.getLocation(), Sound.BLOCK_ANVIL_BREAK, 1.0f, 0.8f);
                player.sendMessage(Component.text("강화 실패! 강화 단계가 +" + result.level() + "(으)로 하락했습니다.", NamedTextColor.RED));
            }
            case MAINTAIN -> {
                playFailureParticles(player);
                player.playSound(player.getLocation(), Sound.ENTITY_VILLAGER_NO, 0.8f, 1.0f);
                player.sendMessage(Component.text("강화 실패! +" + result.level() + " 단계가 유지됩니다.", NamedTextColor.YELLOW));
            }
        }
    }

    private void playFailureParticles(Player player) {
        player.getWorld().spawnParticle(
                Particle.LARGE_SMOKE,
                player.getLocation().add(0, 1.0, 0),
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

        animation.display().remove();
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

    private record ActiveAnimation(ItemDisplay display, BukkitTask task, ItemStack resultItem) {
    }
}

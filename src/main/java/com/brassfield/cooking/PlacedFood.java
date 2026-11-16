package com.brassfield.cooking;

import com.brassfield.common.ItemsAdderItemProvider;
import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.Chunk;
import org.bukkit.GameMode;
import org.bukkit.Location;
import org.bukkit.NamespacedKey;
import org.bukkit.Sound;
import org.bukkit.block.Block;
import org.bukkit.block.BlockFace;
import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.configuration.file.FileConfiguration;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Interaction;
import org.bukkit.entity.ItemDisplay;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.block.Action;
import org.bukkit.event.block.BlockBreakEvent;
import org.bukkit.event.block.BlockExplodeEvent;
import org.bukkit.event.block.BlockPistonExtendEvent;
import org.bukkit.event.block.BlockPistonRetractEvent;
import org.bukkit.event.entity.EntityExplodeEvent;
import org.bukkit.event.player.PlayerInteractEntityEvent;
import org.bukkit.event.player.PlayerInteractEvent;
import org.bukkit.inventory.EquipmentSlot;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;
import org.bukkit.persistence.PersistentDataContainer;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.util.Transformation;
import org.joml.AxisAngle4f;
import org.joml.Vector3f;

import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import java.util.logging.Logger;

/**
 * 요리를 블록 위에 올려놓는다 (3D 모델이 있는 요리만).
 * <ul>
 *   <li>요리를 들고 웅크린 채 블록 윗면을 우클릭하면 놓는다. 그냥 우클릭은 원래대로 먹기.</li>
 *   <li>놓인 요리는 ItemDisplay(3D 모델 표시) + Interaction(클릭 판정) 두 엔티티. Interaction 의 PDC 에 주인과 표시 UUID 를 적는다.</li>
 *   <li>놓인 요리를 우클릭하면 먹고, 웅크린 채 우클릭하면 아이템으로 되돌린다. 기본은 놓은 사람만 (관리자는 누구 것이든).</li>
 *   <li>요리 밑 블록을 부수거나, 피스톤으로 밀거나, 폭발로 터지면 요리는 아이템으로 떨어진다. 한 청크에 놓을 수 있는 개수를 제한한다.</li>
 * </ul>
 * ItemsAdder 는 바닥·액자·GUI 에서 2D 아이콘을 보이므로, 표시는 3D 모델이 그대로 보이는 NONE 변환을 쓴다.
 */
public final class PlacedFood implements Listener {

    private static final float FALLBACK_SATURATION = 2.4f;
    private static final int FALLBACK_NUTRITION = 4;

    private final JavaPlugin plugin;
    private final ItemsAdderItemProvider itemProvider;
    private final NamespacedKey ownerKey;
    private final NamespacedKey displayKey;
    private final Set<String> placeable;
    private final int chunkLimit;
    private final boolean othersCanUse;
    private final float scale;

    private PlacedFood(JavaPlugin plugin, ItemsAdderItemProvider itemProvider, Set<String> placeable,
                       int chunkLimit, boolean othersCanUse, float scale) {
        this.plugin = plugin;
        this.itemProvider = itemProvider;
        this.ownerKey = new NamespacedKey(plugin, "placed_food_owner");
        this.displayKey = new NamespacedKey(plugin, "placed_food_display");
        this.placeable = placeable;
        this.chunkLimit = chunkLimit;
        this.othersCanUse = othersCanUse;
        this.scale = scale;
    }

    /**
     * config.yml 의 placed-food 항목을 읽는다. 꺼져 있거나 항목이 없으면 null.
     */
    public static PlacedFood load(JavaPlugin plugin, FileConfiguration config, ItemsAdderItemProvider itemProvider, Logger logger) {
        ConfigurationSection section = config.getConfigurationSection("placed-food");
        if (section == null || !section.getBoolean("enabled", true)) {
            return null;
        }
        List<String> items = section.getStringList("items");
        if (items.isEmpty()) {
            logger.warning("placed-food.items 가 비어 있어 요리 놓기를 끕니다.");
            return null;
        }
        return new PlacedFood(plugin, itemProvider, new HashSet<>(items),
                Math.max(1, section.getInt("per-chunk-limit", 16)),
                section.getBoolean("others-can-use", false),
                (float) section.getDouble("scale", 0.8));
    }

    // ── 놓기 ──
    @EventHandler(priority = EventPriority.HIGH)
    public void onPlace(PlayerInteractEvent event) {
        if (event.getAction() != Action.RIGHT_CLICK_BLOCK || event.getHand() != EquipmentSlot.HAND
                || event.getBlockFace() != BlockFace.UP || event.getClickedBlock() == null) {
            return;
        }
        Player player = event.getPlayer();
        ItemStack hand = player.getInventory().getItemInMainHand();
        if (!player.isSneaking() || player.getGameMode() == GameMode.SPECTATOR || player.getGameMode() == GameMode.ADVENTURE) {
            return;
        }
        String id = itemProvider.idOf(hand);
        if (id == null || !placeable.contains(id)) {
            return;
        }
        event.setUseInteractedBlock(org.bukkit.event.Event.Result.DENY);
        event.setUseItemInHand(org.bukkit.event.Event.Result.DENY);
        event.setCancelled(true);

        Block base = event.getClickedBlock();
        Block above = base.getRelative(BlockFace.UP);
        if (!above.isPassable() || above.isLiquid() || foodOn(base) != null) {
            player.sendMessage(Component.text("여기에는 요리를 놓을 수 없습니다.", NamedTextColor.RED));
            return;
        }
        if (countIn(base.getChunk()) >= chunkLimit) {
            player.sendMessage(Component.text("이 구역에는 요리를 더 놓을 수 없습니다. (최대 " + chunkLimit + "개)", NamedTextColor.RED));
            return;
        }
        ItemStack one = hand.clone();
        one.setAmount(1);
        Location top = base.getLocation().add(0.5, 1.0, 0.5);
        float yaw = Math.round(player.getLocation().getYaw() / 90f) * 90f;      // 앞면이 놓는 사람을 보게 (90도 단위)

        ItemDisplay display = base.getWorld().spawn(top.clone().add(0, scale / 2.0, 0), ItemDisplay.class, d -> {
            d.setItemStack(one);
            d.setItemDisplayTransform(ItemDisplay.ItemDisplayTransform.NONE);
            d.setRotation(yaw, 0f);
            d.setTransformation(new Transformation(new Vector3f(), new AxisAngle4f(), new Vector3f(scale, scale, scale), new AxisAngle4f()));
            d.setPersistent(true);
            d.getPersistentDataContainer().set(displayKey, PersistentDataType.STRING, "food");
        });
        base.getWorld().spawn(top, Interaction.class, i -> {
            i.setInteractionWidth(0.85f * scale);
            i.setInteractionHeight(0.6f * scale);
            i.setResponsive(true);
            i.setPersistent(true);
            PersistentDataContainer pdc = i.getPersistentDataContainer();
            pdc.set(ownerKey, PersistentDataType.STRING, player.getUniqueId().toString());
            pdc.set(displayKey, PersistentDataType.STRING, display.getUniqueId().toString());
        });
        if (player.getGameMode() != GameMode.CREATIVE) {
            hand.setAmount(hand.getAmount() - 1);
        }
        player.swingMainHand();
        base.getWorld().playSound(top, Sound.BLOCK_WOOD_PLACE, 0.8f, 1.2f);
    }

    // ── 먹기·집기 ──
    @EventHandler(priority = EventPriority.HIGH)
    public void onUse(PlayerInteractEntityEvent event) {
        if (!(event.getRightClicked() instanceof Interaction hitbox) || event.getHand() != EquipmentSlot.HAND) {
            return;
        }
        PersistentDataContainer pdc = hitbox.getPersistentDataContainer();
        String owner = pdc.get(ownerKey, PersistentDataType.STRING);
        if (owner == null) {
            return;
        }
        event.setCancelled(true);
        Player player = event.getPlayer();
        ItemDisplay display = displayOf(hitbox);
        if (display == null) {                                       // 표시가 사라진 판정만 남은 경우 정리
            hitbox.remove();
            return;
        }
        if (!othersCanUse && !player.getUniqueId().toString().equals(owner) && !player.hasPermission("brassfield.food.admin")) {
            player.sendMessage(Component.text("다른 사람이 놓은 요리입니다.", NamedTextColor.RED));
            return;
        }
        ItemStack food = display.getItemStack();
        if (player.isSneaking()) {                                   // 집기
            player.getInventory().addItem(food).values()
                    .forEach(left -> player.getWorld().dropItemNaturally(player.getLocation(), left));
            player.getWorld().playSound(hitbox.getLocation(), Sound.ENTITY_ITEM_PICKUP, 0.6f, 1.0f);
            remove(hitbox, display);
            return;
        }
        if (player.getFoodLevel() >= 20) {                           // 먹기
            player.sendMessage(Component.text("배가 불러서 더 먹을 수 없습니다.", NamedTextColor.YELLOW));
            return;
        }
        int nutrition = FALLBACK_NUTRITION;
        float saturation = FALLBACK_SATURATION;
        ItemMeta meta = food.getItemMeta();
        if (meta != null && meta.hasFood()) {
            nutrition = meta.getFood().getNutrition();
            saturation = meta.getFood().getSaturation();
        }
        int level = Math.min(20, player.getFoodLevel() + nutrition);
        player.setFoodLevel(level);
        player.setSaturation(Math.min(level, player.getSaturation() + saturation));
        player.getWorld().playSound(hitbox.getLocation(), Sound.ENTITY_GENERIC_EAT, 1.0f, 1.0f);
        player.getWorld().playSound(hitbox.getLocation(), Sound.ENTITY_PLAYER_BURP, 0.5f, 1.0f);
        remove(hitbox, display);
    }

    // ── 밑 블록을 부수면 아이템으로 떨어진다 ──
    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true)
    public void onBaseBreak(BlockBreakEvent event) {
        dropFoodOn(event.getBlock());
    }

    // ── 피스톤: 밑 블록이 밀려가거나, 밀려온 블록이 요리 자리로 들어오면 아이템으로 떨어진다 ──
    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true)
    public void onPistonExtend(BlockPistonExtendEvent event) {
        pistonMoved(event.getBlock(), event.getBlocks(), event.getDirection(), true);
    }

    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true)
    public void onPistonRetract(BlockPistonRetractEvent event) {
        pistonMoved(event.getBlock(), event.getBlocks(), event.getDirection(), false);
    }

    private void pistonMoved(Block piston, List<Block> moved, BlockFace direction, boolean extend) {
        if (extend) {
            dropFoodOn(piston.getRelative(direction).getRelative(BlockFace.DOWN));   // 피스톤 머리가 들어오는 칸
        }
        for (Block block : moved) {
            dropFoodOn(block);                                                     // 밀려가는 블록 위의 요리
            dropFoodOn(block.getRelative(direction).getRelative(BlockFace.DOWN));   // 블록이 들어오는 칸에 놓인 요리
        }
    }

    // ── 폭발: 터지는 블록 위의 요리는 아이템으로 떨어진다 ──
    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true)
    public void onEntityExplode(EntityExplodeEvent event) {
        event.blockList().forEach(this::dropFoodOn);
    }

    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true)
    public void onBlockExplode(BlockExplodeEvent event) {
        event.blockList().forEach(this::dropFoodOn);
    }

    /**
     * base 블록 위에 놓인 요리가 있으면 아이템으로 떨어뜨리고 지운다.
     */
    private void dropFoodOn(Block base) {
        Interaction hitbox = foodOn(base);
        if (hitbox == null) {
            return;
        }
        ItemDisplay display = displayOf(hitbox);
        if (display != null) {
            hitbox.getWorld().dropItemNaturally(hitbox.getLocation(), display.getItemStack());
        }
        remove(hitbox, display);
    }

    private Interaction foodOn(Block base) {
        Location top = base.getLocation().add(0.5, 1.0, 0.5);
        for (Entity entity : base.getWorld().getNearbyEntities(top, 0.3, 0.3, 0.3)) {
            if (entity instanceof Interaction hitbox && hitbox.getPersistentDataContainer().has(ownerKey, PersistentDataType.STRING)) {
                return hitbox;
            }
        }
        return null;
    }

    private ItemDisplay displayOf(Interaction hitbox) {
        String uuid = hitbox.getPersistentDataContainer().get(displayKey, PersistentDataType.STRING);
        if (uuid == null) {
            return null;
        }
        Entity entity = plugin.getServer().getEntity(UUID.fromString(uuid));
        return entity instanceof ItemDisplay display ? display : null;
    }

    private int countIn(Chunk chunk) {
        int count = 0;
        for (Entity entity : chunk.getEntities()) {
            if (entity instanceof Interaction && entity.getPersistentDataContainer().has(ownerKey, PersistentDataType.STRING)) {
                count++;
            }
        }
        return count;
    }

    private static void remove(Interaction hitbox, ItemDisplay display) {
        if (display != null) {
            display.remove();
        }
        hitbox.remove();
    }
}

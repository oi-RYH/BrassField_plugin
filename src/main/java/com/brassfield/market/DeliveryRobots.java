package com.brassfield.market;

import com.brassfield.common.ItemsAdderItemProvider;
import org.bukkit.Location;
import org.bukkit.NamespacedKey;
import org.bukkit.World;
import org.bukkit.entity.Entity;
import org.bukkit.entity.ItemDisplay;
import org.bukkit.entity.Player;
import org.bukkit.event.Event;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.world.EntitiesLoadEvent;
import org.bukkit.event.world.EntitiesUnloadEvent;
import org.bukkit.inventory.ItemStack;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.scheduler.BukkitTask;

import java.lang.reflect.Method;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.function.Consumer;

/**
 * 납품 로봇 DL-7 의 머리. 몸은 ItemsAdder 가구(rustport:dl7)이고, 머리는 몸 위에 따로 띄운 ItemDisplay 다.
 * <ul>
 *   <li>로봇을 설치하면 바로, 이미 설치된 로봇은 청크가 불러와질 때 머리를 붙인다. 머리 PDC 에 몸 UUID 를 적는다.</li>
 *   <li>가까운 플레이어 쪽으로 고개를 천천히 돌린다 (몸 정면에서 좌우 70도까지). 위아래로 살짝 숨 쉬듯 움직인다.</li>
 *   <li>표정: 가까이 사람이 있으면 기본, 없으면 졸림. 창을 열면 반짝, 판매하면 행복(큰 판매는 하트)을 잠깐 띄운다.</li>
 *   <li>로봇을 부수면 머리도 지운다.</li>
 * </ul>
 * 표정은 ItemsAdder 아이템 rustport:dl7_head_&lt;표정&gt; (모델 machine/dl7/head_&lt;표정&gt;).
 * ItemsAdder 가구 API 는 리플렉션으로 쓴다.
 */
public final class DeliveryRobots implements Listener {

    private static final String CUSTOM_FURNITURE = "dev.lone.itemsadder.api.CustomFurniture";
    private static final String PLACE_EVENT = "dev.lone.itemsadder.api.Events.FurniturePlaceSuccessEvent";
    private static final String BREAK_EVENT = "dev.lone.itemsadder.api.Events.FurnitureBreakEvent";
    private static final String HEAD_PREFIX = "rustport:dl7_head_";

    private static final int UPDATE_TICKS = 4;
    private static final double HEAD_HEIGHT = 14.5 / 16 + 0.5;    // 바닥 → 머리 모델 가운데 (머리 아래끝 14.5칸 + 모델 반 높이)
    private static final double HEAD_FORWARD = 2.5 / 16;         // 머리가 몸 가운데보다 정면 쪽으로 나온 거리
    private static final double LOOK_RANGE = 8;
    private static final float MAX_TURN = 70f;
    private static final float TURN_STEP = 12f;
    private static final double BOB = 0.02;
    private static final int BOB_TICKS = 80;
    private static final int CLEANUP_EVERY = 25;

    private final JavaPlugin plugin;
    private final ItemsAdderItemProvider itemProvider;
    private final String furnitureId;
    private final NamespacedKey ownerKey;
    private final Set<ItemDisplay> heads = new HashSet<>();
    private final Map<UUID, String> shownFace = new HashMap<>();
    private final Map<UUID, Reaction> reactions = new HashMap<>();
    private final Map<String, ItemStack> faceItems = new HashMap<>();
    private Method byAlreadySpawned;
    private Method getNamespacedId;
    private BukkitTask task;
    private long tick;

    private record Reaction(String face, long until) {
    }

    public DeliveryRobots(JavaPlugin plugin, ItemsAdderItemProvider itemProvider, String furnitureId) {
        this.plugin = plugin;
        this.itemProvider = itemProvider;
        this.furnitureId = furnitureId;
        this.ownerKey = new NamespacedKey(plugin, "robot_head_owner");
    }

    public void start() {
        if (!plugin.getServer().getPluginManager().isPluginEnabled("ItemsAdder")) {
            return;
        }
        try {
            Class<?> furniture = Class.forName(CUSTOM_FURNITURE);
            byAlreadySpawned = furniture.getMethod("byAlreadySpawned", Entity.class);
            getNamespacedId = furniture.getMethod("getNamespacedID");
            listen(PLACE_EVENT, true, this::ensureHead);
            listen(BREAK_EVENT, false, this::removeHeads);
        } catch (ReflectiveOperationException exception) {
            plugin.getLogger().warning("ItemsAdder 가구 API를 불러오지 못해 DL-7 머리를 쓸 수 없습니다: " + exception);
            return;
        }
        plugin.getServer().getPluginManager().registerEvents(this, plugin);
        plugin.getServer().getScheduler().runTaskLater(plugin, this::scanLoadedWorlds, 40L);
        plugin.getServer().getScheduler().runTaskLater(plugin, this::scanLoadedWorlds, 200L);
        task = plugin.getServer().getScheduler().runTaskTimer(plugin, this::animate, UPDATE_TICKS, UPDATE_TICKS);
    }

    public void stop() {
        if (task != null) {
            task.cancel();
        }
        heads.clear();
    }

    /**
     * 로봇 머리에 표정을 잠깐(ticks) 띄운다.
     */
    void react(Entity robot, String face, int ticks) {
        ItemDisplay head = headOf(robot);
        if (head != null) {
            reactions.put(head.getUniqueId(), new Reaction(face, tick + ticks));
        }
    }

    @EventHandler
    public void onEntitiesLoad(EntitiesLoadEvent event) {
        for (Entity entity : event.getEntities()) {
            if (isHead(entity)) {
                heads.add((ItemDisplay) entity);
            }
        }
        event.getEntities().forEach(this::ensureHead);
    }

    @EventHandler
    public void onEntitiesUnload(EntitiesUnloadEvent event) {
        event.getEntities().forEach(heads::remove);
    }

    private void scanLoadedWorlds() {
        for (World world : plugin.getServer().getWorlds()) {
            for (Entity entity : world.getEntities()) {
                if (isHead(entity)) {
                    heads.add((ItemDisplay) entity);
                }
            }
            world.getEntities().forEach(this::ensureHead);
        }
    }

    private void ensureHead(Entity robot) {
        if (isHead(robot) || !furnitureId.equals(furnitureIdOf(robot)) || headOf(robot) != null) {
            return;
        }
        ItemStack face = faceItem("normal");
        if (face == null) {
            return;   // ItemsAdder 가 아직 아이템을 불러오지 못함 → 다음 훑기 때 다시 시도
        }
        Location location = headLocation(robot, 0);
        ItemDisplay head = robot.getWorld().spawn(location, ItemDisplay.class, display -> {
            display.setItemStack(face);
            display.setItemDisplayTransform(ItemDisplay.ItemDisplayTransform.NONE);
            display.setPersistent(true);
            display.setTeleportDuration(UPDATE_TICKS);
            display.getPersistentDataContainer().set(ownerKey, PersistentDataType.STRING, robot.getUniqueId().toString());
        });
        heads.add(head);
        shownFace.put(head.getUniqueId(), "normal");
    }

    private void removeHeads(Entity robot) {
        String owner = robot.getUniqueId().toString();
        for (Entity nearby : robot.getNearbyEntities(1.5, 3, 1.5)) {
            if (isHead(nearby) && owner.equals(ownerOf(nearby))) {
                heads.remove(nearby);
                nearby.remove();
            }
        }
    }

    private ItemDisplay headOf(Entity robot) {
        String owner = robot.getUniqueId().toString();
        for (Entity nearby : robot.getNearbyEntities(1.5, 3, 1.5)) {
            if (isHead(nearby) && owner.equals(ownerOf(nearby))) {
                return (ItemDisplay) nearby;
            }
        }
        return null;
    }

    /**
     * 몸의 정면 방향(모델 -z)은 엔티티 방향(yaw)과 같다고 본다: (-sin yaw, cos yaw).
     */
    private static Location headLocation(Entity robot, double bob) {
        Location base = robot.getLocation();
        double yaw = Math.toRadians(base.getYaw());
        Location location = base.clone().add(-Math.sin(yaw) * HEAD_FORWARD, HEAD_HEIGHT + bob, Math.cos(yaw) * HEAD_FORWARD);
        location.setPitch(0);
        return location;
    }

    private void animate() {
        tick += UPDATE_TICKS;
        boolean cleanup = (tick / UPDATE_TICKS) % CLEANUP_EVERY == 0;
        double bob = BOB * Math.sin(2 * Math.PI * (tick % BOB_TICKS) / BOB_TICKS);
        heads.removeIf(head -> !head.isValid());
        for (ItemDisplay head : new HashSet<>(heads)) {
            String owner = ownerOf(head);
            Entity robot = owner == null ? null : plugin.getServer().getEntity(UUID.fromString(owner));
            if (robot == null || !robot.isValid()) {
                if (cleanup) {
                    heads.remove(head);
                    head.remove();
                }
                continue;
            }
            Location target = headLocation(robot, bob);
            float bodyYaw = robot.getLocation().getYaw();
            Player nearest = nearestPlayer(head.getLocation());
            float desired = bodyYaw;
            if (nearest != null) {
                double dx = nearest.getLocation().getX() - target.getX();
                double dz = nearest.getLocation().getZ() - target.getZ();
                float look = (float) Math.toDegrees(Math.atan2(-dx, dz));   // Bukkit yaw: 방향 (-sin, cos)
                desired = bodyYaw + Math.max(-MAX_TURN, Math.min(MAX_TURN, wrap(look - bodyYaw)));
            }
            float current = head.getLocation().getYaw();
            float step = Math.max(-TURN_STEP, Math.min(TURN_STEP, wrap(desired - current)));
            target.setYaw(current + step);
            head.teleport(target);

            Reaction reaction = reactions.get(head.getUniqueId());
            String face;
            if (reaction != null && reaction.until() > tick) {
                face = reaction.face();
            } else {
                reactions.remove(head.getUniqueId());
                face = nearest != null ? "normal" : "sleepy";
            }
            if (!face.equals(shownFace.get(head.getUniqueId()))) {
                ItemStack item = faceItem(face);
                if (item != null) {
                    head.setItemStack(item);
                    shownFace.put(head.getUniqueId(), face);
                }
            }
        }
    }

    private static Player nearestPlayer(Location location) {
        Player nearest = null;
        double best = LOOK_RANGE * LOOK_RANGE;
        for (Player player : location.getWorld().getPlayers()) {
            double distance = player.getLocation().distanceSquared(location);
            if (distance < best && !player.isInvisible()) {
                best = distance;
                nearest = player;
            }
        }
        return nearest;
    }

    private static float wrap(float angle) {
        angle %= 360f;
        if (angle > 180f) {
            angle -= 360f;
        } else if (angle < -180f) {
            angle += 360f;
        }
        return angle;
    }

    private ItemStack faceItem(String face) {
        ItemStack cached = faceItems.get(face);
        if (cached != null) {
            return cached;
        }
        try {
            ItemStack item = itemProvider.create(HEAD_PREFIX + face);
            faceItems.put(face, item);
            return item;
        } catch (IllegalStateException exception) {
            return null;
        }
    }

    private boolean isHead(Entity entity) {
        return entity instanceof ItemDisplay && ownerOf(entity) != null;
    }

    private String ownerOf(Entity entity) {
        return entity.getPersistentDataContainer().get(ownerKey, PersistentDataType.STRING);
    }

    private String furnitureIdOf(Entity entity) {
        if (byAlreadySpawned == null) {
            return null;
        }
        try {
            Object furniture = byAlreadySpawned.invoke(null, entity);
            return furniture == null ? null : (String) getNamespacedId.invoke(furniture);
        } catch (ReflectiveOperationException | RuntimeException exception) {
            return null;
        }
    }

    private void listen(String eventClassName, boolean nextTick, Consumer<Entity> action) throws ReflectiveOperationException {
        Class<? extends Event> eventClass = Class.forName(eventClassName).asSubclass(Event.class);
        Method getEntity = eventClass.getMethod("getBukkitEntity");
        plugin.getServer().getPluginManager().registerEvent(eventClass, this, EventPriority.MONITOR, (listener, event) -> {
            if (!eventClass.isInstance(event)) {
                return;
            }
            try {
                Entity entity = (Entity) getEntity.invoke(event);
                if (entity == null) {
                    return;
                }
                if (nextTick) {
                    plugin.getServer().getScheduler().runTask(plugin, () -> action.accept(entity));
                } else {
                    action.accept(entity);
                }
            } catch (ReflectiveOperationException exception) {
                plugin.getLogger().warning("DL-7 머리 처리 중 오류가 발생했습니다: " + exception);
            }
        }, plugin, true);
    }
}

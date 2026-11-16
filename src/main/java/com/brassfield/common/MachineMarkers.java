package com.brassfield.common;

import org.bukkit.Location;
import org.bukkit.NamespacedKey;
import org.bukkit.World;
import org.bukkit.entity.Display;
import org.bukkit.entity.Entity;
import org.bukkit.entity.ItemDisplay;
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
import org.bukkit.util.Transformation;
import org.joml.AxisAngle4f;
import org.joml.Vector3f;

import java.lang.reflect.Method;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/**
 * 거래·강화 기계 위에 빨간 역삼각형 표시를 띄운다. 표시는 위아래로 부드럽게 움직이며 천천히 360도 돈다.
 * <ul>
 *   <li>기계를 설치하면 바로, 이미 설치된 기계는 청크가 불러와질 때 표시를 붙인다.</li>
 *   <li>표시는 ItemDisplay 엔티티이고, 어느 기계 것인지 기계 엔티티 UUID를 PDC에 적어 둔다.</li>
 *   <li>몇 틱마다 다음 각도·높이를 지정하고 클라이언트 보간에 맡겨 매끄럽게 움직인다.</li>
 *   <li>기계를 부수거나 기계가 사라지면 표시도 지운다.</li>
 * </ul>
 * ItemsAdder 가구 API는 리플렉션으로 쓴다.
 */
public final class MachineMarkers implements Listener {

    private static final String MARKER_ITEM_ID = "rustport:machine_marker";
    private static final String CUSTOM_FURNITURE = "dev.lone.itemsadder.api.CustomFurniture";
    private static final String PLACE_EVENT = "dev.lone.itemsadder.api.Events.FurniturePlaceSuccessEvent";
    private static final String BREAK_EVENT = "dev.lone.itemsadder.api.Events.FurnitureBreakEvent";

    private static final int UPDATE_TICKS = 4;
    private static final int TURN_TICKS = 160;        // 한 바퀴 8초
    private static final int BOB_TICKS = 60;          // 위아래 한 번 3초
    private static final float BOB_HEIGHT = 0.12f;
    private static final int CLEANUP_EVERY = 25;      // 업데이트 25번(5초)마다 주인 없는 표시 정리

    private final JavaPlugin plugin;
    private final ItemsAdderItemProvider itemProvider;
    private final NamespacedKey ownerKey;
    private final Map<String, Double> heights = new HashMap<>();
    private final Set<ItemDisplay> markers = new HashSet<>();
    private Method byAlreadySpawned;
    private Method getNamespacedId;
    private BukkitTask task;
    private long tick;

    public MachineMarkers(JavaPlugin plugin, ItemsAdderItemProvider itemProvider) {
        this.plugin = plugin;
        this.itemProvider = itemProvider;
        this.ownerKey = new NamespacedKey(plugin, "machine_marker_owner");
    }

    /**
     * 표시를 붙일 기계와, 기계 바닥에서 표시 중심까지의 높이(블록)를 등록한다.
     */
    public void register(String furnitureId, double height) {
        heights.put(furnitureId, height);
    }

    public void start() {
        if (!plugin.getServer().getPluginManager().isPluginEnabled("ItemsAdder")) {
            return;
        }
        try {
            Class<?> furniture = Class.forName(CUSTOM_FURNITURE);
            byAlreadySpawned = furniture.getMethod("byAlreadySpawned", Entity.class);
            getNamespacedId = furniture.getMethod("getNamespacedID");
            listen(PLACE_EVENT, true, this::ensureMarker);
            listen(BREAK_EVENT, false, this::removeMarkers);
        } catch (ReflectiveOperationException exception) {
            plugin.getLogger().warning("ItemsAdder 가구 API를 불러오지 못해 기계 표시를 쓸 수 없습니다: " + exception);
            return;
        }
        plugin.getServer().getPluginManager().registerEvents(this, plugin);
        // ItemsAdder는 서버가 켜진 뒤 조금 늦게 아이템을 불러오므로, 이미 불러와진 청크는 잠시 뒤 두 번 훑는다.
        plugin.getServer().getScheduler().runTaskLater(plugin, this::scanLoadedWorlds, 40L);
        plugin.getServer().getScheduler().runTaskLater(plugin, this::scanLoadedWorlds, 200L);
        task = plugin.getServer().getScheduler().runTaskTimer(plugin, this::animate, UPDATE_TICKS, UPDATE_TICKS);
    }

    public void stop() {
        if (task != null) {
            task.cancel();
        }
        markers.clear();
    }

    @EventHandler
    public void onEntitiesLoad(EntitiesLoadEvent event) {
        for (Entity entity : event.getEntities()) {
            if (isMarker(entity)) {
                markers.add((ItemDisplay) entity);
            }
        }
        for (Entity entity : event.getEntities()) {
            ensureMarker(entity);
        }
    }

    @EventHandler
    public void onEntitiesUnload(EntitiesUnloadEvent event) {
        event.getEntities().forEach(markers::remove);
    }

    private void scanLoadedWorlds() {
        for (World world : plugin.getServer().getWorlds()) {
            for (Entity entity : world.getEntities()) {
                if (isMarker(entity)) {
                    markers.add((ItemDisplay) entity);
                }
            }
            for (Entity entity : world.getEntities()) {
                ensureMarker(entity);
            }
        }
    }

    /**
     * 등록된 기계 엔티티라면, 아직 표시가 없을 때 표시를 띄운다.
     */
    private void ensureMarker(Entity machine) {
        if (machine instanceof ItemDisplay display && isMarker(display)) {
            return;
        }
        Double height = heights.get(furnitureId(machine));
        if (height == null) {
            return;
        }
        Location location = markerLocation(machine, height);
        ItemDisplay existing = markerOf(machine);
        if (existing != null) {
            // 이미 떠 있는 표시도 설정 높이로 맞춘다 (높이를 바꾼 뒤 재시작하면 옮겨진다)
            if (existing.getLocation().distanceSquared(location) > 1.0E-4) {
                existing.teleport(location);
            }
            return;
        }
        ItemStack markerItem;
        try {
            markerItem = itemProvider.create(MARKER_ITEM_ID);
        } catch (IllegalStateException exception) {
            return;  // ItemsAdder가 아직 아이템을 불러오지 못함 → 다음 훑기 때 다시 시도
        }

        ItemDisplay marker = machine.getWorld().spawn(location, ItemDisplay.class, display -> {
            display.setItemStack(markerItem);
            display.setItemDisplayTransform(ItemDisplay.ItemDisplayTransform.FIXED);
            display.setBrightness(new Display.Brightness(15, 15));
            display.setPersistent(true);
            display.setInterpolationDuration(UPDATE_TICKS);
            display.getPersistentDataContainer().set(ownerKey, PersistentDataType.STRING, machine.getUniqueId().toString());
        });
        markers.add(marker);
    }

    private void removeMarkers(Entity machine) {
        String owner = machine.getUniqueId().toString();
        for (Entity nearby : machine.getNearbyEntities(1, 6, 1)) {
            if (isMarker(nearby) && owner.equals(ownerOf(nearby))) {
                markers.remove(nearby);
                nearby.remove();
            }
        }
    }

    private ItemDisplay markerOf(Entity machine) {
        String owner = machine.getUniqueId().toString();
        for (Entity nearby : machine.getNearbyEntities(1, 6, 1)) {
            if (isMarker(nearby) && owner.equals(ownerOf(nearby))) {
                return (ItemDisplay) nearby;
            }
        }
        return null;
    }

    private static Location markerLocation(Entity machine, double height) {
        Location location = machine.getLocation().clone();
        location.setYaw(0);
        location.setPitch(0);
        return location.add(0, height, 0);
    }

    private void animate() {
        tick += UPDATE_TICKS;
        boolean cleanup = (tick / UPDATE_TICKS) % CLEANUP_EVERY == 0;
        float angle = (float) (2 * Math.PI * (tick % TURN_TICKS) / TURN_TICKS);
        float bob = (float) (BOB_HEIGHT * Math.sin(2 * Math.PI * (tick % BOB_TICKS) / BOB_TICKS));
        Transformation transformation = new Transformation(
                new Vector3f(0, bob, 0),
                new AxisAngle4f(angle, 0, 1, 0),
                new Vector3f(1, 1, 1),
                new AxisAngle4f()
        );

        markers.removeIf(marker -> !marker.isValid());
        for (ItemDisplay marker : new HashSet<>(markers)) {
            if (cleanup && isOrphan(marker)) {
                markers.remove(marker);
                marker.remove();
                continue;
            }
            marker.setInterpolationDelay(0);
            marker.setInterpolationDuration(UPDATE_TICKS);
            marker.setTransformation(transformation);
        }
    }

    /**
     * 표시의 주인 기계가 사라졌는지. (같은 청크라 기계가 불러와져 있어야 정상)
     */
    private boolean isOrphan(ItemDisplay marker) {
        String owner = ownerOf(marker);
        if (owner == null) {
            return true;
        }
        Entity machine = plugin.getServer().getEntity(UUID.fromString(owner));
        if (machine == null || !machine.isValid()) {
            return true;
        }
        // 표시를 더 붙이지 않기로 한 기계(예: 개인 기기가 된 조리대)면 정리한다. ID를 못 읽으면(로딩 중) 건드리지 않는다
        String id = furnitureId(machine);
        return id != null && !heights.containsKey(id);
    }

    private boolean isMarker(Entity entity) {
        return entity instanceof ItemDisplay && ownerOf(entity) != null;
    }

    private String ownerOf(Entity entity) {
        return entity.getPersistentDataContainer().get(ownerKey, PersistentDataType.STRING);
    }

    private String furnitureId(Entity entity) {
        try {
            Object furniture = byAlreadySpawned.invoke(null, entity);
            return furniture == null ? null : (String) getNamespacedId.invoke(furniture);
        } catch (ReflectiveOperationException | RuntimeException exception) {
            return null;
        }
    }

    /**
     * @param nextTick 설치 직후엔 ItemsAdder가 엔티티를 마저 세팅하므로 다음 틱에 처리한다. 파괴는 엔티티가 사라지기 전에 바로 처리한다.
     */
    private void listen(String eventClassName, boolean nextTick, java.util.function.Consumer<Entity> action)
            throws ReflectiveOperationException {
        Class<? extends Event> eventClass = Class.forName(eventClassName).asSubclass(Event.class);
        Method getEntity = eventClass.getMethod("getBukkitEntity");
        // MONITOR + 취소된 이벤트 무시: 실제로 설치·파괴가 확정된 경우에만 반응한다.
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
                plugin.getLogger().warning("기계 표시 처리 중 오류가 발생했습니다: " + exception);
            }
        }, plugin, true);
    }
}

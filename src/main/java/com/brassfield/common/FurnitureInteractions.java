package com.brassfield.common;

import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Player;
import org.bukkit.event.Cancellable;
import org.bukkit.event.Event;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.block.Action;
import org.bukkit.event.player.PlayerEvent;
import org.bukkit.plugin.java.JavaPlugin;

import java.lang.reflect.Method;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.function.BiConsumer;
import java.util.function.Consumer;

/**
 * 마을에 설치한 거래 기계(ItemsAdder 가구)와의 상호작용을 맡는다.
 * <ul>
 *   <li>기계를 우클릭하면 그 기계 ID에 등록된 동작(GUI 열기 등)을 실행한다.</li>
 *   <li>마을 공용 기계는 관리자 권한이 있어야 부술 수 있다. (플레이어가 마을 기계를 뜯어 가지 못하게)</li>
 *   <li>개인 기기({@link #personal})는 누구나 설치하고 부술 수 있다.</li>
 *   <li>기계를 부수면 그 기계 ID에 등록된 부술 때 동작(안에 든 것 떨어뜨리기 등)을 실행한다.</li>
 * </ul>
 * ItemsAdder가 없어도 플러그인이 죽지 않도록 ItemsAdder 이벤트는 리플렉션으로 등록한다.
 */
public final class FurnitureInteractions implements Listener {

    public static final String ADMIN_PERMISSION = "brassfield.machine.admin";

    private static final String INTERACT_EVENT = "dev.lone.itemsadder.api.Events.FurnitureInteractEvent";
    private static final String BREAK_EVENT = "dev.lone.itemsadder.api.Events.FurnitureBreakEvent";

    private final JavaPlugin plugin;
    private final Map<String, BiConsumer<Player, Entity>> handlers = new HashMap<>();
    private final Map<String, Consumer<Entity>> breakHandlers = new HashMap<>();
    private final Set<String> personalIds = new HashSet<>();

    public FurnitureInteractions(JavaPlugin plugin) {
        this.plugin = plugin;
    }

    /**
     * 기계를 우클릭했을 때 실행할 동작을 등록한다. (furnitureId 예: "rustport:stone_vending_machine")
     */
    public void onInteract(String furnitureId, Consumer<Player> handler) {
        handlers.put(furnitureId, (player, furniture) -> handler.accept(player));
    }

    /**
     * 기계를 우클릭했을 때 실행할 동작 (어느 기계인지 가구 엔티티도 받는다. 기계마다 상태가 따로인 경우)
     */
    public void onInteractAt(String furnitureId, BiConsumer<Player, Entity> handler) {
        handlers.put(furnitureId, handler);
    }

    /**
     * 플레이어가 각자 설치하는 개인 기기로 지정한다 (관리자가 아니어도 부술 수 있다).
     */
    public void personal(String furnitureId) {
        personalIds.add(furnitureId);
    }

    /**
     * 기계를 부쉈을 때 실행할 동작 (공용 기계는 관리자만 부술 수 있다).
     */
    public void onBreak(String furnitureId, Consumer<Entity> handler) {
        breakHandlers.put(furnitureId, handler);
    }

    public void start() {
        if (!plugin.getServer().getPluginManager().isPluginEnabled("ItemsAdder")) {
            plugin.getLogger().warning("ItemsAdder가 없어 거래 기계를 쓸 수 없습니다.");
            return;
        }
        try {
            listen(INTERACT_EVENT, this::handleInteract);
            listen(BREAK_EVENT, this::handleBreak);
        } catch (ReflectiveOperationException exception) {
            plugin.getLogger().warning("ItemsAdder 가구 이벤트를 불러오지 못해 거래 기계를 쓸 수 없습니다: " + exception);
        }
    }

    private void handleInteract(Event event, String furnitureId) throws ReflectiveOperationException {
        BiConsumer<Player, Entity> handler = handlers.get(furnitureId);
        if (handler == null) {
            return;
        }
        Object action = event.getClass().getMethod("getAction").invoke(event);
        if (action != null && action != Action.RIGHT_CLICK_AIR && action != Action.RIGHT_CLICK_BLOCK) {
            return;
        }
        // 가구 회전·앉기 같은 ItemsAdder 기본 동작 대신 기계 동작만 실행한다.
        ((Cancellable) event).setCancelled(true);
        handler.accept(((PlayerEvent) event).getPlayer(), furnitureEntity(event));
    }

    private void handleBreak(Event event, String furnitureId) throws ReflectiveOperationException {
        Player player = ((PlayerEvent) event).getPlayer();
        if (!handlers.containsKey(furnitureId)) {
            return;
        }
        if (personalIds.contains(furnitureId) || player.hasPermission(ADMIN_PERMISSION)) {
            Consumer<Entity> breakHandler = breakHandlers.get(furnitureId);
            if (breakHandler != null && !((Cancellable) event).isCancelled()) {
                breakHandler.accept(furnitureEntity(event));
            }
            return;
        }
        ((Cancellable) event).setCancelled(true);
        player.sendMessage(Component.text("마을의 기계는 부술 수 없습니다.", NamedTextColor.RED));
    }

    private static Entity furnitureEntity(Event event) throws ReflectiveOperationException {
        return (Entity) event.getClass().getMethod("getBukkitEntity").invoke(event);
    }

    private void listen(String eventClassName, FurnitureHandler handler) throws ReflectiveOperationException {
        Class<? extends Event> eventClass = Class.forName(eventClassName).asSubclass(Event.class);
        Method getNamespacedId = eventClass.getMethod("getNamespacedID");
        // 다른 플러그인이 먼저 취소했어도 기계 동작은 실행되도록 취소된 이벤트도 받는다.
        plugin.getServer().getPluginManager().registerEvent(eventClass, this, EventPriority.NORMAL, (listener, event) -> {
            if (!eventClass.isInstance(event)) {
                return;
            }
            try {
                handler.handle(event, (String) getNamespacedId.invoke(event));
            } catch (ReflectiveOperationException exception) {
                plugin.getLogger().warning("거래 기계 처리 중 오류가 발생했습니다: " + exception);
            }
        }, plugin, false);
    }

    @FunctionalInterface
    private interface FurnitureHandler {
        void handle(Event event, String furnitureId) throws ReflectiveOperationException;
    }
}

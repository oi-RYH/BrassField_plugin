package com.brassfield.enhancement;

import com.brassfield.common.ItemsAdderItemProvider;
import org.bukkit.Material;
import org.bukkit.NamespacedKey;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;
import org.bukkit.persistence.PersistentDataContainer;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.plugin.java.JavaPlugin;

import java.util.Collection;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Optional;

/**
 * 강화 종류 등록부. 아이템이 어떤 강화 종류인지(enhance_track)와 몇 단계인지(enhance_level)를 아이템 데이터로 읽고 쓴다.
 * enhance_track 이 없는 예전 아이템은 무기로 본다 (방어구 · 장신구 강화 이전에 만들어진 강화 아이템은 모두 무기).
 */
public final class EnhanceTracks {

    // 플러그인 이름이 RustportEnhancement였을 때 만들어진 아이템의 강화 단계 키. 읽기만 하고, 다시 만들 때 새 키로 바뀐다.
    private static final NamespacedKey LEGACY_LEVEL_KEY = new NamespacedKey("rustportenhancement", "enhance_level");

    private static final Map<String, EnhanceTrack> TRACKS = new LinkedHashMap<>();
    private static NamespacedKey levelKey;
    private static NamespacedKey trackKey;
    private static ItemsAdderItemProvider itemProvider;
    private static WeaponTrack weapon;
    private static final Map<ArmorTrack.Part, ArmorTrack> ARMOR = new java.util.EnumMap<>(ArmorTrack.Part.class);

    private EnhanceTracks() {
    }

    public static void init(JavaPlugin plugin) {
        levelKey = new NamespacedKey(plugin, "enhance_level");
        trackKey = new NamespacedKey(plugin, "enhance_track");
        itemProvider = new ItemsAdderItemProvider(plugin);
        TRACKS.clear();
        weapon = new WeaponTrack(plugin);
        register(weapon);
        ARMOR.clear();
        for (ArmorTrack.Part part : ArmorTrack.Part.values()) {
            ArmorTrack track = new ArmorTrack(plugin, part);
            ARMOR.put(part, track);
            register(track);
        }
    }

    public static void register(EnhanceTrack track) {
        if (TRACKS.putIfAbsent(track.key(), track) != null) {
            throw new IllegalStateException("강화 종류 이름이 겹칩니다: " + track.key());
        }
    }

    public static WeaponTrack weapon() {
        return weapon;
    }

    public static ArmorTrack armor(ArmorTrack.Part part) {
        return ARMOR.get(part);
    }

    public static Collection<EnhanceTrack> all() {
        return TRACKS.values();
    }

    /** 아이템의 강화 종류. 강화할 수 없는 아이템이면 비어 있다 */
    public static Optional<EnhanceTrack> trackOf(ItemStack item) {
        if (item == null || item.getType().isAir()) {
            return Optional.empty();
        }
        PersistentDataContainer data = item.getItemMeta().getPersistentDataContainer();
        String key = data.get(trackKey, PersistentDataType.STRING);
        if (key != null) {
            return Optional.ofNullable(TRACKS.get(key));
        }
        if (data.has(levelKey, PersistentDataType.INTEGER) || data.has(LEGACY_LEVEL_KEY, PersistentDataType.INTEGER)) {
            return Optional.of(weapon);                                // 종류 기록 이전의 강화 아이템 = 무기
        }
        return TRACKS.values().stream().filter(track -> track.isFreshItem(item)).findFirst();
    }

    public static boolean isEnhanceable(ItemStack item) {
        return trackOf(item).isPresent();
    }

    /** 아이템의 강화 단계 (없으면 0, 종류의 최대 단계를 넘지 않음) */
    public static int levelOf(ItemStack item) {
        if (item == null || item.getType().isAir()) {
            return 0;
        }
        PersistentDataContainer data = item.getItemMeta().getPersistentDataContainer();
        Integer stored = data.get(levelKey, PersistentDataType.INTEGER);
        if (stored == null) {
            stored = data.get(LEGACY_LEVEL_KEY, PersistentDataType.INTEGER);
        }
        int max = trackOf(item).map(EnhanceTrack::maxLevel).orElse(0);
        return stored == null ? 0 : Math.max(0, Math.min(stored, max));
    }

    /** 아이템 데이터에 강화 종류 · 단계를 적는다 (각 종류의 applyLevel 에서 부른다) */
    public static void writeIdentity(ItemMeta meta, EnhanceTrack track, int level) {
        PersistentDataContainer data = meta.getPersistentDataContainer();
        data.set(trackKey, PersistentDataType.STRING, track.key());
        data.set(levelKey, PersistentDataType.INTEGER, level);
        data.remove(LEGACY_LEVEL_KEY);
    }

    static ItemsAdderItemProvider itemProvider() {
        return itemProvider;
    }

    public static ItemStack createCustomOrFallback(String namespacedId, Material fallback) {
        try {
            return itemProvider.create(namespacedId);
        } catch (IllegalStateException exception) {
            return ItemStack.of(fallback);
        }
    }
}

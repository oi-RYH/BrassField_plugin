package com.brassfield.stone;

import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.plugin.java.JavaPlugin;

import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * plugins/BrassField/stones.yml 에 보유량을 저장한다.
 * <pre>
 * players:
 *   &lt;uuid&gt;:
 *     LOW: 12
 *     MIDDLE: 0
 *     HIGH: 3
 * </pre>
 */
public final class YamlStoneStorage implements StoneStorage {

    private static final String ROOT = "players";

    private final JavaPlugin plugin;
    private final File file;

    public YamlStoneStorage(JavaPlugin plugin) {
        this.plugin = plugin;
        this.file = new File(plugin.getDataFolder(), "stones.yml");
    }

    @Override
    public Map<UUID, EnumMap<StoneGrade, Long>> loadAll() {
        Map<UUID, EnumMap<StoneGrade, Long>> result = new HashMap<>();
        if (!file.exists()) {
            return result;
        }

        YamlConfiguration yaml = YamlConfiguration.loadConfiguration(file);
        ConfigurationSection players = yaml.getConfigurationSection(ROOT);
        if (players == null) {
            return result;
        }

        for (String key : players.getKeys(false)) {
            UUID playerId;
            try {
                playerId = UUID.fromString(key);
            } catch (IllegalArgumentException exception) {
                plugin.getLogger().warning("stones.yml에 잘못된 UUID가 있어 건너뜁니다: " + key);
                continue;
            }

            EnumMap<StoneGrade, Long> balances = new EnumMap<>(StoneGrade.class);
            for (StoneGrade grade : StoneGrade.values()) {
                if (grade.isCurrency()) {
                    balances.put(grade, Math.max(0L, players.getLong(key + "." + grade.name())));
                }
            }
            result.put(playerId, balances);
        }
        return result;
    }

    @Override
    public void saveAll(Map<UUID, EnumMap<StoneGrade, Long>> snapshot) {
        YamlConfiguration yaml = new YamlConfiguration();
        snapshot.forEach((playerId, balances) ->
                balances.forEach((grade, amount) -> yaml.set(ROOT + "." + playerId + "." + grade.name(), amount))
        );

        try {
            Path target = file.toPath();
            Files.createDirectories(target.getParent());
            // 쓰는 도중 서버가 꺼져도 기존 파일이 깨지지 않도록 임시 파일에 쓴 뒤 바꿔치기한다.
            Path temp = target.resolveSibling(file.getName() + ".tmp");
            Files.writeString(temp, yaml.saveToString(), StandardCharsets.UTF_8);
            Files.move(temp, target, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
        } catch (IOException exception) {
            plugin.getLogger().severe("강화석 보유량 저장에 실패했습니다: " + exception);
        }
    }
}

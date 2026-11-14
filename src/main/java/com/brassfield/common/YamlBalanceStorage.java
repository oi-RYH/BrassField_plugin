package com.brassfield.common;

import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.plugin.java.JavaPlugin;

import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * plugins/BrassField/&lt;파일&gt; 에 보유량을 저장한다.
 * <pre>
 * players:
 *   &lt;uuid&gt;:
 *     &lt;재화 키&gt;: 12
 * </pre>
 */
public final class YamlBalanceStorage implements BalanceStorage {

    private static final String ROOT = "players";

    private final JavaPlugin plugin;
    private final File file;

    public YamlBalanceStorage(JavaPlugin plugin, String fileName) {
        this.plugin = plugin;
        this.file = new File(plugin.getDataFolder(), fileName);
    }

    @Override
    public Map<UUID, Map<String, Long>> loadAll() {
        Map<UUID, Map<String, Long>> result = new HashMap<>();
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
                plugin.getLogger().warning(file.getName() + "에 잘못된 UUID가 있어 건너뜁니다: " + key);
                continue;
            }

            ConfigurationSection section = players.getConfigurationSection(key);
            if (section == null) {
                continue;
            }
            Map<String, Long> balances = new HashMap<>();
            for (String currency : section.getKeys(false)) {
                balances.put(currency, Math.max(0L, section.getLong(currency)));
            }
            result.put(playerId, balances);
        }
        return result;
    }

    @Override
    public void saveAll(Map<UUID, Map<String, Long>> snapshot) {
        YamlConfiguration yaml = new YamlConfiguration();
        snapshot.forEach((playerId, balances) ->
                balances.forEach((currency, amount) -> yaml.set(ROOT + "." + playerId + "." + currency, amount))
        );

        try {
            Path target = file.toPath();
            Files.createDirectories(target.getParent());
            // 쓰는 도중 서버가 꺼져도 기존 파일이 깨지지 않도록 임시 파일에 쓴 뒤 바꿔치기한다.
            Path temp = target.resolveSibling(file.getName() + ".tmp");
            Files.writeString(temp, yaml.saveToString(), StandardCharsets.UTF_8);
            Files.move(temp, target, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
        } catch (IOException exception) {
            plugin.getLogger().severe(file.getName() + " 저장에 실패했습니다: " + exception);
        }
    }
}

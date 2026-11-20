package com.brassfield.accessory;

import net.kyori.adventure.key.Key;
import org.bukkit.Bukkit;
import org.bukkit.World;
import org.bukkit.plugin.java.JavaPlugin;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;

/**
 * G 키(빠른 동작 · Quick Actions) 메뉴: 바닐라 다이얼로그를 데이터팩으로 등록한다.
 * 플러그인이 켜질 때 기본 세계의 datapacks/brassfield_menu 에 써 두고, 내용이 바뀌었으면 다음 서버 재시작부터 적용된다
 * (데이터팩은 플러그인보다 먼저 불러오기 때문).
 * 단추는 minecraft:custom 동작 → PlayerCustomClickEvent (AccessoryListener) 로 받는다.
 */
public final class MenuDialogPack {

    public static final Key ACCESSORY = Key.key("brassfield", "accessory");
    private static final String FOLDER = "brassfield_menu";

    private static final String PACK_MCMETA = """
            {
              "pack": {
                "description": "BrassField G 키 메뉴",
                "min_format": 101,
                "max_format": 101
              }
            }
            """;

    private static final String MENU = """
            {
              "type": "minecraft:multi_action",
              "title": {"text": "BRASS FIELD", "color": "gold", "bold": true},
              "external_title": {"text": "BRASS FIELD 메뉴"},
              "body": [
                {"type": "minecraft:plain_message", "contents": {"text": "원하는 기능을 고르세요.", "color": "gray"}}
              ],
              "columns": 1,
              "can_close_with_escape": true,
              "after_action": "close",
              "actions": [
                {
                  "label": {"text": "장신구", "color": "yellow"},
                  "tooltip": {"text": "목걸이 · 귀걸이 · 반지를 장착합니다"},
                  "width": 150,
                  "action": {"type": "minecraft:custom", "id": "brassfield:accessory"}
                }
              ]
            }
            """;

    private static final String QUICK_ACTIONS = """
            {
              "values": ["brassfield:menu"]
            }
            """;

    private MenuDialogPack() {
    }

    public static void install(JavaPlugin plugin) {
        World world = Bukkit.getWorlds().isEmpty() ? null : Bukkit.getWorlds().get(0);
        if (world == null) {
            return;
        }
        Path root = world.getWorldFolder().toPath().resolve("datapacks").resolve(FOLDER);
        Map<String, String> files = Map.of(
                "pack.mcmeta", PACK_MCMETA,
                "data/brassfield/dialog/menu.json", MENU,
                "data/minecraft/tags/dialog/quick_actions.json", QUICK_ACTIONS
        );
        boolean changed = false;
        try {
            for (Map.Entry<String, String> file : files.entrySet()) {
                Path path = root.resolve(file.getKey());
                if (Files.exists(path) && Files.readString(path, StandardCharsets.UTF_8).equals(file.getValue())) {
                    continue;
                }
                Files.createDirectories(path.getParent());
                Files.writeString(path, file.getValue(), StandardCharsets.UTF_8);
                changed = true;
            }
        } catch (IOException exception) {
            plugin.getLogger().warning("G 키 메뉴 데이터팩을 쓰지 못했습니다: " + exception.getMessage());
            return;
        }
        if (changed) {
            plugin.getLogger().warning("G 키 메뉴 데이터팩을 새로 썼습니다 (" + root + "). 서버를 한 번 더 재시작해야 적용됩니다.");
        }
    }
}

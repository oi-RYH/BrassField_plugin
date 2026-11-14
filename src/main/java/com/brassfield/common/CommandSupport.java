package com.brassfield.common;

import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.Bukkit;
import org.bukkit.OfflinePlayer;
import org.bukkit.command.CommandSender;
import org.bukkit.entity.Player;

import java.util.List;

/**
 * 관리자 명령어(/강화석, /골드 등)가 함께 쓰는 플레이어 찾기·숫자 해석·안내 메시지.
 * 실패하면 보낸 사람에게 이유를 알려주고 null을 돌려준다.
 */
public final class CommandSupport {

    private CommandSupport() {
    }

    /**
     * 접속 중이거나 서버에 접속한 적이 있는 플레이어를 찾는다.
     */
    public static OfflinePlayer findPlayer(CommandSender sender, String name) {
        Player online = Bukkit.getPlayerExact(name);
        if (online != null) {
            return online;
        }
        OfflinePlayer cached = Bukkit.getOfflinePlayerIfCached(name);
        if (cached == null) {
            error(sender, "서버에 접속한 적이 있는 플레이어를 찾을 수 없습니다: " + name);
        }
        return cached;
    }

    public static Long parseAmount(CommandSender sender, String text, long minimum) {
        try {
            long amount = Long.parseLong(text);
            if (amount < minimum) {
                error(sender, "수량은 " + minimum + " 이상이어야 합니다: " + text);
                return null;
            }
            return amount;
        } catch (NumberFormatException exception) {
            error(sender, "수량은 숫자여야 합니다: " + text);
            return null;
        }
    }

    public static String nameOf(OfflinePlayer player) {
        return player.getName() == null ? player.getUniqueId().toString() : player.getName();
    }

    public static void error(CommandSender sender, String message) {
        sender.sendMessage(Component.text(message, NamedTextColor.RED));
    }

    public static List<String> onlinePlayerNames(String prefix) {
        return filter(Bukkit.getOnlinePlayers().stream().map(Player::getName).toList(), prefix);
    }

    public static List<String> filter(List<String> options, String prefix) {
        return options.stream().filter(option -> option.startsWith(prefix)).toList();
    }

    /**
     * 1234567 → "1,234,567"
     */
    public static String formatNumber(long value) {
        return String.format("%,d", value);
    }
}

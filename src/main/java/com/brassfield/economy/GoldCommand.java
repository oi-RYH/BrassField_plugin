package com.brassfield.economy;

import static com.brassfield.common.CommandSupport.error;
import static com.brassfield.common.CommandSupport.filter;
import static com.brassfield.common.CommandSupport.findPlayer;
import static com.brassfield.common.CommandSupport.formatNumber;
import static com.brassfield.common.CommandSupport.nameOf;
import static com.brassfield.common.CommandSupport.onlinePlayerNames;
import static com.brassfield.common.CommandSupport.parseAmount;

import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.OfflinePlayer;
import org.bukkit.command.Command;
import org.bukkit.command.CommandSender;
import org.bukkit.command.TabExecutor;
import org.bukkit.entity.Player;

import java.util.List;
import java.util.UUID;

/**
 * /골드                                  내 골드 확인
 * /골드 확인 &lt;플레이어&gt;                   (관리자) 다른 플레이어 골드 확인
 * /골드 지급|차감|설정 &lt;플레이어&gt; &lt;금액&gt;    (관리자) 골드 변경
 */
public final class GoldCommand implements TabExecutor {

    public static final String ADMIN_PERMISSION = "brassfield.gold.admin";

    private static final List<String> ADMIN_SUBCOMMANDS = List.of("확인", "지급", "차감", "설정");

    private final GoldWallet wallet;

    public GoldCommand(GoldWallet wallet) {
        this.wallet = wallet;
    }

    @Override
    public boolean onCommand(CommandSender sender, Command command, String label, String[] args) {
        if (args.length == 0) {
            if (!(sender instanceof Player player)) {
                sender.sendMessage("콘솔에서는 /" + label + " 확인 <플레이어> 를 사용하세요.");
                return true;
            }
            sendBalance(sender, player.getUniqueId(), "내");
            return true;
        }

        if (!sender.hasPermission(ADMIN_PERMISSION)) {
            error(sender, "권한이 없습니다.");
            return true;
        }

        switch (args[0]) {
            case "확인" -> handleCheck(sender, label, args);
            case "지급", "차감", "설정" -> handleChange(sender, label, args);
            default -> sendUsage(sender, label);
        }
        return true;
    }

    private void handleCheck(CommandSender sender, String label, String[] args) {
        if (args.length != 2) {
            error(sender, "사용법: /" + label + " 확인 <플레이어>");
            return;
        }
        OfflinePlayer target = findPlayer(sender, args[1]);
        if (target != null) {
            sendBalance(sender, target.getUniqueId(), nameOf(target) + "님의");
        }
    }

    private void handleChange(CommandSender sender, String label, String[] args) {
        String subcommand = args[0];
        if (args.length != 3) {
            error(sender, "사용법: /" + label + " " + subcommand + " <플레이어> <금액>");
            return;
        }
        OfflinePlayer target = findPlayer(sender, args[1]);
        Long amount = parseAmount(sender, args[2], subcommand.equals("설정") ? 0 : 1);
        if (target == null || amount == null) {
            return;
        }

        UUID playerId = target.getUniqueId();
        switch (subcommand) {
            case "지급" -> wallet.deposit(playerId, amount);
            case "차감" -> {
                if (!wallet.withdraw(playerId, amount)) {
                    error(sender, nameOf(target) + "님의 골드가 부족합니다. (보유: " + formatNumber(wallet.get(playerId)) + "골드)");
                    return;
                }
            }
            default -> wallet.set(playerId, amount);
        }

        sender.sendMessage(Component.text(nameOf(target) + "님의 골드 " + subcommand + " 완료. (보유: "
                + formatNumber(wallet.get(playerId)) + "골드)", NamedTextColor.GREEN));
    }

    private void sendBalance(CommandSender sender, UUID playerId, String owner) {
        sender.sendMessage(Component.text(owner + " 골드: ", NamedTextColor.YELLOW)
                .append(Component.text(formatNumber(wallet.get(playerId)) + "골드", NamedTextColor.GOLD)));
    }

    private void sendUsage(CommandSender sender, String label) {
        sender.sendMessage(Component.text("골드 관리자 명령어", NamedTextColor.YELLOW));
        sender.sendMessage(Component.text("/" + label + " 확인 <플레이어>", NamedTextColor.GRAY));
        sender.sendMessage(Component.text("/" + label + " 지급|차감|설정 <플레이어> <금액>", NamedTextColor.GRAY));
    }

    @Override
    public List<String> onTabComplete(CommandSender sender, Command command, String alias, String[] args) {
        if (!sender.hasPermission(ADMIN_PERMISSION)) {
            return List.of();
        }
        if (args.length == 1) {
            return filter(ADMIN_SUBCOMMANDS, args[0]);
        }
        if (args.length == 2 && ADMIN_SUBCOMMANDS.contains(args[0])) {
            return onlinePlayerNames(args[1]);
        }
        return List.of();
    }
}

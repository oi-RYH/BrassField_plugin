package com.brassfield.stone;

import static com.brassfield.common.CommandSupport.error;
import static com.brassfield.common.CommandSupport.filter;
import static com.brassfield.common.CommandSupport.findPlayer;
import static com.brassfield.common.CommandSupport.nameOf;
import static com.brassfield.common.CommandSupport.onlinePlayerNames;
import static com.brassfield.common.CommandSupport.parseAmount;

import com.brassfield.common.ItemDelivery;
import com.brassfield.common.ItemsAdderItemProvider;
import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.Bukkit;
import org.bukkit.OfflinePlayer;
import org.bukkit.command.Command;
import org.bukkit.command.CommandSender;
import org.bukkit.command.TabExecutor;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;

import java.util.List;
import java.util.UUID;

/**
 * /강화석                                          내 보유량 확인
 * /강화석 확인 &lt;플레이어&gt;                           (관리자) 다른 플레이어 보유량 확인
 * /강화석 지급|차감|설정 &lt;플레이어&gt; &lt;등급&gt; &lt;수량&gt;    (관리자) 보유량 변경
 * /강화석 상자 &lt;플레이어&gt; &lt;등급&gt; [개수]             (관리자) 강화석 상자 아이템 지급
 */
public final class StoneCommand implements TabExecutor {

    public static final String ADMIN_PERMISSION = "brassfield.stone.admin";

    private static final List<String> ADMIN_SUBCOMMANDS = List.of("확인", "지급", "차감", "설정", "상자");
    private static final List<String> GRADE_NAMES = List.of("하급", "중급", "상급");

    private final StoneWallet wallet;
    private final ItemsAdderItemProvider itemProvider;

    public StoneCommand(StoneWallet wallet, ItemsAdderItemProvider itemProvider) {
        this.wallet = wallet;
        this.itemProvider = itemProvider;
    }

    @Override
    public boolean onCommand(CommandSender sender, Command command, String label, String[] args) {
        if (args.length == 0) {
            if (!(sender instanceof Player player)) {
                sender.sendMessage("콘솔에서는 /" + label + " 확인 <플레이어> 를 사용하세요.");
                return true;
            }
            sendBalances(sender, player.getUniqueId(), "내");
            return true;
        }

        if (!sender.hasPermission(ADMIN_PERMISSION)) {
            error(sender, "권한이 없습니다.");
            return true;
        }

        String subcommand = args[0];
        switch (subcommand) {
            case "확인" -> handleCheck(sender, label, args);
            case "지급", "차감", "설정" -> handleChange(sender, label, args);
            case "상자" -> handleChest(sender, label, args);
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
            sendBalances(sender, target.getUniqueId(), nameOf(target) + "님의");
        }
    }

    private void handleChange(CommandSender sender, String label, String[] args) {
        String subcommand = args[0];
        if (args.length != 4) {
            error(sender, "사용법: /" + label + " " + subcommand + " <플레이어> <하급|중급|상급> <수량>");
            return;
        }
        OfflinePlayer target = findPlayer(sender, args[1]);
        StoneGrade grade = parseGrade(sender, args[2]);
        Long amount = parseAmount(sender, args[3], subcommand.equals("설정") ? 0 : 1);
        if (target == null || grade == null || amount == null) {
            return;
        }

        UUID playerId = target.getUniqueId();
        switch (subcommand) {
            case "지급" -> wallet.deposit(playerId, grade, amount);
            case "차감" -> {
                if (!wallet.withdraw(playerId, grade, amount)) {
                    error(sender, nameOf(target) + "님의 " + grade.displayName() + " 강화석이 부족합니다. (보유: "
                            + wallet.get(playerId, grade) + "개)");
                    return;
                }
            }
            default -> wallet.set(playerId, grade, amount);
        }

        sender.sendMessage(Component.text(nameOf(target) + "님의 " + grade.displayName() + " 강화석 " + subcommand
                + " 완료. (보유: " + wallet.get(playerId, grade) + "개)", NamedTextColor.GREEN));
    }

    private void handleChest(CommandSender sender, String label, String[] args) {
        if (args.length != 3 && args.length != 4) {
            error(sender, "사용법: /" + label + " 상자 <플레이어> <하급|중급|상급> [개수]");
            return;
        }
        Player target = Bukkit.getPlayerExact(args[1]);
        if (target == null) {
            error(sender, "접속 중인 플레이어를 찾을 수 없습니다: " + args[1]);
            return;
        }
        StoneGrade grade = parseGrade(sender, args[2]);
        Long count = args.length == 4 ? parseAmount(sender, args[3], 1) : Long.valueOf(1);
        if (grade == null || count == null) {
            return;
        }
        if (count > 64 * 36) {
            error(sender, "한 번에 지급할 수 있는 상자는 최대 " + (64 * 36) + "개입니다.");
            return;
        }

        ItemStack chest = itemProvider.create(StoneChestListener.chestIdOf(grade));
        int remaining = count.intValue();
        while (remaining > 0) {
            ItemStack stack = chest.clone();
            int stackSize = Math.min(remaining, stack.getMaxStackSize());
            stack.setAmount(stackSize);
            ItemDelivery.giveOrDrop(target, stack);
            remaining -= stackSize;
        }
        sender.sendMessage(Component.text(target.getName() + "님에게 " + grade.displayName() + " 강화석 상자 "
                + count + "개를 지급했습니다.", NamedTextColor.GREEN));
    }

    private void sendBalances(CommandSender sender, UUID playerId, String owner) {
        sender.sendMessage(Component.text(owner + " 강화석 보유량", NamedTextColor.YELLOW));
        for (StoneGrade grade : StoneGrade.values()) {
            if (!grade.isCurrency()) {
                continue;
            }
            sender.sendMessage(Component.text(" - " + grade.displayName() + ": ", NamedTextColor.GRAY)
                    .append(Component.text(wallet.get(playerId, grade) + "개", grade.color())));
        }
    }

    private void sendUsage(CommandSender sender, String label) {
        sender.sendMessage(Component.text("강화석 관리자 명령어", NamedTextColor.YELLOW));
        sender.sendMessage(Component.text("/" + label + " 확인 <플레이어>", NamedTextColor.GRAY));
        sender.sendMessage(Component.text("/" + label + " 지급|차감|설정 <플레이어> <하급|중급|상급> <수량>", NamedTextColor.GRAY));
        sender.sendMessage(Component.text("/" + label + " 상자 <플레이어> <하급|중급|상급> [개수]", NamedTextColor.GRAY));
    }

    private StoneGrade parseGrade(CommandSender sender, String name) {
        StoneGrade grade = StoneGrade.fromDisplayName(name);
        if (grade == null) {
            error(sender, "강화석 등급은 하급, 중급, 상급 중 하나여야 합니다: " + name);
        }
        return grade;
    }

    @Override
    public List<String> onTabComplete(CommandSender sender, Command command, String alias, String[] args) {
        if (!sender.hasPermission(ADMIN_PERMISSION)) {
            return List.of();
        }
        if (args.length == 1) {
            return filter(ADMIN_SUBCOMMANDS, args[0]);
        }
        if (!ADMIN_SUBCOMMANDS.contains(args[0])) {
            return List.of();
        }
        if (args.length == 2) {
            return onlinePlayerNames(args[1]);
        }
        if (args.length == 3 && !args[0].equals("확인")) {
            return filter(GRADE_NAMES, args[2]);
        }
        return List.of();
    }
}

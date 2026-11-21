package com.brassfield.accessory;

import com.brassfield.accessory.AccessoryKind.Grade;
import com.brassfield.accessory.AccessoryKind.Set;
import com.brassfield.accessory.AccessoryKind.Variant;
import com.brassfield.common.ItemsAdderGuiBackground;
import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.Bukkit;
import org.bukkit.command.Command;
import org.bukkit.command.CommandExecutor;
import org.bukkit.command.CommandSender;
import org.bukkit.command.TabCompleter;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;
import org.jetbrains.annotations.NotNull;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * /장신구 : 장착 창 열기 (G 키 메뉴의 단추와 같음)
 * /장신구 지급 <세트> <종류> <등급> [강화 0~3] [플레이어] : (관리자) 장신구 지급. 세트 · 등급은 영어 id 나 한글 이름
 * /장신구 전체 [등급] [강화] : (관리자) 15종을 한 번에 지급 (아이콘 확인용)
 * /장신구 리롤 : (관리자) 손에 든 장신구의 보조옵션을 다시 굴림
 * /장신구 리롤권 [개수] [플레이어] : (관리자) 보조옵션권 지급
 */
public final class AccessoryCommand implements CommandExecutor, TabCompleter {

    private static final String ADMIN = "brassfield.accessory.admin";

    private final AccessoryManager manager;
    private final ItemsAdderGuiBackground background;

    public AccessoryCommand(AccessoryManager manager, ItemsAdderGuiBackground background) {
        this.manager = manager;
        this.background = background;
    }

    public void open(Player player) {
        new AccessoryGui(manager, background, player).open(background);
    }

    @Override
    public boolean onCommand(@NotNull CommandSender sender, @NotNull Command cmd, @NotNull String label, String @NotNull [] args) {
        if (args.length == 0) {
            if (sender instanceof Player player) {
                open(player);
            } else {
                sender.sendMessage("플레이어만 열 수 있습니다.");
            }
            return true;
        }
        if (!sender.hasPermission(ADMIN)) {
            sender.sendMessage(Component.text("권한이 없습니다.", NamedTextColor.RED));
            return true;
        }
        if (args[0].equals("리롤권")) {
            int amount = 1;
            try {
                amount = args.length > 1 ? Math.max(1, Math.min(64, Integer.parseInt(args[1]))) : 1;
            } catch (NumberFormatException ignored) {
                // 기본 1장
            }
            Player target = args.length > 2 ? Bukkit.getPlayerExact(args[2]) : sender instanceof Player p ? p : null;
            if (target == null) {
                sender.sendMessage(Component.text("플레이어를 찾을 수 없습니다.", NamedTextColor.RED));
                return true;
            }
            target.getInventory().addItem(RerollTicket.create(amount))
                    .values().forEach(left -> target.getWorld().dropItem(target.getLocation(), left));
            sender.sendMessage(Component.text("보조옵션권 " + amount + "장을 지급했습니다.", NamedTextColor.GREEN));
            return true;
        }
        if (args[0].equals("리롤")) {
            if (!(sender instanceof Player player)) {
                return true;
            }
            ItemStack hand = player.getInventory().getItemInMainHand();
            Accessories.Info info = Accessories.read(hand).orElse(null);
            if (info == null) {
                sender.sendMessage(Component.text("장신구를 손에 들고 쓰세요.", NamedTextColor.RED));
                return true;
            }
            player.getInventory().setItemInMainHand(Accessories.create(
                    new Accessories.Info(info.set(), info.variant(), info.grade(), info.level())));
            sender.sendMessage(Component.text("보조옵션을 다시 굴렸습니다.", NamedTextColor.GREEN));
            return true;
        }
        if (args[0].equals("전체")) {
            Grade grade = args.length > 1 ? AccessoryKind.parse(Grade.class, args[1]) : Grade.COMMON;
            int level = args.length > 2 ? parseLevel(args[2]) : 0;
            if (!(sender instanceof Player player) || grade == null || level < 0) {
                sender.sendMessage("사용법: /" + label + " 전체 [등급] [강화 0~3]");
                return true;
            }
            for (Set set : Set.values()) {
                for (Variant variant : Variant.values()) {
                    give(player, new Accessories.Info(set, variant, grade, level));
                }
            }
            return true;
        }
        if (!args[0].equals("지급") || args.length < 4) {
            sender.sendMessage("사용법: /" + label + " 지급 <세트> <종류> <등급> [강화 0~3] [플레이어]");
            return true;
        }
        Set set = AccessoryKind.parse(Set.class, args[1]);
        Variant variant = AccessoryKind.parse(Variant.class, args[2]);
        Grade grade = AccessoryKind.parse(Grade.class, args[3]);
        int level = args.length > 4 ? parseLevel(args[4]) : 0;
        Player target = args.length > 5 ? Bukkit.getPlayerExact(args[5]) : sender instanceof Player p ? p : null;
        if (set == null || variant == null || grade == null || level < 0 || target == null) {
            sender.sendMessage(Component.text("세트 · 종류 · 등급 · 강화 · 플레이어를 확인하세요.", NamedTextColor.RED));
            return true;
        }
        give(target, new Accessories.Info(set, variant, grade, level));
        sender.sendMessage(Component.text("장신구를 지급했습니다.", NamedTextColor.GREEN));
        return true;
    }

    private static void give(Player player, Accessories.Info info) {
        player.getInventory().addItem(Accessories.create(info))
                .values().forEach(left -> player.getWorld().dropItem(player.getLocation(), left));
    }

    private static int parseLevel(String text) {
        try {
            int level = Integer.parseInt(text);
            return level >= 0 && level <= AccessoryKind.MAX_LEVEL ? level : -1;
        } catch (NumberFormatException exception) {
            return -1;
        }
    }

    @Override
    public List<String> onTabComplete(@NotNull CommandSender sender, @NotNull Command cmd, @NotNull String label, String @NotNull [] args) {
        if (!sender.hasPermission(ADMIN)) {
            return List.of();
        }
        List<String> options = new ArrayList<>();
        if (args.length == 1) {
            options.addAll(List.of("지급", "전체", "리롤", "리롤권"));
        } else if (args[0].equals("지급")) {
            switch (args.length) {
                case 2 -> Arrays.stream(Set.values()).forEach(s -> options.add(s.id()));
                case 3 -> Arrays.stream(Variant.values()).forEach(v -> options.add(v.id()));
                case 4 -> Arrays.stream(Grade.values()).forEach(g -> options.add(g.id()));
                case 5 -> options.addAll(List.of("0", "1", "2", "3"));
                case 6 -> Bukkit.getOnlinePlayers().forEach(p -> options.add(p.getName()));
                default -> {
                }
            }
        } else if (args[0].equals("전체")) {
            if (args.length == 2) {
                Arrays.stream(Grade.values()).forEach(g -> options.add(g.id()));
            } else if (args.length == 3) {
                options.addAll(List.of("0", "1", "2", "3"));
            }
        }
        String last = args[args.length - 1];
        return options.stream().filter(o -> o.startsWith(last)).toList();
    }
}

package com.brassfield.shop;

import com.brassfield.common.CommandSupport;
import org.bukkit.command.Command;
import org.bukkit.command.CommandExecutor;
import org.bukkit.command.CommandSender;
import org.bukkit.entity.Player;

/**
 * /상점 (관리자): NPC 없이 강화석 상점을 연다. 플레이어는 강화석 상인 NPC를 우클릭해 연다.
 */
public final class StoneShopCommand implements CommandExecutor {

    public static final String ADMIN_PERMISSION = "brassfield.shop.admin";

    private final StoneShop shop;

    public StoneShopCommand(StoneShop shop) {
        this.shop = shop;
    }

    @Override
    public boolean onCommand(CommandSender sender, Command command, String label, String[] args) {
        if (!(sender instanceof Player player)) {
            sender.sendMessage("플레이어만 사용할 수 있는 명령어예요.");
            return true;
        }
        if (!player.hasPermission(ADMIN_PERMISSION)) {
            CommandSupport.error(player, "권한이 없습니다. 강화석 상인 NPC를 찾아가세요.");
            return true;
        }
        shop.open(player);
        return true;
    }
}

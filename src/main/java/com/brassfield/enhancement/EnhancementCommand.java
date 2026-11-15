package com.brassfield.enhancement;

import com.brassfield.common.CommandSupport;
import com.brassfield.common.ItemsAdderGuiBackground;
import com.brassfield.stone.StoneWallet;
import org.bukkit.command.Command;
import org.bukkit.command.CommandExecutor;
import org.bukkit.command.CommandSender;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;

/**
 * 강화 GUI를 여는 곳. 플레이어는 마을의 증폭 공작대(거래 기계)를 우클릭해 열고,
 * /강화 명령어는 관리자 테스트용이다.
 */
public final class EnhancementCommand implements CommandExecutor {

    /**
     * 강화 GUI를 여는 거래 기계 (ItemsAdder 가구 ID)
     */
    public static final String MACHINE_ID = "rustport:enhancement_machine";
    public static final String ADMIN_PERMISSION = "brassfield.enhance.admin";

    private final ItemsAdderGuiBackground guiBackground;
    private final StoneWallet wallet;

    public EnhancementCommand(ItemsAdderGuiBackground guiBackground, StoneWallet wallet) {
        this.guiBackground = guiBackground;
        this.wallet = wallet;
    }

    @Override
    public boolean onCommand(CommandSender sender, Command command, String label, String[] args) {
        if (!(sender instanceof Player player)) {
            sender.sendMessage("플레이어만 사용할 수 있는 명령어예요.");
            return true;
        }
        if (!player.hasPermission(ADMIN_PERMISSION)) {
            CommandSupport.error(player, "마을의 증폭 공작대를 찾아가세요.");
            return true;
        }

        openGui(player, null);
        return true;
    }

    public void openGui(Player player, ItemStack targetItem) {
        new EnhancementGui(targetItem, guiBackground, wallet, player.getUniqueId()).open(player);
    }
}

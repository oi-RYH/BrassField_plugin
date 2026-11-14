package com.brassfield.enhancement;

import com.brassfield.common.ItemsAdderGuiBackground;
import com.brassfield.stone.StoneWallet;
import org.bukkit.command.Command;
import org.bukkit.command.CommandExecutor;
import org.bukkit.command.CommandSender;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;

/**
 * /강화 명령어. 강화 GUI를 여는 곳은 여기 한 군데로 모은다.
 */
public final class EnhancementCommand implements CommandExecutor {

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

        openGui(player, null);
        return true;
    }

    public void openGui(Player player, ItemStack targetItem) {
        new EnhancementGui(targetItem, guiBackground, wallet, player.getUniqueId()).open(player);
    }
}

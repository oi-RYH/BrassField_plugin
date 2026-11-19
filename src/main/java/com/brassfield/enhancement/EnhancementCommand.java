package com.brassfield.enhancement;

import com.brassfield.common.CommandSupport;
import com.brassfield.common.ItemDelivery;
import com.brassfield.common.ItemsAdderGuiBackground;
import com.brassfield.stone.StoneWallet;
import org.bukkit.command.Command;
import org.bukkit.command.CommandExecutor;
import org.bukkit.command.CommandSender;
import org.bukkit.entity.Player;

/**
 * 강화 GUI를 여는 곳. 플레이어는 마을의 증폭 공작대(거래 기계)를 우클릭해 열고,
 * /강화 명령어는 관리자 테스트용이다 (/강화 무기|방어구 [단계] = 해당 단계 장비 지급).
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

        if (args.length >= 1 && (args[0].equals("무기") || args[0].equals("방어구"))) {
            int level;
            try {
                level = args.length >= 2 ? Integer.parseInt(args[1]) : 0;
            } catch (NumberFormatException exception) {
                CommandSupport.error(player, "사용법: /강화 <무기|방어구> [단계]");
                return true;
            }
            if (args[0].equals("무기")) {
                ItemDelivery.giveOrDrop(player, EnhanceTracks.weapon().buildItem(level));
            } else {
                for (ArmorTrack.Part part : ArmorTrack.Part.values()) {
                    ItemDelivery.giveOrDrop(player, EnhanceTracks.armor(part).buildItem(level));
                }
            }
            player.sendMessage("§a+" + level + " " + args[0] + "를 지급했습니다.");
            return true;
        }

        openGui(player);
        return true;
    }

    public void openGui(Player player) {
        openGui(player, -1);
    }

    /** selectedSlot = 처음부터 골라 둘 플레이어 가방 칸 (강화 후 다시 열 때), 없으면 -1 */
    public void openGui(Player player, int selectedSlot) {
        new EnhancementGui(selectedSlot, guiBackground, wallet, player.getUniqueId()).open(player);
    }
}

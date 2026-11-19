package com.brassfield.enhancement;

import com.brassfield.common.CommandSupport;
import com.brassfield.common.ItemDelivery;
import com.brassfield.common.ItemsAdderGuiBackground;
import com.brassfield.stone.StoneWallet;
import org.bukkit.command.Command;
import org.bukkit.command.CommandExecutor;
import org.bukkit.command.CommandSender;
import org.bukkit.Location;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Player;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * 강화 GUI를 여는 곳. 플레이어는 마을의 강화 모루(가구)를 우클릭해 열고,
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
    private static final double ANVIL_RANGE = 8;
    private final Map<UUID, Location> anvils = new HashMap<>();

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

        anvils.remove(player.getUniqueId());                           // 명령어로 열면 모루 없이 (앞에 띄우는 연출)
        openGui(player);
        return true;
    }

    public void openGui(Player player) {
        openGui(player, -1);
    }

    /** 모루 가구를 눌러 열 때: 그 모루 위치를 기억해 강화 연출을 모루 위에서 한다 */
    public void openAtAnvil(Player player, Entity anvil) {
        anvils.put(player.getUniqueId(), anvil.getLocation());
        openGui(player, -1);
    }

    /** 이 플레이어가 마지막으로 연 모루 위치 (같은 월드 · 가까이 있을 때만), 없으면 null — /강화 로 연 경우 등 */
    public Location anvilOf(Player player) {
        Location anvil = anvils.get(player.getUniqueId());
        if (anvil == null || anvil.getWorld() != player.getWorld()
                || anvil.distanceSquared(player.getLocation()) > ANVIL_RANGE * ANVIL_RANGE) {
            return null;
        }
        return anvil.clone();
    }

    public void forget(Player player) {
        anvils.remove(player.getUniqueId());
    }

    /** selectedSlot = 처음부터 골라 둘 플레이어 가방 칸 (강화 후 다시 열 때), 없으면 -1 */
    public void openGui(Player player, int selectedSlot) {
        new EnhancementGui(selectedSlot, guiBackground, wallet, player.getUniqueId()).open(player);
    }
}

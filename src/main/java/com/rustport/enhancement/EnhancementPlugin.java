package com.rustport.enhancement;

import org.bukkit.Material;
import org.bukkit.command.Command;
import org.bukkit.command.CommandExecutor;
import org.bukkit.command.CommandSender;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;
import org.bukkit.plugin.java.JavaPlugin;

import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;

import java.util.Objects;

public class EnhancementPlugin extends JavaPlugin implements CommandExecutor {

    private EnhancementAnimation animation;

    @Override
    public void onEnable() {
        EnhancementItem.init(this);
        getLogger().info("강화 플러그인이 로드됐습니다!");

        Objects.requireNonNull(getCommand("강화"), "plugin.yml에 강화 명령어가 없습니다.").setExecutor(this);

        EnhancementService enhancementService = new EnhancementService();
        animation = new EnhancementAnimation(this);
        getServer().getPluginManager().registerEvents(
                new EnhancementGuiListener(this, enhancementService, animation),
                this
        );
    }

    @Override
    public void onDisable() {
        if (animation != null) {
            animation.shutdown();
        }
        getLogger().info("강화 플러그인이 종료됩니다.");
    }

    @Override
    public boolean onCommand(CommandSender sender, Command command, String label, String[] args) {
        if (!(sender instanceof Player player)) {
            sender.sendMessage("플레이어만 사용할 수 있는 명령어예요.");
            return true;
        }

        ItemStack itemInHand = player.getInventory().getItemInMainHand();

        if (itemInHand.getType() == Material.AIR) {
            player.sendMessage(Component.text("손에 강화할 아이템을 들어주세요.", NamedTextColor.RED));
            return true;
        }

        if (!EnhancementItem.isEnhanceable(itemInHand)) {
            player.sendMessage(Component.text("나무, 돌, 철, 다이아몬드 검만 강화할 수 있습니다.", NamedTextColor.RED));
            return true;
        }

        // 강화가 끝나면 손에 든 아이템을 비움 (GUI 안으로 옮긴 셈)
        player.getInventory().setItemInMainHand(null);
        openEnhancementGui(player, itemInHand.clone());

        return true;
    }

    void openEnhancementGui(Player player, ItemStack targetItem) {
        player.openInventory(new EnhancementGui(targetItem).getInventory());
    }
}

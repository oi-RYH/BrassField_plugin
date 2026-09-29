package com.rustport.enhancement;

import org.bukkit.command.Command;
import org.bukkit.command.CommandExecutor;
import org.bukkit.command.CommandSender;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;
import org.bukkit.plugin.java.JavaPlugin;

import java.util.Objects;

public class EnhancementPlugin extends JavaPlugin implements CommandExecutor {

    private EnhancementAnimation animation;
    private ItemsAdderGuiBackground guiBackground;

    @Override
    public void onEnable() {
        EnhancementItem.init(this);
        guiBackground = new ItemsAdderGuiBackground(this);
        if (!guiBackground.isAvailable()) {
            getLogger().warning("ItemsAdder 배경 GUI를 사용할 수 없어 기본 배경으로 대체합니다.");
        }
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

        openEnhancementGui(player, null);

        return true;
    }

    void openEnhancementGui(Player player, ItemStack targetItem) {
        new EnhancementGui(targetItem, guiBackground).open(player);
    }
}

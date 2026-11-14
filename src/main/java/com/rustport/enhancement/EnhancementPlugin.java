package com.rustport.enhancement;

import org.bukkit.command.Command;
import org.bukkit.command.CommandExecutor;
import org.bukkit.command.CommandSender;
import org.bukkit.command.PluginCommand;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;
import org.bukkit.plugin.java.JavaPlugin;

import java.util.Objects;

public class EnhancementPlugin extends JavaPlugin implements CommandExecutor {

    private EnhancementAnimation animation;
    private ItemsAdderGuiBackground guiBackground;
    private StoneWallet stoneWallet;

    @Override
    public void onEnable() {
        EnhancementItem.init(this);
        guiBackground = new ItemsAdderGuiBackground(this);
        if (!guiBackground.isAvailable()) {
            getLogger().warning("ItemsAdder 배경 GUI를 사용할 수 없어 기본 배경으로 대체합니다.");
        }
        getLogger().info("강화 플러그인이 로드됐습니다!");

        stoneWallet = new StoneWallet(new YamlStoneStorage(this), getLogger());
        ItemsAdderItemProvider itemProvider = new ItemsAdderItemProvider(this);

        Objects.requireNonNull(getCommand("강화"), "plugin.yml에 강화 명령어가 없습니다.").setExecutor(this);
        StoneCommand stoneCommand = new StoneCommand(stoneWallet, itemProvider);
        PluginCommand stoneCommandEntry = Objects.requireNonNull(getCommand("강화석"), "plugin.yml에 강화석 명령어가 없습니다.");
        stoneCommandEntry.setExecutor(stoneCommand);
        stoneCommandEntry.setTabCompleter(stoneCommand);

        EnhancementService enhancementService = new EnhancementService();
        animation = new EnhancementAnimation(this);
        getServer().getPluginManager().registerEvents(
                new EnhancementGuiListener(this, enhancementService, animation, stoneWallet),
                this
        );
        getServer().getPluginManager().registerEvents(new StoneChestListener(itemProvider, stoneWallet), this);
        getServer().getPluginManager().registerEvents(new StarterKitListener(), this);
    }

    @Override
    public void onDisable() {
        // 서버 종료 시에는 플러그인이 먼저 꺼진 뒤 플레이어가 내보내져 창 닫기 이벤트를 처리할 수 없다.
        // 그래서 여기서 열린 강화 창의 아이템을 직접 돌려주고 창을 닫는다.
        for (Player player : getServer().getOnlinePlayers()) {
            if (player.getOpenInventory().getTopInventory().getHolder() instanceof EnhancementGui gui) {
                gui.returnItemsTo(player);
                player.closeInventory();
            }
        }
        if (animation != null) {
            animation.shutdown();
        }
        if (stoneWallet != null) {
            stoneWallet.shutdown();
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
        new EnhancementGui(targetItem, guiBackground, stoneWallet, player.getUniqueId()).open(player);
    }
}

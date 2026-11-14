package com.brassfield;

import com.brassfield.common.ItemsAdderGuiBackground;
import com.brassfield.common.ItemsAdderItemProvider;
import com.brassfield.enhancement.EnhancementAnimation;
import com.brassfield.enhancement.EnhancementCommand;
import com.brassfield.enhancement.EnhancementGui;
import com.brassfield.enhancement.EnhancementGuiListener;
import com.brassfield.enhancement.EnhancementItem;
import com.brassfield.enhancement.EnhancementService;
import com.brassfield.enhancement.StarterKitListener;
import com.brassfield.stone.StoneChestListener;
import com.brassfield.stone.StoneCommand;
import com.brassfield.stone.StoneWallet;
import com.brassfield.stone.YamlStoneStorage;
import org.bukkit.command.PluginCommand;
import org.bukkit.entity.Player;
import org.bukkit.plugin.PluginManager;
import org.bukkit.plugin.java.JavaPlugin;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Objects;

/**
 * BrassField 서버 플러그인. 각 모듈(common·enhancement·stone, 이후 economy 등)을 만들고 연결만 한다.
 */
public class BrassFieldPlugin extends JavaPlugin {

    private static final String LEGACY_PLUGIN_NAME = "RustportEnhancement";

    private EnhancementAnimation animation;
    private StoneWallet stoneWallet;

    @Override
    public void onEnable() {
        migrateLegacyStoneData();

        ItemsAdderItemProvider itemProvider = new ItemsAdderItemProvider(this);
        ItemsAdderGuiBackground guiBackground = new ItemsAdderGuiBackground(this);
        if (!guiBackground.isAvailable()) {
            getLogger().warning("ItemsAdder 배경 GUI를 사용할 수 없어 기본 배경으로 대체합니다.");
        }

        // 강화석
        stoneWallet = new StoneWallet(new YamlStoneStorage(this), getLogger());
        StoneCommand stoneCommand = new StoneCommand(stoneWallet, itemProvider);
        PluginCommand stoneCommandEntry = command("강화석");
        stoneCommandEntry.setExecutor(stoneCommand);
        stoneCommandEntry.setTabCompleter(stoneCommand);

        // 강화
        EnhancementItem.init(this);
        EnhancementCommand enhancementCommand = new EnhancementCommand(guiBackground, stoneWallet);
        command("강화").setExecutor(enhancementCommand);
        animation = new EnhancementAnimation(this);

        PluginManager pluginManager = getServer().getPluginManager();
        pluginManager.registerEvents(new EnhancementGuiListener(
                this, enhancementCommand, new EnhancementService(), animation, stoneWallet
        ), this);
        pluginManager.registerEvents(new StoneChestListener(itemProvider, stoneWallet), this);
        pluginManager.registerEvents(new StarterKitListener(), this);

        getLogger().info("BrassField 플러그인이 로드됐습니다!");
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
        getLogger().info("BrassField 플러그인이 종료됩니다.");
    }

    private PluginCommand command(String name) {
        return Objects.requireNonNull(getCommand(name), "plugin.yml에 " + name + " 명령어가 없습니다.");
    }

    /**
     * 플러그인 이름이 RustportEnhancement → BrassField로 바뀌면서 데이터 폴더도 바뀌었다.
     * 새 폴더에 stones.yml이 없으면 예전 폴더의 파일을 한 번 복사해 온다.
     */
    private void migrateLegacyStoneData() {
        Path target = getDataFolder().toPath().resolve("stones.yml");
        Path legacy = getDataFolder().toPath().resolveSibling(LEGACY_PLUGIN_NAME).resolve("stones.yml");
        if (Files.exists(target) || !Files.exists(legacy)) {
            return;
        }
        try {
            Files.createDirectories(target.getParent());
            Files.copy(legacy, target);
            getLogger().info("예전 데이터 폴더의 stones.yml을 가져왔습니다: " + legacy);
        } catch (IOException exception) {
            getLogger().severe("예전 stones.yml을 가져오지 못했습니다: " + exception);
        }
    }
}

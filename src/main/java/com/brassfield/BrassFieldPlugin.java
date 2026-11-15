package com.brassfield;

import com.brassfield.common.BalanceBook;
import com.brassfield.common.FurnitureInteractions;
import com.brassfield.common.ItemsAdderGuiBackground;
import com.brassfield.common.ItemsAdderItemProvider;
import com.brassfield.common.MachineMarkers;
import com.brassfield.common.YamlBalanceStorage;
import com.brassfield.economy.GoldCommand;
import com.brassfield.economy.GoldWallet;
import com.brassfield.enhancement.EnhancementAnimation;
import com.brassfield.enhancement.EnhancementCommand;
import com.brassfield.enhancement.EnhancementGui;
import com.brassfield.enhancement.EnhancementGuiListener;
import com.brassfield.enhancement.EnhancementItem;
import com.brassfield.enhancement.EnhancementService;
import com.brassfield.enhancement.StarterKitListener;
import com.brassfield.hud.CurrencySidebar;
import com.brassfield.market.CropMarket;
import com.brassfield.market.CropPrices;
import com.brassfield.market.CropSellGui;
import com.brassfield.market.CropSellListener;
import com.brassfield.shop.StoneShop;
import com.brassfield.shop.StoneShopCommand;
import com.brassfield.shop.StoneShopListener;
import com.brassfield.shop.StoneShopPrices;
import com.brassfield.shop.citizens.CitizensShopHook;
import com.brassfield.stone.StoneChestListener;
import com.brassfield.stone.StoneCommand;
import com.brassfield.stone.StoneWallet;
import org.bukkit.command.PluginCommand;
import org.bukkit.entity.Player;
import org.bukkit.plugin.PluginManager;
import org.bukkit.plugin.java.JavaPlugin;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Objects;

/**
 * BrassField 서버 플러그인. 각 모듈(common·enhancement·stone·economy·shop·hud)을 만들고 연결만 한다.
 */
public class BrassFieldPlugin extends JavaPlugin {

    private static final String LEGACY_PLUGIN_NAME = "RustportEnhancement";

    private EnhancementAnimation animation;
    private BalanceBook stoneBook;
    private BalanceBook goldBook;
    private BalanceBook cropSalesBook;
    private boolean citizensHooked;
    private CurrencySidebar currencySidebar;
    private MachineMarkers machineMarkers;

    @Override
    public void onEnable() {
        migrateLegacyStoneData();
        saveDefaultConfig();
        // 업데이트로 새로 생긴 설정 항목(예: crop-shop)을 기존 config.yml에 채워 넣는다
        getConfig().options().copyDefaults(true);
        saveConfig();

        ItemsAdderItemProvider itemProvider = new ItemsAdderItemProvider(this);
        ItemsAdderGuiBackground guiBackground = new ItemsAdderGuiBackground(this);
        if (!guiBackground.isAvailable()) {
            getLogger().warning("ItemsAdder 배경 GUI를 사용할 수 없어 기본 배경으로 대체합니다.");
        }

        // 강화석
        stoneBook = new BalanceBook(new YamlBalanceStorage(this, "stones.yml"), getLogger(), "Stone");
        StoneWallet stoneWallet = new StoneWallet(stoneBook);
        StoneCommand stoneCommand = new StoneCommand(stoneWallet, itemProvider);
        PluginCommand stoneCommandEntry = command("강화석");
        stoneCommandEntry.setExecutor(stoneCommand);
        stoneCommandEntry.setTabCompleter(stoneCommand);

        // 골드
        goldBook = new BalanceBook(new YamlBalanceStorage(this, "gold.yml"), getLogger(), "Gold");
        GoldWallet goldWallet = new GoldWallet(goldBook);
        GoldCommand goldCommand = new GoldCommand(goldWallet);
        PluginCommand goldCommandEntry = command("골드");
        goldCommandEntry.setExecutor(goldCommand);
        goldCommandEntry.setTabCompleter(goldCommand);

        // 강화석 상점
        StoneShop stoneShop = new StoneShop(
                goldWallet, stoneWallet, StoneShopPrices.load(getConfig(), getLogger()), itemProvider
        );
        command("상점").setExecutor(new StoneShopCommand(stoneShop));

        // 거래 기계 (ItemsAdder 가구)
        FurnitureInteractions machines = new FurnitureInteractions(this);
        machines.onInteract(StoneShop.MACHINE_ID, stoneShop::open);
        // 기계 위 빨간 표시: 기계 바닥에서 표시 중심까지 높이(블록)
        machineMarkers = new MachineMarkers(this, itemProvider);
        machineMarkers.register(StoneShop.MACHINE_ID, 3.65);   // 자판기는 1.5배(3블록 높이)

        // 작물 매입 (판매 기록: 플레이어별·작물별 판매 개수와 받은 골드)
        cropSalesBook = new BalanceBook(new YamlBalanceStorage(this, "crop_sales.yml"), getLogger(), "CropSales");
        CropMarket cropMarket = new CropMarket(goldWallet, CropPrices.load(getConfig(), getLogger()), itemProvider, cropSalesBook);
        machines.onInteract(CropMarket.MACHINE_ID, cropMarket::open);
        machineMarkers.register(CropMarket.MACHINE_ID, 3.65);   // 거래기는 1.5배(3블록 높이)

        // 강화
        EnhancementItem.init(this);
        EnhancementCommand enhancementCommand = new EnhancementCommand(guiBackground, stoneWallet);
        command("강화").setExecutor(enhancementCommand);
        animation = new EnhancementAnimation(this);
        machines.onInteract(EnhancementCommand.MACHINE_ID, player -> enhancementCommand.openGui(player, null));
        machineMarkers.register(EnhancementCommand.MACHINE_ID, 2.6);

        PluginManager pluginManager = getServer().getPluginManager();
        pluginManager.registerEvents(new EnhancementGuiListener(
                this, enhancementCommand, new EnhancementService(), animation, stoneWallet
        ), this);
        pluginManager.registerEvents(new StoneChestListener(itemProvider, stoneWallet), this);
        pluginManager.registerEvents(new StarterKitListener(), this);
        pluginManager.registerEvents(new StoneShopListener(stoneShop), this);
        pluginManager.registerEvents(new CropSellListener(this), this);
        machines.start();
        machineMarkers.start();

        // 재화 사이드바
        currencySidebar = new CurrencySidebar(this, goldWallet, stoneWallet, guiBackground);
        currencySidebar.start();

        if (pluginManager.isPluginEnabled("Citizens")) {
            CitizensShopHook.register(this, stoneShop);
            citizensHooked = true;
        } else {
            getLogger().warning("Citizens가 없어 강화석 상인 NPC를 쓸 수 없습니다. (/상점 으로만 열 수 있음)");
        }

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
            if (player.getOpenInventory().getTopInventory().getHolder() instanceof CropSellGui gui) {
                gui.returnItemsTo(player);
                player.closeInventory();
            }
        }
        if (animation != null) {
            animation.shutdown();
        }
        if (currencySidebar != null) {
            currencySidebar.stop();
        }
        if (machineMarkers != null) {
            machineMarkers.stop();
        }
        if (citizensHooked) {
            CitizensShopHook.unregister();
        }
        if (stoneBook != null) {
            stoneBook.shutdown();
        }
        if (goldBook != null) {
            goldBook.shutdown();
        }
        if (cropSalesBook != null) {
            cropSalesBook.shutdown();
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

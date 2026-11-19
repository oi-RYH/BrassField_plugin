package com.brassfield;

import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;

import com.brassfield.common.BalanceBook;
import com.brassfield.common.FurnitureInteractions;
import com.brassfield.common.ItemsAdderGuiBackground;
import com.brassfield.common.ItemsAdderItemProvider;
import com.brassfield.common.MachineMarkers;
import com.brassfield.common.YamlBalanceStorage;
import com.brassfield.cooking.CookingListener;
import com.brassfield.cooking.CookingMachines;
import com.brassfield.cooking.CookingRecipes;
import com.brassfield.cooking.CookingStation;
import com.brassfield.cooking.FoodBuffs;
import com.brassfield.cooking.MortarCrafting;
import com.brassfield.cooking.PlacedFood;
import com.brassfield.economy.GoldCommand;
import com.brassfield.economy.GoldWallet;
import com.brassfield.enhancement.EnhancementAnimation;
import com.brassfield.enhancement.EnhancementCommand;
import com.brassfield.enhancement.EnhancementGui;
import com.brassfield.enhancement.EnhancementGuiListener;
import com.brassfield.enhancement.EnhanceTracks;
import com.brassfield.enhancement.EnhancementService;
import com.brassfield.enhancement.StarterKitListener;
import com.brassfield.hud.CurrencySidebar;
import com.brassfield.market.CropMarket;
import com.brassfield.market.CropPrices;
import com.brassfield.market.CropSellGui;
import com.brassfield.market.CropSellListener;
import com.brassfield.market.DeliveryRobots;
import com.brassfield.market.FoodMarket;
import com.brassfield.market.FoodSellGui;
import com.brassfield.market.FoodSellListener;
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
 * BrassField 서버 플러그인. 각 모듈(common·enhancement·stone·economy·shop·market·cooking·hud)을 만들고 연결만 한다.
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
    private CookingMachines cookingMachines;
    private BalanceBook foodSalesBook;
    private FoodMarket foodMarket;
    private DeliveryRobots deliveryRobots;

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
                goldWallet, stoneWallet, StoneShopPrices.load(getConfig(), getLogger()), itemProvider, guiBackground
        );
        command("상점").setExecutor(new StoneShopCommand(stoneShop));

        // 거래 기계 (ItemsAdder 가구). 빨간 표시는 마을 공용 기계에만 붙인다
        FurnitureInteractions machines = new FurnitureInteractions(this);
        machines.onInteract(StoneShop.MACHINE_ID, stoneShop::open);
        // 기계 위 빨간 표시: 기계 바닥에서 표시 중심까지 높이(블록)
        machineMarkers = new MachineMarkers(this, itemProvider);
        machineMarkers.register(StoneShop.MACHINE_ID, 3.65);   // 자판기는 1.5배(3블록 높이)

        // 작물 매입 (판매 기록: 플레이어별·작물별 판매 개수와 받은 골드)
        cropSalesBook = new BalanceBook(new YamlBalanceStorage(this, "crop_sales.yml"), getLogger(), "CropSales");
        CropMarket cropMarket = new CropMarket(goldWallet, CropPrices.load(getConfig(), getLogger()), itemProvider, cropSalesBook,
                guiBackground);
        machines.onInteract(CropMarket.MACHINE_ID, cropMarket::open);
        machineMarkers.register(CropMarket.MACHINE_ID, 3.65);   // 거래기는 1.5배(3블록 높이)

        // 요리 납품 로봇 DL-7 (마을 공용): 요리를 골드로 산다. 서버 전체 판매량으로 4시간마다 ±10% 가격 변동
        foodSalesBook = new BalanceBook(new YamlBalanceStorage(this, "food_sales.yml"), getLogger(), "FoodSales");
        foodMarket = FoodMarket.load(this, getConfig(), goldWallet, itemProvider, guiBackground, foodSalesBook, getLogger());
        if (foodMarket != null) {
            deliveryRobots = new DeliveryRobots(this, itemProvider, FoodMarket.MACHINE_ID);
            foodMarket.robots(deliveryRobots);
            machines.onInteractAt(FoodMarket.MACHINE_ID, foodMarket::open);
            machineMarkers.register(FoodMarket.MACHINE_ID, 2.75);
        }
        FoodMarket priceMarket = foodMarket;                         // /요리가격: DL-7 납품 단가표와 오늘의 주문 (창에서 뺀 대신)
        command("요리가격").setExecutor((sender, cmd, label, args) -> {
            if (priceMarket == null) {
                sender.sendMessage(Component.text("요리 납품(DL-7)이 꺼져 있습니다.", NamedTextColor.RED));
            } else {
                priceMarket.sendPriceList(sender);
            }
            return true;
        });

        // 요리 기기 7종 (조리대 + 보조 도구 6, 개인 기기: 누구나 설치·회수, 빨간 표시 없음. 기기마다 조리칸 하나, 실제 시간 기준으로 익음)
        cookingMachines = new CookingMachines(this, CookingRecipes.loadStations(getConfig(), itemProvider, getLogger()), itemProvider,
                guiBackground);
        for (CookingStation station : cookingMachines.stations()) {
            machines.onInteractAt(station.furnitureId(), (player, furniture) -> cookingMachines.open(player, furniture, station));
            machines.onBreak(station.furnitureId(), cookingMachines::destroy);
            machines.personal(station.furnitureId());
        }

        // 강화
        EnhanceTracks.init(this);
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
        pluginManager.registerEvents(new com.brassfield.enhancement.ArmorDamageListener(), this);
        pluginManager.registerEvents(new StoneShopListener(stoneShop), this);
        pluginManager.registerEvents(new CropSellListener(this), this);
        pluginManager.registerEvents(new FoodSellListener(this), this);
        pluginManager.registerEvents(new CookingListener(this), this);
        // 절구: 제작 칸에서 쓰는 도구 (절구는 남고 재료만 쓴다)
        pluginManager.registerEvents(new MortarCrafting(this, CookingRecipes.loadMortar(getConfig(), itemProvider, getLogger()), itemProvider), this);
        // 요리 놓기: 웅크려 우클릭으로 블록 위에 3D 요리를 놓고, 우클릭으로 먹고, 웅크려 우클릭으로 집는다
        // 2단계 요리 버프: 먹으면 이로운 효과 하나가 무작위로 붙는다
        FoodBuffs foodBuffs = FoodBuffs.load(getConfig(), itemProvider, getLogger());
        if (foodBuffs != null) {
            pluginManager.registerEvents(foodBuffs, this);
        }
        PlacedFood placedFood = PlacedFood.load(this, getConfig(), itemProvider, foodBuffs, getLogger());
        if (placedFood != null) {
            pluginManager.registerEvents(placedFood, this);
        }
        machines.start();
        cookingMachines.start();
        machineMarkers.start();
        if (foodMarket != null) {
            foodMarket.start();
            deliveryRobots.start();
        }

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
            if (player.getOpenInventory().getTopInventory().getHolder() instanceof FoodSellGui gui) {
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
        if (cookingMachines != null) {
            cookingMachines.stop();
        }
        if (foodMarket != null) {
            foodMarket.stop();
        }
        if (deliveryRobots != null) {
            deliveryRobots.stop();
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
        if (foodSalesBook != null) {
            foodSalesBook.shutdown();
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

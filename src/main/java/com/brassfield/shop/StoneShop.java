package com.brassfield.shop;

import com.brassfield.common.CommandSupport;
import com.brassfield.common.ItemsAdderGuiBackground;
import com.brassfield.common.ItemsAdderItemProvider;
import com.brassfield.economy.GoldWallet;
import com.brassfield.stone.StoneGrade;
import com.brassfield.stone.StoneWallet;
import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.Sound;
import org.bukkit.entity.Player;

import java.util.UUID;

/**
 * 강화석 상점: 골드를 내고 강화석을 산다. 골드와 강화석은 각 모듈의 공개 API(GoldWallet, StoneWallet)로만 다룬다.
 */
public final class StoneShop {

    /**
     * 강화석 상점을 여는 거래 기계 (ItemsAdder 가구 ID)
     */
    public static final String MACHINE_ID = "rustport:stone_vending_machine";

    private final GoldWallet goldWallet;
    private final StoneWallet stoneWallet;
    private final StoneShopPrices prices;
    private final ItemsAdderItemProvider itemProvider;
    private final ItemsAdderGuiBackground guiBackground;

    public StoneShop(GoldWallet goldWallet, StoneWallet stoneWallet, StoneShopPrices prices,
                     ItemsAdderItemProvider itemProvider, ItemsAdderGuiBackground guiBackground) {
        this.goldWallet = goldWallet;
        this.stoneWallet = stoneWallet;
        this.prices = prices;
        this.itemProvider = itemProvider;
        this.guiBackground = guiBackground;
    }

    public void open(Player player) {
        new StoneShopGui(this, player.getUniqueId()).open(player);
    }

    void purchase(Player player, StoneGrade grade, int quantity) {
        UUID playerId = player.getUniqueId();
        long total = Math.multiplyExact(priceOf(grade), quantity);
        if (!goldWallet.withdraw(playerId, total)) {
            player.sendMessage(Component.text("골드가 부족합니다. (필요: " + CommandSupport.formatNumber(total)
                    + "골드, 보유: " + CommandSupport.formatNumber(goldWallet.get(playerId)) + "골드)", NamedTextColor.RED));
            player.playSound(player.getLocation(), Sound.ENTITY_VILLAGER_NO, 0.8f, 1.0f);
            return;
        }

        stoneWallet.deposit(playerId, grade, quantity);
        player.playSound(player.getLocation(), Sound.ENTITY_EXPERIENCE_ORB_PICKUP, 0.8f, 1.2f);
        player.sendMessage(Component.text(grade.displayName() + " 강화석 " + quantity + "개를 구매했습니다. ", NamedTextColor.GREEN)
                .append(Component.text("(-" + CommandSupport.formatNumber(total) + "골드)", NamedTextColor.GRAY)));
    }

    long priceOf(StoneGrade grade) {
        return prices.priceOf(grade);
    }

    long goldOf(UUID playerId) {
        return goldWallet.get(playerId);
    }

    long stonesOf(UUID playerId, StoneGrade grade) {
        return stoneWallet.get(playerId, grade);
    }

    ItemsAdderItemProvider itemProvider() {
        return itemProvider;
    }

    ItemsAdderGuiBackground guiBackground() {
        return guiBackground;
    }
}

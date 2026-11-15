package com.brassfield.market;

import com.brassfield.common.BalanceBook;
import com.brassfield.common.CommandSupport;
import com.brassfield.common.ItemDelivery;
import com.brassfield.common.ItemsAdderItemProvider;
import com.brassfield.economy.GoldWallet;
import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.Sound;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * 종자·작물 거래: 작물 수확물을 골드로 사고(매입), 씨앗을 골드로 판다. 골드는 경제 모듈의 공개 API(GoldWallet)로만 다룬다.
 * 거래 기록(플레이어별·작물별 판매 개수와 받은 골드, 씨앗 구매 개수와 쓴 골드)을 남겨,
 * 나중에 물가 안전장치가 필요한지 판단하는 데 쓴다.
 */
public final class CropMarket {

    /**
     * 종자·작물 거래 GUI를 여는 거래 기계 (ItemsAdder 가구 ID)
     */
    public static final String MACHINE_ID = "rustport:crop_buyer";
    private static final String GOLD_RECORD = "_gold";
    private static final String SEED_GOLD_RECORD = "_seed_gold";
    private static final int MAX_SEED_PURCHASE = 64 * 9;

    private final GoldWallet goldWallet;
    private final CropPrices prices;
    private final ItemsAdderItemProvider itemProvider;
    private final BalanceBook salesRecord;

    public CropMarket(GoldWallet goldWallet, CropPrices prices, ItemsAdderItemProvider itemProvider, BalanceBook salesRecord) {
        this.goldWallet = goldWallet;
        this.prices = prices;
        this.itemProvider = itemProvider;
        this.salesRecord = salesRecord;
    }

    public void open(Player player) {
        new CropSellGui(this).open(player);
    }

    void openSeeds(Player player) {
        new SeedShopGui(this, player.getUniqueId()).open(player);
    }

    long goldOf(UUID playerId) {
        return goldWallet.get(playerId);
    }

    ItemsAdderItemProvider itemProvider() {
        return itemProvider;
    }

    /**
     * 씨앗을 산다. 골드가 부족하면 아무것도 바꾸지 않는다. 가방이 가득 차면 바닥에 떨어뜨린다.
     */
    void buySeeds(Player player, CropPrices.Entry crop, int amount) {
        UUID playerId = player.getUniqueId();
        amount = Math.max(1, Math.min(amount, MAX_SEED_PURCHASE));
        long cost = Math.multiplyExact(crop.seedPrice(), amount);
        ItemStack seed;
        try {
            seed = itemProvider.create(crop.seedItemId());
        } catch (IllegalStateException exception) {
            player.sendMessage(Component.text("씨앗 아이템을 찾을 수 없습니다: " + crop.seedItemId(), NamedTextColor.RED));
            return;
        }
        if (!goldWallet.withdraw(playerId, cost)) {
            player.sendMessage(Component.text("골드가 부족합니다. (필요: " + CommandSupport.formatNumber(cost)
                    + "골드, 보유: " + CommandSupport.formatNumber(goldWallet.get(playerId)) + "골드)", NamedTextColor.RED));
            player.playSound(player.getLocation(), Sound.ENTITY_VILLAGER_NO, 0.8f, 1.0f);
            return;
        }

        int remaining = amount;
        while (remaining > 0) {
            ItemStack stack = seed.clone();
            int size = Math.min(remaining, stack.getMaxStackSize());
            stack.setAmount(size);
            ItemDelivery.giveOrDrop(player, stack);
            remaining -= size;
        }
        salesRecord.deposit(playerId, crop.seedItemId(), amount);
        salesRecord.deposit(playerId, SEED_GOLD_RECORD, cost);

        player.playSound(player.getLocation(), Sound.ENTITY_ITEM_PICKUP, 0.8f, 1.2f);
        player.sendMessage(Component.text(crop.name() + " 씨앗 " + amount + "개를 샀습니다. ", NamedTextColor.GREEN)
                .append(Component.text("(-" + CommandSupport.formatNumber(cost) + "골드)", NamedTextColor.GRAY)));
    }

    /**
     * 아이템 한 묶음의 매입가 (개수 포함). 매입하지 않는 아이템이면 0.
     */
    long valueOf(ItemStack item) {
        if (item == null || item.getType().isAir()) {
            return 0;
        }
        return prices.priceOf(itemProvider.idOf(item)) * item.getAmount();
    }

    boolean isSellable(ItemStack item) {
        return valueOf(item) > 0;
    }

    CropPrices prices() {
        return prices;
    }

    /**
     * 아이템들을 판다. 매입하지 않는 아이템은 건너뛰고, 판 아이템은 호출한 쪽에서 치운다.
     *
     * @return 받은 골드 (팔 것이 없으면 0)
     */
    long sell(Player player, Iterable<ItemStack> items) {
        UUID playerId = player.getUniqueId();
        long total = 0;
        int count = 0;
        Map<String, Long> soldById = new HashMap<>();
        for (ItemStack item : items) {
            long value = valueOf(item);
            if (value <= 0) {
                continue;
            }
            total = Math.addExact(total, value);
            count += item.getAmount();
            soldById.merge(itemProvider.idOf(item), (long) item.getAmount(), Long::sum);
        }
        if (total <= 0) {
            return 0;
        }

        goldWallet.deposit(playerId, total);
        soldById.forEach((id, amount) -> salesRecord.deposit(playerId, id, amount));
        salesRecord.deposit(playerId, GOLD_RECORD, total);

        player.playSound(player.getLocation(), Sound.ENTITY_EXPERIENCE_ORB_PICKUP, 0.8f, 1.1f);
        player.sendMessage(Component.text("작물 " + count + "개를 팔아 ", NamedTextColor.GREEN)
                .append(Component.text(CommandSupport.formatNumber(total) + "골드", NamedTextColor.GOLD))
                .append(Component.text("를 받았습니다.", NamedTextColor.GREEN)));
        return total;
    }
}

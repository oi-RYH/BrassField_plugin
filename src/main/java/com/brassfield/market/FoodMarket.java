package com.brassfield.market;

import com.brassfield.common.BalanceBook;
import com.brassfield.common.CommandSupport;
import com.brassfield.common.ItemsAdderGuiBackground;
import com.brassfield.common.ItemsAdderItemProvider;
import com.brassfield.economy.GoldWallet;
import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.Sound;
import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.configuration.file.FileConfiguration;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;
import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.scheduler.BukkitTask;

import java.io.File;
import java.io.IOException;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ThreadLocalRandom;
import java.util.logging.Logger;

/**
 * 요리 납품 로봇 DL-7: 요리를 골드로 사들인다. 골드는 경제 모듈의 공개 API(GoldWallet)로만 다룬다.
 * <ul>
 *   <li>기본가는 config.yml 의 food-market.prices (재료 난이도 점수 × 단계 배율).</li>
 *   <li>서버 전체 판매량을 window-hours(4시간)마다 집계해, 직전 구간에 많이 팔린 요리는 내리고 덜 팔린 요리는 올린다.
 *       변동 = max-change × (1 − 판매 비중 ÷ 기준 비중), ±max-change 로 제한. 기준 비중 = 1 ÷ 요리 수.
 *       직전 구간에 아무것도 안 팔렸으면 모두 기본가. 구간 사이에는 가격이 고정이다.</li>
 *   <li>일간 주문서: 매일 daily-orders.hour 시(6시)에 묶음마다 무작위로 요리를 골라(2단계 2개 + 1단계 1개),
 *       그날은 4시간 변동 없이 +bonus(80%)에 산다. 한도 없음.</li>
 *   <li>상태(구간 시작·구간 판매량·현재 변동·오늘의 주문)는 food_market.yml, 플레이어별 판매 기록은 food_sales.yml.</li>
 * </ul>
 */
public final class FoodMarket {

    /**
     * 요리 판매 창을 여는 납품 로봇 (ItemsAdder 가구 ID)
     */
    public static final String MACHINE_ID = "rustport:dl7";
    private static final String GOLD_RECORD = "_gold";
    private static final DateTimeFormatter TIME = DateTimeFormatter.ofPattern("HH:mm");

    private final JavaPlugin plugin;
    private final GoldWallet goldWallet;
    private final ItemsAdderItemProvider itemProvider;
    private final ItemsAdderGuiBackground guiBackground;
    private final BalanceBook salesRecord;
    private final Map<String, Long> basePrices;
    private final int windowHours;
    private final double maxChange;
    private final File stateFile;
    private final Map<String, Long> windowSales = new HashMap<>();
    private final Map<String, Double> changes = new HashMap<>();
    private final Map<String, String> names = new HashMap<>();
    private long windowStart;
    private final int orderHour;
    private final double orderBonus;
    private final List<OrderGroup> orderGroups;
    private final List<String> orders = new ArrayList<>();
    private long orderStart;
    private DeliveryRobots robots;
    private BukkitTask task;

    /**
     * 일간 주문서 묶음: from 중에서 count 개를 고른다.
     */
    private record OrderGroup(int count, List<String> from) {
    }

    private FoodMarket(JavaPlugin plugin, GoldWallet goldWallet, ItemsAdderItemProvider itemProvider,
                       ItemsAdderGuiBackground guiBackground, BalanceBook salesRecord,
                       Map<String, Long> basePrices, int windowHours, double maxChange,
                       int orderHour, double orderBonus, List<OrderGroup> orderGroups) {
        this.plugin = plugin;
        this.goldWallet = goldWallet;
        this.itemProvider = itemProvider;
        this.guiBackground = guiBackground;
        this.salesRecord = salesRecord;
        this.basePrices = basePrices;
        this.windowHours = windowHours;
        this.maxChange = maxChange;
        this.orderHour = orderHour;
        this.orderBonus = orderBonus;
        this.orderGroups = orderGroups;
        this.stateFile = new File(plugin.getDataFolder(), "food_market.yml");
    }

    /**
     * config.yml 의 food-market 을 읽는다. 항목이 없거나 가격이 비어 있으면 null.
     */
    public static FoodMarket load(JavaPlugin plugin, FileConfiguration config, GoldWallet goldWallet,
                                  ItemsAdderItemProvider itemProvider, ItemsAdderGuiBackground guiBackground,
                                  BalanceBook salesRecord, Logger logger) {
        ConfigurationSection section = config.getConfigurationSection("food-market");
        ConfigurationSection prices = section == null ? null : section.getConfigurationSection("prices");
        if (prices == null) {
            logger.warning("food-market.prices 가 없어 요리 판매(DL-7)를 끕니다.");
            return null;
        }
        Map<String, Long> base = new LinkedHashMap<>();
        for (String id : prices.getKeys(false)) {
            long price = prices.getLong(id);
            if (price > 0) {
                base.put(id, price);
            }
        }
        if (base.isEmpty()) {
            logger.warning("food-market.prices 가 비어 있어 요리 판매(DL-7)를 끕니다.");
            return null;
        }
        int hours = Math.max(1, section.getInt("window-hours", 4));
        double max = Math.max(0, section.getDouble("max-change", 0.10));
        List<OrderGroup> groups = new ArrayList<>();
        for (Map<?, ?> raw : section.getMapList("daily-orders.groups")) {
            Object count = raw.get("count");
            Object from = raw.get("from");
            if (count instanceof Number number && from instanceof List<?> list) {
                List<String> ids = list.stream().map(String::valueOf).filter(base::containsKey).toList();
                if (!ids.isEmpty() && number.intValue() > 0) {
                    groups.add(new OrderGroup(number.intValue(), ids));
                }
            }
        }
        int orderHour = Math.floorMod(section.getInt("daily-orders.hour", 6), 24);
        double orderBonus = Math.max(0, section.getDouble("daily-orders.bonus", 0.8));
        FoodMarket market = new FoodMarket(plugin, goldWallet, itemProvider, guiBackground, salesRecord, base, hours, max,
                orderHour, orderBonus, groups);
        market.loadState();
        logger.info("요리 판매(DL-7): 요리 " + base.size() + "종, " + hours + "시간마다 ±" + Math.round(max * 100) + "% 가격 변동");
        return market;
    }

    public void robots(DeliveryRobots robots) {
        this.robots = robots;
    }

    public void start() {
        rollIfNeeded();
        task = plugin.getServer().getScheduler().runTaskTimer(plugin, this::rollIfNeeded, 1200L, 1200L);
    }

    // ── 일간 주문서 ──

    /**
     * 지금 주문서의 시작 시각 (매일 orderHour 시. 그 전이면 어제 orderHour 시).
     */
    private long orderStartOf(long now) {
        ZonedDateTime time = Instant.ofEpochMilli(now).atZone(ZoneId.systemDefault());
        ZonedDateTime start = time.truncatedTo(ChronoUnit.DAYS).withHour(orderHour);
        if (time.isBefore(start)) {
            start = start.minusDays(1);
        }
        return start.toInstant().toEpochMilli();
    }

    /**
     * 날이 바뀌었으면(orderHour 시) 주문 요리를 새로 뽑고 서버에 알린다.
     */
    private void rollOrdersIfNeeded(long now) {
        long start = orderStartOf(now);
        if (start == orderStart || orderGroups.isEmpty()) {
            return;
        }
        orderStart = start;
        orders.clear();
        java.util.Random random = ThreadLocalRandom.current();
        for (OrderGroup group : orderGroups) {
            List<String> pool = new ArrayList<>(group.from());
            pool.removeAll(orders);
            Collections.shuffle(pool, random);
            orders.addAll(pool.subList(0, Math.min(group.count(), pool.size())));
        }
        if (!orders.isEmpty()) {
            Component message = Component.text("[DL-7] ", NamedTextColor.GOLD)
                    .append(Component.text("오늘의 납품 주문: " + ordersText() + " (+" + Math.round(orderBonus * 100) + "%)",
                            NamedTextColor.YELLOW));
            plugin.getServer().getOnlinePlayers().forEach(player -> player.sendMessage(message));
        }
    }

    boolean isOrdered(String id) {
        return orders.contains(id);
    }

    List<String> orders() {
        return Collections.unmodifiableList(orders);
    }

    double orderBonus() {
        return orderBonus;
    }

    String ordersText() {
        return String.join(", ", orders.stream().map(this::nameOf).toList());
    }

    public void stop() {
        if (task != null) {
            task.cancel();
        }
        saveState();
    }

    /**
     * 납품 로봇을 우클릭했을 때: 판매 창을 열고 로봇이 반응한다.
     */
    public void open(Player player, Entity robot) {
        rollIfNeeded();
        new FoodSellGui(this, robot).open(player);
        if (robots != null) {
            robots.react(robot, "sparkle", 40);
        }
        String line = ThreadLocalRandom.current().nextInt(20) == 0
                ? "…수신 확인 없음. 계속 보냅니다."
                : "삐빅. DL-7, 납품 수령 모드 가동.";
        say(player, line);
        if (!orders.isEmpty()) {
            say(player, "오늘의 주문: " + ordersText() + " (+" + Math.round(orderBonus * 100) + "%)");
        }
    }

    ItemsAdderGuiBackground guiBackground() {
        return guiBackground;
    }

    JavaPlugin plugin() {
        return plugin;
    }

    /**
     * ItemsAdder 아이템을 만든다. 없으면 fallback 을 쓴다.
     */
    ItemStack icon(String itemId, ItemStack fallback) {
        try {
            return itemProvider.create(itemId);
        } catch (IllegalStateException exception) {
            return fallback;
        }
    }

    /**
     * /요리가격: 요리 단가표와 오늘의 주문을 채팅으로 보여 준다 (DL-7 납품 창에서 단가표를 뺀 대신).
     */
    public void sendPriceList(org.bukkit.command.CommandSender sender) {
        rollIfNeeded();
        sender.sendMessage(Component.text("── DL-7 요리 납품 단가 (다음 변동 " + nextChangeTime() + ") ──", NamedTextColor.GOLD));
        for (Map.Entry<String, Long> entry : basePrices().entrySet()) {
            String id = entry.getKey();
            double change = changeOf(id);
            Component line = Component.text(nameOf(id) + ": ", NamedTextColor.WHITE)
                    .append(Component.text(CommandSupport.formatNumber(priceOf(id)) + "골드", NamedTextColor.YELLOW));
            if (isOrdered(id)) {
                line = line.append(Component.text(" ★주문 +" + Math.round(change * 100) + "%", NamedTextColor.GOLD));
            } else if (change > 1e-9) {
                line = line.append(Component.text(" ▲" + Math.round(change * 100) + "%", NamedTextColor.GREEN));
            } else if (change < -1e-9) {
                line = line.append(Component.text(" ▼" + Math.round(-change * 100) + "%", NamedTextColor.RED));
            }
            sender.sendMessage(line);
        }
        sender.sendMessage(Component.text("많이 납품된 요리는 내리고, 덜 납품된 요리는 올립니다.", NamedTextColor.GRAY));
        if (!orders.isEmpty()) {
            sender.sendMessage(Component.text("오늘의 주문: " + ordersText() + " (+" + Math.round(orderBonus * 100) + "%, 매일 오전 6시에 바뀜)",
                    NamedTextColor.GOLD));
        }
    }

    static void say(Player player, String line) {
        player.sendMessage(Component.text("[DL-7] ", NamedTextColor.GOLD).append(Component.text(line, NamedTextColor.YELLOW)));
    }

    // ── 가격 ──

    /**
     * 요리 1개의 지금 매입가. 매입하지 않는 아이템이면 0.
     */
    long priceOf(String id) {
        Long base = id == null ? null : basePrices.get(id);
        if (base == null) {
            return 0;
        }
        return Math.max(1, Math.round(base * (1 + changeOf(id))));
    }

    /**
     * 가격 변동 비율. 오늘의 주문 요리는 4시간 변동 없이 +orderBonus 로 고정.
     */
    double changeOf(String id) {
        return isOrdered(id) ? orderBonus : changes.getOrDefault(id, 0.0);
    }

    Map<String, Long> basePrices() {
        return Collections.unmodifiableMap(basePrices);
    }

    String nameOf(String id) {
        return names.computeIfAbsent(id, key -> {
            try {
                ItemMeta meta = itemProvider.create(key).getItemMeta();
                if (meta != null && meta.hasDisplayName()) {
                    return net.kyori.adventure.text.serializer.plain.PlainTextComponentSerializer.plainText()
                            .serialize(meta.displayName());
                }
            } catch (IllegalStateException ignored) {
                // ItemsAdder 가 아직 아이템을 불러오지 못함
            }
            return key.substring(key.indexOf(':') + 1);
        });
    }

    String nextChangeTime() {
        return Instant.ofEpochMilli(windowStart + windowHours * 3_600_000L).atZone(ZoneId.systemDefault()).format(TIME);
    }

    long valueOf(ItemStack item) {
        if (item == null || item.getType().isAir()) {
            return 0;
        }
        return priceOf(itemProvider.idOf(item)) * item.getAmount();
    }

    boolean isSellable(ItemStack item) {
        return valueOf(item) > 0;
    }

    // ── 판매 ──

    /**
     * 요리를 판다. 매입하지 않는 아이템은 건너뛰고, 판 아이템은 호출한 쪽에서 치운다.
     *
     * @return 받은 골드 (팔 것이 없으면 0)
     */
    long sell(Player player, Iterable<ItemStack> items, Entity robot) {
        rollIfNeeded();
        UUID playerId = player.getUniqueId();
        long total = 0;
        int count = 0;
        boolean cheap = false;
        Map<String, Long> soldById = new HashMap<>();
        for (ItemStack item : items) {
            long value = valueOf(item);
            if (value <= 0) {
                continue;
            }
            String id = itemProvider.idOf(item);
            total = Math.addExact(total, value);
            count += item.getAmount();
            soldById.merge(id, (long) item.getAmount(), Long::sum);
            cheap |= !isOrdered(id) && changeOf(id) <= -maxChange + 1e-9 && maxChange > 0;
        }
        if (total <= 0) {
            return 0;
        }

        goldWallet.deposit(playerId, total);
        soldById.forEach((id, amount) -> {
            salesRecord.deposit(playerId, id, amount);
            windowSales.merge(id, amount, Long::sum);
        });
        salesRecord.deposit(playerId, GOLD_RECORD, total);
        saveState();

        player.playSound(player.getLocation(), Sound.ENTITY_EXPERIENCE_ORB_PICKUP, 0.8f, 1.1f);
        player.sendMessage(Component.text("요리 " + count + "개를 납품해 ", NamedTextColor.GREEN)
                .append(Component.text(CommandSupport.formatNumber(total) + "골드", NamedTextColor.GOLD))
                .append(Component.text("를 받았습니다.", NamedTextColor.GREEN)));
        say(player, cheap ? "해당 품목 재고 충분. 단가를 조정합니다." : "포장 완료. 오늘 밤 열차로 발송합니다.");
        if (robots != null && robot != null) {
            robots.react(robot, total >= 10_000 ? "heart" : "happy", 60);
        }
        return total;
    }

    // ── 4시간 집계 ──

    private long windowStartOf(long now) {
        ZonedDateTime time = Instant.ofEpochMilli(now).atZone(ZoneId.systemDefault()).truncatedTo(ChronoUnit.HOURS);
        if (24 % windowHours == 0) {                     // 하루를 나누면 0시부터 맞춘다 (4시간 → 0·4·8·12·16·20시)
            time = time.withHour(time.getHour() - time.getHour() % windowHours);
            return time.toInstant().toEpochMilli();
        }
        long length = windowHours * 3_600_000L;
        return now - Math.floorMod(now, length);
    }

    /**
     * 구간이 끝났으면 직전 구간 판매량으로 다음 구간 가격을 정한다.
     */
    private void rollIfNeeded() {
        long now = System.currentTimeMillis();
        rollOrdersIfNeeded(now);
        long length = windowHours * 3_600_000L;
        if (windowStart > 0 && now < windowStart + length) {
            return;
        }
        boolean previousWindowJustEnded = windowStart > 0 && now < windowStart + 2 * length;
        changes.clear();
        long total = windowSales.values().stream().mapToLong(Long::longValue).sum();
        if (previousWindowJustEnded && total > 0) {
            double fair = 1.0 / basePrices.size();
            for (String id : basePrices.keySet()) {
                double share = windowSales.getOrDefault(id, 0L) / (double) total;
                double change = Math.max(-maxChange, Math.min(maxChange, maxChange * (1 - share / fair)));
                if (Math.abs(change) > 1e-9) {
                    changes.put(id, change);
                }
            }
        }
        windowSales.clear();
        windowStart = windowStartOf(now);
        saveState();
    }

    private void loadState() {
        if (!stateFile.exists()) {
            return;
        }
        YamlConfiguration yaml = YamlConfiguration.loadConfiguration(stateFile);
        windowStart = yaml.getLong("window-start", 0);
        orderStart = yaml.getLong("order-start", 0);
        orders.addAll(yaml.getStringList("orders"));
        ConfigurationSection sales = yaml.getConfigurationSection("sales");
        if (sales != null) {
            for (String id : sales.getKeys(false)) {
                windowSales.put(id, sales.getLong(id));
            }
        }
        ConfigurationSection saved = yaml.getConfigurationSection("changes");
        if (saved != null) {
            for (String id : saved.getKeys(false)) {
                changes.put(id, saved.getDouble(id));
            }
        }
    }

    private void saveState() {
        YamlConfiguration yaml = new YamlConfiguration();
        yaml.options().setHeader(java.util.List.of("DL-7 요리 판매 구간 상태 (BrassField 가 관리, 직접 수정하지 말 것)"));
        yaml.set("window-start", windowStart);
        yaml.set("order-start", orderStart);
        yaml.set("orders", new ArrayList<>(orders));
        windowSales.forEach((id, amount) -> yaml.set("sales." + id, amount));
        changes.forEach((id, change) -> yaml.set("changes." + id, change));
        try {
            yaml.save(stateFile);
        } catch (IOException exception) {
            plugin.getLogger().warning("food_market.yml 저장 실패: " + exception.getMessage());
        }
    }
}

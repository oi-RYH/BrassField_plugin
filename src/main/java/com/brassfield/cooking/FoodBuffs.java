package com.brassfield.cooking;

import com.brassfield.common.ItemsAdderItemProvider;
import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.NamespacedKey;
import org.bukkit.Registry;
import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.configuration.file.FileConfiguration;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.player.PlayerItemConsumeEvent;
import org.bukkit.potion.PotionEffect;
import org.bukkit.potion.PotionEffectType;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ThreadLocalRandom;
import java.util.logging.Logger;

/**
 * 2단계 요리를 먹으면 그 요리에 어울리는 효과 후보 중 하나를 무작위로 붙인다 (레벨 I).
 * 효과 이름·효과별 최대 시간·요리별 후보와 지속 시간은 config.yml 의 food-buffs.
 * 손에 들고 먹을 때(PlayerItemConsumeEvent)와 놓인 요리를 먹을 때(PlacedFood) 모두 {@link #apply} 를 쓴다.
 */
public final class FoodBuffs implements Listener {

    private record Buff(PotionEffectType type, String name, int maxSeconds) {
    }

    private record Dish(int seconds, List<Buff> buffs) {
    }

    private final ItemsAdderItemProvider itemProvider;
    private final Map<String, Dish> dishes;

    private FoodBuffs(ItemsAdderItemProvider itemProvider, Map<String, Dish> dishes) {
        this.itemProvider = itemProvider;
        this.dishes = dishes;
    }

    /**
     * config.yml 의 food-buffs 를 읽는다. 꺼져 있거나 비어 있으면 null.
     */
    public static FoodBuffs load(FileConfiguration config, ItemsAdderItemProvider itemProvider, Logger logger) {
        ConfigurationSection section = config.getConfigurationSection("food-buffs");
        if (section == null || !section.getBoolean("enabled", true)) {
            return null;
        }
        ConfigurationSection names = section.getConfigurationSection("effects");
        ConfigurationSection caps = section.getConfigurationSection("max-seconds");
        ConfigurationSection items = section.getConfigurationSection("items");
        Map<String, Dish> dishes = new HashMap<>();
        if (items != null) {
            for (String id : items.getKeys(false)) {
                List<Buff> buffs = new ArrayList<>();
                for (String key : items.getStringList(id + ".effects")) {
                    PotionEffectType type = Registry.EFFECT.get(NamespacedKey.minecraft(key));
                    if (type == null) {
                        logger.warning("food-buffs." + id + ": 알 수 없는 효과 " + key);
                        continue;
                    }
                    String name = names == null ? key : names.getString(key, key);
                    buffs.add(new Buff(type, name, caps == null ? 0 : caps.getInt(key, 0)));
                }
                int seconds = items.getInt(id + ".seconds", 60);
                if (!buffs.isEmpty() && seconds > 0) {
                    dishes.put(id, new Dish(seconds, buffs));
                }
            }
        }
        if (dishes.isEmpty()) {
            logger.warning("food-buffs 에 요리가 없어 요리 버프를 끕니다.");
            return null;
        }
        return new FoodBuffs(itemProvider, dishes);
    }

    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true)
    public void onEat(PlayerItemConsumeEvent event) {
        apply(event.getPlayer(), itemProvider.idOf(event.getItem()));
    }

    /**
     * id 가 버프 요리면 그 요리의 후보 중 하나를 무작위로 붙이고 액션바로 알린다.
     */
    public void apply(Player player, String id) {
        Dish dish = id == null ? null : dishes.get(id);
        if (dish == null) {
            return;
        }
        Buff buff = dish.buffs().get(ThreadLocalRandom.current().nextInt(dish.buffs().size()));
        int seconds = buff.maxSeconds() > 0 ? Math.min(dish.seconds(), buff.maxSeconds()) : dish.seconds();
        player.addPotionEffect(new PotionEffect(buff.type(), seconds * 20, 0, false, true, true));
        String time = seconds % 60 == 0 ? (seconds / 60) + "분" : seconds + "초";
        player.sendActionBar(Component.text("요리 효과: " + buff.name() + " (" + time + ")", NamedTextColor.GOLD));
    }
}

package com.brassfield.shop.citizens;

import com.brassfield.shop.StoneShop;
import net.citizensnpcs.api.CitizensAPI;
import net.citizensnpcs.api.event.NPCRightClickEvent;
import net.citizensnpcs.api.trait.TraitInfo;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.plugin.java.JavaPlugin;

/**
 * Citizens 연동. Citizens 클래스를 직접 쓰므로 Citizens가 켜져 있을 때만 이 클래스를 불러야 한다.
 * NPC 외형·위치는 Citizens가, 상점 동작(가격·골드·강화석)은 BrassField가 맡는다.
 */
public final class CitizensShopHook implements Listener {

    private final StoneShop shop;

    private CitizensShopHook(StoneShop shop) {
        this.shop = shop;
    }

    public static void register(JavaPlugin plugin, StoneShop shop) {
        CitizensAPI.getTraitFactory().registerTrait(TraitInfo.create(StoneShopTrait.class));
        plugin.getServer().getPluginManager().registerEvents(new CitizensShopHook(shop), plugin);
    }

    public static void unregister() {
        CitizensAPI.getTraitFactory().deregisterTrait(TraitInfo.create(StoneShopTrait.class));
    }

    @EventHandler
    public void onNpcRightClick(NPCRightClickEvent event) {
        if (event.getNPC().hasTrait(StoneShopTrait.class)) {
            shop.open(event.getClicker());
        }
    }
}

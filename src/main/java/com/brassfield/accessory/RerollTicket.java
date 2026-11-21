package com.brassfield.accessory;

import io.papermc.paper.datacomponent.DataComponentTypes;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.GameMode;
import org.bukkit.Material;
import org.bukkit.NamespacedKey;
import org.bukkit.Sound;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.inventory.ClickType;
import org.bukkit.event.inventory.InventoryClickEvent;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;
import org.bukkit.persistence.PersistentDataType;

import java.util.List;

/**
 * 보조옵션권 (임시: 종이 아이템 + 반짝임). 커서에 들고 가방의 장신구를 클릭하면 그 장신구의 보조옵션을 모두 다시 굴리고 1장 쓴다.
 * 장착 창의 장착한 장신구에도 쓸 수 있다 (AccessoryListener). 등급 제한 · 잠금 리롤은 미정 (노션 Q4 · Q5).
 * 입수: 몬스터 · 보스 드랍 (드랍 시스템을 만들 때). 그전엔 /장신구 리롤권 [개수] (관리자).
 */
public final class RerollTicket implements Listener {

    static final NamespacedKey KEY = new NamespacedKey("brassfield", "acc_reroll_ticket");

    public static ItemStack create(int amount) {
        ItemStack item = new ItemStack(Material.PAPER, Math.max(1, amount));
        item.setData(DataComponentTypes.ENCHANTMENT_GLINT_OVERRIDE, true);
        ItemMeta meta = item.getItemMeta();
        meta.getPersistentDataContainer().set(KEY, PersistentDataType.BYTE, (byte) 1);
        meta.displayName(Accessories.plain("보조옵션권", NamedTextColor.YELLOW));
        meta.lore(List.of(
                Accessories.plain("커서에 들고 장신구를 클릭하면", NamedTextColor.GRAY),
                Accessories.plain("보조옵션을 모두 다시 굴립니다.", NamedTextColor.GRAY),
                Accessories.plain("(장착 창의 장신구에도 쓸 수 있음)", NamedTextColor.DARK_GRAY)));
        item.setItemMeta(meta);
        return item;
    }

    public static boolean is(ItemStack item) {
        return item != null && !item.getType().isAir() && item.hasItemMeta()
                && item.getItemMeta().getPersistentDataContainer().has(KEY, PersistentDataType.BYTE);
    }

    /** 보조옵션을 새로 굴린 같은 장신구 (세트 · 종류 · 등급 · 강화 유지) */
    static ItemStack reroll(ItemStack accessory) {
        Accessories.Info info = Accessories.read(accessory).orElseThrow();
        return Accessories.create(new Accessories.Info(info.set(), info.variant(), info.grade(), info.level()));
    }

    /** 커서의 보조옵션권 1장 쓰기 */
    static void consume(InventoryClickEvent event) {
        ItemStack cursor = event.getCursor();
        cursor.setAmount(cursor.getAmount() - 1);
        event.getView().setCursor(cursor.getAmount() > 0 ? cursor : null);
    }

    static void feedback(Player player) {
        player.playSound(player, Sound.BLOCK_ENCHANTMENT_TABLE_USE, 0.8f, 1.3f);
    }

    /** 가방(아무 창의 플레이어 칸 포함)에서 장신구 위에 보조옵션권을 클릭 */
    @EventHandler(priority = EventPriority.HIGH)
    public void onApply(InventoryClickEvent event) {
        if (!(event.getWhoClicked() instanceof Player player) || player.getGameMode() == GameMode.CREATIVE
                || (event.getClick() != ClickType.LEFT && event.getClick() != ClickType.RIGHT)
                || !is(event.getCursor()) || event.getClickedInventory() != player.getInventory()) {
            return;
        }
        ItemStack target = event.getCurrentItem();
        if (!Accessories.isAccessory(target) || target.getAmount() != 1) {
            return;
        }
        event.setCancelled(true);
        event.setCurrentItem(reroll(target));
        consume(event);
        feedback(player);
    }
}

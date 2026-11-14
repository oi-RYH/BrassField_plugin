package com.rustport.enhancement;

import org.bukkit.Bukkit;
import org.bukkit.entity.Player;
import org.bukkit.inventory.Inventory;
import org.bukkit.inventory.InventoryHolder;
import org.bukkit.plugin.java.JavaPlugin;

import java.lang.reflect.Array;
import java.lang.reflect.Constructor;
import java.lang.reflect.Method;

/**
 * ItemsAdder의 font_image 기반 GUI 배경(TexturedInventoryWrapper)에 접근하는 다리 역할.
 * ItemsAdder가 설치되어 있지 않아도 이 플러그인이 죽지 않도록 전부 리플렉션으로 접근한다.
 */
public final class ItemsAdderGuiBackground {

    private static final String FONT_IMAGE_WRAPPER_CLASS = "dev.lone.itemsadder.api.FontImages.FontImageWrapper";
    private static final String TEXTURED_INVENTORY_WRAPPER_CLASS = "dev.lone.itemsadder.api.FontImages.TexturedInventoryWrapper";

    private final JavaPlugin plugin;
    private final boolean available;

    private Class<?> fontImageWrapperClass;
    private Method fontImageInstanceMethod;
    private Constructor<?> texturedInventoryConstructor;
    private Method showInventoryMethod;
    private Method getInternalMethod;
    private Method getStringMethod;

    public ItemsAdderGuiBackground(JavaPlugin plugin) {
        this.plugin = plugin;
        this.available = Bukkit.getPluginManager().isPluginEnabled("ItemsAdder") && loadReflection();
    }

    private boolean loadReflection() {
        try {
            fontImageWrapperClass = Class.forName(FONT_IMAGE_WRAPPER_CLASS);
            Class<?> texturedInventoryWrapperClass = Class.forName(TEXTURED_INVENTORY_WRAPPER_CLASS);
            Class<?> fontImageArrayClass = Array.newInstance(fontImageWrapperClass, 0).getClass();

            fontImageInstanceMethod = fontImageWrapperClass.getMethod("instance", String.class);
            texturedInventoryConstructor = texturedInventoryWrapperClass.getConstructor(
                    InventoryHolder.class, int.class, String.class, int.class, int.class, fontImageArrayClass
            );
            showInventoryMethod = texturedInventoryWrapperClass.getMethod("showInventory", Player.class);
            getInternalMethod = texturedInventoryWrapperClass.getMethod("getInternal");
            getStringMethod = fontImageWrapperClass.getMethod("getString");
            return true;
        } catch (ReflectiveOperationException exception) {
            plugin.getLogger().warning(
                    "ItemsAdder 폰트 이미지 GUI API를 불러오지 못했습니다. 기본 배경으로 대체합니다: " + exception
            );
            return false;
        }
    }

    public boolean isAvailable() {
        return available;
    }

    /**
     * font_image를 배경으로 쓰는 인벤토리를 만든다.
     * ItemsAdder가 없거나 font_image를 찾지 못하면 null을 반환하니, 호출부에서 바닐라 배경으로 대체해야 한다.
     */
    public TexturedGui build(
            InventoryHolder holder,
            int size,
            String title,
            String fontImageNamespacedId,
            int titleOffset,
            int textureOffset
    ) {
        if (!available) {
            return null;
        }

        try {
            Object fontImage = fontImageInstanceMethod.invoke(null, fontImageNamespacedId);
            if (fontImage == null) {
                plugin.getLogger().warning("ItemsAdder 폰트 이미지를 찾을 수 없습니다: " + fontImageNamespacedId);
                return null;
            }

            Object texturesArray = Array.newInstance(fontImageWrapperClass, 1);
            Array.set(texturesArray, 0, fontImage);

            Object texturedInventory = texturedInventoryConstructor.newInstance(
                    holder, size, title, titleOffset, textureOffset, texturesArray
            );
            Inventory inventory = (Inventory) getInternalMethod.invoke(texturedInventory);
            return new TexturedGui(texturedInventory, inventory);
        } catch (ReflectiveOperationException exception) {
            plugin.getLogger().warning("ItemsAdder 배경 GUI 생성에 실패했습니다: " + exception);
            return null;
        }
    }

    public void show(TexturedGui texturedGui, Player player) {
        try {
            showInventoryMethod.invoke(texturedGui.handle(), player);
        } catch (ReflectiveOperationException exception) {
            plugin.getLogger().warning("ItemsAdder 배경 GUI를 여는 중 오류가 발생했습니다: " + exception);
            player.openInventory(texturedGui.inventory());
        }
    }

    /**
     * font_image에 해당하는 글자(문자열)를 돌려준다. 제목을 직접 조립할 때 사용한다.
     */
    public String glyph(String fontImageNamespacedId) {
        try {
            Object fontImage = fontImageInstanceMethod.invoke(null, fontImageNamespacedId);
            return fontImage == null ? "" : (String) getStringMethod.invoke(fontImage);
        } catch (ReflectiveOperationException exception) {
            plugin.getLogger().warning("ItemsAdder 폰트 이미지 글자를 가져오지 못했습니다: " + exception);
            return "";
        }
    }

    public record TexturedGui(Object handle, Inventory inventory) {
    }
}

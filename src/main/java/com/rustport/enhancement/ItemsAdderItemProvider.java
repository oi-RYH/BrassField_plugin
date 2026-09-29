package com.rustport.enhancement;

import org.bukkit.inventory.ItemStack;
import org.bukkit.plugin.java.JavaPlugin;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;

public final class ItemsAdderItemProvider {

    private static final String CUSTOM_STACK_CLASS = "dev.lone.itemsadder.api.CustomStack";

    private final JavaPlugin plugin;
    private final Method getInstanceMethod;
    private final Method byItemStackMethod;
    private final Method getItemStackMethod;
    private final Method getNamespacedIdMethod;

    public ItemsAdderItemProvider(JavaPlugin plugin) {
        this.plugin = plugin;
        try {
            Class<?> customStackClass = Class.forName(CUSTOM_STACK_CLASS);
            getInstanceMethod = customStackClass.getMethod("getInstance", String.class);
            byItemStackMethod = customStackClass.getMethod("byItemStack", ItemStack.class);
            getItemStackMethod = customStackClass.getMethod("getItemStack");
            getNamespacedIdMethod = customStackClass.getMethod("getNamespacedID");
        } catch (ReflectiveOperationException exception) {
            throw new IllegalStateException("ItemsAdder API를 불러오지 못했습니다.", exception);
        }
    }

    public ItemStack create(String namespacedId) {
        Object customStack = invoke(getInstanceMethod, null, namespacedId);
        if (customStack == null) {
            throw new IllegalStateException("ItemsAdder 아이템을 찾을 수 없습니다: " + namespacedId);
        }

        ItemStack item = (ItemStack) invoke(getItemStackMethod, customStack);
        return item.clone();
    }

    public boolean matches(ItemStack item, String namespacedId) {
        Object customStack = invoke(byItemStackMethod, null, item);
        if (customStack == null) {
            return false;
        }
        return namespacedId.equals(invoke(getNamespacedIdMethod, customStack));
    }

    private Object invoke(Method method, Object target, Object... arguments) {
        try {
            return method.invoke(target, arguments);
        } catch (IllegalAccessException | InvocationTargetException exception) {
            plugin.getLogger().severe("ItemsAdder API 호출에 실패했습니다: " + method.getName());
            throw new IllegalStateException("ItemsAdder API 호출 실패", exception);
        }
    }
}

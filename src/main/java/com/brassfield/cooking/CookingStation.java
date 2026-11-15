package com.brassfield.cooking;

/**
 * 요리 기기 한 종류 (조리대, 제분기, 착즙기 …): 설정 키, ItemsAdder 가구 ID, 창 제목, 레시피.
 */
public record CookingStation(String key, String furnitureId, String title, CookingRecipes recipes) {
}

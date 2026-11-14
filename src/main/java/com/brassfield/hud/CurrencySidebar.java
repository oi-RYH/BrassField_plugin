package com.brassfield.hud;

import com.brassfield.common.BalanceChangedEvent;
import com.brassfield.common.FontSpace;
import com.brassfield.common.ItemsAdderGuiBackground;
import com.brassfield.economy.GoldWallet;
import com.brassfield.stone.StoneGrade;
import com.brassfield.stone.StoneWallet;
import io.papermc.paper.scoreboard.numbers.NumberFormat;
import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import net.kyori.adventure.text.format.TextColor;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.player.PlayerJoinEvent;
import org.bukkit.event.player.PlayerQuitEvent;
import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.scheduler.BukkitTask;
import org.bukkit.scoreboard.Criteria;
import org.bukkit.scoreboard.DisplaySlot;
import org.bukkit.scoreboard.Objective;
import org.bukkit.scoreboard.Scoreboard;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * 재화 사이드바: 화면 오른쪽 사이드바에 황동 판(hud_panel)을 깔고 골드와 하급·중급·상급 강화석을 보여준다.
 * <p>
 * 사이드바는 가장 긴 줄(= 제목)의 폭에 맞춰 그려진다. 제목 폭을 {@link #CONTENT_WIDTH}로 고정하고,
 * 제목 줄에 판 그림을 넣어 아래 4줄까지 덮도록 늘어뜨린 뒤, 각 줄에 아이콘과 오른쪽 정렬 숫자를 올린다.
 * 좌표는 사이드바 글자 시작점(x=0) 기준이고, 판 그림은 x=-8 에서 시작한다. (판 62px = 왼쪽 여백 8 + 폭 52 + 2)
 * <p>
 * 재화가 바뀌면(BalanceChangedEvent) 그 플레이어만 바로 다시 그리고,
 * ItemsAdder 글꼴이 늦게 준비되는 경우를 위해 몇 초마다 바뀐 줄이 있는지 확인한다.
 */
public final class CurrencySidebar implements Listener {

    private static final long REFRESH_TICKS = 40L;
    private static final int CONTENT_WIDTH = 52;
    private static final int PANEL_LEFT = -8;
    private static final int PANEL_WIDTH = 62;
    private static final int ICON_X = 1;
    private static final int NUMBER_RIGHT_X = 46;
    private static final int ICON_ADVANCE = 10;
    private static final int DIGIT_ADVANCE = 6;
    private static final int DOT_ADVANCE = 2;

    // 숫자 색은 아이콘에 맞춘다: 골드는 밝은 금색, 강화석은 받침·결정 색 (철 → 황동 → 불꽃)
    private static final List<Line> LINES = List.of(
            new Line("rustport:hud_coin", null, TextColor.color(255, 236, 170), "골드"),
            new Line("rustport:hud_gem_low", StoneGrade.LOW, TextColor.color(190, 180, 166), "하급"),
            new Line("rustport:hud_gem_mid", StoneGrade.MIDDLE, TextColor.color(255, 200, 90), "중급"),
            new Line("rustport:hud_gem_high", StoneGrade.HIGH, TextColor.color(255, 120, 40), "상급")
    );

    private final JavaPlugin plugin;
    private final GoldWallet goldWallet;
    private final StoneWallet stoneWallet;
    private final ItemsAdderGuiBackground fontImages;
    private final Map<String, String> glyphCache = new HashMap<>();
    private final Map<UUID, Objective> objectives = new HashMap<>();
    private BukkitTask task;

    public CurrencySidebar(JavaPlugin plugin, GoldWallet goldWallet, StoneWallet stoneWallet, ItemsAdderGuiBackground fontImages) {
        this.plugin = plugin;
        this.goldWallet = goldWallet;
        this.stoneWallet = stoneWallet;
        this.fontImages = fontImages;
    }

    public void start() {
        plugin.getServer().getPluginManager().registerEvents(this, plugin);
        plugin.getServer().getOnlinePlayers().forEach(this::show);
        task = plugin.getServer().getScheduler().runTaskTimer(plugin,
                () -> plugin.getServer().getOnlinePlayers().forEach(this::update), REFRESH_TICKS, REFRESH_TICKS);
    }

    public void stop() {
        if (task != null) {
            task.cancel();
        }
        for (Player player : plugin.getServer().getOnlinePlayers()) {
            if (objectives.containsKey(player.getUniqueId())) {
                player.setScoreboard(plugin.getServer().getScoreboardManager().getMainScoreboard());
            }
        }
        objectives.clear();
    }

    @EventHandler
    public void onPlayerJoin(PlayerJoinEvent event) {
        show(event.getPlayer());
    }

    @EventHandler
    public void onPlayerQuit(PlayerQuitEvent event) {
        objectives.remove(event.getPlayer().getUniqueId());
    }

    @EventHandler
    public void onBalanceChanged(BalanceChangedEvent event) {
        Player player = plugin.getServer().getPlayer(event.getPlayerId());
        if (player != null) {
            update(player);
        }
    }

    private void show(Player player) {
        Scoreboard scoreboard = plugin.getServer().getScoreboardManager().getNewScoreboard();
        Objective objective = scoreboard.registerNewObjective("brassfield_hud", Criteria.DUMMY, Component.empty());
        objective.setDisplaySlot(DisplaySlot.SIDEBAR);
        objective.numberFormat(NumberFormat.blank());
        for (int i = 0; i < LINES.size(); i++) {
            // 점수가 높을수록 위에 표시된다.
            objective.getScore(entry(i)).setScore(LINES.size() - i);
        }
        player.setScoreboard(scoreboard);
        objectives.put(player.getUniqueId(), objective);
        update(player);
    }

    private void update(Player player) {
        Objective objective = objectives.get(player.getUniqueId());
        if (objective == null) {
            return;
        }
        boolean textured = !glyph("rustport:hud_panel").isEmpty();
        setIfChanged(objective, null, textured ? texturedTitle() : Component.text("재화", NamedTextColor.GOLD));
        for (int i = 0; i < LINES.size(); i++) {
            Line line = LINES.get(i);
            long amount = line.grade() == null
                    ? goldWallet.get(player.getUniqueId())
                    : stoneWallet.get(player.getUniqueId(), line.grade());
            setIfChanged(objective, entry(i), textured ? texturedLine(line, amount) : plainLine(line, amount));
        }
    }

    /**
     * 제목: 판 그림을 x=-8 에 그리고, 전체 폭이 정확히 CONTENT_WIDTH 가 되게 맞춘다. (사이드바 폭 고정)
     */
    private Component texturedTitle() {
        String title = FontSpace.of(PANEL_LEFT) + fontImages.glyph("rustport:hud_panel")
                + FontSpace.of(CONTENT_WIDTH - PANEL_LEFT - PANEL_WIDTH);
        return Component.text(title, NamedTextColor.WHITE);
    }

    private Component texturedLine(Line line, long amount) {
        String number = CompactNumber.format(amount);
        int numberWidth = 0;
        StringBuilder digits = new StringBuilder();
        for (char ch : number.toCharArray()) {
            digits.append(glyph(String.format("rustport:hud_char_%04x", (int) ch)));
            numberWidth += ch == '.' ? DOT_ADVANCE : DIGIT_ADVANCE;
        }
        int numberX = NUMBER_RIGHT_X - numberWidth;
        String icon = FontSpace.of(ICON_X) + glyph(line.iconId());
        // 아이콘은 원래 색, 숫자는 재화별 색으로 칠한다.
        return Component.text(icon, NamedTextColor.WHITE)
                .append(Component.text(FontSpace.of(numberX - ICON_X - ICON_ADVANCE) + digits, line.color()));
    }

    private Component plainLine(Line line, long amount) {
        return Component.text(line.label() + " ", NamedTextColor.GRAY)
                .append(Component.text(CompactNumber.format(amount), line.color()));
    }

    private void setIfChanged(Objective objective, String entry, Component text) {
        if (entry == null) {
            if (!text.equals(objective.displayName())) {
                objective.displayName(text);
            }
            return;
        }
        var score = objective.getScore(entry);
        if (!text.equals(score.customName())) {
            score.customName(text);
        }
    }

    private String glyph(String fontImageId) {
        String cached = glyphCache.get(fontImageId);
        if (cached != null) {
            return cached;
        }
        String glyph = fontImages.glyph(fontImageId);
        // ItemsAdder가 글자 뒤에 붙이는 -1px 보정을 떼어 바닐라 글자 간격(그림 폭 + 1px)을 그대로 쓴다.
        glyph = glyph.endsWith("") ? glyph.substring(0, glyph.length() - 1) : glyph;
        // ItemsAdder가 아직 글꼴을 불러오기 전이면 빈 값이 오므로, 그때는 저장하지 않고 다음에 다시 찾는다.
        if (!glyph.isEmpty()) {
            glyphCache.put(fontImageId, glyph);
        }
        return glyph;
    }

    private static String entry(int index) {
        return "hud_line_" + index;
    }

    private record Line(String iconId, StoneGrade grade, TextColor color, String label) {
    }
}

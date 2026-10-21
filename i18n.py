"""Tiny translation layer: tr("key", **values)."""

from PyQt6.QtCore import QLocale

LANGUAGES = {
    "ru": "Русский",
    "en": "English",
}

STRINGS = {
    # Navigation
    "nav_calc": ("Калькулятор", "Calculator"),
    "nav_crosshair": ("Прицел", "Crosshair"),
    "nav_settings": ("Настройки", "Settings"),
    "nav_web": ("SquadCalc", "SquadCalc"),

    # Calculator
    "target": ("Цель", "Target"),
    "solution": ("Решение", "Solution"),
    "weapon": ("Оружие", "Weapon"),
    "search": ("Поиск оружия…", "Search weapons…"),
    "recent": ("Недавние", "Recent"),
    "nothing_found": ("Ничего не найдено", "Nothing found"),
    "arc_auto": ("Авто", "Auto"),
    "arc_low": ("Настильная", "Low"),
    "arc_high": ("Навесная", "High"),
    "distance": ("Дистанция, м", "Distance, m"),
    "height": ("Перепад высот, м", "Height diff, m"),
    "height_hint": ("цель выше +, ниже −", "target higher +, lower −"),
    "fov": ("FOV", "FOV"),
    "fov_hint": ("горизонтальный FOV", "horizontal FOV"),
    "calculate": ("Рассчитать", "Calculate"),
    "reset_aim": ("Сбросить", "Reset"),
    "ready": ("Введите дистанцию", "Enter the distance"),
    "unreachable": ("Недостижимо", "Unreachable"),
    "enter_distance": ("Введите дистанцию", "Enter the distance"),
    "bad_fov": ("FOV должен быть от 1 до 179", "FOV must be between 1 and 179"),
    "bad_distance": ("Дистанция должна быть больше 0", "Distance must be greater than 0"),

    "stat_tof": ("Время полёта", "Flight time"),
    "stat_apex": ("Высота подъёма", "Apex"),
    "stat_offset": ("Смещение метки", "Mark offset"),
    "stat_impact": ("Угол падения", "Impact angle"),
    "stat_velocity": ("Средняя скорость", "Avg. velocity"),
    "stat_alt": ("Другая траектория", "Other arc"),
    "off_screen": ("за экраном", "off-screen"),
    "unit_s": ("с", "s"),
    "unit_m": ("м", "m"),
    "unit_px": ("пикс", "px"),
    "unit_mps": ("м/с", "m/s"),
    "mil": ("мил", "mil"),

    "how_to": ("Как стрелять", "How to fire"),
    "how_overlay_on": ("Включите оверлей ({hotkey}).", "Turn the overlay on ({hotkey})."),
    "how_overlay_1": (
        "Совместите метку оверлея с целью — ствол окажется поднят ровно "
        "на {angle}.",
        "Put the overlay mark on the target — the barrel is then raised by "
        "exactly {angle}."
    ),
    "how_overlay_2": (
        "FOV в игре должен быть {fov}°. Через оптику — укажите FOV прицела.",
        "Your in-game FOV must be {fov}°. Through a scope, enter the scope FOV."
    ),
    "how_overlay_offscreen": (
        "Метка за пределами экрана: поднимите ствол на {angle} по шкале "
        "прицела или подойдите ближе.",
        "The mark is off-screen: raise the barrel by {angle} using the sight "
        "scale, or move closer."
    ),
    "how_elevation_1": (
        "Развернитесь на цель по азимуту (карта или SquadCalc).",
        "Turn to the target bearing (map or SquadCalc)."
    ),
    "how_elevation_2": (
        "Выставьте угол возвышения {angle}.",
        "Set the elevation to {angle}."
    ),
    "how_tof_moving": (
        "Снаряд летит {tof} с: по цели, идущей 10 м/с, упреждение ≈ {lead} м.",
        "Flight time {tof} s: lead a target moving at 10 m/s by ≈ {lead} m."
    ),
    "how_tof_adjust": (
        "Разрыв через {tof} с. Недолёт — увеличьте дистанцию, перелёт — уменьшите.",
        "Impact after {tof} s. Short — add distance, long — reduce it."
    ),
    "how_unreachable_range": (
        "Цель дальше максимальной дальности (~{max} м). Подойдите ближе "
        "или выберите другое оружие.",
        "The target is beyond maximum range (~{max} m). Move closer or "
        "pick another weapon."
    ),
    "how_unreachable_close": (
        "Слишком близко: минимальная дистанция {min} м.",
        "Too close: minimum distance is {min} m."
    ),
    "how_unreachable_limit": (
        "Нужен угол {angle}°, а орудие наводится только от {low}° до {high}°. "
        "Попробуйте другую траекторию.",
        "Needs {angle}°, but the weapon only elevates from {low}° to {high}°. "
        "Try the other arc."
    ),

    "chip_velocity": ("{v} м/с", "{v} m/s"),
    "chip_gravity": ("гравитация ×{g}", "gravity ×{g}"),
    "chip_range": ("до {r} м", "up to {r} m"),
    "chip_range_inf": ("без падения", "no drop"),
    "chip_boost": ("разгон {a:+g} м/с² · {t:g} с", "boost {a:+g} m/s² · {t:g} s"),
    "chip_min": ("от {m} м", "from {m} m"),
    "chip_mod": ("мод: {mod}", "mod: {mod}"),

    # Categories
    "cat_grenade_launchers": ("Подствольные гранатомёты", "Grenade launchers"),
    "cat_agl": ("Автоматические гранатомёты", "Automatic grenade launchers"),
    "cat_launchers": ("Противотанковые гранатомёты", "Anti-tank launchers"),
    "cat_guns": ("Безоткатные и полевые орудия", "Recoilless & field guns"),
    "cat_tanks": ("Танковые пушки", "Tank guns"),
    "cat_autocannons": ("Автоматические пушки", "Autocannons"),
    "cat_hmg": ("Крупнокалиберные пулемёты", "Heavy machine guns"),
    "cat_indirect": ("Непрямой огонь", "Indirect fire"),
    "cat_mods": ("Моды", "Mods"),
    "cat_other": ("Другое", "Other"),

    # Splash / updates
    "splash_checking": ("Проверка обновлений…", "Checking for updates…"),
    "splash_downloading": ("Загрузка {v}…", "Downloading {v}…"),
    "splash_installing": ("Установка…", "Installing…"),
    "splash_failed": ("Не удалось обновиться: {e}", "Update failed: {e}"),
    "error_title": ("Squad Ballistics — ошибка", "Squad Ballistics — error"),
    "error_saved": ("Подробности сохранены в:\n{path}", "Details saved to:\n{path}"),

    # Crosshair page
    "presets": ("Пресеты", "Presets"),
    "preset_classic": ("Классика", "Classic"),
    "preset_dot": ("Точка", "Dot"),
    "preset_circle": ("Круг", "Circle"),
    "preset_t": ("T-образный", "T-shape"),
    "preset_cross": ("Крест", "Cross"),
    "shape": ("Форма", "Shape"),
    "size": ("Размеры", "Size"),
    "color": ("Цвет", "Color"),
    "effects": ("Эффекты", "Effects"),
    "preview": ("Предпросмотр", "Preview"),
    "opt_dot": ("Точка", "Center dot"),
    "opt_lines": ("Линии", "Lines"),
    "opt_t": ("T-образный (без нижней)", "T-style (no bottom line)"),
    "opt_circle": ("Круг", "Circle"),
    "opt_outline": ("Обводка", "Outline"),
    "opt_glow": ("Свечение", "Glow"),
    "opt_animated": ("Плавное движение", "Smooth motion"),
    "opt_info": ("Подпись у метки", "Label next to the mark"),
    "sl_dot": ("Точка", "Dot size"),
    "sl_length": ("Длина линий", "Line length"),
    "sl_gap": ("Зазор", "Gap"),
    "sl_thickness": ("Толщина", "Thickness"),
    "sl_outline": ("Толщина обводки", "Outline width"),
    "sl_circle": ("Радиус круга", "Circle radius"),
    "sl_opacity": ("Непрозрачность", "Opacity"),
    "outline_color": ("Цвет обводки", "Outline color"),
    "white": ("Белый", "White"),
    "black": ("Чёрный", "Black"),

    # Settings page
    "s_interface": ("Интерфейс", "Interface"),
    "s_language": ("Язык", "Language"),
    "s_lang_auto": ("Как в системе", "System"),
    "s_accent": ("Акцент", "Accent"),
    "s_on_top": ("Окно поверх всех", "Keep window on top"),
    "s_calc": ("Калькулятор", "Calculator"),
    "s_units": ("Главная единица угла", "Primary angle unit"),
    "s_units_auto": ("По оружию", "Per weapon"),
    "s_units_deg": ("Градусы", "Degrees"),
    "s_units_mil": ("Милы", "Mils"),
    "s_auto_calc": ("Считать при вводе", "Calculate while typing"),
    "s_mods": ("Показывать оружие из модов", "Show mod weapons"),
    "s_step": ("Шаг дистанции (колесо и клавиши)", "Distance step (wheel & keys)"),
    "s_overlay": ("Оверлей", "Overlay"),
    "s_monitor": ("Монитор", "Monitor"),
    "s_offset_x": ("Центр: смещение X", "Center offset X"),
    "s_offset_y": ("Центр: смещение Y", "Center offset Y"),
    "s_calibration": ("Калибровка смещения, %", "Offset calibration, %"),
    "s_hotkeys": ("Горячие клавиши", "Hotkeys"),
    "s_hotkeys_hint": (
        "В Windows работают поверх игры. Игра при этом эти клавиши не получает.",
        "Global on Windows, so they work in game. The game no longer receives these keys."
    ),
    "hk_toggle_overlay": ("Оверлей вкл/выкл", "Overlay on/off"),
    "hk_reset_offset": ("Сбросить метку", "Reset mark"),
    "hk_distance_up": ("Дистанция +", "Distance +"),
    "hk_distance_down": ("Дистанция −", "Distance −"),
    "hk_none": ("Нет", "None"),
    "s_about": ("О программе", "About"),
    "s_version": ("Версия {v}", "Version {v}"),
    "s_open_config": ("Папка настроек", "Settings folder"),
    "s_reset": ("Сбросить настройки", "Reset settings"),
    "s_reset_confirm": (
        "Сбросить все настройки прицела и программы?",
        "Reset all crosshair and app settings?"
    ),
    # Map page
    "map_loading": ("Загрузка карты…", "Loading the map…"),
    "map_reload": ("Обновить", "Reload"),
    "map_retry": ("Повторить", "Retry"),
    "map_compat_button": ("Режим совместимости", "Compatibility mode"),
    "map_compat_on": ("режим совместимости", "compatibility mode"),
    "map_failed_title": ("Карта не загрузилась", "The map did not load"),
    "map_failed_text": (
        "Нет связи с squadcalc.app. Проверьте интернет и нажмите «Повторить». "
        "Если в обычном браузере сайт открывается — откройте карту там.",
        "Could not reach squadcalc.app. Check your connection and press "
        "Retry. If the site opens in your regular browser, use it there."
    ),
    "map_slow_title": ("Карта грузится слишком долго", "The map takes too long"),
    "map_slow_text": (
        "Сайт отвечает очень медленно или соединение блокируется. Подождите, "
        "нажмите «Повторить» или откройте карту в обычном браузере.",
        "The site responds very slowly or the connection is blocked. Wait, "
        "press Retry or open the map in your regular browser."
    ),
    "map_crashed_title": ("Карта перестала отвечать", "The map stopped responding"),
    "map_crashed_text": (
        "Встроенный браузер закрылся с ошибкой. Нажмите «Повторить». Если это "
        "повторяется — включите режим совместимости.",
        "The embedded browser crashed. Press Retry. If it keeps happening, "
        "turn on compatibility mode."
    ),
    "map_black_title": ("Карта чёрная?", "Is the map black?"),
    "map_black_text": (
        "Похоже, видеокарта не рисует встроенный браузер. Режим совместимости "
        "рисует карту без видеокарты (программа перезапустится).",
        "Your graphics driver does not seem to draw the embedded browser. "
        "Compatibility mode draws the map without the GPU (the app restarts)."
    ),
    "map_missing_title": ("Встроенная карта недоступна", "Embedded map unavailable"),
    "map_missing_text": (
        "В этой сборке нет встроенного браузера. Откройте карту в обычном "
        "браузере.",
        "This build has no embedded browser. Open the map in your regular "
        "browser."
    ),
    "s_map": ("Карта", "Map"),
    "s_map_render": ("Отрисовка карты", "Map rendering"),
    "s_map_render_auto": ("Обычная", "Normal"),
    "s_map_render_software": ("Совместимая", "Compatible"),
    "s_map_render_hint": (
        "Совместимая — если карта чёрная или мерцает: рисует без видеокарты, "
        "чуть медленнее. Изменение применяется после перезапуска.",
        "Compatible — if the map is black or flickers: draws without the GPU, "
        "a bit slower. Applied after a restart."
    ),
    "s_map_external": ("Открывать карту в обычном браузере", "Open the map in the regular browser"),
    "s_map_clear": ("Очистить кэш карты", "Clear map cache"),
    "s_map_cleared": ("Кэш очищен", "Cache cleared"),
    "restart_title": ("Перезапуск", "Restart"),
    "restart_text": (
        "Перезапустить программу сейчас, чтобы применить изменения?",
        "Restart the app now to apply the change?"
    ),

    "web_open": ("Открыть в браузере", "Open in browser"),
}

_language = "en"


def system_language():
    if QLocale.system().language() in (
        QLocale.Language.Russian,
        QLocale.Language.Ukrainian,
        QLocale.Language.Belarusian,
        QLocale.Language.Kazakh
    ):
        return "ru"
    return "en"


def set_language(code):
    global _language
    _language = code if code in LANGUAGES else system_language()


def language():
    return _language


def tr(string_id, /, **values):
    pair = STRINGS.get(string_id)

    if pair is None:
        text = string_id
    else:
        text = pair[0] if _language == "ru" else pair[1]

    return text.format(**values) if values else text


def category_name(category):
    key = f"cat_{category}"
    return tr(key) if key in STRINGS else category


def weapon_note(weapon):
    if _language == "ru" and weapon.note_ru:
        return weapon.note_ru
    return weapon.note

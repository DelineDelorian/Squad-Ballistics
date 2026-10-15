# About Project

## English

Squad Ballistics is a modern ballistic assistant and tactical overlay system created for the game **Squad**.

The application helps players accurately calculate projectile trajectories, offsets, and aiming corrections for indirect fire and long-range shooting using almost every type of weapon available in the game.

The project is designed primarily for:

* mortars
* grenade launchers
* vehicle cannons
* mounted weapons
* indirect fire systems
* high-angle ballistic shooting

Squad Ballistics provides a real-time customizable crosshair overlay, advanced ballistic calculations, FOV scaling, and an integrated browser for SquadCalc support.

The application was built with focus on:

* minimalistic tactical design
* high usability
* modern UI/UX
* fast calculations
* overlay customization
* standalone desktop experience

Main Features:

* Real-time ballistic calculations
* Dynamic crosshair overlay
* True Crosshair Editor
* RGB customization
* Glow / Bloom effects
* Built-in SquadCalc browser
* Auto-update system
* Hotkeys support
* Modern tactical interface
* Transparent overlay technology
* FOV scaling system
* Dynamic weapons database

Squad Ballistics is constantly evolving and aims to become one of the most advanced ballistic utility tools for Squad players.

---

# О проекте

## Русский

Squad Ballistics — это современный баллистический ассистент и система тактического оверлея для игры **Squad**.

Приложение помогает игрокам точно рассчитывать траекторию снарядов, поправки и смещение прицела для стрельбы навесом и ведения огня на дальние дистанции практически из всех видов оружия в игре.

Проект предназначен в первую очередь для:

* миномётов
* гранатомётов
* пушек техники
* стационарного вооружения
* систем непрямого огня
* навесной стрельбы

Squad Ballistics предоставляет:

* настраиваемый overlay-прицел в реальном времени
* баллистические вычисления
* масштабирование под FOV
* встроенный браузер с интеграцией SquadCalc
* современный минималистичный интерфейс

Главная цель проекта — сделать удобный и красивый инструмент для игроков Squad, который позволяет быстрее и точнее вести огонь на больших дистанциях.

Основные возможности:

* Баллистические расчёты в реальном времени
* Overlay-прицел
* True Crosshair Editor
* RGB кастомизация
* Glow / Bloom эффекты
* Встроенный браузер SquadCalc
* Система автообновлений
* Поддержка hotkeys
* Современный tactical UI
* Прозрачный overlay
* FOV scaling system
* Динамическая база оружия

Проект постоянно развивается и со временем должен стать полноценным тактическим инструментом для игроков Squad.

---

# Usage / Использование

1. Select a weapon, enter the distance to the target and (optionally) the height difference. Target higher than you is `+`, lower is `-`.
2. Enter your horizontal FOV: the in-game FOV setting, or the zoomed FOV when aiming through a scope.
3. Press **CALCULATE** or Enter. The overlay moves the aim mark below the screen centre: put the mark on the target and fire.
4. For high-angle weapons (mortars, Hell Cannon) the aim point is off-screen. Use the elevation shown in the app (degrees and mils).

1. Выберите оружие, введите дистанцию до цели и (необязательно) перепад высот: цель выше вас — `+`, ниже — `-`.
2. Укажите горизонтальный FOV: значение из настроек игры или FOV в прицеле, если стреляете через оптику.
3. Нажмите **CALCULATE** или Enter. Метка оверлея сместится вниз от центра экрана: наведите метку на цель и стреляйте.
4. Для навесного огня (миномёты, Hell Cannon) точка прицеливания за пределами экрана, используйте угол из программы (градусы и милы).

| Hotkey | Action / Действие |
|--------|-------------------|
| F8 | Show / hide overlay — показать / скрыть оверлей |
| F9 | Reset aim mark to centre — вернуть метку в центр |

On Windows the hotkeys are global, so they work while the game is focused. / В Windows горячие клавиши глобальные и работают поверх игры.

If the mark is slightly off in your setup, adjust **OFFSET CALIBRATION %** on the crosshair page. / Если метка немного не совпадает, подстройте **OFFSET CALIBRATION %** на странице прицела.

## How it works / Как считается

* No air drag, gravity `9.78 m/s² × gravity scale` of the weapon (the same model as SquadCalc). UB-32 rockets use the deceleration phase.
* Elevation: `θ = atan((v² ∓ √(v⁴ − g(g·d² + 2·h·v²))) / (g·d))`, low or high arc.
* Screen offset: rectilinear projection, `offset = (screen_width / 2) / tan(FOV / 2) × tan(θ)`, so it works on any resolution.

## Weapons database / База оружия

Weapons live in `weapons.json`. Only `velocity` is required:

```json
"SPG-9": {
    "velocity": 435,
    "gravity": 1.2,
    "arc": "low",
    "unit": "deg",
    "min_distance": 0,
    "elevation_limits": [-90, 90],
    "angle_offset": 0,
    "deceleration": 0,
    "deceleration_time": 0,
    "category": "Anti-tank",
    "note": ""
}
```

* `gravity`: projectile gravity scale (1 = normal).
* `arc`: default trajectory, `low` or `high`.
* `unit`: `mil` shows mils first (mortars).
* `angle_offset`: subtracted from the elevation, for weapons whose elevation readout is shifted (technical mortar).
* `deceleration` / `deceleration_time`: rocket slow-down phase (UB-32).

## Development / Разработка

```bash
pip install -r requirements-dev.txt
python app.py                  # run from source
pytest                         # tests (every weapon is checked)
pyinstaller SquadBallistics.spec  # build dist/SquadBallistics
```

User settings are stored in `%APPDATA%\SquadBallistics\config.json`. The old `configs/config.json` is migrated automatically.

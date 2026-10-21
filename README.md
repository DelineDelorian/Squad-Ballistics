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

1. Pick a weapon (searchable list, recent weapons on top), enter the distance and, optionally, the height difference: target higher `+`, lower `-`.
2. Enter your horizontal FOV: the in-game setting, or the zoomed FOV when aiming through a scope.
3. The result updates while you type. The **How to fire** block tells you exactly what to do for the selected weapon.
4. Direct fire (launchers, grenade launchers, guns): put the overlay mark on the target and fire.
5. Indirect fire (mortars, Hell Cannon, rockets): set the shown elevation (mils or degrees) on the weapon.

1. Выберите оружие (поиск по списку, недавние сверху), введите дистанцию и при необходимости перепад высот: цель выше `+`, ниже `-`.
2. Укажите горизонтальный FOV: значение из настроек игры или FOV прицела при стрельбе через оптику.
3. Результат пересчитывается при вводе. Блок **«Как стрелять»** говорит, что делать для выбранного оружия.
4. Прямая наводка (гранатомёты, пушки): совместите метку оверлея с целью и стреляйте.
5. Навесной огонь (миномёты, Hell Cannon, ракеты): выставьте показанный угол (милы или градусы) на орудии.

Tips / Советы:

* Both `.` and `,` work as the decimal separator on any keyboard layout; `-` anywhere in the height field flips the sign. / Дробную часть можно вводить через `.` или `,` в любой раскладке (на русской подойдут и клавиши «ю»/«б»); `-` в любом месте поля высоты меняет знак.
* The mouse wheel over a field changes the value (Shift ×0.1, Ctrl ×10). / Колесо мыши над полем меняет значение (Shift ×0.1, Ctrl ×10).

| Hotkey (default) | Action / Действие |
|------------------|-------------------|
| F8 | Show / hide overlay — показать / скрыть оверлей |
| F9 | Reset aim mark — сбросить метку |
| — | Distance + / − (bind in Settings) — дистанция + / − (назначается в настройках) |

Hotkeys can be changed in **Settings**. On Windows they are global, so they work while the game is focused. / Клавиши меняются в **Настройках**. В Windows они глобальные и работают поверх игры.

If the mark is slightly off in your setup, adjust **Offset calibration** in Settings. / Если метка немного не совпадает, подстройте **Калибровку смещения** в настройках.

### Map / Карта

The map tab embeds [SquadCalc](https://squadcalc.app). Map tiles are cached on disk, so a map you have opened loads instantly next time. / Вкладка карты встраивает SquadCalc; тайлы кэшируются на диске.

* **Black map / чёрная карта:** the app offers **Compatibility mode** (draws without the GPU) when the map looks black; it can also be switched in Settings → Map. / Если карта чёрная, программа предложит **режим совместимости** (Настройки → Карта).
* **Does not load / не грузится:** press **Retry** or **Open in browser**; Settings → Map → *Open the map in the regular browser* makes that the default. / Кнопки **Повторить** и **Открыть в браузере**; в настройках можно всегда открывать карту в обычном браузере.
* The embedded browser does not use QUIC, Encrypted Client Hello or secure DNS, which networks with blocking (e.g. in Russia) break. / Встроенный браузер не использует QUIC, ECH и защищённый DNS, которые ломаются в сетях с блокировками.

## Features / Возможности

* 52 standard weapons in 8 groups plus 7 popular mod weapons (hidden by default). / 52 стандартных вида оружия в 8 группах и 7 модовых (по умолчанию скрыты).
* Rocket boost and slow-down phases (RPG-7, Carl Gustav, NLAW, UB-32). / Учёт разгона и торможения ракет.
* Trajectory view, flight time, apex, impact angle, lead for moving targets. / График траектории, время полёта, высота подъёма, угол падения, упреждение.
* Crosshair page with live preview, presets, color swatches, outline and glow. / Прицел с живым предпросмотром, пресетами, палитрой, обводкой и свечением.
* Russian / English interface, accent colors, monitor choice, overlay center offset, label next to the mark. / Русский и английский интерфейс, цвет акцента, выбор монитора, смещение центра, подпись у метки.

## How it works / Как считается

* No air drag, gravity `9.78 m/s² × gravity scale` of the weapon. Rocket boost/slow-down is folded into the equivalent velocity over the distance.
* Elevation: `θ = atan((v² ∓ √(v⁴ − g(g·d² + 2·h·v²))) / (g·d))`, low or high arc.
* Screen offset: rectilinear projection, `offset = (screen_width / 2) / tan(FOV / 2) × tan(θ)`, so it works on any resolution.
* Data: in-game values from the [official Squad wiki](https://squad.fandom.com/wiki/Weapons) and [SquadCalc](https://github.com/sh4rkman/SquadCalc). After a game patch, edit `weapons.json`.

## Weapons database / База оружия

Weapons live in `weapons.json`. Only `velocity` is required:

```json
"RPG-7 · PG-7V HEAT / OG-7V": {
    "velocity": 117,
    "gravity": 1,
    "acceleration": 187.5,
    "acceleration_time": 0.8,
    "category": "launchers",
    "note": "English tip",
    "note_ru": "Подсказка"
}
```

* `gravity`: projectile gravity scale (1 = normal, 0 = no drop).
* `acceleration` / `acceleration_time`: rocket motor phase in m/s² and seconds (negative = slows down, UB-32).
* `arc`: default trajectory, `low` or `high`; `aim`: `overlay` (direct fire) or `elevation` (set the angle on the weapon).
* `unit`: `mil` shows mils first (mortars).
* `angle_offset`: subtracted from the elevation, for weapons whose readout is shifted (technical mortar).
* `min_distance`, `elevation_limits` `[min, max]`, `category`, `mod`.

## Development / Разработка

Windows, quick start (downloads the project into `Desktop\Squad-Ballistics`
and installs everything). Paste into PowerShell:

Windows, быстрый старт (скачает проект в `Рабочий стол\Squad-Ballistics` и
всё установит). Вставьте в PowerShell:

```powershell
irm https://raw.githubusercontent.com/DelineDelorian/Squad-Ballistics/refs/heads/claude/trusting-cray-6sbies/tools/get.ps1 | iex
```

| File | What it does / Что делает |
|------|---------------------------|
| `setup.bat` | Installs Python (if missing) and dependencies — установка |
| `run.bat` | Runs the app from source — запуск без сборки |
| `build.bat` | Builds and self-checks the single-file `dist\SquadBallistics.exe` — сборка exe |
| `test.bat` | Runs the tests — тесты |

Manual / вручную:

```bash
pip install -r requirements-dev.txt
python app.py                     # run from source
pytest                            # tests (every weapon is checked)
pyinstaller SquadBallistics.spec  # build dist/SquadBallistics
```

Every push builds the exe on GitHub Actions (**build-windows**, see
*Artifacts*) without publishing a release. How to publish an update:
[RELEASING.md](RELEASING.md).

Каждый push собирает exe в GitHub Actions (**build-windows**, раздел
*Artifacts*) без публикации релиза. Как выпустить обновление:
[RELEASING.md](RELEASING.md).

The app is a single `SquadBallistics.exe` and writes nothing next to it. / Программа — один файл `SquadBallistics.exe`, рядом с ним ничего не создаётся:

| What / Что | Where / Где |
|------------|-------------|
| Settings / настройки, `crash.log` | `%APPDATA%\SquadBallistics` |
| Map cache, SquadCalc settings / кэш карты | `%LOCALAPPDATA%\SquadBallistics\WebEngine` |
| Update download / загрузка обновления | `%TEMP%\SquadBallisticsUpdate` |

The old `configs/config.json` of versions ≤ 1.1.0 is migrated automatically, and their leftover `_internal` folder is removed after updating.

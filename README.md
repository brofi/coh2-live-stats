# <img src="src/coh2_live_stats/res/coh2_live_stats.ico" alt="Icon" width="64" align="center"/> CoH2 Live Stats

[![CI branch master](https://github.com/brofi/coh2-live-stats/actions/workflows/ci.yml/badge.svg)](https://github.com/brofi/coh2-live-stats/actions/workflows/ci.yml)

[//]: # (<mark_description>)

Show player and team stats of a currently played, replayed or last played Company of Heroes 2 match.

[//]: # (</mark_description>)


![Example output](src/coh2_live_stats/res/example_default.svg)

Example output on [Windows Terminal](https://github.com/microsoft/terminal)
with [gruvbox](https://github.com/morhetz/gruvbox) colors
and [Inconsolata](https://github.com/googlefonts/Inconsolata) font.

## Installation

You can either run _CoH2 Live Stats_ as a standalone bundled application or install and run it with Python.

### Run Bundle [Recommended]

1. [Download](https://github.com/brofi/coh2-live-stats/releases) latest release of _CoH2LiveStats-bundle-[version].zip_
2. Unzip and run _CoH2LiveStats.exe_


### Install from source

1. Get source code
   * [Download](https://github.com/brofi/coh2-live-stats/archive/refs/heads/master.zip) source files and unzip
   * **_or_** download and install [Git](https://git-scm.com/download/win) and run `git clone https://github.com/brofi/coh2-live-stats.git`
2. Download and install [Python](https://www.python.org/downloads/windows/) >= 3.12
3. Run `pip install .` from project root
4. Run `python -m coh2_live_stats` or simply `coh2livestats`

### Requirements

* Microsoft Windows
* (Optional) [Windows Terminal](https://github.com/microsoft/terminal) for proper UTF-8 support
* **_or_** Linux

## Configuration

_CoH2 Live Stats_ is configured via a TOML configuration file. A default configuration file named __coh2livestats.toml_
is supplied with the bundled application. A configuration file can be put in the user's home directory (_%USERPROFILE%_)
or left next to the application's executable.\
A configuration file can have one of the following names:

[//]: # (<mark_valid_configs>)

* _coh2livestats.toml
* .coh2livestats.toml
* coh2livestats.toml
* _coh2_live_stats.toml
* .coh2_live_stats.toml
* coh2_live_stats.toml

[//]: # (</mark_valid_configs>)

The first **valid** configuration file detected in the above order is used. The following sections describe all
available configuration attributes grouped by TOML table. All attributes ungrouped are found [here](#appendix). More
information on TOML syntax is found [here](https://toml.io/).


[//]: # (<mark_settings>)

### `[]` Root level settings

| Attribute | Type   | Description                                                                       |
|:----------|:-------|:----------------------------------------------------------------------------------|
| `logfile` | `Path` | Path to observed Company of Heroes 2 log file (supports OS environment variables) |

### `[notification]` Notification sound settings

| Attribute    | Type   | Default  | Description                                                                 |
|:-------------|:-------|:---------|:----------------------------------------------------------------------------|
| `play_sound` | `bool` | `true`   | Play a notification sound when a new multiplayer match was found            |
| `sound`      | `Path` | `'horn'` | Built-in notification sound name or full path to custom waveform audio file |

### `[table]` Output table settings

| Attribute                   | Type     | Default   | Description                                                                                 |
|:----------------------------|:---------|:----------|:--------------------------------------------------------------------------------------------|
| `color`                     | `bool`   | `true`    | Use color for output                                                                        |
| `border`                    | `Border` | `'inner'` | Border type of the output table                                                             |
| `header`                    | `bool`   | `true`    | Show output table header                                                                    |
| `show_average`              | `bool`   | `true`    | Show team's average rank and level                                                          |
| `always_show_team`          | `bool`   | `false`   | Always show team columns, even if they're empty                                             |
| `drop_ratio_high_threshold` | `float`  | `0.05`    | Drop ratios are considered high if they're higher than or equal this value (used for color) |
| `win_ratio_high_threshold`  | `float`  | `0.6`     | Win ratios are considered high if they're higher than or equal this value (used for color)  |
| `win_ratio_low_threshold`   | `float`  | `0.5`     | Win ratios are considered low if they're lower than this value (used for color)             |
| `prestige_star_char`        | `str`    | `'*'`     | Character to use for one prestige level star                                                |
| `prestige_half_star_char`   | `str`    | `'~'`     | Character to use for a half prestige level star                                             |

### `[table.colors]` Output table color settings

| Attribute | Type    | Default          | Description               |
|:----------|:--------|:-----------------|:--------------------------|
| `border`  | `Color` | `'bright black'` | Output table border color |
| `label`   | `Color` | `'bright black'` | Output table header color |

### `[table.colors.player]` Player-specific color settings

| Attribute        | Type    | Default          | Description                                        |
|:-----------------|:--------|:-----------------|:---------------------------------------------------|
| `high_drop_rate` | `Color` | `'red'`          | Color for a high player drop ratio                 |
| `high`           | `Color` | `'bright white'` | Color for highest ranked player and high win ratio |
| `low`            | `Color` | `'bright black'` | Color for lowest ranked player and low win ratio   |
| `win_streak`     | `Color` | `'green'`        | Color for a win streak                             |
| `loss_streak`    | `Color` | `'red'`          | Color for a loss streak                            |

### `[table.colors.faction]` Faction colors

| Attribute | Type    | Default    | Description             |
|:----------|:--------|:-----------|:------------------------|
| `wm`      | `Color` | `'red'`    | Wehrmacht color         |
| `su`      | `Color` | `'red'`    | Soviet Union color      |
| `okw`     | `Color` | `'cyan'`   | Oberkommando West color |
| `us`      | `Color` | `'blue'`   | US Forces color         |
| `uk`      | `Color` | `'yellow'` | British Forces color    |

### `[table.columns]` Output table columns

| Attribute       | Description                                                                                                                            |
|:----------------|:---------------------------------------------------------------------------------------------------------------------------------------|
| `faction`       | Player faction                                                                                                                         |
| `rank`          | Leaderboard rank if the player currently has a rank or highest known rank (indicator: +) if available or estimated rank (indicator: ?) |
| `level`         | Rank level representing the leaderboard rank                                                                                           |
| `prestige`      | Experience expressed in stars                                                                                                          |
| `streak`        | Number of games won (positive) or lost (negative) in a row                                                                             |
| `wins`          | Number of games won                                                                                                                    |
| `losses`        | Number of games lost                                                                                                                   |
| `win_ratio`     | Percentage of games won                                                                                                                |
| `drop_ratio`    | Percentage of games dropped                                                                                                            |
| `num_games`     | Total number of games played                                                                                                           |
| `team`          | The pre-made team the player is part of if any                                                                                         |
| `team_rank`     | The current rank of the pre-made team if any                                                                                           |
| `team_level`    | The current rank level of the pre-made team if any                                                                                     |
| `steam_profile` | Steam profile URL                                                                                                                      |
| `country`       | Player country                                                                                                                         |
| `name`          | Player name                                                                                                                            |

### For each `column` in `[table.columns]`:

| Attribute | Type    | Description                                |
|:----------|:--------|:-------------------------------------------|
| `label`   | `str`   | `column` header                            |
| `visible` | `bool`  | Whether to show the `column`               |
| `align`   | `Align` | `column` alignment                         |
| `pos`     | `int`   | `column` position used for column ordering |

### Custom types

| Type     | Values                                                                                                                                                                                                                                 |
|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `Border` | `'full'`, `'inner'` or `'none'`                                                                                                                                                                                                        |
| `Align`  | `'l'`, `'c'` or `'r'`                                                                                                                                                                                                                  |
| `Sound`  | `'horn_subtle'`, `'horn'` or `'horn_epic'`                                                                                                                                                                                             |
| `Color`  | `'black'`, `'red'`, `'green'`, `'yellow'`, `'blue'`, `'magenta'`, `'cyan'`, `'white'`, `'bright black'`, `'bright red'`, `'bright green'`, `'bright yellow'`, `'bright blue'`, `'bright magenta'`, `'bright cyan'` or `'bright white'` |


[//]: # (</mark_settings>)

### Example Configurations

[//]: # (<mark_examples>)


#### Description

* Add full border and remove the average row
* Remove column `drop_ratio` and `num_games`
* Add column `streak` and `prestige`
* Move column `prestige` to the front
* Move column `faction` in front of column `name`
* Unify faction colors


#### TOML configuration

```toml
[table]
border = 'full'
show_average = false

[table.columns.drop_ratio]
visible = false

[table.columns.num_games]
visible = false

[table.columns.streak]
visible = true

[table.columns.prestige]
visible = true
pos = -1

[table.columns.faction]
pos = 1

[table.columns.name]
pos = 2

[table.colors.faction]
okw = "red"
su = "blue"
uk = "blue"
```

#### Resulting output

![Example output](src/coh2_live_stats/res/example_0.svg)

#### Description

A minimalistic output configuration

#### TOML configuration

```toml
[table]
color = false
header = false
border = 'none'
show_average = false

[table.columns]
rank.visible = false
win_ratio.visible = false
drop_ratio.visible = false
num_games.visible = false
country.visible = false
team_rank.visible = false
```

#### Resulting output

![Example output](src/coh2_live_stats/res/example_1.svg)


[//]: # (</mark_examples>)

## Development

### Setup

* Create virtual environment: `python -m venv venv`
* Activate virtual environment:
  * Bash: `. venv/bin/activate`
  * PowerShell: `venv\Scripts\Activate.ps1`
  * cmd.exe: `venv\Scripts\activate.bat`


* Install project with development dependencies in editable mode:
```console
$ pip install invoke
$ inv install --dev
```

* Install `pre-commit` hooks:
```console
$ pre-commit install
```

* Install missing stub packages:
```console
$ mypy --install-types --non-interactive src tests scripts tasks.py
```

### Build

* Build with `setuptools` and `build` and create a `PyInstaller` bundle:
```console
$ inv build
```
* Distribution bundle: `.\dist_bundle\CoH2LiveStats-bundle-{version}.zip`
* See `inv -l` and `inv [task] -h` for more information on available `invoke` tasks


## Appendix

[//]: # (<mark_appendix>)

<details>
<summary>All configuration options</summary>

| Attribute                             | Type     | Default          | Description                                                                                                                            |
|:--------------------------------------|:---------|:-----------------|:---------------------------------------------------------------------------------------------------------------------------------------|
| `logfile`                             | `Path`   |                  | Path to observed Company of Heroes 2 log file (supports OS environment variables)                                                      |
| `[notification]`                      |          |                  | Notification sound settings                                                                                                            |
| `notification.play_sound`             | `bool`   | `true`           | Play a notification sound when a new multiplayer match was found                                                                       |
| `notification.sound`                  | `Path`   | `'horn'`         | Built-in notification sound name or full path to custom waveform audio file                                                            |
| `[table]`                             |          |                  | Output table settings                                                                                                                  |
| `table.color`                         | `bool`   | `true`           | Use color for output                                                                                                                   |
| `table.border`                        | `Border` | `'inner'`        | Border type of the output table                                                                                                        |
| `table.header`                        | `bool`   | `true`           | Show output table header                                                                                                               |
| `table.show_average`                  | `bool`   | `true`           | Show team's average rank and level                                                                                                     |
| `table.always_show_team`              | `bool`   | `false`          | Always show team columns, even if they're empty                                                                                        |
| `table.drop_ratio_high_threshold`     | `float`  | `0.05`           | Drop ratios are considered high if they're higher than or equal this value (used for color)                                            |
| `table.win_ratio_high_threshold`      | `float`  | `0.6`            | Win ratios are considered high if they're higher than or equal this value (used for color)                                             |
| `table.win_ratio_low_threshold`       | `float`  | `0.5`            | Win ratios are considered low if they're lower than this value (used for color)                                                        |
| `table.prestige_star_char`            | `str`    | `'*'`            | Character to use for one prestige level star                                                                                           |
| `table.prestige_half_star_char`       | `str`    | `'~'`            | Character to use for a half prestige level star                                                                                        |
| `[table.colors]`                      |          |                  | Output table color settings                                                                                                            |
| `table.colors.border`                 | `Color`  | `'bright black'` | Output table border color                                                                                                              |
| `table.colors.label`                  | `Color`  | `'bright black'` | Output table header color                                                                                                              |
| `[table.colors.player]`               |          |                  | Player-specific color settings                                                                                                         |
| `table.colors.player.high_drop_rate`  | `Color`  | `'red'`          | Color for a high player drop ratio                                                                                                     |
| `table.colors.player.high`            | `Color`  | `'bright white'` | Color for highest ranked player and high win ratio                                                                                     |
| `table.colors.player.low`             | `Color`  | `'bright black'` | Color for lowest ranked player and low win ratio                                                                                       |
| `table.colors.player.win_streak`      | `Color`  | `'green'`        | Color for a win streak                                                                                                                 |
| `table.colors.player.loss_streak`     | `Color`  | `'red'`          | Color for a loss streak                                                                                                                |
| `[table.colors.faction]`              |          |                  | Faction colors                                                                                                                         |
| `table.colors.faction.wm`             | `Color`  | `'red'`          | Wehrmacht color                                                                                                                        |
| `table.colors.faction.su`             | `Color`  | `'red'`          | Soviet Union color                                                                                                                     |
| `table.colors.faction.okw`            | `Color`  | `'cyan'`         | Oberkommando West color                                                                                                                |
| `table.colors.faction.us`             | `Color`  | `'blue'`         | US Forces color                                                                                                                        |
| `table.colors.faction.uk`             | `Color`  | `'yellow'`       | British Forces color                                                                                                                   |
| `[table.columns]`                     |          |                  | Output table columns                                                                                                                   |
| `[table.columns.faction]`             |          |                  | Player faction                                                                                                                         |
| `table.columns.faction.label`         | `str`    | `'Fac'`          | `faction` header                                                                                                                       |
| `table.columns.faction.visible`       | `bool`   | `true`           | Whether to show the `faction`                                                                                                          |
| `table.columns.faction.align`         | `Align`  | `'l'`            | `faction` alignment                                                                                                                    |
| `table.columns.faction.pos`           | `int`    | `0`              | `faction` position used for column ordering                                                                                            |
| `[table.columns.rank]`                |          |                  | Leaderboard rank if the player currently has a rank or highest known rank (indicator: +) if available or estimated rank (indicator: ?) |
| `table.columns.rank.label`            | `str`    | `'Rank'`         | `rank` header                                                                                                                          |
| `table.columns.rank.visible`          | `bool`   | `true`           | Whether to show the `rank`                                                                                                             |
| `table.columns.rank.align`            | `Align`  | `'r'`            | `rank` alignment                                                                                                                       |
| `table.columns.rank.pos`              | `int`    | `0`              | `rank` position used for column ordering                                                                                               |
| `[table.columns.level]`               |          |                  | Rank level representing the leaderboard rank                                                                                           |
| `table.columns.level.label`           | `str`    | `'Lvl'`          | `level` header                                                                                                                         |
| `table.columns.level.visible`         | `bool`   | `true`           | Whether to show the `level`                                                                                                            |
| `table.columns.level.align`           | `Align`  | `'r'`            | `level` alignment                                                                                                                      |
| `table.columns.level.pos`             | `int`    | `0`              | `level` position used for column ordering                                                                                              |
| `[table.columns.prestige]`            |          |                  | Experience expressed in stars                                                                                                          |
| `table.columns.prestige.label`        | `str`    | `'XP'`           | `prestige` header                                                                                                                      |
| `table.columns.prestige.visible`      | `bool`   | `false`          | Whether to show the `prestige`                                                                                                         |
| `table.columns.prestige.align`        | `Align`  | `'l'`            | `prestige` alignment                                                                                                                   |
| `table.columns.prestige.pos`          | `int`    | `0`              | `prestige` position used for column ordering                                                                                           |
| `[table.columns.streak]`              |          |                  | Number of games won (positive) or lost (negative) in a row                                                                             |
| `table.columns.streak.label`          | `str`    | `'+/-'`          | `streak` header                                                                                                                        |
| `table.columns.streak.visible`        | `bool`   | `false`          | Whether to show the `streak`                                                                                                           |
| `table.columns.streak.align`          | `Align`  | `'l'`            | `streak` alignment                                                                                                                     |
| `table.columns.streak.pos`            | `int`    | `0`              | `streak` position used for column ordering                                                                                             |
| `[table.columns.wins]`                |          |                  | Number of games won                                                                                                                    |
| `table.columns.wins.label`            | `str`    | `'W'`            | `wins` header                                                                                                                          |
| `table.columns.wins.visible`          | `bool`   | `false`          | Whether to show the `wins`                                                                                                             |
| `table.columns.wins.align`            | `Align`  | `'l'`            | `wins` alignment                                                                                                                       |
| `table.columns.wins.pos`              | `int`    | `0`              | `wins` position used for column ordering                                                                                               |
| `[table.columns.losses]`              |          |                  | Number of games lost                                                                                                                   |
| `table.columns.losses.label`          | `str`    | `'L'`            | `losses` header                                                                                                                        |
| `table.columns.losses.visible`        | `bool`   | `false`          | Whether to show the `losses`                                                                                                           |
| `table.columns.losses.align`          | `Align`  | `'l'`            | `losses` alignment                                                                                                                     |
| `table.columns.losses.pos`            | `int`    | `0`              | `losses` position used for column ordering                                                                                             |
| `[table.columns.win_ratio]`           |          |                  | Percentage of games won                                                                                                                |
| `table.columns.win_ratio.label`       | `str`    | `'W%'`           | `win_ratio` header                                                                                                                     |
| `table.columns.win_ratio.visible`     | `bool`   | `true`           | Whether to show the `win_ratio`                                                                                                        |
| `table.columns.win_ratio.align`       | `Align`  | `'r'`            | `win_ratio` alignment                                                                                                                  |
| `table.columns.win_ratio.pos`         | `int`    | `0`              | `win_ratio` position used for column ordering                                                                                          |
| `[table.columns.drop_ratio]`          |          |                  | Percentage of games dropped                                                                                                            |
| `table.columns.drop_ratio.label`      | `str`    | `'Drop%'`        | `drop_ratio` header                                                                                                                    |
| `table.columns.drop_ratio.visible`    | `bool`   | `true`           | Whether to show the `drop_ratio`                                                                                                       |
| `table.columns.drop_ratio.align`      | `Align`  | `'r'`            | `drop_ratio` alignment                                                                                                                 |
| `table.columns.drop_ratio.pos`        | `int`    | `0`              | `drop_ratio` position used for column ordering                                                                                         |
| `[table.columns.num_games]`           |          |                  | Total number of games played                                                                                                           |
| `table.columns.num_games.label`       | `str`    | `'Total'`        | `num_games` header                                                                                                                     |
| `table.columns.num_games.visible`     | `bool`   | `true`           | Whether to show the `num_games`                                                                                                        |
| `table.columns.num_games.align`       | `Align`  | `'l'`            | `num_games` alignment                                                                                                                  |
| `table.columns.num_games.pos`         | `int`    | `0`              | `num_games` position used for column ordering                                                                                          |
| `[table.columns.team]`                |          |                  | The pre-made team the player is part of if any                                                                                         |
| `table.columns.team.label`            | `str`    | `'Team'`         | `team` header                                                                                                                          |
| `table.columns.team.visible`          | `bool`   | `true`           | Whether to show the `team`                                                                                                             |
| `table.columns.team.align`            | `Align`  | `'c'`            | `team` alignment                                                                                                                       |
| `table.columns.team.pos`              | `int`    | `0`              | `team` position used for column ordering                                                                                               |
| `[table.columns.team_rank]`           |          |                  | The current rank of the pre-made team if any                                                                                           |
| `table.columns.team_rank.label`       | `str`    | `'T_Rank'`       | `team_rank` header                                                                                                                     |
| `table.columns.team_rank.visible`     | `bool`   | `true`           | Whether to show the `team_rank`                                                                                                        |
| `table.columns.team_rank.align`       | `Align`  | `'r'`            | `team_rank` alignment                                                                                                                  |
| `table.columns.team_rank.pos`         | `int`    | `0`              | `team_rank` position used for column ordering                                                                                          |
| `[table.columns.team_level]`          |          |                  | The current rank level of the pre-made team if any                                                                                     |
| `table.columns.team_level.label`      | `str`    | `'T_Lvl'`        | `team_level` header                                                                                                                    |
| `table.columns.team_level.visible`    | `bool`   | `true`           | Whether to show the `team_level`                                                                                                       |
| `table.columns.team_level.align`      | `Align`  | `'r'`            | `team_level` alignment                                                                                                                 |
| `table.columns.team_level.pos`        | `int`    | `0`              | `team_level` position used for column ordering                                                                                         |
| `[table.columns.steam_profile]`       |          |                  | Steam profile URL                                                                                                                      |
| `table.columns.steam_profile.label`   | `str`    | `'Profile'`      | `steam_profile` header                                                                                                                 |
| `table.columns.steam_profile.visible` | `bool`   | `false`          | Whether to show the `steam_profile`                                                                                                    |
| `table.columns.steam_profile.align`   | `Align`  | `'l'`            | `steam_profile` alignment                                                                                                              |
| `table.columns.steam_profile.pos`     | `int`    | `0`              | `steam_profile` position used for column ordering                                                                                      |
| `[table.columns.country]`             |          |                  | Player country                                                                                                                         |
| `table.columns.country.label`         | `str`    | `'Country'`      | `country` header                                                                                                                       |
| `table.columns.country.visible`       | `bool`   | `true`           | Whether to show the `country`                                                                                                          |
| `table.columns.country.align`         | `Align`  | `'l'`            | `country` alignment                                                                                                                    |
| `table.columns.country.pos`           | `int`    | `0`              | `country` position used for column ordering                                                                                            |
| `[table.columns.name]`                |          |                  | Player name                                                                                                                            |
| `table.columns.name.label`            | `str`    | `'Name'`         | `name` header                                                                                                                          |
| `table.columns.name.visible`          | `bool`   | `true`           | Whether to show the `name`                                                                                                             |
| `table.columns.name.align`            | `Align`  | `'l'`            | `name` alignment                                                                                                                       |
| `table.columns.name.pos`              | `int`    | `0`              | `name` position used for column ordering                                                                                               |

</details>
<details>
<summary>Full default configuration</summary>

```toml
logfile = "%USERPROFILE%\\Documents\\My Games\\Company of Heroes 2\\warnings.log"

[notification]
play_sound = true
sound = "horn"

[table]
color = true
border = "inner"
header = true
show_average = true
always_show_team = false
drop_ratio_high_threshold = 0.05
win_ratio_high_threshold = 0.6
win_ratio_low_threshold = 0.5
prestige_star_char = "*"
prestige_half_star_char = "~"

[table.colors]
border = "BRIGHT_BLACK"
label = "BRIGHT_BLACK"

[table.colors.player]
high_drop_rate = "RED"
high = "BRIGHT_WHITE"
low = "BRIGHT_BLACK"
win_streak = "GREEN"
loss_streak = "RED"

[table.colors.faction]
wm = "RED"
su = "RED"
okw = "CYAN"
us = "BLUE"
uk = "YELLOW"

[table.columns]
[table.columns.faction]
label = "Fac"
visible = true
align = "l"
pos = 0

[table.columns.rank]
label = "Rank"
visible = true
align = "r"
pos = 0

[table.columns.level]
label = "Lvl"
visible = true
align = "r"
pos = 0

[table.columns.prestige]
label = "XP"
visible = false
align = "l"
pos = 0

[table.columns.streak]
label = "+/-"
visible = false
align = "l"
pos = 0

[table.columns.wins]
label = "W"
visible = false
align = "l"
pos = 0

[table.columns.losses]
label = "L"
visible = false
align = "l"
pos = 0

[table.columns.win_ratio]
label = "W%"
visible = true
align = "r"
pos = 0

[table.columns.drop_ratio]
label = "Drop%"
visible = true
align = "r"
pos = 0

[table.columns.num_games]
label = "Total"
visible = true
align = "l"
pos = 0

[table.columns.team]
label = "Team"
visible = true
align = "c"
pos = 0

[table.columns.team_rank]
label = "T_Rank"
visible = true
align = "r"
pos = 0

[table.columns.team_level]
label = "T_Lvl"
visible = true
align = "r"
pos = 0

[table.columns.steam_profile]
label = "Profile"
visible = false
align = "l"
pos = 0

[table.columns.country]
label = "Country"
visible = true
align = "l"
pos = 0

[table.columns.name]
label = "Name"
visible = true
align = "l"
pos = 0

```
</details>

[//]: # (</mark_appendix>)

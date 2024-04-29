# CoH2 Live Stats

Show match stats of a currently played, replayed or last played Company of Heroes 2 match.

---

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

| Attribute | Type | Description                                                                       |
|:----------|:-----|:----------------------------------------------------------------------------------|
| `logfile` | Path | Path to observed Company of Heroes 2 log file (supports OS environment variables) |

### `[notification]` Notification sound settings

| Attribute    | Type | Default | Description                                                                 |
|:-------------|:-----|:--------|:----------------------------------------------------------------------------|
| `play_sound` | bool | True    | Play a notification sound when a new multiplayer match was found            |
| `sound`      | Path | horn    | Built-in notification sound name or full path to custom waveform audio file |

### `[table]` Output table settings

| Attribute                   | Type  | Default | Description                                                                                 |
|:----------------------------|:------|:--------|:--------------------------------------------------------------------------------------------|
| `color`                     | bool  | True    | Use color for output                                                                        |
| `border`                    | bool  | False   | Draw a border around the output table                                                       |
| `show_average`              | bool  | True    | Show team's average rank and level                                                          |
| `always_show_team`          | bool  | False   | Always show team columns, even if they're empty                                             |
| `drop_ratio_high_threshold` | float | 0.05    | Drop ratios are considered high if they're higher than or equal this value (used for color) |
| `win_ratio_high_threshold`  | float | 0.6     | Win ratios are considered high if they're higher than or equal this value (used for color)  |
| `win_ratio_low_threshold`   | float | 0.5     | Win ratios are considered low if they're lower than this value (used for color)             |
| `prestige_star_char`        | str   | *       | Character to use for one prestige level star                                                |
| `prestige_half_star_char`   | str   | ~       | Character to use for a half prestige level star                                             |

### `[table.colors]` Output table color settings

| Attribute | Type  | Default      | Description               |
|:----------|:------|:-------------|:--------------------------|
| `border`  | Color | bright black | Output table border color |
| `label`   | Color | bright black | Output table header color |

### `[table.colors.player]` Player-specific color settings

| Attribute        | Type  | Default      | Description                                        |
|:-----------------|:------|:-------------|:---------------------------------------------------|
| `high_drop_rate` | Color | red          | Color for a high player drop ratio                 |
| `high`           | Color | bright white | Color for highest ranked player and high win ratio |
| `low`            | Color | bright black | Color for lowest ranked player and low win ratio   |

### `[table.colors.faction]` Faction colors

| Attribute | Type  | Default | Description             |
|:----------|:------|:--------|:------------------------|
| `wm`      | Color | red     | Wehrmacht color         |
| `su`      | Color | red     | Soviet Union color      |
| `okw`     | Color | cyan    | Oberkommando West color |
| `us`      | Color | blue    | US Forces color         |
| `uk`      | Color | yellow  | British Forces color    |

### `[table.columns]` Output table columns

| Attribute       | Description                                                                                                                            |
|:----------------|:---------------------------------------------------------------------------------------------------------------------------------------|
| `faction`       | Player faction                                                                                                                         |
| `rank`          | Leaderboard rank if the player currently has a rank or highest known rank (indicator: +) if available or estimated rank (indicator: ?) |
| `level`         | Rank level representing the leaderboard rank                                                                                           |
| `prestige`      | Experience expressed in stars                                                                                                          |
| `win_ratio`     | Percentage of games won                                                                                                                |
| `drop_ratio`    | Percentage of games dropped                                                                                                            |
| `team`          | The pre-made team the player is part of if any                                                                                         |
| `team_rank`     | The current rank of the pre-made team if any                                                                                           |
| `team_level`    | The current rank level of the pre-made team if any                                                                                     |
| `steam_profile` | Steam profile URL                                                                                                                      |
| `country`       | Player country                                                                                                                         |
| `name`          | Player name                                                                                                                            |

### For each `column` in `[table.columns]`:

| Attribute | Type    | Description                                |
|:----------|:--------|:-------------------------------------------|
| `label`   | str     | `column` header                            |
| `visible` | bool    | Whether to show the `column`               |
| `align`   | l, c, r | `column` alignment                         |
| `pos`     | int     | `column` position used for column ordering |

### Appendix

<details>
<summary>All settings</summary>

| Attribute                             | Type    | Default      | Description                                                                                                                            |
|:--------------------------------------|:--------|:-------------|:---------------------------------------------------------------------------------------------------------------------------------------|
| `logfile`                             | Path    |              | Path to observed Company of Heroes 2 log file (supports OS environment variables)                                                      |
| `[notification]`                      |         |              | Notification sound settings                                                                                                            |
| `notification.play_sound`             | bool    | True         | Play a notification sound when a new multiplayer match was found                                                                       |
| `notification.sound`                  | Path    | horn         | Built-in notification sound name or full path to custom waveform audio file                                                            |
| `[table]`                             |         |              | Output table settings                                                                                                                  |
| `table.color`                         | bool    | True         | Use color for output                                                                                                                   |
| `table.border`                        | bool    | False        | Draw a border around the output table                                                                                                  |
| `table.show_average`                  | bool    | True         | Show team's average rank and level                                                                                                     |
| `table.always_show_team`              | bool    | False        | Always show team columns, even if they're empty                                                                                        |
| `table.drop_ratio_high_threshold`     | float   | 0.05         | Drop ratios are considered high if they're higher than or equal this value (used for color)                                            |
| `table.win_ratio_high_threshold`      | float   | 0.6          | Win ratios are considered high if they're higher than or equal this value (used for color)                                             |
| `table.win_ratio_low_threshold`       | float   | 0.5          | Win ratios are considered low if they're lower than this value (used for color)                                                        |
| `table.prestige_star_char`            | str     | *            | Character to use for one prestige level star                                                                                           |
| `table.prestige_half_star_char`       | str     | ~            | Character to use for a half prestige level star                                                                                        |
| `[table.colors]`                      |         |              | Output table color settings                                                                                                            |
| `table.colors.border`                 | Color   | bright black | Output table border color                                                                                                              |
| `table.colors.label`                  | Color   | bright black | Output table header color                                                                                                              |
| `[table.colors.player]`               |         |              | Player-specific color settings                                                                                                         |
| `table.colors.player.high_drop_rate`  | Color   | red          | Color for a high player drop ratio                                                                                                     |
| `table.colors.player.high`            | Color   | bright white | Color for highest ranked player and high win ratio                                                                                     |
| `table.colors.player.low`             | Color   | bright black | Color for lowest ranked player and low win ratio                                                                                       |
| `[table.colors.faction]`              |         |              | Faction colors                                                                                                                         |
| `table.colors.faction.wm`             | Color   | red          | Wehrmacht color                                                                                                                        |
| `table.colors.faction.su`             | Color   | red          | Soviet Union color                                                                                                                     |
| `table.colors.faction.okw`            | Color   | cyan         | Oberkommando West color                                                                                                                |
| `table.colors.faction.us`             | Color   | blue         | US Forces color                                                                                                                        |
| `table.colors.faction.uk`             | Color   | yellow       | British Forces color                                                                                                                   |
| `[table.columns]`                     |         |              | Output table columns                                                                                                                   |
| `[table.columns.faction]`             |         |              | Player faction                                                                                                                         |
| `table.columns.faction.label`         | str     | Fac          | `faction` header                                                                                                                       |
| `table.columns.faction.visible`       | bool    | True         | Whether to show the `faction`                                                                                                          |
| `table.columns.faction.align`         | l, c, r | l            | `faction` alignment                                                                                                                    |
| `table.columns.faction.pos`           | int     | 0            | `faction` position used for column ordering                                                                                            |
| `[table.columns.rank]`                |         |              | Leaderboard rank if the player currently has a rank or highest known rank (indicator: +) if available or estimated rank (indicator: ?) |
| `table.columns.rank.label`            | str     | Rank         | `rank` header                                                                                                                          |
| `table.columns.rank.visible`          | bool    | True         | Whether to show the `rank`                                                                                                             |
| `table.columns.rank.align`            | l, c, r | r            | `rank` alignment                                                                                                                       |
| `table.columns.rank.pos`              | int     | 0            | `rank` position used for column ordering                                                                                               |
| `[table.columns.level]`               |         |              | Rank level representing the leaderboard rank                                                                                           |
| `table.columns.level.label`           | str     | Lvl          | `level` header                                                                                                                         |
| `table.columns.level.visible`         | bool    | True         | Whether to show the `level`                                                                                                            |
| `table.columns.level.align`           | l, c, r | r            | `level` alignment                                                                                                                      |
| `table.columns.level.pos`             | int     | 0            | `level` position used for column ordering                                                                                              |
| `[table.columns.prestige]`            |         |              | Experience expressed in stars                                                                                                          |
| `table.columns.prestige.label`        | str     | XP           | `prestige` header                                                                                                                      |
| `table.columns.prestige.visible`      | bool    | False        | Whether to show the `prestige`                                                                                                         |
| `table.columns.prestige.align`        | l, c, r | l            | `prestige` alignment                                                                                                                   |
| `table.columns.prestige.pos`          | int     | 0            | `prestige` position used for column ordering                                                                                           |
| `[table.columns.win_ratio]`           |         |              | Percentage of games won                                                                                                                |
| `table.columns.win_ratio.label`       | str     | W%           | `win_ratio` header                                                                                                                     |
| `table.columns.win_ratio.visible`     | bool    | True         | Whether to show the `win_ratio`                                                                                                        |
| `table.columns.win_ratio.align`       | l, c, r | r            | `win_ratio` alignment                                                                                                                  |
| `table.columns.win_ratio.pos`         | int     | 0            | `win_ratio` position used for column ordering                                                                                          |
| `[table.columns.drop_ratio]`          |         |              | Percentage of games dropped                                                                                                            |
| `table.columns.drop_ratio.label`      | str     | Drop%        | `drop_ratio` header                                                                                                                    |
| `table.columns.drop_ratio.visible`    | bool    | True         | Whether to show the `drop_ratio`                                                                                                       |
| `table.columns.drop_ratio.align`      | l, c, r | r            | `drop_ratio` alignment                                                                                                                 |
| `table.columns.drop_ratio.pos`        | int     | 0            | `drop_ratio` position used for column ordering                                                                                         |
| `[table.columns.team]`                |         |              | The pre-made team the player is part of if any                                                                                         |
| `table.columns.team.label`            | str     | Team         | `team` header                                                                                                                          |
| `table.columns.team.visible`          | bool    | True         | Whether to show the `team`                                                                                                             |
| `table.columns.team.align`            | l, c, r | c            | `team` alignment                                                                                                                       |
| `table.columns.team.pos`              | int     | 0            | `team` position used for column ordering                                                                                               |
| `[table.columns.team_rank]`           |         |              | The current rank of the pre-made team if any                                                                                           |
| `table.columns.team_rank.label`       | str     | T_Rank       | `team_rank` header                                                                                                                     |
| `table.columns.team_rank.visible`     | bool    | True         | Whether to show the `team_rank`                                                                                                        |
| `table.columns.team_rank.align`       | l, c, r | r            | `team_rank` alignment                                                                                                                  |
| `table.columns.team_rank.pos`         | int     | 0            | `team_rank` position used for column ordering                                                                                          |
| `[table.columns.team_level]`          |         |              | The current rank level of the pre-made team if any                                                                                     |
| `table.columns.team_level.label`      | str     | T_Level      | `team_level` header                                                                                                                    |
| `table.columns.team_level.visible`    | bool    | True         | Whether to show the `team_level`                                                                                                       |
| `table.columns.team_level.align`      | l, c, r | r            | `team_level` alignment                                                                                                                 |
| `table.columns.team_level.pos`        | int     | 0            | `team_level` position used for column ordering                                                                                         |
| `[table.columns.steam_profile]`       |         |              | Steam profile URL                                                                                                                      |
| `table.columns.steam_profile.label`   | str     | Profile      | `steam_profile` header                                                                                                                 |
| `table.columns.steam_profile.visible` | bool    | False        | Whether to show the `steam_profile`                                                                                                    |
| `table.columns.steam_profile.align`   | l, c, r | l            | `steam_profile` alignment                                                                                                              |
| `table.columns.steam_profile.pos`     | int     | 0            | `steam_profile` position used for column ordering                                                                                      |
| `[table.columns.country]`             |         |              | Player country                                                                                                                         |
| `table.columns.country.label`         | str     | Country      | `country` header                                                                                                                       |
| `table.columns.country.visible`       | bool    | True         | Whether to show the `country`                                                                                                          |
| `table.columns.country.align`         | l, c, r | l            | `country` alignment                                                                                                                    |
| `table.columns.country.pos`           | int     | 0            | `country` position used for column ordering                                                                                            |
| `[table.columns.name]`                |         |              | Player name                                                                                                                            |
| `table.columns.name.label`            | str     | Name         | `name` header                                                                                                                          |
| `table.columns.name.visible`          | bool    | True         | Whether to show the `name`                                                                                                             |
| `table.columns.name.align`            | l, c, r | l            | `name` alignment                                                                                                                       |
| `table.columns.name.pos`              | int     | 0            | `name` position used for column ordering                                                                                               |

</details>

[//]: # (</mark_settings>)

### Example Configurations

[//]: # (<mark_examples>)


#### Description

* Add a border and remove the average row
* Remove column `drop_ratio`
* Add column `prestige`
* Move column `prestige` to the front
* Move column `faction` in front of column `name`
* Unify faction colors


#### TOML configuration

```toml
[table]
border = true
show_average = false

[table.columns.drop_ratio]
visible = false

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
show_average = false

[table.columns]
rank.visible = false
win_ratio.visible = false
drop_ratio.visible = false
country.visible = false
team.label = "T"
team_rank.visible = false
team_level.label = "TL"
```

#### Resulting output

![Example output](src/coh2_live_stats/res/example_1.svg)


[//]: # (</mark_examples>)

## Development

### Setup

* Create and activate virtual environment:
```console
$  python -m venv venv
$ .\venv\Scripts\Activate.ps1
```

* Install project with development dependencies in editable mode:
```console
$ pip install invoke
$ inv install --dev
```

* Install `pre-commit` hooks:
```console
$ pre-commit install
```

### Build

* Build with `setuptools` and `build` and create a `PyInstaller` bundle:
```console
$ inv build
```
* Distribution bundle: `.\dist\CoH2LiveStats-bundle-{version}.zip`
* See `inv -l` and `inv [task] -h` for more information on available `invoke` tasks

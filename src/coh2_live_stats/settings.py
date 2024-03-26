#  Copyright (C) 2024 Andreas Becker.
#
#  This file is part of CoH2LiveStats.
#
#  CoH2LiveStats is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any
#  later version.
#
#  Foobar is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with Foobar. If not,
#  see <https://www.gnu.org/licenses/>.

import operator
import sys
from contextlib import suppress
from functools import reduce
from os.path import expandvars
from pathlib import Path
from tomllib import load, TOMLDecodeError

from .data.align import Align
from .data.color import Color
from .data.column import Column
from .data.faction import Faction

type Key = tuple[str, ...]


class _Section:
    def __init__(self, *key):
        self.KEY: Key = key


class _SectionTableColorsPlayer(_Section):
    def __init__(self, *key):
        super().__init__(*key, 'player')
        self.KEY_HIGH_DROP_RATE = *self.KEY, 'high_drop_rate'
        self.KEY_HIGH = *self.KEY, 'high'
        self.KEY_LOW = *self.KEY, 'low'


class _SectionTableColorsFaction(_Section):
    def __init__(self, *key):
        super().__init__(*key, 'faction')

    def key(self, f: Faction):
        return *self.KEY, f.name.lower()


class _SectionTableColumns(_Section):
    KEY_COLUMN_LABEL = 'label'
    KEY_COLUMN_ALIGN = 'align'

    def __init__(self, *key):
        super().__init__(*key, 'columns')

    def key(self, c: Column):
        return *self.KEY, c.name.lower()

    def key_label(self, c: Column):
        return *self.key(c), self.KEY_COLUMN_LABEL

    def key_align(self, c: Column):
        return *self.key(c), self.KEY_COLUMN_ALIGN


class _SectionTableColors(_Section):
    def __init__(self, *key):
        super().__init__(*key, 'colors')
        self.KEY_BORDER = *self.KEY, 'border'
        self.KEY_LABEL = *self.KEY, 'label'
        self.Player = _SectionTableColorsPlayer(*self.KEY)
        self.Faction = _SectionTableColorsFaction(*self.KEY)


class _SectionTable(_Section):
    def __init__(self):
        super().__init__('table')
        self.KEY_COLOR = *self.KEY, 'color'
        self.KEY_BORDER = *self.KEY, 'border'
        self.KEY_SHOW_AVERAGE = *self.KEY, 'show_average'
        self.KEY_ALWAYS_SHOW_TEAM = *self.KEY, 'always_show_team'
        self.Colors = _SectionTableColors(*self.KEY)
        self.Columns = _SectionTableColumns(*self.KEY)


class _SectionNotification(_Section):
    def __init__(self):
        super().__init__('notification')
        self.KEY_PLAY_SOUND = *self.KEY, 'play_sound'
        self.KEY_SOUND = *self.KEY, 'sound'


class Keys:
    KEY_LOGFILE = ('logfile',)
    Table = _SectionTable()
    Notification = _SectionNotification()

    @staticmethod
    def name(key: Key):
        return str(key[-1]) if len(key) > 0 else ''


class Settings:
    _config_default = {
        Keys.name(Keys.KEY_LOGFILE):
            str(Path.home().joinpath('Documents', 'My Games', 'Company of Heroes 2', 'warnings.log')),
        Keys.name(Keys.Table.KEY): {
            Keys.name(Keys.Table.KEY_COLOR): True,
            Keys.name(Keys.Table.KEY_BORDER): False,
            Keys.name(Keys.Table.KEY_SHOW_AVERAGE): True,
            Keys.name(Keys.Table.KEY_ALWAYS_SHOW_TEAM): False,
            Keys.name(Keys.Table.Columns.KEY): {
                Keys.name(Keys.Table.Columns.key(Column.FACTION)): {
                    Keys.Table.Columns.KEY_COLUMN_LABEL: 'Fac',
                    Keys.Table.Columns.KEY_COLUMN_ALIGN: Align.LEFT.value,
                },
                Keys.name(Keys.Table.Columns.key(Column.RANK)): {
                    Keys.Table.Columns.KEY_COLUMN_LABEL: 'Rank',
                    Keys.Table.Columns.KEY_COLUMN_ALIGN: Align.RIGHT.value,
                },
                Keys.name(Keys.Table.Columns.key(Column.LEVEL)): {
                    Keys.Table.Columns.KEY_COLUMN_LABEL: 'Lvl',
                    Keys.Table.Columns.KEY_COLUMN_ALIGN: Align.RIGHT.value,
                },
                Keys.name(Keys.Table.Columns.key(Column.WIN_RATIO)): {
                    Keys.Table.Columns.KEY_COLUMN_LABEL: 'W%',
                    Keys.Table.Columns.KEY_COLUMN_ALIGN: Align.RIGHT.value,
                },
                Keys.name(Keys.Table.Columns.key(Column.DROP_RATIO)): {
                    Keys.Table.Columns.KEY_COLUMN_LABEL: 'D%',
                    Keys.Table.Columns.KEY_COLUMN_ALIGN: Align.RIGHT.value,
                },
                Keys.name(Keys.Table.Columns.key(Column.TEAM)): {
                    Keys.Table.Columns.KEY_COLUMN_LABEL: 'Team',
                    Keys.Table.Columns.KEY_COLUMN_ALIGN: Align.CENTER.value,
                },
                Keys.name(Keys.Table.Columns.key(Column.TEAM_RANK)): {
                    Keys.Table.Columns.KEY_COLUMN_LABEL: 'T_Rank',
                    Keys.Table.Columns.KEY_COLUMN_ALIGN: Align.RIGHT.value,
                },
                Keys.name(Keys.Table.Columns.key(Column.TEAM_LEVEL)): {
                    Keys.Table.Columns.KEY_COLUMN_LABEL: 'T_Level',
                    Keys.Table.Columns.KEY_COLUMN_ALIGN: Align.RIGHT.value,
                },
                Keys.name(Keys.Table.Columns.key(Column.COUNTRY)): {
                    Keys.Table.Columns.KEY_COLUMN_LABEL: 'Country',
                    Keys.Table.Columns.KEY_COLUMN_ALIGN: Align.LEFT.value,
                },
                Keys.name(Keys.Table.Columns.key(Column.NAME)): {
                    Keys.Table.Columns.KEY_COLUMN_LABEL: 'Name',
                    Keys.Table.Columns.KEY_COLUMN_ALIGN: Align.LEFT.value,
                }
            },
            Keys.name(Keys.Table.Colors.KEY): {
                Keys.name(Keys.Table.Colors.KEY_BORDER): Color.BRIGHT_BLACK.name,
                Keys.name(Keys.Table.Colors.KEY_LABEL): Color.BRIGHT_BLACK.name,
                Keys.name(Keys.Table.Colors.Player.KEY): {
                    Keys.name(Keys.Table.Colors.Player.KEY_HIGH_DROP_RATE): Color.RED.name,
                    Keys.name(Keys.Table.Colors.Player.KEY_HIGH): Color.BRIGHT_WHITE.name,
                    Keys.name(Keys.Table.Colors.Player.KEY_LOW): Color.BRIGHT_BLACK.name,
                },
                Keys.name(Keys.Table.Colors.Faction.KEY): {
                    Keys.name(Keys.Table.Colors.Faction.key(Faction.WM)): Color.RED.name,
                    Keys.name(Keys.Table.Colors.Faction.key(Faction.SU)): Color.RED.name,
                    Keys.name(Keys.Table.Colors.Faction.key(Faction.OKW)): Color.CYAN.name,
                    Keys.name(Keys.Table.Colors.Faction.key(Faction.US)): Color.BLUE.name,
                    Keys.name(Keys.Table.Colors.Faction.key(Faction.UK)): Color.YELLOW.name,
                }
            }
        },
        Keys.name(Keys.Notification.KEY): {
            Keys.name(Keys.Notification.KEY_PLAY_SOUND): True,
            Keys.name(Keys.Notification.KEY_SOUND): 'horn',
        }}

    def __init__(self):
        self._config = self._get_config()
        self._validate()

    @staticmethod
    def _get_config():
        config = {}
        config_paths = ['%USERPROFILE%', str(Path(getattr(sys, '_MEIPASS', __file__)).parent)]
        config_names = [f'{p}{b}.toml' for b in ['coh2livestats', 'coh2_live_stats'] for p in ['_', '.', '']]
        config_files = [Path(expandvars(p)).joinpath(n) for p in config_paths for n in config_names]
        for c in config_files:
            try:
                with open(c, 'rb') as f:
                    config = load(f)
                    break
            except TOMLDecodeError as e:
                print('Error: Invalid TOML')
                print(f'\tFile: {c}')
                print(f'\tCause: {e.args[0]}')
            except FileNotFoundError:
                pass
        return config

    def get_logfile(self):
        return self.get_as_path(Keys.KEY_LOGFILE)

    def get_as_path(self, key: Key):
        return Path(expandvars(self.get(key)))

    def get_faction_color(self, faction: Faction):
        return self.get_as_color((*Keys.Table.Colors.Faction.KEY, faction.name.lower()))

    def get_as_color(self, key: Key):
        return Color[self.get(key).upper()]

    def get_notification_sound(self):
        v = self.get(Keys.Notification.KEY_SOUND)
        if v in ['horn', 'horn_subtle', 'horn_epic']:
            return Path(getattr(sys, '_MEIPASS', str(Path(__file__).parent))).joinpath('res', f'{v}.wav')
        else:
            return self.get_as_path(Keys.Notification.KEY_SOUND)

    def get_columns(self):
        return self.get(Keys.Table.Columns.KEY)

    def get_column(self, c: Column):
        return self.get_columns().get(c.name.lower())

    def has_column(self, c: Column):
        return self.get_column(c) is not None

    def _get_column_value(self, c: Column, key: str, default):
        col = self.get_column(c)
        return col.get(key, default) if col is not None else None

    def get_column_label(self, c: Column) -> str | None:
        return self._get_column_value(c, Keys.Table.Columns.KEY_COLUMN_LABEL,
                                      self.get_default(Keys.Table.Columns.key_label(c)))

    def get_column_align(self, c: Column) -> str | None:
        return self._get_column_value(c, Keys.Table.Columns.KEY_COLUMN_ALIGN,
                                      self.get_default(Keys.Table.Columns.key_align(c)))

    def get_column_index(self, c: Column):
        with suppress(ValueError):
            return list(self.get_columns().keys()).index(c.name.lower())
        return -1

    def get(self, key: Key):
        value = self.get_unsafe(key)
        if value is None:
            value = self.get_default(key)
        return value

    def get_default(self, key: Key):
        value = self.get_unsafe(key, self._config_default)
        if value is None:
            raise ValueError(f'No default value for key {'.'.join(key)!r}')
        return value

    def get_unsafe(self, key: Key, config=None):
        if config is None:
            config = self._config
        with suppress(KeyError):
            return reduce(operator.getitem, key, config)
        return None

    def _validate(self):
        try:
            self._validate_file(Keys.KEY_LOGFILE)
            self._validate_bool(Keys.Notification.KEY_PLAY_SOUND)
            self._validate_sound(Keys.Notification.KEY_SOUND)
            self._validate_columns()
            self._validate_bool(Keys.Table.KEY_COLOR)
            self._validate_bool(Keys.Table.KEY_BORDER)
            self._validate_bool(Keys.Table.KEY_SHOW_AVERAGE)
            self._validate_bool(Keys.Table.KEY_ALWAYS_SHOW_TEAM)
            self._validate_colors(self.get(Keys.Table.Colors.KEY), Keys.Table.Colors.KEY)

        except TOMLDecodeError as e:
            print(f'Failed to validate config values:')
            raise e

    def _validate_sound(self, key):
        if self.get(key) not in ['horn', 'horn_subtle', 'horn_epic']:
            self._validate_file(key)

    def _validate_file(self, key):
        value = self.get(key)
        if not Path(expandvars(str(value))).is_file():
            raise TOMLDecodeError(f'Not a file for key {key!r} with value: {value!r}')

    def _validate_columns(self):
        labels = []
        for k, c in self.get_columns().items():
            try:
                c = Column[k.upper()]
            except KeyError:
                pass
            else:
                self._validate_string(Keys.Table.Columns.key_label(c))
                self._validate_align(Keys.Table.Columns.key_align(c))
                labels.append(self.get(Keys.Table.Columns.key_label(c)))
        if not len(labels) == len(set(labels)):
            raise TOMLDecodeError('Column labels must be unique.')

    def _validate_string(self, key: Key):
        value = self.get(key)
        if not type(value) is str:
            raise TOMLDecodeError(f'Not a string for key {key!r} with value: {value!r}')

    def _validate_align(self, key: Key):
        value = self.get(key)
        if len(value) > 1 or value not in ('l', 'c', 'r'):
            raise TOMLDecodeError(f'Not an alignment value for key {key!r} with value: {value!r}')

    def _validate_bool(self, key: Key):
        value = self.get(key)
        if not type(value) is bool:
            raise TOMLDecodeError(f'Not a boolean for key {key!r} with value: {value!r}')

    def _validate_colors(self, d: dict, kk: Key):
        for k, v in d.items():
            kk = *kk, k
            if type(v) is dict:
                self._validate_colors(v, kk)
            else:
                try:
                    _ = Color[str(v).upper()]
                except KeyError:
                    raise TOMLDecodeError(f'Not a color for key {'.'.join(kk)!r} with value: {v!r}')
            kk = kk[:-1]

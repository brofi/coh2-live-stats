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

import sys
from os.path import expandvars
from pathlib import Path
from tomllib import load, TOMLDecodeError

from .data.color import Color
from .data.column import Column
from .data.faction import Faction


class _Section:
    def __init__(self, *key):
        self.KEY: tuple = key


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


class Settings:
    def __init__(self):
        self._config = self._get_config()
        self._validate()

    def _get_config(self):
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
        return self._set_defaults(config)

    def get_logfile(self):
        return self.get_as_path(Keys.KEY_LOGFILE)

    def get_as_path(self, key: tuple):
        return Path(expandvars(self.get(key)))

    def get_faction_color(self, faction: Faction):
        return self.get_as_color((*Keys.Table.Colors.Faction.KEY, faction.name.lower()))

    def get_as_color(self, key: tuple):
        return Color[self.get(key).upper()]

    def get_notification_sound(self):
        v = self.get(Keys.Notification.KEY_SOUND)
        if v in ['horn', 'horn_subtle', 'horn_epic']:
            return Path(getattr(sys, '_MEIPASS', str(Path(__file__).parent))).joinpath('res', f'{v}.wav')
        else:
            return self.get_as_path(Keys.Notification.KEY_SOUND)

    def has_key(self, key: tuple):
        return self.get_safe(key) is not None

    def get_column_index(self, c: Column):
        if self.has_key(Keys.Table.Columns.key(c)):
            for i, k in enumerate(self.get(Keys.Table.Columns.KEY).keys()):
                if k == c.name.lower():
                    return i
        return -1

    def get_safe(self, key: tuple):
        try:
            return self.get(key)
        except KeyError:
            pass
        return None

    def get(self, key: tuple):
        val = self._config
        for k in key:
            if k not in val:
                raise KeyError(f'No setting named {k!r}.')
            val = val.get(k)
        return val

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
        columns = self.get_safe(Keys.Table.Columns.KEY)
        if columns:
            labels = []
            for k, c in columns.items():
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

    def _validate_string(self, key: tuple):
        value = self.get(key)
        if not type(value) is str:
            raise TOMLDecodeError(f'Not a string for key {key!r} with value: {value!r}')

    def _validate_align(self, key: tuple):
        value = self.get(key)
        if len(value) > 1 or value not in ('l', 'c', 'r'):
            raise TOMLDecodeError(f'Not an alignment value for key {key!r} with value: {value!r}')

    def _validate_bool(self, key: tuple):
        value = self.get(key)
        if not type(value) is bool:
            raise TOMLDecodeError(f'Not a boolean for key {key!r} with value: {value!r}')

    def _validate_colors(self, d: dict, kk: tuple):
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

    @staticmethod
    def _set_defaults(config):
        logfile = str(Path.home().joinpath('Documents', 'My Games', 'Company of Heroes 2', 'warnings.log'))
        config.setdefault('logfile', logfile)

        sec_table = config.setdefault('table', {})
        sec_table.setdefault('color', True)
        sec_table.setdefault('border', False)
        sec_table.setdefault('show_average', True)
        sec_table.setdefault('always_show_team', False)

        sec = sec_table.setdefault('columns', {})
        if not sec:
            col = sec.setdefault('faction', {})
            col.setdefault('label', 'Fac')
            col.setdefault('align', 'l')
            col = sec.setdefault('rank', {})
            col.setdefault('label', 'Rank')
            col.setdefault('align', 'r')
            col = sec.setdefault('level', {})
            col.setdefault('label', 'Lvl')
            col.setdefault('align', 'r')
            col = sec.setdefault('win_ratio', {})
            col.setdefault('label', 'W%')
            col.setdefault('align', 'r')
            col = sec.setdefault('drop_ratio', {})
            col.setdefault('label', 'D%')
            col.setdefault('align', 'r')
            col = sec.setdefault('team', {})
            col.setdefault('label', 'Team')
            col.setdefault('align', 'c')
            col = sec.setdefault('team_rank', {})
            col.setdefault('label', 'T_Rank')
            col.setdefault('align', 'r')
            col = sec.setdefault('team_level', {})
            col.setdefault('label', 'T_Level')
            col.setdefault('align', 'r')
            col = sec.setdefault('country', {})
            col.setdefault('label', 'Country')
            col.setdefault('align', 'l')
            col = sec.setdefault('name', {})
            col.setdefault('label', 'Name')
            col.setdefault('align', 'l')

        sec_color = sec_table.setdefault('colors', {})
        sec_color.setdefault('border', Color.BRIGHT_BLACK.name)
        sec_color.setdefault('label', Color.BRIGHT_BLACK.name)
        sec = sec_color.setdefault('player', {})
        sec.setdefault('high_drop_rate', Color.RED.name)
        sec.setdefault('high', Color.BRIGHT_WHITE.name)
        sec.setdefault('low', Color.BRIGHT_BLACK.name)
        sec = sec_color.setdefault('faction', {})
        sec.setdefault('wm', Color.RED.name)
        sec.setdefault('su', Color.RED.name)
        sec.setdefault('okw', Color.CYAN.name)
        sec.setdefault('us', Color.BLUE.name)
        sec.setdefault('uk', Color.YELLOW.name)

        sec = config.setdefault('notification', {})
        sec.setdefault('play_sound', True)
        sec.setdefault('sound', 'horn')
        return config

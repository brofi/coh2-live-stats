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

    def get_as_path(self, key: str):
        return Path(expandvars(self.get(key)))

    def get_as_color(self, key: str):
        return Color[self.get(key).upper()]

    def has_column(self, col: str):
        columns = self.get('table.columns')
        if columns:
            return columns.get(col) is not None
        return False

    def get_column_index(self, col: str):
        if self.has_column(col):
            for i, k in enumerate(self.get('table.columns').keys()):
                if k == col:
                    return i
        return -1

    def get_safe(self, key: str):
        try:
            return self.get(key)
        except KeyError:
            pass
        return None

    def get(self, key: str):
        val = self._config
        for k in key.split('.'):
            if k not in val:
                raise KeyError(f'No setting named {k!r}.')
            val = val.get(k)
        return val

    def _validate(self):
        try:
            self._validate_file('logfile')
            self._validate_file('notification.wavfile')
            self._validate_bool('notification.sound')
            self._validate_columns(self.get('table.columns'))
            self._validate_bool('table.color')
            self._validate_bool('table.border')
            self._validate_bool('table.show_average')
            self._validate_bool('table.always_show_team')
            self._validate_colors(self.get('table.colors'), 'table.colors')

        except TOMLDecodeError as e:
            print(f'Failed to validate config values:')
            raise e

    def _validate_file(self, key):
        value = self.get(key)
        if not Path(expandvars(str(value))).is_file():
            raise TOMLDecodeError(f'Not a file for key {key!r} with value: {value!r}')

    def _validate_columns(self, columns: dict):
        for k, col in columns.items():
            self._validate_string(f'table.columns.{k}.label')
            self._validate_align(f'table.columns.{k}.align')
        labels = [col.get('label') for col in columns.values()]
        if not len(labels) == len(set(labels)):
            raise TOMLDecodeError('Column labels must be unique.')

    def _validate_string(self, key):
        value = self.get(key)
        if not type(value) is str:
            raise TOMLDecodeError(f'Not a string for key {key!r} with value: {value!r}')

    def _validate_align(self, key):
        value = self.get(key)
        if len(value) > 1 or value not in ('l', 'c', 'r'):
            raise TOMLDecodeError(f'Not an alignment value for key {key!r} with value: {value!r}')

    def _validate_bool(self, key):
        value = self.get(key)
        if not type(value) is bool:
            raise TOMLDecodeError(f'Not a boolean for key {key!r} with value: {value!r}')

    def _validate_colors(self, d: dict, kk: str):
        for k, v in d.items():
            kk = f'{kk}.{k}'
            if type(v) is dict:
                self._validate_colors(v, kk)
            else:
                try:
                    _ = Color[str(v).upper()]
                except KeyError:
                    raise TOMLDecodeError(f'Not a color for key {kk!r} with value: {v!r}')
            kk = kk.removesuffix(f'.{k}')

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
        sec.setdefault('sound', True)
        wavfile = str(Path(getattr(sys, '_MEIPASS', str(Path(__file__).parent))).joinpath('res').joinpath('notify.wav'))
        sec.setdefault('wavfile', wavfile)
        return config

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


class Settings:
    def __init__(self):
        self._config = self._get_config()

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
            except TOMLDecodeError:
                print(f'Failed to parse configuration file: {c}')
            except FileNotFoundError:
                pass
        return self._set_defaults(config)

    def get_logfile_path(self):
        return Path(expandvars(self.get('logfile')))

    def get(self, key: str):
        val = self._config
        for k in key.split('.'):
            if k not in val:
                raise KeyError(f'No setting named {k}.')
            val = val.get(k)
        return val

    @staticmethod
    def _set_defaults(config):
        logfile = str(Path.home().joinpath('Documents', 'My Games', 'Company of Heroes 2', 'warnings.log'))
        config.setdefault('logfile', logfile)
        return config

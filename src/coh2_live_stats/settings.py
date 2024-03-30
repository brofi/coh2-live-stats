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
from contextlib import suppress
from enum import Enum
from os.path import expandvars
from pathlib import Path
from tomllib import load, TOMLDecodeError
from typing import get_args, Literal, Annotated

from pydantic import BeforeValidator, PlainSerializer, BaseModel, create_model, field_validator, FilePath, Field
from pydantic_settings import BaseSettings, SettingsConfigDict, PydanticBaseSettingsSource, TomlConfigSettingsSource

from .data.color import Color
from .data.faction import Faction

_Align = Literal['l', 'c', 'r']
_Sound = Literal['horn_subtle', 'horn', 'horn_epic']


def _validate_color(v: str):
    with suppress(KeyError):
        return Color[v.upper()]
    raise ValueError(f'not a color: {v!r}. Valid colors are: {', '.join([c.name for c in Color])}.')


# Custom `Color` type for validation/serialization
_CT = Annotated[Color, BeforeValidator(_validate_color), PlainSerializer(lambda c: c.name)]


def _serialize_path(p: Path):
    env = '%USERPROFILE%'
    return str(p).replace(expandvars(env), env)


# A Path that can handle variables, gets serialized as a string and must point to a file.
_PT = Annotated[FilePath, BeforeValidator(lambda p: expandvars(p)), PlainSerializer(_serialize_path)]

# Custom ratio type.
_RT = Annotated[float, Field(ge=0, le=1)]


class _TableColorsPlayer(BaseModel):
    high_drop_rate: _CT = Color.RED
    high: _CT = Color.BRIGHT_WHITE
    low: _CT = Color.BRIGHT_BLACK


_TableColorsFaction = create_model('_TableColorsFaction', **{f.name.lower(): (_CT, f.default_color) for f in Faction})


class _TableColors(BaseModel):
    border: _CT = Color.BRIGHT_BLACK
    label: _CT = Color.BRIGHT_BLACK
    player: _TableColorsPlayer = _TableColorsPlayer()
    faction: _TableColorsFaction = _TableColorsFaction()

    def get_faction_color(self, f: Faction):
        return getattr(self.faction, f.name.lower())


class _ColumnDefaults(Enum):
    FACTION = 'Fac', 'l', True
    RANK = 'Rank', 'r', True
    LEVEL = 'Lvl', 'r', True
    WIN_RATIO = 'W%', 'r', True
    DROP_RATIO = 'D%', 'r', True
    TEAM = 'Team', 'c', True
    TEAM_RANK = 'T_Rank', 'r', True
    TEAM_LEVEL = 'T_Level', 'r', True
    STEAM_PROFILE = 'Profile', 'l', False
    COUNTRY = 'Country', 'l', True
    NAME = 'Name', 'l', True

    def __init__(self, label: str, align: _Align, visible: bool):
        self.pos = 0
        self.label = label
        self.align = align
        self.visible = visible


def _create_columns_model():
    field_definitions = {}
    for d in _ColumnDefaults:
        model_col = create_model('_TableColumn',
                                 visible=(bool, d.visible),
                                 pos=(int, d.pos),
                                 label=(str, d.label),
                                 align=(_Align, d.align))
        field_definitions[d.name.lower()] = model_col, model_col()
    return create_model('_TableColumns', **field_definitions)


_TableColumns = _create_columns_model()


class _Table(BaseModel):
    color: bool = True
    border: bool = False
    show_average: bool = True
    always_show_team: bool = False
    drop_ratio_high_threshold: _RT = 0.05
    win_ratio_high_threshold: _RT = 0.6
    win_ratio_low_threshold: _RT = 0.5
    columns: _TableColumns = _TableColumns()
    colors: _TableColors = _TableColors()


class _Notification(BaseModel):
    play_sound: bool = True
    sound: _PT = Field(default='horn', validate_default=True)

    # noinspection PyNestedDecorators
    @field_validator('sound', mode='before')
    @classmethod
    def resolve_sound_name(cls, v) -> Path:
        if v in get_args(_Sound):
            return Path(getattr(sys, '_MEIPASS', str(Path(__file__).parent))).joinpath('res', f'{v}.wav')
        return v


def _get_config():
    config = None
    config_paths = ['%USERPROFILE%', str(Path(getattr(sys, '_MEIPASS', __file__)).parent)]
    config_names = [f'{p}{b}.toml' for b in ['coh2livestats', 'coh2_live_stats'] for p in ['_', '.', '']]
    config_files = [Path(expandvars(p)).joinpath(n) for p in config_paths for n in config_names]
    for c in config_files:
        try:
            with open(c, 'rb') as f:
                _ = load(f)
                config = c
                break
        except TOMLDecodeError as e:
            print('Error: Invalid TOML')
            print(f'\tFile: {c}')
            print(f'\tCause: {e.args[0]}')
        except FileNotFoundError:
            pass
    return config


class Settings(BaseSettings):
    model_config = SettingsConfigDict(toml_file=_get_config(), frozen=True)

    logfile: _PT = Path.home().joinpath('Documents', 'My Games', 'Company of Heroes 2', 'warnings.log')
    table: _Table = _Table()
    notification: _Notification = _Notification()

    @classmethod
    def settings_customise_sources(cls,
                                   settings_cls: type[BaseSettings],
                                   init_settings: PydanticBaseSettingsSource,
                                   env_settings: PydanticBaseSettingsSource,
                                   dotenv_settings: PydanticBaseSettingsSource,
                                   file_secret_settings: PydanticBaseSettingsSource
                                   ) -> tuple[PydanticBaseSettingsSource, ...]:
        return TomlConfigSettingsSource(settings_cls),

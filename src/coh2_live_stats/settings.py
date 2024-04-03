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

import logging
import sys
from contextlib import suppress
from enum import Enum
from os.path import expandvars
from pathlib import Path
from tomllib import TOMLDecodeError, load
from typing import get_args, Literal, Annotated

from pydantic import BeforeValidator, PlainSerializer, BaseModel, create_model, field_validator, FilePath, Field
from pydantic_settings import BaseSettings, SettingsConfigDict, PydanticBaseSettingsSource, TomlConfigSettingsSource

from .data.color import Color
from .data.faction import Faction

LOG = logging.getLogger('coh2_live_stats')

# When running in PyInstaller bundle:
# getattr(sys, '_MEIPASS', __file__): ... \CoH2LiveStats\dist\CoH2LiveStats\lib                 (_MEIPASS)
# __file__:                           ... \CoH2LiveStats\dist\CoH2LiveStats\lib\settings.py
# When running in a normal Python process:
# getattr(sys, '_MEIPASS', __file__): ... \CoH2LiveStats\src\coh2_live_stats\settings.py        (getattr default)
# __file__:                           ... \CoH2LiveStats\src\coh2_live_stats\settings.py

CONFIG_PATHS = ['%USERPROFILE%', str(Path(getattr(sys, '_MEIPASS', __file__)).parent)]
CONFIG_NAMES = [f'{p}{b}.toml' for b in ['coh2livestats', 'coh2_live_stats'] for p in ['_', '.', '']]
CONFIG_FILES = [Path(expandvars(p)).joinpath(n) for p in CONFIG_PATHS for n in CONFIG_NAMES]

CONFIG_FILE_DEV: Path = Path(__file__).with_name(CONFIG_NAMES[0])

Align = Literal['l', 'c', 'r']
Sound = Literal['horn_subtle', 'horn', 'horn_epic']


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

# Custom string type for a character.
_Char = Annotated[str, Field(min_length=1, max_length=1)]


class _TableColorsPlayer(BaseModel):
    high_drop_rate: _CT = Field(Color.RED, description="Color for a high player drop ratio")
    high: _CT = Field(Color.BRIGHT_WHITE, description="Color for highest ranked player and high win ratio")
    low: _CT = Field(Color.BRIGHT_BLACK, description="Color for lowest ranked player and low win ratio")


_TableColorsFaction = create_model('_TableColorsFaction', **{
    f.name.lower(): (_CT, Field(f.default_color, description=f"{f.full_name} color")) for f in Faction})


class _TableColors(BaseModel):
    border: _CT = Field(Color.BRIGHT_BLACK, description="Output table border color")
    label: _CT = Field(Color.BRIGHT_BLACK, description="Output table header color")
    player: _TableColorsPlayer = Field(_TableColorsPlayer(), description="Player-specific color options")
    faction: _TableColorsFaction = Field(_TableColorsFaction(), description="Faction colors")

    def get_faction_color(self, f: Faction):
        return getattr(self.faction, f.name.lower())


class _ColumnDefaults(Enum):
    FACTION = 'Fac', 'l', True
    RANK = 'Rank', 'r', True
    LEVEL = 'Lvl', 'r', True
    PRESTIGE = 'XP', 'l', False
    WIN_RATIO = 'W%', 'r', True
    DROP_RATIO = 'D%', 'r', True
    TEAM = 'Team', 'c', True
    TEAM_RANK = 'T_Rank', 'r', True
    TEAM_LEVEL = 'T_Level', 'r', True
    STEAM_PROFILE = 'Profile', 'l', False
    COUNTRY = 'Country', 'l', True
    NAME = 'Name', 'l', True

    def __init__(self, label: str, align: Align, visible: bool):
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
                                 align=(Align, d.align))
        field_definitions[d.name.lower()] = model_col, Field(model_col())
    return create_model('_TableColumns', **field_definitions)


_TableColumns = _create_columns_model()


class _Table(BaseModel):
    color: bool = Field(True, description="Use color for output")
    border: bool = Field(False, description="Draw a border around the output table")
    show_average: bool = Field(True, description="Show team's average rank and level")
    always_show_team: bool = Field(False, description="Always show team columns, even if they're empty")
    drop_ratio_high_threshold: _RT = Field(
        0.05,
        description="Drop ratios are considered high if they're higher than or equal this value (used for color)")
    win_ratio_high_threshold: _RT = Field(
        0.6,
        description="Win ratios are considered high if they're higher than or equal this value (used for color)")
    win_ratio_low_threshold: _RT = Field(
        0.5,
        description="Win ratios are considered low if they're lower than this value (used for color)")
    prestige_star_char: _Char = Field("*", description="Character to use for one prestige level star")
    prestige_half_star_char: _Char = Field("~", description="Character to use for a half prestige level star")
    colors: _TableColors = Field(_TableColors(), description="Output table color options")
    columns: _TableColumns = Field(_TableColumns(), description="Output table column options")


class _Notification(BaseModel):
    play_sound: bool = Field(True, description="Play a notification sound when a new multiplayer match was found")
    sound: _PT = Field(default='horn', validate_default=True,
                       description="Built-in notification sound name or full path to custom waveform audio file")

    # noinspection PyNestedDecorators
    @field_validator('sound', mode='before')
    @classmethod
    def resolve_sound_name(cls, v) -> Path:
        if v in get_args(Sound):
            return Path(getattr(sys, '_MEIPASS', str(Path(__file__).parent))).joinpath('res', f'{v}.wav')
        return v


class Settings(BaseSettings):
    logfile: _PT = Field(
        Path.home().joinpath('Documents', 'My Games', 'Company of Heroes 2', 'warnings.log'), validate_default=True,
        description="Path to observed Company of Heroes 2 log file (supports OS environment variables)")
    notification: _Notification = Field(_Notification(), description="Notification sound options")
    table: _Table = Field(_Table(), description="Output table options")


class TomlSettings(Settings):
    @classmethod
    def settings_customise_sources(
            cls,
            settings_cls: type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return TomlConfigSettingsSource(settings_cls, cls._first_valid_config()),

    @staticmethod
    def _first_valid_config() -> Path | None:
        for c in CONFIG_FILES:
            with suppress(FileNotFoundError):
                with open(c, 'rb') as f:
                    LOG.info('Found TOML configuration: %s', c)
                    try:
                        _ = load(f)
                        return c
                    except TOMLDecodeError as e:
                        LOG.warning('Failed to parse TOML configuration: %s', e.args[0])


class SettingsFactory:
    @staticmethod
    def create_settings(values: any = None) -> Settings:
        if values is None:
            settings = TomlSettings()
            LOG.info('Loading %s[file=%s]', settings.__class__.__name__, settings.model_config.get('toml_file'))
            return settings
        return Settings(**values)

    @staticmethod
    def create_default_settings() -> Settings:
        return SettingsFactory.create_settings({})

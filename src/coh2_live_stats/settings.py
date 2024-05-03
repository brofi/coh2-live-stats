#  Copyright (C) 2024 Andreas Becker.
#
#  This file is part of CoH2LiveStats.
#
#  CoH2LiveStats is free software: you can redistribute it and/or modify it under the
#  terms of the GNU General Public License as published by the Free Software
#  Foundation, either version 3 of the License, or (at your option) any later version.
#
#  CoH2LiveStats is distributed in the hope that it will be useful, but WITHOUT ANY
#  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
#  PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with
#  CoH2LiveStats. If not, see <https://www.gnu.org/licenses/>.

"""Application settings model and validation."""

import logging
import sys
from contextlib import suppress
from enum import Enum
from os.path import expandvars
from pathlib import Path
from tomllib import TOMLDecodeError, load
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    ClassVar,
    Literal,
    NamedTuple,
    cast,
    get_args,
    override,
)

from pydantic import (
    BaseModel,
    BeforeValidator,
    Field,
    FilePath,
    PlainSerializer,
    create_model,
    field_serializer,
    field_validator,
)
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

from .data.color import Color
from .data.faction import Faction

LOG = logging.getLogger('coh2_live_stats')

# When running in PyInstaller bundle:
# getattr(sys, '_MEIPASS', __file__): ...\dist\CoH2LiveStats\lib          (_MEIPASS)
# __file__: ...\dist\CoH2LiveStats\lib\coh2_live_stats\settings.pyc
# When running in a normal Python process:
# getattr(sys, '_MEIPASS', __file__): ...\src\coh2_live_stats\settings.py (attr default)
# __file__: ...\src\coh2_live_stats\settings.py
CONFIG_PATHS = ['%USERPROFILE%', str(Path(getattr(sys, '_MEIPASS', __file__)).parent)]
CONFIG_NAMES = [
    f'{p}{b}.toml' for b in ['coh2livestats', 'coh2_live_stats'] for p in ['_', '.', '']
]
CONFIG_FILES = [
    Path(expandvars(p)).joinpath(n) for p in CONFIG_PATHS for n in CONFIG_NAMES
]

CONFIG_FILE_DEV: Path = Path(__file__).with_name(CONFIG_NAMES[0])

Align = Literal['l', 'c', 'r']
Border = Literal['full', 'inner', 'none']
Sound = Literal['horn_subtle', 'horn', 'horn_epic']


def resolve_sound_name(s: Sound) -> Path:
    """Return the ``Path`` for the given ``Sound``."""
    return Path(getattr(sys, '_MEIPASS', str(Path(__file__).parent))).joinpath(
        'res', f'{s}.wav'
    )


def _validate_color(v: str) -> Color:
    with suppress(KeyError):
        return Color[v.upper()]
    msg = f'not a color: {v!r}. Valid colors are: {', '.join([c.name for c in Color])}.'
    raise ValueError(msg)


# Custom `Color` type for validation/serialization
_CT = Annotated[
    Color, BeforeValidator(_validate_color), PlainSerializer(lambda c: c.name)
]


def _serialize_path(p: Path) -> str:
    env = '%USERPROFILE%'
    return str(p).replace(expandvars(env), env)


# A Path that can handle variables, gets serialized as a string and must point to a
# file.
_PT = Annotated[FilePath, BeforeValidator(expandvars), PlainSerializer(_serialize_path)]

# Custom ratio type.
_RT = Annotated[float, Field(ge=0, le=1)]

# Custom string type for a character.
_Char = Annotated[str, Field(min_length=1, max_length=1)]


class _TableColorsPlayer(BaseModel):
    high_drop_rate: _CT = Field(
        Color.RED, description='Color for a high player drop ratio'
    )
    high: _CT = Field(
        Color.BRIGHT_WHITE,
        description='Color for highest ranked player and high win ratio',
    )
    low: _CT = Field(
        Color.BRIGHT_BLACK,
        description='Color for lowest ranked player and low win ratio',
    )
    win_streak: _CT = Field(Color.GREEN, description='Color for a win streak')
    loss_streak: _CT = Field(Color.RED, description='Color for a loss streak')


if TYPE_CHECKING:
    _TableColorsFaction = Any
else:
    _TableColorsFaction = create_model(
        '_TableColorsFaction',
        **{
            f.name.lower(): (
                _CT,
                Field(f.default_color, description=f'{f.full_name} color'),
            )
            for f in Faction
        },
    )


class _TableColors(BaseModel):
    border: _CT = Field(Color.BRIGHT_BLACK, description='Output table border color')
    label: _CT = Field(Color.BRIGHT_BLACK, description='Output table header color')
    player: _TableColorsPlayer = Field(
        _TableColorsPlayer(), description='Player-specific color settings'
    )
    faction: _TableColorsFaction = Field(
        _TableColorsFaction(), description='Faction colors'
    )

    def get_faction_color(self, f: Faction) -> Color:
        return cast(Color, getattr(self.faction, f.name.lower()))


class _Col(NamedTuple):
    label: str
    visible: bool = True
    align: Align = 'l'
    pos: int = 0
    description: str = ''


class _ColumnDefaults(_Col, Enum):
    FACTION = _Col('Fac', description='Player faction')
    RANK = _Col(
        'Rank',
        align='r',
        description='Leaderboard rank if the player currently has a rank or highest '
        'known rank (indicator: +) if available or estimated rank (indicator: ?)',
    )
    LEVEL = _Col(
        'Lvl', align='r', description='Rank level representing the leaderboard rank'
    )
    PRESTIGE = _Col('XP', visible=False, description='Experience expressed in stars')
    STREAK = _Col(
        '+/-',
        visible=False,
        description='Number of games won (positive) or lost (negative) in a row',
    )
    WINS = _Col('W', visible=False, description='Number of games won')
    LOSSES = _Col('L', visible=False, description='Number of games lost')
    WIN_RATIO = _Col('W%', align='r', description='Percentage of games won')
    DROP_RATIO = _Col('Drop%', align='r', description='Percentage of games dropped')
    NUM_GAMES = _Col('Total', description='Total number of games played')
    TEAM = _Col(
        'Team', align='c', description='The pre-made team the player is part of if any'
    )
    TEAM_RANK = _Col(
        'T_Rank', align='r', description='The current rank of the pre-made team if any'
    )
    TEAM_LEVEL = _Col(
        'T_Lvl',
        align='r',
        description='The current rank level of the pre-made team if any',
    )
    STEAM_PROFILE = _Col('Profile', visible=False, description='Steam profile URL')
    COUNTRY = _Col('Country', description='Player country')
    NAME = _Col('Name', description='Player name')


def _create_columns_model() -> type[BaseModel]:
    field_definitions: dict[str, Any] = {}
    for d in _ColumnDefaults:
        col_name = d.name.lower()
        model_col = create_model(
            '_TableColumn',
            label=(str, Field(d.label, description=f'`{col_name}` header')),
            visible=(
                bool,
                Field(d.visible, description=f'Whether to show the `{col_name}`'),
            ),
            align=(Align, Field(d.align, description=f'`{col_name}` alignment')),
            pos=(
                int,
                Field(
                    d.pos, description=f'`{col_name}` position used for column ordering'
                ),
            ),
        )
        field_col = Field(model_col(), description=d.description)
        field_definitions[col_name] = model_col, field_col
    return create_model('_TableColumns', **field_definitions)


if TYPE_CHECKING:
    _TableColumns = Any
else:
    _TableColumns = _create_columns_model()


class _Table(BaseModel):
    color: bool = Field(default=True, description='Use color for output')
    border: Border = Field(
        default='inner', description='Border type of the output table'
    )
    header: bool = Field(default=True, description='Show output table header')
    show_average: bool = Field(
        default=True, description="Show team's average rank and level"
    )
    always_show_team: bool = Field(
        default=False, description="Always show team columns, even if they're empty"
    )
    drop_ratio_high_threshold: _RT = Field(
        0.05,
        description="Drop ratios are considered high if they're higher than or equal "
        'this value (used for color)',
    )
    win_ratio_high_threshold: _RT = Field(
        0.6,
        description="Win ratios are considered high if they're higher than or equal "
        'this value (used for color)',
    )
    win_ratio_low_threshold: _RT = Field(
        0.5,
        description="Win ratios are considered low if they're lower than this value "
        '(used for color)',
    )
    prestige_star_char: _Char = Field(
        '*', description='Character to use for one prestige level star'
    )
    prestige_half_star_char: _Char = Field(
        '~', description='Character to use for a half prestige level star'
    )
    colors: _TableColors = Field(
        _TableColors(), description='Output table color settings'
    )
    columns: _TableColumns = Field(_TableColumns(), description='Output table columns')


class _Notification(BaseModel):
    play_sound: bool = Field(
        default=True,
        description='Play a notification sound when a new multiplayer match was found',
    )
    sound: _PT = Field(
        default=resolve_sound_name('horn'),
        description='Built-in notification sound name or full path to custom waveform '
        'audio file',
    )

    # noinspection PyNestedDecorators
    @field_validator('sound', mode='before')
    @classmethod
    def validate_sound(cls, v: str) -> Path:
        if v in get_args(Sound):
            return resolve_sound_name(v)  # type: ignore[arg-type]
        return Path(v)

    # noinspection PyNestedDecorators
    @field_serializer('sound')
    @staticmethod
    def serialize_sound(sound: Path) -> str:
        s: Sound
        for s in get_args(Sound):
            if sound == resolve_sound_name(s):
                return s
        return str(sound)


class Settings(BaseSettings):
    """Pydantic model for application settings."""

    _LOGFILE_DEFAULT: ClassVar[Path] = Path().home()
    if sys.platform == 'win32' or sys.platform == 'cygwin':
        _LOGFILE_DEFAULT = _LOGFILE_DEFAULT.joinpath(
            'Documents', 'My Games', 'Company of Heroes 2'
        )
    elif sys.platform == 'linux':
        _LOGFILE_DEFAULT = _LOGFILE_DEFAULT.joinpath(
            '.local', 'share', 'feral-interactive', 'CompanyOfHeroes2', 'AppData'
        )
    _LOGFILE_DEFAULT /= 'warnings.log'

    logfile: _PT = Field(
        _LOGFILE_DEFAULT,
        validate_default=True,
        description='Path to observed Company of Heroes 2 log file (supports OS '
        'environment variables)',
    )
    notification: _Notification = Field(
        _Notification(), description='Notification sound settings'
    )
    table: _Table = Field(_Table(), description='Output table settings')


class TomlSettings(Settings):
    """Pydantic model for application settings backed by a user configuration."""

    def __init__(self, config: Path | None = None, **values: Any) -> None:  # noqa: ANN401
        """Initialize ``TomlSettings``.

        :param config: config file or ``None`` to use the first valid config
        :param values: values that overwrite the default values
        """
        TomlSettings.model_config = SettingsConfigDict(
            toml_file=config
            if config is not None
            else TomlSettings._first_valid_config()
        )
        super().__init__(**values)

    @classmethod
    @override
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (TomlConfigSettingsSource(settings_cls),)

    @staticmethod
    def _first_valid_config() -> Path | None:
        for c in CONFIG_FILES:
            with suppress(FileNotFoundError), c.open('rb') as f:
                LOG.info('Found TOML config: %s', c)
                try:
                    _ = load(f)
                except TOMLDecodeError as e:
                    LOG.warning(
                        'Failed to parse TOML\n\tFile: %s\n\tCause: %s'.expandtabs(4),
                        c,
                        e.args[0],
                    )
                else:
                    return c
        return None

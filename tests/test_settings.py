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

import os
from collections.abc import Generator
from os.path import expandvars
from pathlib import Path
from typing import Any

import pytest
from coh2_live_stats.data.color import Color
from coh2_live_stats.settings import Settings, TomlSettings
from pydantic import BaseModel, ValidationError

Key = tuple[str, ...]


@pytest.fixture(scope='module')
def config_file() -> Generator[Path, Any, None]:
    config = Path('_coh2livestats.toml')
    config.touch()
    yield config
    config.unlink()


@pytest.fixture(scope='module')
def color_key() -> Key | None:
    return _get_first_key_of_type(Settings(), Color)


@pytest.fixture(scope='module')
def path_key() -> Key | None:
    return _get_first_key_of_type(Settings(), type(Path()))


def _get_first_key_of_type(
    model: BaseModel, cls: type, init_key: Key = ()
) -> Key | None:
    found_key = None
    for attr_name, field_info in model.model_fields.items():
        if found_key is not None:
            break
        if type(field_info.default) is cls:
            return *init_key, attr_name
        if isinstance(field_info.default, BaseModel):
            found_key = _get_first_key_of_type(
                getattr(model, attr_name), cls, (*init_key, attr_name)
            )
    return found_key


def _get_model_value(model: BaseModel, key: Key) -> object:
    val = getattr(model, key[0])
    if len(key[1:]) > 0:
        return _get_model_value(val, key[1:])
    return val


@pytest.mark.parametrize('color', list(Color))
def test_valid_colors(config_file: Path, color_key: Key, color: Color) -> None:
    if color_key is not None:
        config_file.write_text(f"{'.'.join(color_key)} = '{color.name.capitalize()}'")
        settings = TomlSettings(config_file)
        assert _get_model_value(settings, color_key) == color


def test_invalid_color(config_file: Path, color_key: Key) -> None:
    if color_key is not None:
        config_file.write_text(f"{'.'.join(color_key)} = '0_NotAColor'")
        with pytest.raises(ValidationError):
            TomlSettings(config_file)


@pytest.mark.skipif(
    os.name == 'posix', reason='tests expansion of windows environment variables'
)
def test_valid_path(config_file: Path, path_key: Key) -> None:
    if path_key is not None:
        test_path = '%COMSPEC%'
        config_file.write_text(f"{'.'.join(path_key)} = '{test_path}'")
        settings = TomlSettings(config_file)
        assert _get_model_value(settings, path_key) == Path(expandvars(test_path))


def test_invalid_path(config_file: Path, path_key: Key) -> None:
    if path_key is not None:
        config_file.write_text(f"{'.'.join(path_key)} = '/NotAFile/'")
        with pytest.raises(ValidationError):
            TomlSettings(config_file)

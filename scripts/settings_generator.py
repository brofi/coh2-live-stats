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

"""Script for generating a TOML settings file.

The settings file is generated from the *coh2_live_stats* *pydantic* settings model.
The resulting TOML file has all the application settings default values in it, so using
it without changing some values has no effect. *Pydantic* ``Field`` descriptions are
used as comments.
"""

from typing import cast, get_args

from coh2_live_stats.data.color import Color
from coh2_live_stats.settings import (
    CONFIG_FILE_DEV,
    CONFIG_NAMES,
    CONFIG_PATHS,
    Align,
    Border,
    Settings,
    Sound,
)
from pydantic import BaseModel
from tomlkit import TOMLDocument, comment, document, dumps, items, nl
from tomlkit.items import AbstractTable, Comment, Trivia

from scripts.script_util import bullet, list_inline, list_multi, list_single

_NORMAL_COLORS = [
    c.name.lower() for c in Color if Color.BLACK <= c.value <= Color.WHITE
]
_BRIGHT_COLORS = [
    c.name.lower() for c in Color if Color.BRIGHT_BLACK <= c.value <= Color.BRIGHT_WHITE
]

_HEADER_COMMENT = f"""Configuration file for CoH2LiveStats

Valid config locations:
{list_multi(CONFIG_PATHS[:-1], 4)}
{bullet('Next to executable', 4)}
Valid config names:
{list_multi(CONFIG_NAMES, 4)}

Valid border types:
    {list_single(get_args(Border))}

Valid colors:
    {list_single(_NORMAL_COLORS)}
    {list_single(_BRIGHT_COLORS)}

Valid sound values:
    {list_single(get_args(Sound))}
    {bullet('Path to custom WAV file')}

Valid alignment values: {list_inline(get_args(Align))}

Notes:
    {bullet('CJK characters can distort table (table.border = false and name column '
            'last is recommended)')}"""


def _create_doc(_model: BaseModel) -> TOMLDocument:
    _doc: TOMLDocument = document()
    for _k, _v in _model.model_dump().items():
        _doc.add(_k, _v)
    return _doc


def _init_doc(
    _model: BaseModel, _container: TOMLDocument | AbstractTable
) -> TOMLDocument:
    for attr_name, field_info in _model.model_fields.items():
        attr_dump = _model.model_dump()[attr_name]
        item = items.item(attr_dump)
        if field_info.description:
            item.comment(field_info.description)
        _container[attr_name] = (
            _init_doc(getattr(_model, attr_name), item)
            if isinstance(item, AbstractTable)
            else item
        )
    return cast(TOMLDocument, _container)


def write_default() -> None:
    """Write TOML settings file with comments from the default application settings."""
    settings = Settings()

    doc: TOMLDocument = document()
    for line in _HEADER_COMMENT.splitlines():
        doc.add(comment(line) if line else Comment(Trivia(comment='#')))
    doc.add(nl()).add(nl())
    _init_doc(settings, doc)

    CONFIG_FILE_DEV.write_text(dumps(doc))


def get_default() -> str:
    """Get TOML string from the default application settings."""
    return dumps(_create_doc(Settings()))


if __name__ == '__main__':
    write_default()

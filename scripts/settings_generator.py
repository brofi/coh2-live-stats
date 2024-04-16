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

from collections.abc import Sequence
from datetime import datetime
from typing import get_args

from coh2_live_stats import __version__
from coh2_live_stats.data.color import Color
from coh2_live_stats.settings import (
    CONFIG_FILE_DEV,
    CONFIG_NAMES,
    CONFIG_PATHS,
    Align,
    SettingsFactory,
    Sound,
)
from pydantic import BaseModel
from tomlkit import TOMLDocument, comment, document, dumps, items, nl
from tomlkit.items import AbstractTable, Comment, Trivia


def _wrap(__s: str, __w: str = "'") -> str:
    return f"{__w}{__s}{__w}"


def _bullet(__s: str, __c: str = '*', __indent: int = 4) -> str:
    return f"{' ' * __indent}{__c} {__s}"


def _list_multi(__seq: Sequence[str]) -> str:
    return '\n'.join(map(_bullet, __seq))


def _list_single(__seq: Sequence[str]) -> str:
    return _bullet(_list_inline(__seq))


def _list_inline(__s: Sequence[str]) -> str:
    return (
        ' or '.join((', '.join(_wrap(s) for s in __s[:-1]), _wrap(__s[-1])))
        if len(__s) > 1
        else str(__s)[1:-1]
    )


header_comment = f'''Configuration file for CoH2LiveStats

Generated {datetime.now().astimezone().isoformat(timespec='seconds')}
Version {__version__}

Valid config locations:
{_list_multi(CONFIG_PATHS[:-1])}
{_bullet('Next to executable')}
Valid config names:
{_list_multi(CONFIG_NAMES)}

Valid colors:
{_list_single([c.name.lower() for c in Color if Color.BLACK <= c.value <= Color.WHITE])}
{_list_single([c.name.lower() for c in Color if Color.BRIGHT_BLACK <= c.value <= Color.BRIGHT_WHITE])}

Valid sound values:
{_list_single(get_args(Sound))}
{_bullet('Path to custom WAV file')}

Valid alignment values: {_list_inline(get_args(Align))}

Notes:
{_bullet('CJK characters can distort table (table.border = false and name column last is recommended)')}'''


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
    return _container


def default() -> None:
    """Create a TOML settings file from the default application settings."""
    settings = SettingsFactory.create_default_settings()

    doc: TOMLDocument = document()
    for line in header_comment.splitlines():
        doc.add(comment(line) if line else Comment(Trivia(comment="#")))
    doc.add(nl()).add(nl())
    _init_doc(settings, doc)

    CONFIG_FILE_DEV.write_text(dumps(doc))


if __name__ == '__main__':
    default()

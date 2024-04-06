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

from collections.abc import Sequence
from datetime import datetime
from typing import get_args

from pydantic import BaseModel
from tomlkit import document, comment, nl, TOMLDocument, items, dump
from tomlkit.items import AbstractTable

from coh2_live_stats.data.color import Color
from coh2_live_stats.settings import (
    SettingsFactory,
    CONFIG_NAMES,
    Sound,
    Align,
    CONFIG_FILE_DEV,
    CONFIG_PATHS,
)
from coh2_live_stats import __version__


def wrap(__s: str, __w: str = "'") -> str:
    return f"{__w}{__s}{__w}"


def bullet(__s: str, __c: str = '*', __indent: int = 4):
    return f"{' ' * __indent}{__c} {__s}"


def list_multi(__seq: Sequence[str]) -> str:
    return '\n'.join(map(bullet, __seq))


def list_single(__seq: Sequence[str]) -> str:
    return bullet(list_inline(__seq))


def list_inline(__s: Sequence[str]) -> str:
    return (
        ' or '.join((', '.join(wrap(s) for s in __s[:-1]), wrap(__s[-1])))
        if len(__s) > 1
        else str(__s)[1:-1]
    )


def color_names(bright: bool = False) -> list[str]:
    return [
        c.name.lower()
        for c in Color
        if (bright and c.name.startswith('BRIGHT_'))
        or (not bright and not c.name.startswith('BRIGHT_'))
    ]


header_comment = f'''Configuration file for CoH2LiveStats

Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Version {__version__}

Valid config locations:
{list_multi(CONFIG_PATHS[:-1])}
{bullet('Next to executable')}
Valid config names:
{list_multi(CONFIG_NAMES)}

Valid colors:
{list_single(color_names())}
{list_single(color_names(bright=True))}

Valid sound values:
{list_single(get_args(Sound))}
{bullet('Path to custom WAV file')}

Valid alignment values: {list_inline(get_args(Align))}

Notes:
{bullet('CJK characters can distort table (table.border = false and name column last is recommended)')}'''


def create_doc(_model: BaseModel) -> TOMLDocument:
    _doc: TOMLDocument = document()
    for _k, _v in _model.model_dump().items():
        _doc.add(_k, _v)
    return _doc


def init_doc(
    _model: BaseModel, _container: TOMLDocument | AbstractTable
) -> TOMLDocument:
    for attr_name, field_info in _model.model_fields.items():
        attr_dump = _model.model_dump()[attr_name]
        item = items.item(attr_dump)
        if field_info.description:
            item.comment(field_info.description)
        _container[attr_name] = (
            init_doc(getattr(_model, attr_name), item)
            if isinstance(item, AbstractTable)
            else item
        )
    return _container


def main():
    settings = SettingsFactory.create_default_settings()

    doc: TOMLDocument = document()
    for line in header_comment.splitlines():
        doc.add(comment(line) if line else comment(''))
    doc.add(nl()).add(nl())
    init_doc(settings, doc)

    with open(CONFIG_FILE_DEV, 'w') as f:
        dump(doc, f)


if __name__ == '__main__':
    main()

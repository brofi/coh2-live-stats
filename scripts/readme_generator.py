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

"""Module for generated markdown."""

import re
from collections.abc import Callable
from pathlib import Path
from typing import Any, Final

import prettytable
from coh2_live_stats.data.color import Color
from coh2_live_stats.data.faction import Faction
from coh2_live_stats.data.player import Player
from coh2_live_stats.data.team import Team
from coh2_live_stats.output import Output
from coh2_live_stats.settings import Settings
from prettytable import PrettyTable
from pydantic import BaseModel

RGB = tuple[int, int, int]

README_FILE = Path(__file__).parents[1].joinpath('README.md')
SVG_FILE = (
    Path(__file__)
    .parents[1]
    .joinpath('src', 'coh2_live_stats', 'res', 'example_output.svg')
)

_STYLES: Final[dict] = {
    'campbell': {
        'fonts': ['Cascadia Mono', 'Consolas'],
        'size': '11.5pt',
        'space': '1.24em',
        'width': 900,
        'height': 320,
        'palette': {
            'fg': (204, 204, 204),
            'bg': (12, 12, 12),
            Color.BLACK.value: (12, 12, 12),
            Color.RED.value: (197, 15, 31),
            Color.GREEN.value: (19, 161, 14),
            Color.YELLOW.value: (193, 156, 0),
            Color.BLUE.value: (0, 55, 218),
            Color.MAGENTA.value: (136, 23, 152),
            Color.CYAN.value: (58, 150, 221),
            Color.WHITE.value: (204, 204, 204),
            Color.BRIGHT_BLACK.value: (118, 118, 118),
            Color.BRIGHT_RED.value: (231, 72, 86),
            Color.BRIGHT_GREEN.value: (22, 198, 12),
            Color.BRIGHT_YELLOW.value: (249, 241, 165),
            Color.BRIGHT_BLUE.value: (59, 120, 255),
            Color.BRIGHT_MAGENTA.value: (180, 0, 158),
            Color.BRIGHT_CYAN.value: (97, 214, 214),
            Color.BRIGHT_WHITE.value: (242, 242, 242),
        },
    },
    'gruvbox': {
        'fonts': ['Inconsolata', 'Cascadia Mono'],
        'size': '12pt',
        'space': '1.125em',
        'width': 800,
        'height': 300,
        'palette': {
            'fg': (235, 219, 178),
            'bg': (29, 32, 33),
            Color.BLACK.value: (40, 40, 40),
            Color.RED.value: (204, 36, 29),
            Color.GREEN.value: (152, 151, 26),
            Color.YELLOW.value: (215, 153, 33),
            Color.BLUE.value: (69, 133, 136),
            Color.MAGENTA.value: (177, 98, 134),
            Color.CYAN.value: (104, 157, 106),
            Color.WHITE.value: (168, 153, 132),
            Color.BRIGHT_BLACK.value: (146, 131, 116),
            Color.BRIGHT_RED.value: (251, 73, 52),
            Color.BRIGHT_GREEN.value: (184, 187, 38),
            Color.BRIGHT_YELLOW.value: (250, 189, 47),
            Color.BRIGHT_BLUE.value: (131, 165, 152),
            Color.BRIGHT_MAGENTA.value: (211, 134, 155),
            Color.BRIGHT_CYAN.value: (142, 192, 124),
            Color.BRIGHT_WHITE.value: (235, 219, 178),
        },
    },
}

_HG = Player(
    id=6,
    name='Hans Gruber',
    relic_id=8,
    team_id=0,
    faction=Faction.WM,
    steam_profile='',
    prestige=300,
    country='de',
    wins=4831,
    losses=3211,
    drops=103,
    rank=12,
    highest_rank=2,
)
_RPM = Player(
    id=0,
    name='R.P. McMurphy',
    relic_id=2,
    team_id=0,
    faction=Faction.OKW,
    steam_profile='',
    prestige=300,
    country='ie',
    wins=789,
    losses=654,
    drops=51,
    rank=213,
    highest_rank=185,
)
_WS = Player(
    id=2,
    name='Walter Sobchak',
    relic_id=4,
    team_id=0,
    faction=Faction.WM,
    steam_profile='',
    prestige=300,
    country='pl',
    wins=543,
    losses=612,
    drops=59,
    rank=337,
    highest_rank=289,
)
_TB = Player(
    id=4,
    name='Travis Bickle',
    relic_id=6,
    team_id=0,
    faction=Faction.OKW,
    steam_profile='',
    prestige=249,
    country='us',
    wins=2862,
    losses=2690,
    drops=201,
    rank=107,
    highest_rank=101,
)
_JW = Player(
    id=1,
    name='Jules Winnfield',
    relic_id=3,
    team_id=1,
    faction=Faction.US,
    steam_profile='',
    prestige=300,
    country='us',
    wins=3410,
    losses=2471,
    drops=83,
    rank=98,
    highest_rank=81,
)
_RD = Player(
    id=5,
    name='Raoul Duke',
    relic_id=7,
    team_id=1,
    faction=Faction.SU,
    steam_profile='',
    prestige=300,
    country='pt',
    wins=1720,
    losses=1082,
    drops=57,
    rank=68,
    highest_rank=67,
)
_VV = Player(
    id=3,
    name='Vincent Vega',
    relic_id=5,
    team_id=1,
    faction=Faction.US,
    steam_profile='',
    prestige=249,
    country='nl',
    wins=639,
    losses=730,
    drops=19,
    rank=224,
    highest_rank=193,
)
_TD = Player(
    id=7,
    name='Tyler Durden',
    relic_id=9,
    team_id=1,
    faction=Faction.UK,
    steam_profile='',
    prestige=149,
    country='us',
    wins=120,
    losses=117,
    drops=8,
    rank=348,
    highest_rank=298,
)

_RANK_TOTALS: Final[dict[Faction, int]] = {
    Faction.WM: 8165,
    Faction.SU: 7354,
    Faction.OKW: 7606,
    Faction.US: 4601,
    Faction.UK: 5704,
}

_TEAM_OF_2_ALLIES_RANK_TOTAL = 4360
_TEAM_OF_3_AXIS_RANK_TOTAL = 1372


def _sample_players() -> list[Player]:
    team1 = Team(0, [_JW.relic_id, _VV.relic_id], 157)
    team1.rank_level = Player.rank_level_from_rank(
        team1.rank, _TEAM_OF_2_ALLIES_RANK_TOTAL
    )
    for p in _JW, _VV:
        p.teams.append(team1)

    team2 = Team(0, [_RPM.relic_id, _WS.relic_id, _HG.relic_id], 98)
    team2.rank_level = Player.rank_level_from_rank(
        team2.rank, _TEAM_OF_3_AXIS_RANK_TOTAL
    )
    for p in _RPM, _WS, _HG:
        p.teams.append(team2)

    players = [_HG, _RPM, _WS, _JW, _TB, _RD, _VV, _TD]
    for p in players:
        p.rank_total = _RANK_TOTALS[p.faction]
        p.rank_level = Player.rank_level_from_rank(p.rank, p.rank_total)
        p.highest_rank_level = Player.rank_level_from_rank(p.highest_rank, p.rank_total)
    return players


RE_COLOR = re.compile(r'\x1b\[(?P<color>[3|9][0-7])m(?P<value>.*?)\x1b\[0m')


def _example_output_recolored(
    style: dict[str, Any], repl: Callable[[RGB, str], str]
) -> str:
    output = Output(Settings())
    output.init_table(_sample_players())
    out = output.table_string()
    for m in RE_COLOR.finditer(out):
        fg: RGB = style['palette'][int(m.group('color'))]
        out = out.replace(m.group(), repl(fg, m.group('value')))
    return out


def _inline_color_html(color: RGB, value: str) -> str:
    return f"<span style='color:rgb{color}'>{value}</span>"


def _inline_color_svg(color: RGB, value: str) -> str:
    return f'<tspan fill="rgb{color}">{value}</tspan>'


def _example_output_html(style: dict[str, Any]) -> str:
    out = _example_output_recolored(style, _inline_color_html)
    out = (
        '<pre style="'
        f'font-family:{','.join(style['fonts'])},monospace;'
        f'font-size:{style['size']};'
        f'color:rgb{style['palette']['fg']};'
        f'background-color:rgb{style['palette']['bg']};'
        f'">{out}</pre>\n'
    )
    out = out.replace('\x1b[0m', '\n')
    return re.sub(r'\s+$', '', out, flags=re.MULTILINE)


def _example_output_svg(style: dict[str, Any]) -> str:
    out = _example_output_recolored(style, _inline_color_svg)
    out = out.replace('\x1b[0m', '')

    pad = 10
    lines = out.split('\n')
    for i, line in enumerate(lines):
        lines[i] = f'\t\t<tspan x="{pad}" dy="{style['space']}">{line}</tspan>'

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{style['width']}" '
        f'height="{style['height']}">\n'
        f'\t<rect width="100%" height="100%" fill="rgb{style['palette']['bg']}"/>\n'
        f'\t<text x="{pad}" y="{pad}" fill="rgb{style['palette']['fg']}" '
        f'font-family="{','.join(style['fonts'])}" '
        f'font-size="{style['size']}" '
        f'style="white-space:pre">\n'
        f'{'\n'.join(lines)}\n'
        f'\t</text>\n'
        f'</svg>\n'
    )


class _MarkdownTable:
    def __init__(self, key: str, description: str) -> None:
        self.key = key
        self.description = description
        self.table = PrettyTable()
        self.table.set_style(prettytable.MARKDOWN)
        self.table.field_names = ['Attribute', 'Description']
        self.table.align = 'l'

    def get_lines_with_header(self, header: str = '') -> list[str]:
        if not header:
            header = f'`[{self.key}]` {self.description}'
        return [f'### {header}', *self.get_lines()]

    def get_lines(self) -> list[str]:
        table_lines = self.table.get_string().split('\n')
        table_lines[1] = table_lines[1].replace('| :-', '|:--').replace('-: |', '--:|')
        return ['', *table_lines, '']


def _create_tables_recursive(
    model: BaseModel,
    tables: list[_MarkdownTable] | None = None,
    key: str = '',
    description: str = '',
) -> list[_MarkdownTable]:
    if tables is None:
        tables = []
    mdt = _MarkdownTable(key, description)
    tables.append(mdt)
    for attr_name, field_info in model.model_fields.items():
        descr = field_info.description or ''
        if isinstance(field_info.default, BaseModel):
            k = f'{key}{'.' if key else ''}{attr_name}'
            _create_tables_recursive(getattr(model, attr_name), tables, k, descr)
        else:
            mdt.table.add_row([f'`{attr_name}`', descr])
    return tables


def _create_table_recursive(
    model: BaseModel,
    mdt: _MarkdownTable | None = None,
    key: str = '',
    description: str = '',
) -> _MarkdownTable:
    if mdt is None:
        mdt = _MarkdownTable(key, description)
    for attr_name, field_info in model.model_fields.items():
        is_model = isinstance(field_info.default, BaseModel)
        k = f'{key}{'.' if key else ''}{attr_name}'
        mdt.table.add_row(
            [f'`{f'[{k}]' if is_model else k}`', field_info.description or '']
        )
        if is_model:
            _create_table_recursive(getattr(model, attr_name), mdt, k, '')
    return mdt


def _create_table(settings: Settings, key: str = '') -> _MarkdownTable:
    model_names = key.split('.')
    model: BaseModel = settings
    descriptions = ['']
    for name in model_names:
        m = getattr(model, name, None)
        if m is None or not isinstance(m, BaseModel):
            msg = f'Not a model: {name!r}'
            raise ValueError(msg)
        descriptions.append(model.model_fields[name].description or '')
        model = m

    mdt = _MarkdownTable(key, descriptions[-1])
    for attr_name, field_info in model.model_fields.items():
        mdt.table.add_row([f'`{attr_name}`', field_info.description])
    return mdt


def _settings_section() -> list[str]:
    tables = _create_tables_recursive(Settings(), description='Root level settings')
    out: list[str] = []
    for table in tables:
        if 'table.columns' not in table.key:
            out.extend(table.get_lines_with_header())

    settings = Settings()
    out.extend(_create_table(settings, 'table.columns').get_lines_with_header())
    col_table = _create_table(settings, 'table.columns.faction')
    row: list[str]
    i_name = 'column'
    for row in col_table.table.rows:
        row[1] = row[1].replace('faction', i_name)

    out.extend(
        col_table.get_lines_with_header(f'For each `{i_name}` in `[table.columns]`:')
    )
    out.extend(
        (
            '### Appendix',
            '',
            '<details>',
            '<summary>All settings</summary>',
            *_create_table_recursive(settings).get_lines(),
            '</details>',
        )
    )
    return out


def write_example_svg() -> None:
    """Write generated SVG file of example output."""
    SVG_FILE.touch()
    SVG_FILE.write_text(_example_output_svg(_STYLES['gruvbox']).expandtabs(4))


RE_MARKS = re.compile(
    r'^(?P<start>\[//]: # \(<(?P<mark>.*?)>\))$'
    r'(?P<value>.*?)'
    r'^(?P<end>\[//]: # \(</.*?>\))$',
    re.DOTALL | re.MULTILINE,
)


def replace_marks() -> None:
    """Insert generated markdown between predefined marks in the `README.md` file."""
    marks = {'mark_settings': '\n'.join(_settings_section())}

    with README_FILE.open() as f:
        readme = f.read()

    for m in RE_MARKS.finditer(readme):
        repl = marks.get(m.group('mark')) or ''
        readme = readme.replace(
            m.group(), f'{m.group('start')}\n\n{repl}\n\n{m.group('end')}'
        )

    README_FILE.write_text(readme)


if __name__ == '__main__':
    write_example_svg()
    replace_marks()

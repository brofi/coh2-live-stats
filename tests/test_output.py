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

import operator
import re
from collections.abc import Callable
from copy import deepcopy
from functools import partial
from random import randint
from typing import Any, Final

import pytest
from _pytest.capture import CaptureFixture
from _pytest.fixtures import FixtureRequest
from coh2_live_stats.data.countries import countries
from coh2_live_stats.data.faction import Faction
from coh2_live_stats.data.match import Match, Party
from coh2_live_stats.data.player import Player
from coh2_live_stats.data.team import Team
from coh2_live_stats.output import Output
from coh2_live_stats.settings import Settings
from scripts.script_util import flip

from tests.conftest import (
    random_country,
    random_highest_rank,
    random_rank,
    random_steam_id_64,
    random_team,
    random_xp,
    xp_level_from_xp,
)

COLUMN_NAMES: Final[list[str]] = list(Settings().table.columns.model_fields)


# [@-Z] -> 0x40-0x5a + [\\-_] -> 0x5c-0x5f - without CSI 0x5b ([)
# [0-?] -> 0x30-0x3f: parameter bytes (any number)
# [ -/] -> 0x20-0x2f: intermediate bytes (any number)
# [@-~] -> 0x40-0x7e: final byte (single)
RE_ESCAPE: Final[re.Pattern[str]] = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
"""Regex ANSI escape sequences."""


RE_CTRL_CHAR: Final[re.Pattern[str]] = re.compile(r'[\a\b\f\n\r\t\v]')
"""Regex python control characters."""


def _strip(s: str) -> str:
    return RE_ESCAPE.sub('', s)


def _strip_cap(s: str) -> str:
    return RE_CTRL_CHAR.sub('', _strip(s))


@pytest.fixture(scope='module')
def players_output(players1: list[Player]) -> list[Player]:
    players = deepcopy(players1)
    for p in players:
        p.steam_profile = f'/steam/{random_steam_id_64()}'
        p.prestige = xp_level_from_xp(random_xp())
        p.country = random_country()
        p.wins = randint(0, 5000)
        p.losses = randint(0, p.wins)
        p.drops = randint(0, p.wins + p.losses)
        p.rank_total = randint(1000, 5000)
        p.rank = random_rank(p.rank_total)
        p.rank_level = Player.rank_level_from_rank(p.rank, p.rank_total)
        p.highest_rank = random_highest_rank(p.rank, p.rank_total)
        p.highest_rank_level = Player.rank_level_from_rank(p.highest_rank, p.rank_total)

    r_team = random_team(players)
    t_rank_total = randint(2000, 6000)
    t_rank = random_rank(t_rank_total)
    t_highest_rank = random_highest_rank(t_rank, t_rank_total)
    team = Team(
        randint(100, 1000),
        [m.relic_id for m in r_team],
        t_rank,
        Player.rank_level_from_rank(t_rank, t_rank_total),
        t_highest_rank,
        Player.rank_level_from_rank(t_highest_rank, t_rank_total),
    )
    for p in r_team:
        p.teams.append(team)

    return players


@pytest.fixture(scope='module')
def out(players_output: list[Player]) -> Output:
    o = Output(_get_settings())
    o.init_table(players_output)
    return o


@pytest.fixture(
    scope='module',
    params=[
        0,  # no visible columns
        pow(2, len(Settings().table.columns.model_fields)) - 1,  # all columns visible
    ]
    # every column alone
    + [pow(2, i) for i in range(len(Settings().table.columns.model_fields))],
)
def out_v(request: FixtureRequest, players_output: list[Player]) -> Output:
    o = Output(_get_settings(request.param))
    o.init_table(players_output)
    return o


def _get_settings(visibility_flags: int | None = None) -> Settings:
    settings = Settings()
    if visibility_flags is None:
        visibility_flags = pow(2, len(settings.table.columns.model_fields)) - 1
    cols = settings.table.columns
    for i, col in enumerate(cols.model_fields):
        c = getattr(cols, col)
        c.visible = bool(visibility_flags & (1 << i))
    return settings


def test_print_match_empty(capsys: CaptureFixture[str]) -> None:
    output = Output(_get_settings())
    output.print_match([])
    assert _strip_cap(capsys.readouterr()[0]) == Output.ERR_NO_MATCH


def test_print_columns_empty(
    capsys: CaptureFixture[str], players_output: list[Player]
) -> None:
    output = Output(_get_settings(0))
    output.print_match(players_output)
    assert not _strip_cap(capsys.readouterr()[0])


def test_table_size(out: Output, players_output: list[Player]) -> None:
    num_avg_rows = sum(map(out.has_average_row, Match(players_output).parties))
    assert len(out.table.rows) - num_avg_rows == len(players_output)


def test_visibility(out_v: Output, players_output: list[Player]) -> None:
    cols = out_v.settings.table.columns
    team_columns = [cols.team, cols.team_rank, cols.team_level]
    all_columns = [getattr(cols, col) for col in cols.model_fields]

    match = Match(players_output)
    assert all(
        # All columns should be hidden if not visible
        (not col.visible and col.label not in out_v.table.field_names)
        # Visible non-team columns should be shown
        or (
            col.visible
            and col.label in out_v.table.field_names
            and col not in team_columns
        )
        # Visible team columns...
        or (
            col.visible
            and col in team_columns
            and (
                # ...should be shown if there is a pre-made team...
                (col.label in out_v.table.field_names and out_v.has_team_columns(match))
                # ...and be hidden if there are no pre-made teams but team aren't
                # configured to always be shown.
                or (
                    col.label not in out_v.table.field_names
                    and not out_v.has_team_columns(match)
                )
            )
        )
        for col in all_columns
    )


@pytest.mark.parametrize('col_name', COLUMN_NAMES)
def test_output_columns(
    out: Output, players_output: list[Player], col_name: str
) -> None:
    match = Match(players_output)
    rows_no_avg = deepcopy(out.table.rows)
    for i, party in enumerate(match.parties):
        if out.has_average_row(party):
            rows_no_avg.pop((i + 1) * party.size)

    cols = out.settings.table.columns
    col = getattr(cols, col_name)
    assertions = []
    if col.label in out.table.field_names:
        assertions = [
            _column_validators(match.parties[i // match.parties[0].size], p)[col_name](
                rows_no_avg[i][out.get_column_index(col)]
            )
            for i, p in enumerate(
                [*match.parties[0].players, *match.parties[1].players]
            )
        ]
    assert all(assertions)


def _column_validators(
    party: Party, player: Player
) -> dict[str, Callable[[Any], bool]]:
    cols = Settings().table.columns
    rank_estimate = party.rank_estimates[player.relic_id]
    team = next(iter(party.pre_made_teams), None)
    team_rank = (
        ('A', *team.display_rank)
        if team is not None and len(player.teams) > 0 and player.teams[0] == team
        else ('',) * 3
    )
    return dict(
        zip(
            cols.model_fields.keys(),
            [
                partial(operator.eq, player.faction),
                partial(flip(operator.contains), rank_estimate[1]),
                partial(flip(operator.contains), rank_estimate[2]),
                partial(flip(operator.contains), player.get_prestige_level_stars()),
                partial(operator.eq, player.streak),
                partial(operator.eq, player.wins),
                partial(operator.eq, player.losses),
                partial(operator.eq, player.win_ratio),
                partial(operator.eq, player.drop_ratio),
                partial(operator.eq, player.num_games),
                *(partial(operator.eq, team_rank[i]) for i in range(3)),
                partial(operator.eq, player.get_steam_profile_url()),
                partial(flip(operator.contains), countries[player.country]),
                partial(flip(operator.contains), player.name),
            ],
            strict=True,
        )
    )


@pytest.mark.parametrize('faction', list(Faction))
def test_format_faction(out: Output, faction: Faction) -> None:
    assert _strip(out._format_faction('', faction)) in {faction.name, faction.full_name}  # noqa: SLF001


@pytest.mark.parametrize(
    ('rank', 'level'), [(-1, -1), (199, 16), (1000 * 2 / 3, 20 * 2 / 3)]
)
def test_format_rank(out: Output, rank: int, level: int) -> None:
    assert (
        _strip(out._format_rank(2, '', ('x', rank, False, False))) == f'x{rank}'  # noqa: SLF001
        or f'x{rank:.2f}'
    )
    assert (
        _strip(out._format_rank(1, '', ('x', level, False, False))) == f'x{level}'  # noqa: SLF001
        or f'x{level:.1f}'
    )


@pytest.mark.parametrize(('precision', 'value'), [(1, 1.0), (2, 1 / 3)])
def test_format_ratio(out: Output, precision: int, value: float) -> None:
    assert _strip(out._format_ratio(precision, '', value)) == f'{value:.{precision}%}'  # noqa: SLF001


def test_format_avg_label(out: Output) -> None:
    assert out._format_faction('', 'Avg') == out.settings.table.colors.label.colorize(  # noqa: SLF001
        'Avg'
    )
    assert out._format_ratio(0, '', 'Avg') == out.settings.table.colors.label.colorize(  # noqa: SLF001
        'Avg'
    )
    assert out._format_high_low('', 'Avg') == out.settings.table.colors.label.colorize(  # noqa: SLF001
        'Avg'
    )

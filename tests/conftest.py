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

from random import choice, randint, sample
from typing import Final

import pytest
from _pytest.monkeypatch import MonkeyPatch
from coh2_live_stats.data.countries import countries
from coh2_live_stats.data.faction import Faction
from coh2_live_stats.data.player import Player
from coh2_live_stats.data.team import Team

MIN_XP: Final[int] = 0
MAX_XP: Final[int] = 18785964
MIN_XP_LEVEL: Final[int] = 1
MAX_XP_LEVEL: Final[int] = 300


@pytest.fixture
def _equality(monkeypatch: MonkeyPatch) -> None:
    """Patch ``__eq__`` of ``Player`` and ``Team``.

    For testing purposes all their attributes should be compared for equality, even
    though they are identifiable by their Relic ID / `statGroup` ID.
    """

    def mock_eq(o1: object, o2: object) -> bool:
        if type(o1) is type(o2):
            return o1.__dict__ == o2.__dict__
        return NotImplemented

    monkeypatch.setattr(Player, '__eq__', mock_eq)
    monkeypatch.setattr(Team, '__eq__', mock_eq)


@pytest.fixture(scope='session')
def players1() -> list[Player]:
    return [
        Player(0, 'R.P. McMurphy', 2, 0, Faction.OKW),
        Player(1, 'Jules Winnfield', 3, 1, Faction.US),
        Player(2, 'Walter Sobchak', 4, 0, Faction.WM),
        Player(3, 'Vincent Vega', 5, 1, Faction.US),
        Player(4, 'Travis Bickle', 6, 0, Faction.OKW),
        Player(5, 'Raoul Duke', 7, 1, Faction.SU),
        Player(6, 'Hans Gruber', 8, 0, Faction.WM),
        Player(7, 'Tyler Durden', 9, 1, Faction.UK),
    ]


@pytest.fixture(scope='session')
def players2() -> list[Player]:
    return [
        Player(0, 'Joe Cabot', 10, 0, Faction.WM),
        Player(1, 'Nice Guy Eddie', 11, 1, Faction.US),
        Player(2, 'Mr. White', 12, 0, Faction.WM),
        Player(3, 'Mr. Orange', 13, 1, Faction.UK),
        Player(4, 'Mr. Blonde', 14, 0, Faction.OKW),
        Player(5, 'Mr. Brown', 15, 1, Faction.SU),
        Player(6, 'Mr. Pink', 16, 0, Faction.OKW),
        Player(7, 'Mr. Blue', 17, 1, Faction.SU),
    ]


def random_steam_id_64() -> int:
    """Return a random SteamID64 identifier for individuals.

    See: `Valve Developer Wiki <https://developer.valvesoftware.com/wiki/SteamID>`_.
    """
    z = randint(0, 2147483648 - 1)
    v = 0x0110000100000000
    y = randint(0, 1)
    return z * 2 + v + y


def random_country() -> str:
    return choice(list(countries))


def random_leaderboard_region() -> int:
    return randint(0, 7)


def xp_level_from_xp(xp: int) -> int:
    return round(MIN_XP_LEVEL + ((xp / MAX_XP) * (MAX_XP_LEVEL - MIN_XP_LEVEL)))


def random_xp() -> int:
    return randint(MIN_XP, MAX_XP)


def random_rank(rank_total: int) -> int:
    if rank_total > 0:
        choice([-1, randint(1, rank_total)])
    return -1


def random_highest_rank(rank: int, rank_total: int) -> int:
    if rank > 0:
        return randint(1, rank)
    if rank_total > 0:
        return randint(1, rank_total)
    return -1


def random_team(players: list[Player]) -> list[Player]:
    r_team_id = randint(0, 1)
    r_team_size = randint(2, 4)
    return sample([p for p in players if p.team_id == r_team_id], r_team_size)

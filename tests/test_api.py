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

import datetime
import random
from collections.abc import AsyncGenerator, Generator
from copy import deepcopy
from itertools import product
from typing import Any, Final

import pytest
import pytest_asyncio
import respx
from coh2_live_stats.coh2api import CoH2API, _Difficulty, _SoloMatchType, _TeamMatchType
from coh2_live_stats.data.faction import Faction, TeamFaction
from coh2_live_stats.data.player import Player
from coh2_live_stats.data.team import Team
from respx import MockRouter

from tests.conftest import (
    random_country,
    random_highest_rank,
    random_leaderboard_region,
    random_rank,
    random_steam_id_64,
    random_team,
    random_xp,
    xp_level_from_xp,
)

AVAIL_LEADERBOARDS: Final[dict[str, Any]] = {
    'result': {'code': 0, 'message': 'MOCKED'},
    'leaderboards': [
        {
            'id': 0,
            'name': 'CustomGerman',
            'isranked': 0,
            'leaderboardmap': [
                {'matchtype_id': 0, 'statgroup_type': 1, 'race_id': 0},
                {'matchtype_id': 22, 'statgroup_type': 1, 'race_id': 0},
            ],
        },
        {
            'id': 1,
            'name': 'CustomSoviet',
            'isranked': 0,
            'leaderboardmap': [
                {'matchtype_id': 0, 'statgroup_type': 1, 'race_id': 1},
                {'matchtype_id': 22, 'statgroup_type': 1, 'race_id': 1},
            ],
        },
        {
            'id': 2,
            'name': 'CustomWestGerman',
            'isranked': 0,
            'leaderboardmap': [
                {'matchtype_id': 0, 'statgroup_type': 1, 'race_id': 2},
                {'matchtype_id': 22, 'statgroup_type': 1, 'race_id': 2},
            ],
        },
        {
            'id': 3,
            'name': 'CustomAEF',
            'isranked': 0,
            'leaderboardmap': [
                {'matchtype_id': 0, 'statgroup_type': 1, 'race_id': 3},
                {'matchtype_id': 22, 'statgroup_type': 1, 'race_id': 3},
            ],
        },
        {
            'id': 4,
            'name': '1v1German',
            'isranked': 1,
            'leaderboardmap': [{'matchtype_id': 1, 'statgroup_type': 1, 'race_id': 0}],
        },
        {
            'id': 5,
            'name': '1v1Soviet',
            'isranked': 1,
            'leaderboardmap': [{'matchtype_id': 1, 'statgroup_type': 1, 'race_id': 1}],
        },
        {
            'id': 6,
            'name': '1v1WestGerman',
            'isranked': 1,
            'leaderboardmap': [{'matchtype_id': 1, 'statgroup_type': 1, 'race_id': 2}],
        },
        {
            'id': 7,
            'name': '1v1AEF',
            'isranked': 1,
            'leaderboardmap': [{'matchtype_id': 1, 'statgroup_type': 1, 'race_id': 3}],
        },
        {
            'id': 8,
            'name': '2v2German',
            'isranked': 1,
            'leaderboardmap': [{'matchtype_id': 2, 'statgroup_type': 1, 'race_id': 0}],
        },
        {
            'id': 9,
            'name': '2v2Soviet',
            'isranked': 1,
            'leaderboardmap': [{'matchtype_id': 2, 'statgroup_type': 1, 'race_id': 1}],
        },
        {
            'id': 10,
            'name': '2v2WestGerman',
            'isranked': 1,
            'leaderboardmap': [{'matchtype_id': 2, 'statgroup_type': 1, 'race_id': 2}],
        },
        {
            'id': 11,
            'name': '2v2AEF',
            'isranked': 1,
            'leaderboardmap': [{'matchtype_id': 2, 'statgroup_type': 1, 'race_id': 3}],
        },
        {
            'id': 12,
            'name': '3v3German',
            'isranked': 1,
            'leaderboardmap': [{'matchtype_id': 3, 'statgroup_type': 1, 'race_id': 0}],
        },
        {
            'id': 13,
            'name': '3v3Soviet',
            'isranked': 1,
            'leaderboardmap': [{'matchtype_id': 3, 'statgroup_type': 1, 'race_id': 1}],
        },
        {
            'id': 14,
            'name': '3v3WestGerman',
            'isranked': 1,
            'leaderboardmap': [{'matchtype_id': 3, 'statgroup_type': 1, 'race_id': 2}],
        },
        {
            'id': 15,
            'name': '3v3AEF',
            'isranked': 1,
            'leaderboardmap': [{'matchtype_id': 3, 'statgroup_type': 1, 'race_id': 3}],
        },
        {
            'id': 16,
            'name': '4v4German',
            'isranked': 1,
            'leaderboardmap': [{'matchtype_id': 4, 'statgroup_type': 1, 'race_id': 0}],
        },
        {
            'id': 17,
            'name': '4v4Soviet',
            'isranked': 1,
            'leaderboardmap': [{'matchtype_id': 4, 'statgroup_type': 1, 'race_id': 1}],
        },
        {
            'id': 18,
            'name': '4v4WestGerman',
            'isranked': 1,
            'leaderboardmap': [{'matchtype_id': 4, 'statgroup_type': 1, 'race_id': 2}],
        },
        {
            'id': 19,
            'name': '4v4AEF',
            'isranked': 1,
            'leaderboardmap': [{'matchtype_id': 4, 'statgroup_type': 1, 'race_id': 3}],
        },
        {
            'id': 20,
            'name': 'TeamOf2Axis',
            'isranked': 1,
            'leaderboardmap': [
                {'matchtype_id': 2, 'statgroup_type': 2, 'race_id': 0},
                {'matchtype_id': 2, 'statgroup_type': 2, 'race_id': 2},
                {'matchtype_id': 3, 'statgroup_type': 2, 'race_id': 0},
                {'matchtype_id': 3, 'statgroup_type': 2, 'race_id': 2},
                {'matchtype_id': 4, 'statgroup_type': 2, 'race_id': 0},
                {'matchtype_id': 4, 'statgroup_type': 2, 'race_id': 2},
            ],
        },
        {
            'id': 21,
            'name': 'TeamOf2Allies',
            'isranked': 1,
            'leaderboardmap': [
                {'matchtype_id': 2, 'statgroup_type': 2, 'race_id': 1},
                {'matchtype_id': 2, 'statgroup_type': 2, 'race_id': 3},
                {'matchtype_id': 2, 'statgroup_type': 2, 'race_id': 4},
                {'matchtype_id': 3, 'statgroup_type': 2, 'race_id': 1},
                {'matchtype_id': 3, 'statgroup_type': 2, 'race_id': 3},
                {'matchtype_id': 3, 'statgroup_type': 2, 'race_id': 4},
                {'matchtype_id': 4, 'statgroup_type': 2, 'race_id': 1},
                {'matchtype_id': 4, 'statgroup_type': 2, 'race_id': 3},
                {'matchtype_id': 4, 'statgroup_type': 2, 'race_id': 4},
            ],
        },
        {
            'id': 22,
            'name': 'TeamOf3Axis',
            'isranked': 1,
            'leaderboardmap': [
                {'matchtype_id': 3, 'statgroup_type': 3, 'race_id': 0},
                {'matchtype_id': 3, 'statgroup_type': 3, 'race_id': 2},
                {'matchtype_id': 4, 'statgroup_type': 3, 'race_id': 0},
                {'matchtype_id': 4, 'statgroup_type': 3, 'race_id': 2},
            ],
        },
        {
            'id': 23,
            'name': 'TeamOf3Allies',
            'isranked': 1,
            'leaderboardmap': [
                {'matchtype_id': 3, 'statgroup_type': 3, 'race_id': 1},
                {'matchtype_id': 3, 'statgroup_type': 3, 'race_id': 3},
                {'matchtype_id': 3, 'statgroup_type': 3, 'race_id': 4},
                {'matchtype_id': 4, 'statgroup_type': 3, 'race_id': 1},
                {'matchtype_id': 4, 'statgroup_type': 3, 'race_id': 3},
                {'matchtype_id': 4, 'statgroup_type': 3, 'race_id': 4},
            ],
        },
        {
            'id': 24,
            'name': 'TeamOf4Axis',
            'isranked': 1,
            'leaderboardmap': [
                {'matchtype_id': 4, 'statgroup_type': 4, 'race_id': 0},
                {'matchtype_id': 4, 'statgroup_type': 4, 'race_id': 2},
            ],
        },
        {
            'id': 25,
            'name': 'TeamOf4Allies',
            'isranked': 1,
            'leaderboardmap': [
                {'matchtype_id': 4, 'statgroup_type': 4, 'race_id': 1},
                {'matchtype_id': 4, 'statgroup_type': 4, 'race_id': 3},
                {'matchtype_id': 4, 'statgroup_type': 4, 'race_id': 4},
            ],
        },
        {
            'id': 26,
            'name': '2v2AIEasyAxis',
            'isranked': 0,
            'leaderboardmap': [
                {'matchtype_id': 5, 'statgroup_type': 0, 'race_id': 0},
                {'matchtype_id': 5, 'statgroup_type': 0, 'race_id': 2},
            ],
        },
        {
            'id': 27,
            'name': '2v2AIEasyAllies',
            'isranked': 0,
            'leaderboardmap': [
                {'matchtype_id': 5, 'statgroup_type': 0, 'race_id': 1},
                {'matchtype_id': 5, 'statgroup_type': 0, 'race_id': 3},
                {'matchtype_id': 5, 'statgroup_type': 0, 'race_id': 4},
            ],
        },
        {
            'id': 28,
            'name': '2v2AIMediumAxis',
            'isranked': 0,
            'leaderboardmap': [
                {'matchtype_id': 6, 'statgroup_type': 0, 'race_id': 0},
                {'matchtype_id': 6, 'statgroup_type': 0, 'race_id': 2},
            ],
        },
        {
            'id': 29,
            'name': '2v2AIMediumAllies',
            'isranked': 0,
            'leaderboardmap': [
                {'matchtype_id': 6, 'statgroup_type': 0, 'race_id': 1},
                {'matchtype_id': 6, 'statgroup_type': 0, 'race_id': 3},
                {'matchtype_id': 6, 'statgroup_type': 0, 'race_id': 4},
            ],
        },
        {
            'id': 30,
            'name': '2v2AIHardAxis',
            'isranked': 0,
            'leaderboardmap': [
                {'matchtype_id': 7, 'statgroup_type': 0, 'race_id': 0},
                {'matchtype_id': 7, 'statgroup_type': 0, 'race_id': 2},
            ],
        },
        {
            'id': 31,
            'name': '2v2AIHardAllies',
            'isranked': 0,
            'leaderboardmap': [
                {'matchtype_id': 7, 'statgroup_type': 0, 'race_id': 1},
                {'matchtype_id': 7, 'statgroup_type': 0, 'race_id': 3},
                {'matchtype_id': 7, 'statgroup_type': 0, 'race_id': 4},
            ],
        },
        {
            'id': 32,
            'name': '2v2AIExpertAxis',
            'isranked': 0,
            'leaderboardmap': [
                {'matchtype_id': 8, 'statgroup_type': 0, 'race_id': 0},
                {'matchtype_id': 8, 'statgroup_type': 0, 'race_id': 2},
            ],
        },
        {
            'id': 33,
            'name': '2v2AIExpertAllies',
            'isranked': 0,
            'leaderboardmap': [
                {'matchtype_id': 8, 'statgroup_type': 0, 'race_id': 1},
                {'matchtype_id': 8, 'statgroup_type': 0, 'race_id': 3},
                {'matchtype_id': 8, 'statgroup_type': 0, 'race_id': 4},
            ],
        },
        {
            'id': 34,
            'name': '3v3AIEasyAxis',
            'isranked': 0,
            'leaderboardmap': [
                {'matchtype_id': 9, 'statgroup_type': 0, 'race_id': 0},
                {'matchtype_id': 9, 'statgroup_type': 0, 'race_id': 2},
            ],
        },
        {
            'id': 35,
            'name': '3v3AIEasyAllies',
            'isranked': 0,
            'leaderboardmap': [
                {'matchtype_id': 9, 'statgroup_type': 0, 'race_id': 1},
                {'matchtype_id': 9, 'statgroup_type': 0, 'race_id': 3},
                {'matchtype_id': 9, 'statgroup_type': 0, 'race_id': 4},
            ],
        },
        {
            'id': 36,
            'name': '3v3AIMediumAxis',
            'isranked': 0,
            'leaderboardmap': [
                {'matchtype_id': 10, 'statgroup_type': 0, 'race_id': 0},
                {'matchtype_id': 10, 'statgroup_type': 0, 'race_id': 2},
            ],
        },
        {
            'id': 37,
            'name': '3v3AIMediumAllies',
            'isranked': 0,
            'leaderboardmap': [
                {'matchtype_id': 10, 'statgroup_type': 0, 'race_id': 1},
                {'matchtype_id': 10, 'statgroup_type': 0, 'race_id': 3},
                {'matchtype_id': 10, 'statgroup_type': 0, 'race_id': 4},
            ],
        },
        {
            'id': 38,
            'name': '3v3AIHardAxis',
            'isranked': 0,
            'leaderboardmap': [
                {'matchtype_id': 11, 'statgroup_type': 0, 'race_id': 0},
                {'matchtype_id': 11, 'statgroup_type': 0, 'race_id': 2},
            ],
        },
        {
            'id': 39,
            'name': '3v3AIHardAllies',
            'isranked': 0,
            'leaderboardmap': [
                {'matchtype_id': 11, 'statgroup_type': 0, 'race_id': 1},
                {'matchtype_id': 11, 'statgroup_type': 0, 'race_id': 3},
                {'matchtype_id': 11, 'statgroup_type': 0, 'race_id': 4},
            ],
        },
        {
            'id': 40,
            'name': '3v3AIExpertAxis',
            'isranked': 0,
            'leaderboardmap': [
                {'matchtype_id': 12, 'statgroup_type': 0, 'race_id': 0},
                {'matchtype_id': 12, 'statgroup_type': 0, 'race_id': 2},
            ],
        },
        {
            'id': 41,
            'name': '3v3AIExpertAllies',
            'isranked': 0,
            'leaderboardmap': [
                {'matchtype_id': 12, 'statgroup_type': 0, 'race_id': 1},
                {'matchtype_id': 12, 'statgroup_type': 0, 'race_id': 3},
                {'matchtype_id': 12, 'statgroup_type': 0, 'race_id': 4},
            ],
        },
        {
            'id': 42,
            'name': '4v4AIEasyAxis',
            'isranked': 0,
            'leaderboardmap': [
                {'matchtype_id': 13, 'statgroup_type': 0, 'race_id': 0},
                {'matchtype_id': 13, 'statgroup_type': 0, 'race_id': 2},
            ],
        },
        {
            'id': 43,
            'name': '4v4AIEasyAllies',
            'isranked': 0,
            'leaderboardmap': [
                {'matchtype_id': 13, 'statgroup_type': 0, 'race_id': 1},
                {'matchtype_id': 13, 'statgroup_type': 0, 'race_id': 3},
                {'matchtype_id': 13, 'statgroup_type': 0, 'race_id': 4},
            ],
        },
        {
            'id': 44,
            'name': '4v4AIMediumAxis',
            'isranked': 0,
            'leaderboardmap': [
                {'matchtype_id': 14, 'statgroup_type': 0, 'race_id': 0},
                {'matchtype_id': 14, 'statgroup_type': 0, 'race_id': 2},
            ],
        },
        {
            'id': 45,
            'name': '4v4AIMediumAllies',
            'isranked': 0,
            'leaderboardmap': [
                {'matchtype_id': 14, 'statgroup_type': 0, 'race_id': 1},
                {'matchtype_id': 14, 'statgroup_type': 0, 'race_id': 3},
                {'matchtype_id': 14, 'statgroup_type': 0, 'race_id': 4},
            ],
        },
        {
            'id': 46,
            'name': '4v4AIHardAxis',
            'isranked': 0,
            'leaderboardmap': [
                {'matchtype_id': 15, 'statgroup_type': 0, 'race_id': 0},
                {'matchtype_id': 15, 'statgroup_type': 0, 'race_id': 2},
            ],
        },
        {
            'id': 47,
            'name': '4v4AIHardAllies',
            'isranked': 0,
            'leaderboardmap': [
                {'matchtype_id': 15, 'statgroup_type': 0, 'race_id': 1},
                {'matchtype_id': 15, 'statgroup_type': 0, 'race_id': 3},
                {'matchtype_id': 15, 'statgroup_type': 0, 'race_id': 4},
            ],
        },
        {
            'id': 48,
            'name': '4v4AIExpertAxis',
            'isranked': 0,
            'leaderboardmap': [
                {'matchtype_id': 16, 'statgroup_type': 0, 'race_id': 0},
                {'matchtype_id': 16, 'statgroup_type': 0, 'race_id': 2},
            ],
        },
        {
            'id': 49,
            'name': '4v4AIExpertAllies',
            'isranked': 0,
            'leaderboardmap': [
                {'matchtype_id': 16, 'statgroup_type': 0, 'race_id': 1},
                {'matchtype_id': 16, 'statgroup_type': 0, 'race_id': 3},
                {'matchtype_id': 16, 'statgroup_type': 0, 'race_id': 4},
            ],
        },
        {
            'id': 50,
            'name': 'CustomBritish',
            'isranked': 0,
            'leaderboardmap': [
                {'matchtype_id': 0, 'statgroup_type': 1, 'race_id': 4},
                {'matchtype_id': 22, 'statgroup_type': 1, 'race_id': 4},
            ],
        },
        {
            'id': 51,
            'name': '1v1British',
            'isranked': 1,
            'leaderboardmap': [{'matchtype_id': 1, 'statgroup_type': 1, 'race_id': 4}],
        },
        {
            'id': 52,
            'name': '2v2British',
            'isranked': 1,
            'leaderboardmap': [{'matchtype_id': 2, 'statgroup_type': 1, 'race_id': 4}],
        },
        {
            'id': 53,
            'name': '3v3British',
            'isranked': 1,
            'leaderboardmap': [{'matchtype_id': 3, 'statgroup_type': 1, 'race_id': 4}],
        },
        {
            'id': 54,
            'name': '4v4British',
            'isranked': 1,
            'leaderboardmap': [{'matchtype_id': 4, 'statgroup_type': 1, 'race_id': 4}],
        },
    ],
    'matchTypes': [
        {
            'id': 0,
            'name': 'CUSTOM',
            'locstringid': 11077279,
            'localizedName': 'Friends Games',
        },
        {'id': 1, 'name': '1V1', 'locstringid': 11038958, 'localizedName': '1v1'},
        {'id': 2, 'name': '2V2', 'locstringid': 11038959, 'localizedName': '2v2'},
        {'id': 3, 'name': '3V3', 'locstringid': 11038960, 'localizedName': '3v3'},
        {'id': 4, 'name': '4V4', 'locstringid': 11038961, 'localizedName': '4v4'},
        {'id': 5, 'name': '2V2_AI_EASY', 'locstringid': -1},
        {'id': 6, 'name': '2V2_AI_MEDIUM', 'locstringid': -1},
        {'id': 7, 'name': '2V2_AI_HARD', 'locstringid': -1},
        {'id': 8, 'name': '2V2_AI_EXPERT', 'locstringid': -1},
        {'id': 9, 'name': '3V3_AI_EASY', 'locstringid': -1},
        {'id': 10, 'name': '3V3_AI_MEDIUM', 'locstringid': -1},
        {'id': 11, 'name': '3V3_AI_HARD', 'locstringid': -1},
        {'id': 12, 'name': '3V3_AI_EXPERT', 'locstringid': -1},
        {'id': 13, 'name': '4V4_AI_EASY', 'locstringid': -1},
        {'id': 14, 'name': '4V4_AI_MEDIUM', 'locstringid': -1},
        {'id': 15, 'name': '4V4_AI_HARD', 'locstringid': -1},
        {'id': 16, 'name': '4V4_AI_EXPERT', 'locstringid': -1},
        {
            'id': 22,
            'name': 'CUSTOM_PUBLIC',
            'locstringid': 11077280,
            'localizedName': 'Custom Games',
        },
    ],
    'races': [
        {
            'id': 0,
            'name': 'German',
            'faction_id': 1,
            'locstringid': 11006986,
            'localizedName': 'Wehrmacht',
        },
        {
            'id': 1,
            'name': 'Soviet',
            'faction_id': 0,
            'locstringid': 11049352,
            'localizedName': 'Soviet',
        },
        {
            'id': 2,
            'name': 'WGerman',
            'faction_id': 1,
            'locstringid': 11073205,
            'localizedName': 'Oberkommando West',
        },
        {
            'id': 3,
            'name': 'AEF',
            'faction_id': 0,
            'locstringid': 11073202,
            'localizedName': 'US Forces',
        },
        {
            'id': 4,
            'name': 'British',
            'faction_id': 0,
            'locstringid': 11078364,
            'localizedName': 'British Forces',
        },
    ],
    'factions': [
        {'id': 0, 'name': 'Allies', 'locstringid': 11076369, 'localizedName': 'Allies'},
        {'id': 1, 'name': 'Axis', 'locstringid': 11076370, 'localizedName': 'Axis'},
    ],
    'leaderboardRegions': [
        {'id': 0, 'name': 'Europe', 'locstringid': 11084172},
        {'id': 1, 'name': 'Middle East', 'locstringid': 11084173},
        {'id': 2, 'name': 'Asia', 'locstringid': 11083946},
        {'id': 3, 'name': 'North America', 'locstringid': 11083948},
        {'id': 4, 'name': 'South America', 'locstringid': 11083949},
        {'id': 5, 'name': 'Oceania', 'locstringid': 11083950},
        {'id': 6, 'name': 'Africa', 'locstringid': 11083951},
        {'id': 7, 'name': 'Unknown', 'locstringid': 11083952},
    ],
}


@pytest_asyncio.fixture(scope='module')
async def api() -> AsyncGenerator[CoH2API, Any]:
    api = CoH2API()
    yield api
    await api.close()


@pytest.mark.asyncio(scope='module')
async def test_init_leaderboard(
    mocked_api: MockRouter,  # noqa: ARG001
    api: CoH2API,
) -> None:
    await api.init_leaderboards()
    lb = next(iter(api.leaderboards.values()), None)
    assert lb is not None
    assert lb.get(CoH2API.KEY_LEADERBOARD_RANK_TOTAL) is not None


@pytest.fixture(scope='module')
def mocked_api(
    api: CoH2API,
    players1: list[Player],
    players_json: list[dict[str, Any]],
    leaderboards_json: dict[int, dict[str, Any]],
) -> Generator[MockRouter, Any, None]:
    with respx.mock() as respx_mock:
        params = {'title': 'coh2'}
        for i, p in enumerate(players1):
            respx_mock.get(
                CoH2API.URL_PLAYER, params=params | {'profile_ids': f'[{p.relic_id}]'}
            ).respond(json=players_json[i])

        respx_mock.get(CoH2API.URL_LEADERBOARDS, params=params).respond(
            json=AVAIL_LEADERBOARDS
        )

        for _id in api.leaderboards:
            respx_mock.get(
                CoH2API.URL_LEADERBOARD,
                params=params | {'count': 1, 'leaderboard_id': _id},
            ).respond(json=leaderboards_json[_id])

        yield respx_mock


@pytest.fixture(scope='module')
def leaderboards_json() -> dict[int, dict[str, Any]]:
    leaderboards = {}
    for leaderboard in AVAIL_LEADERBOARDS['leaderboards']:
        leaderboards[leaderboard['id']] = {
            'result': {'code': 0, 'message': 'MOCKED'},
            'statGroups': [],
            'leaderboardStats': [],
            'rankTotal': random.randint(1000, 5000),
        }
    return leaderboards


@pytest.fixture(scope='module')
def players_json(api: CoH2API, players1: list[Player]) -> list[dict[str, Any]]:
    players = [_player_json(api, p) for p in players1]
    team = random_team(players1)
    members = [players[players1.index(m)]['statGroups'][0]['members'][0] for m in team]
    team_lid = api.get_team_leaderboard_id(
        _TeamMatchType(len(team) - 2), TeamFaction(team[0].team_id)
    )
    team_sid = random.randint(1000, 2000)
    for p in team:
        idx = players1.index(p)
        players[idx]['statGroups'].append(
            {'id': team_sid, 'name': '', 'type': len(team), 'members': members}
        )
        players[idx]['leaderboardStats'].append(
            _leaderboard_stats_json(api, team_lid, team_sid)
        )
    return players


def _player_json(api: CoH2API, p: Player) -> dict[str, Any]:
    return {
        'result': {'code': 0, 'message': 'MOCKED'},
        'statGroups': [
            {
                'id': p.relic_id + 100,
                'name': '',
                'type': 1,
                'members': [_member_json(p)],
            }
        ],
        'leaderboardStats': _random_solo_leaderboard_stats(api),
    }


def _member_json(p: Player) -> dict[str, Any]:
    xp = random_xp()
    return {
        'profile_id': p.relic_id,
        'name': f'/steam/{random_steam_id_64()}',
        'alias': p.name,
        'personal_statgroup_id': p.relic_id + 100,
        'xp': xp,
        'level': xp_level_from_xp(xp),
        'leaderboardregion_id': random_leaderboard_region(),
        'country': random_country(),
    }


def _random_solo_leaderboard_stats(api: CoH2API) -> list[dict[str, Any]]:
    num = random.randint(0, len(api.solo_leaderboards) - 1)
    random_leaderboards = random.choices(list(api.solo_leaderboards), k=num)
    return [
        _leaderboard_stats_json(api, _id, random.randint(100, 1000))
        for _id in random_leaderboards
    ]


def _leaderboard_stats_json(
    api: CoH2API, leaderboard_id: int, stat_group_id: int
) -> dict[str, Any]:
    wins = random.randint(0, 5000)
    losses = random.randint(0, wins)
    rank_total = api.leaderboards[leaderboard_id].get(
        CoH2API.KEY_LEADERBOARD_RANK_TOTAL
    )
    if rank_total is None:
        rank_total = -1
    rank = random_rank(rank_total)
    highest_rank = random_highest_rank(rank, rank_total)

    today = datetime.datetime.now(tz=datetime.UTC).date()
    from_date = datetime.datetime(2013, 6, 25, tzinfo=datetime.UTC)
    to_date = datetime.datetime(today.year, today.month, today.day, tzinfo=datetime.UTC)
    if rank == -1:
        to_date -= datetime.timedelta(days=14)
    last_match_date = random.randint(
        int(from_date.timestamp()), int(to_date.timestamp())
    )

    return {
        'statgroup_id': stat_group_id,
        'leaderboard_id': leaderboard_id,
        'wins': wins,
        'losses': losses,
        'streak': random.randint(0, wins - losses),
        'disputes': 0,
        'drops': random.randint(0, wins + losses),
        'rank': rank,
        'ranktotal': rank_total,
        'ranklevel': Player.rank_level_from_rank(rank, rank_total),
        'regionrank': -1,
        'regionranktotal': -1,
        'lastmatchdate': last_match_date,
        'highestrank': highest_rank,
        'highestranklevel': Player.rank_level_from_rank(highest_rank, rank_total),
    }


@pytest.mark.asyncio(scope='module')
@pytest.mark.usefixtures('_equality')
async def test_get_players(
    mocked_api: MockRouter,  # noqa: ARG001
    api: CoH2API,
    players1: list[Player],
    players_json: list[dict[str, Any]],
) -> None:
    players_api = await api.get_players(deepcopy(players1))
    assertions = []

    for i, player in enumerate(players_api):
        player_json = Player(player.id, '', -1, player.team_id, player.faction)

        member_self = players_json[i]['statGroups'][0]['members'][0]
        player_json.relic_id = member_self['profile_id']
        player_json.name = member_self['alias']
        player_json.steam_profile = member_self['name']
        player_json.prestige = member_self['level']
        player_json.country = member_self['country']

        lid = CoH2API.get_solo_leaderboard_id(
            _SoloMatchType(len(players_json) // 2), player.faction
        )
        for s in players_json[i]['leaderboardStats']:
            if s['leaderboard_id'] == lid:
                player_json.wins = s['wins']
                player_json.losses = s['losses']
                player_json.streak = s['streak']
                player_json.drops = s['drops']
                player_json.rank = s['rank']
                player_json.rank_level = s['ranklevel']
                player_json.rank_total = s['ranktotal']
                player_json.highest_rank = s['highestrank']
                player_json.highest_rank_level = s['highestranklevel']
                break

        rank_total = api.leaderboards[lid].get(CoH2API.KEY_LEADERBOARD_RANK_TOTAL)
        if player_json.rank_total <= 0 and rank_total is not None:
            player_json.rank_total = rank_total

        for g in players_json[i]['statGroups'][1:]:
            t = Team(g['id'])
            for m in g['members']:
                t.members.append(m['profile_id'])
            for s in players_json[i]['leaderboardStats']:
                lid = CoH2API.get_team_leaderboard_id(
                    _TeamMatchType(g['type'] - 2), player.team_faction
                )
                if s['statgroup_id'] == t.id and s['leaderboard_id'] == lid:
                    t.rank = s['rank']
                    t.rank_level = s['ranklevel']
                    t.highest_rank = s['highestrank']
                    t.highest_rank_level = s['highestranklevel']
            player_json.teams.append(t)

        assertions.append(player == player_json)

    assert all(assertions)


@pytest_asyncio.fixture(scope='module')
async def available_leaderboards(
    mocked_api: MockRouter,  # noqa: ARG001
    api: CoH2API,
) -> dict[str, Any]:
    return await api.get_leaderboards()


@pytest.fixture
def leaderboard_maps(
    available_leaderboards: dict[str, Any],
) -> dict[int, list[dict[str, int]]]:
    return {
        lb['id']: lb['leaderboardmap'] for lb in available_leaderboards['leaderboards']
    }


@pytest.mark.parametrize(
    ('match_type', 'faction'), list(product(_SoloMatchType, Faction))
)
def test_get_solo_leaderboard_id(
    leaderboard_maps: dict[int, list[dict[str, int]]],
    match_type: _SoloMatchType,
    faction: Faction,
) -> None:
    leaderboard_id = CoH2API.get_solo_leaderboard_id(match_type, faction)
    assert {
        'matchtype_id': match_type.value,
        'statgroup_type': 1,
        'race_id': faction.id,
    } in leaderboard_maps[leaderboard_id]


@pytest.mark.parametrize(
    ('match_type', 'faction'), list(product(_TeamMatchType, TeamFaction))
)
def test_get_team_leaderboard_id(
    leaderboard_maps: dict[int, list[dict[str, int]]],
    match_type: _TeamMatchType,
    faction: TeamFaction,
) -> None:
    leaderboard_id = CoH2API.get_team_leaderboard_id(match_type, faction)
    leaderboard_map = [
        {'matchtype_id': mi, 'statgroup_type': match_type.value + 2, 'race_id': f.id}
        for mi in range(match_type.value + 2, 5)
        for f in Faction.from_team_faction(faction)
    ]
    assert leaderboard_map == leaderboard_maps[leaderboard_id]


@pytest.mark.parametrize(
    ('match_type', 'difficulty', 'faction'),
    list(product(_TeamMatchType, _Difficulty, TeamFaction)),
)
def test_get_ai_leaderboard_id(
    leaderboard_maps: dict[int, list[dict[str, int]]],
    match_type: _TeamMatchType,
    difficulty: _Difficulty,
    faction: TeamFaction,
) -> None:
    leaderboard_id = CoH2API.get_ai_leaderboard_id(match_type, difficulty, faction)
    leaderboard_map = [
        {
            'matchtype_id': 5 + len(_Difficulty) * match_type + difficulty,
            'statgroup_type': 0,
            'race_id': f.id,
        }
        for f in Faction.from_team_faction(faction)
    ]
    assert leaderboard_map == leaderboard_maps[leaderboard_id]

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

"""CoH2 API module."""

import asyncio
import logging
from enum import IntEnum
from typing import Any, cast, override

from httpx import AsyncClient, URL

from .data.faction import Faction, TeamFaction
from .data.player import Player
from .data.team import Team
from .util import cls_name

LOG = logging.getLogger('coh2_live_stats')


class _SoloMatchType(IntEnum):
    """Match types a solo player can play."""

    CUSTOM = 0
    S_1V1 = 1
    S_2V2 = 2
    S_3V3 = 3
    S_4V4 = 4

    @override
    def __repr__(self) -> str:
        return f'{cls_name(self)}.{self.name}'

    @override
    def __str__(self) -> str:
        return self.name.removeprefix('S_').lower()


class _TeamMatchType(IntEnum):
    """Match types pre-made teams can play.

    A team of 2 can play 2v2s, 3v3s and 4v4s. A team of 3 can play 3v3s and 4v4s.
    A team of 4 can play 4v4s.
    """

    T_2V2 = 0
    T_3V3 = 1
    T_4V4 = 2

    @override
    def __repr__(self) -> str:
        return f'{cls_name(self)}.{self.name}'

    @override
    def __str__(self) -> str:
        return self.name.removeprefix('T_').lower()


class _Difficulty(IntEnum):
    """CoH2 AI difficulty levels."""

    EASY = 0
    MEDIUM = 1
    HARD = 2
    EXPERT = 3

    @override
    def __repr__(self) -> str:
        return f'{cls_name(self)}.{self.name}'

    @override
    def __str__(self) -> str:
        return self.name.lower()


Leaderboard = dict[int, dict[str, Any]]


class CoH2API:
    """Used to make ``async`` requests to the CoH2 API."""

    URL_PLAYER = 'https://coh2-api.reliclink.com/community/leaderboard/GetPersonalStat'
    URL_LEADERBOARDS = (
        'https://coh2-api.reliclink.com/community/leaderboard/getAvailableLeaderboards'
    )
    URL_LEADERBOARD = (
        'https://coh2-api.reliclink.com/community/leaderboard/getleaderboard2'
    )

    KEY_LEADERBOARD_NAME = 'name'
    KEY_LEADERBOARD_RANK_TOTAL = 'rank_total'

    def __init__(self, timeout: int = 30) -> None:
        """Initialize the CoH2 API.

        :param timeout: number of seconds after which a request times out
        """
        self.http_client = AsyncClient()
        self.timeout = timeout
        self.solo_leaderboards: Leaderboard = {
            self.get_solo_leaderboard_id(m, f): {
                self.KEY_LEADERBOARD_NAME: f'{m}_{f.name}'
            }
            for m in _SoloMatchType
            if m != _SoloMatchType.CUSTOM
            for f in Faction
        }
        self.team_leaderboards: Leaderboard = {
            self.get_team_leaderboard_id(m, t): {
                self.KEY_LEADERBOARD_NAME: f'Team_of_{m.value + 2}_{t.name.capitalize()}'
            }
            for m in _TeamMatchType
            for t in TeamFaction
        }
        self.leaderboards: Leaderboard = self.solo_leaderboards | self.team_leaderboards

        LOG.info('Initialized %s[timeout=%d]', cls_name(self), self.timeout)

    async def get_players(self, players: list[Player]) -> list[Player]:
        """Initialize given players with CoH2 API data.

        :param players: players to initialize with API data
        :return: initialized players
        """
        LOG.info('GET players: %s', [p.relic_id for p in players])
        r = await asyncio.gather(*(self._get_player(p.relic_id) for p in players))
        if r:
            num_players = len(players)
            players = [
                self._init_player(p, num_players, j)
                for (p, j) in zip(players, r, strict=True)
            ]
        return players

    def _init_player(
        self, player: Player, num_players: int, json: dict[str, Any]
    ) -> Player:
        leaderboard_id = self.get_solo_leaderboard_id(
            _SoloMatchType(num_players // 2), player.faction
        )
        self._set_player_stats_from_json(player, leaderboard_id, json)
        self._set_rank_total(player, leaderboard_id)
        self._set_extra_player_data_from_json(player, json)
        self._set_teams_from_json(player, json)
        LOG.info('Initialized player: %s', player)
        return player

    @staticmethod
    def get_solo_leaderboard_id(__m: _SoloMatchType, __f: Faction) -> int:
        """Relic leaderboard ID for games played solo.

        :param __m: type of the match played
        :param __f: faction the match is played with
        :return: leaderboard ID
        """
        if __m == _SoloMatchType.CUSTOM:
            return 50 if __f == Faction.UK else __f.id
        return 50 + __m if __f == Faction.UK else __m * 4 + __f.id

    @staticmethod
    def get_team_leaderboard_id(__m: _TeamMatchType, __t: TeamFaction) -> int:
        """Relic leaderboard ID for team games.

        :param __m: type of the match played
        :param __t: team faction the match is played for
        :return: leaderboard ID
        """
        return 20 + __m * 2 + __t

    @staticmethod
    def get_ai_leaderboard_id(
        __m: _TeamMatchType, __d: _Difficulty, __t: TeamFaction
    ) -> int:
        """Relic leaderboard ID for AI games.

        :param __m: type of the match played
        :param __d: difficulty of the match played
        :param __t: team faction the match is played for
        :return: leaderboard ID
        """
        return 26 + __m * 8 + __d * 2 + __t

    @staticmethod
    def _set_player_stats_from_json(
        player: Player, leaderboard_id: int, json: dict[str, Any]
    ) -> None:
        if not json:
            return

        for s in json['leaderboardStats']:
            if s['leaderboard_id'] == leaderboard_id:
                player.wins = s['wins']
                player.losses = s['losses']
                player.streak = s['streak']
                player.drops = s['drops']
                player.rank = s['rank']
                player.rank_level = s['ranklevel']
                player.rank_total = s['ranktotal']
                player.highest_rank = s['highestrank']
                player.highest_rank_level = s['highestranklevel']
                return

    def _set_rank_total(self, player: Player, leaderboard_id: int) -> None:
        rank_total = self.leaderboards[leaderboard_id].get(
            self.KEY_LEADERBOARD_RANK_TOTAL
        )
        if player.rank_total <= 0 and rank_total is not None:
            player.rank_total = rank_total

    @staticmethod
    def _set_extra_player_data_from_json(player: Player, json: dict[str, Any]) -> None:
        if not json:
            return

        for g in json['statGroups']:
            for m in g['members']:
                if m['profile_id'] == player.relic_id:
                    player.name = m['alias']
                    player.steam_profile = m['name']
                    player.prestige = m['level']
                    player.country = m['country']
                    return

    def _set_teams_from_json(self, player: Player, json: dict[str, Any]) -> None:
        if not json:
            return

        for g in json['statGroups']:
            if g['type'] <= 1:
                continue
            t = Team(g['id'])
            for m in g['members']:
                t.members.append(m['profile_id'])
            for s in json['leaderboardStats']:
                lid = self.get_team_leaderboard_id(
                    _TeamMatchType(g['type'] - 2), player.team_faction
                )
                if s['statgroup_id'] == t.id and s['leaderboard_id'] == lid:
                    t.rank = s['rank']
                    t.rank_level = s['ranklevel']
                    t.highest_rank = s['highestrank']
                    t.highest_rank_level = s['highestranklevel']
            player.teams.append(t)

    async def _get_player(self, relic_id: int) -> dict[str, Any]:
        if relic_id <= 0:
            return {}

        params = {'title': 'coh2', 'profile_ids': f'[{relic_id}]'}
        LOG.info('GET player: %s', str(URL(self.URL_PLAYER, params=params)))
        r = await self.http_client.get(
            self.URL_PLAYER, params=params, timeout=self.timeout
        )
        r.raise_for_status()
        return cast(dict[str, Any], r.json())

    async def init_leaderboards(self) -> None:
        """Initialize CoH2 leaderboards with their total amount of ranked players."""
        LOG.info('GET leaderboards: %s', list(self.leaderboards))
        r = await asyncio.gather(
            *(self._get_leaderboard(_id) for _id in self.leaderboards)
        )
        if r:
            for i, _id in enumerate(self.leaderboards):
                self.leaderboards[_id][self.KEY_LEADERBOARD_RANK_TOTAL] = r[i][
                    'rankTotal'
                ]
        LOG.info('Initialized leaderboards: %s', self.leaderboards)

    async def get_leaderboards(self) -> dict[str, Any]:
        """Get leaderboard data for all available CoH2 leaderboards.

        Includes match types, races, factions and leaderboard regions as defined by
        Relic.
        """
        r = await self.http_client.get(
            self.URL_LEADERBOARDS, params={'title': 'coh2'}, timeout=self.timeout
        )
        r.raise_for_status()
        return cast(dict[str, Any], r.json())

    async def _get_leaderboard(self, leaderboard_id: int) -> dict[str, Any]:
        params: dict[str, str | int] = {
            'title': 'coh2',
            'count': 1,
            'leaderboard_id': leaderboard_id,
        }
        r = await self.http_client.get(
            self.URL_LEADERBOARD, params=params, timeout=self.timeout
        )
        r.raise_for_status()
        return cast(dict[str, Any], r.json())

    async def close(self) -> None:
        """Close the HTTP Client."""
        LOG.info('Closing HTTP client: %s', cls_name(self.http_client))
        await self.http_client.aclose()

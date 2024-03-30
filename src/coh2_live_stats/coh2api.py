#  Copyright (C) 2024 Andreas Becker.
#
#  This file is part of CoH2LiveStats.
#
#  CoH2LiveStats is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any
#  later version.
#
#  Foobar is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with Foobar. If not,
#  see <https://www.gnu.org/licenses/>.

import asyncio

from httpx import AsyncClient

from .data.leaderboard import Leaderboard
from .data.player import Player
from .data.team import Team


class CoH2API:
    URL_PLAYER = 'https://coh2-api.reliclink.com/community/leaderboard/GetPersonalStat'
    URL_LEADERBOARDS = 'https://coh2-api.reliclink.com/community/leaderboard/getAvailableLeaderboards'
    URL_LEADERBOARD = 'https://coh2-api.reliclink.com/community/leaderboard/getleaderboard2'

    def __init__(self, timeout=60):
        self.http_client = AsyncClient()
        self.timeout = timeout
        self.leaderboards: list[Leaderboard] = []

    async def get_players(self, players: list[Player]) -> list[Player]:
        if not self.leaderboards:
            raise ValueError('Initialize leaderboards first.')

        r = await asyncio.gather(*(self._get_player(p.relic_id) for p in players))
        if r:
            game_mode = (len(players) // 2) - 1
            players = [self._init_player(p, game_mode, j) for (p, j) in zip(players, r)]
            self._derive_pre_made_teams(players)
        return players

    def _init_player(self, player: Player, game_mode: int, json):
        player.leaderboard_id = player.get_leaderboard_id(game_mode)
        self._set_player_stats_from_json(player, json)
        self._set_rank_total(player)
        self._set_extra_player_data_from_json(player, json)
        self._set_teams_from_json(player, json)
        return player

    @staticmethod
    def _set_player_stats_from_json(player: Player, json):
        if not json:
            return

        for s in json['leaderboardStats']:
            if s['leaderboard_id'] == player.leaderboard_id:
                player.wins = s['wins']
                player.losses = s['losses']
                player.drops = s['drops']
                player.rank = s['rank']
                player.rank_level = s['ranklevel']
                player.rank_total = s['ranktotal']
                player.highest_rank = s['highestrank']
                player.highest_rank_level = s['highestranklevel']
                return

    def _set_rank_total(self, player: Player):
        if player.rank_total <= 0:
            for lb in self.leaderboards:
                if lb.id == player.leaderboard_id:
                    player.rank_total = lb.rank_total
                    break

    @staticmethod
    def _set_extra_player_data_from_json(player: Player, json):
        if not json:
            return

        for g in json['statGroups']:
            for m in g['members']:
                if m['profile_id'] == player.relic_id:
                    player.steam_profile = m['name']
                    player.prestige = m['level']
                    player.country = m['country']
                    return

    @staticmethod
    def _set_teams_from_json(player: Player, json):
        if not json:
            return

        for g in json['statGroups']:
            t = Team(g['id'])
            for m in g['members']:
                t.members.append(m['profile_id'])
            for s in json['leaderboardStats']:
                if s['statgroup_id'] == t.id and s['leaderboard_id'] == player.get_team_leaderboard_id(g['type']):
                    t.rank = s['rank']
                    t.rank_level = s['ranklevel']
                    t.highest_rank = s['highestrank']
                    t.highest_rank_level = s['highestranklevel']
            player.teams.append(t)

    @staticmethod
    def _derive_pre_made_teams(players):
        if len(players) < 4:
            return

        for player in players:
            pre_made_teams = []
            max_team_size = -1
            for team in player.teams:
                if len(team.members) > 1:
                    isvalid = True
                    for member in team.members:
                        if member not in [p.relic_id for p in players if p.team == player.team]:
                            isvalid = False
                            break
                    if isvalid:
                        team_size = len(team.members)
                        if team_size > max_team_size:
                            max_team_size = team_size
                        pre_made_teams.append(team)
            pre_made_teams.sort(key=lambda x: x.id)
            for team in pre_made_teams:
                if len(team.members) >= max_team_size:
                    player.pre_made_teams.append(team)

    async def _get_player(self, relic_id):
        if relic_id <= 0:
            return {}

        params = {'title': 'coh2', 'profile_ids': f'[{relic_id}]'}
        r = await self.http_client.get(self.URL_PLAYER, params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    async def init_leaderboards(self):
        leaderboards = []
        r1 = await self._get_leaderboards()
        if r1:
            lbs = [lb for lb in r1['leaderboards'] if lb['isranked'] == 1]
            r2 = await asyncio.gather(*(self._get_leaderboard(lb['id']) for lb in lbs))
            if r2:
                for i, lb in enumerate(lbs):
                    leaderboards.append(Leaderboard(lb['id'], lb['name'], r2[i]['rankTotal']))
        self.leaderboards = leaderboards

    async def _get_leaderboards(self):
        r = await self.http_client.get(self.URL_LEADERBOARDS, params={'title': 'coh2'}, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    async def _get_leaderboard(self, leaderboard_id):
        params = {'title': 'coh2', 'count': 1, 'leaderboard_id': f'{leaderboard_id}'}
        r = await self.http_client.get(self.URL_LEADERBOARD, params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    async def close(self):
        await self.http_client.aclose()

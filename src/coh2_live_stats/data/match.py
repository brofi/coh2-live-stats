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

import logging
from operator import add

from ..util import cls_name
from .player import Player
from .team import Team

LOG = logging.getLogger('coh2_live_stats')


class Match:
    def __init__(self, players: list[Player]):
        if not players or len(players) < 2:
            raise ValueError('No match with less than 2 players.')

        p0 = _Party([p for p in players if p.team_id == 0])
        p1 = _Party([p for p in players if p.team_id == 1])

        if p0.size != p1.size:
            raise ValueError('Parties must be of equal size.')

        self.parties: tuple[_Party, _Party] = p0, p1

        LOG.info('Initialized %s', cls_name(self))

    @property
    def highest_avg_rank_party(self) -> int:
        return (
            0
            if self.parties[0].avg_estimated_rank > self.parties[1].avg_estimated_rank
            else 1
        )

    @property
    def highest_avg_rank_level_party(self) -> int:
        return (
            0
            if self.parties[0].avg_estimated_rank_level
            > self.parties[1].avg_estimated_rank_level
            else 1
        )

    @property
    def has_pre_made_teams(self) -> bool:
        if self.parties[0].pre_made_teams or self.parties[1].pre_made_teams:
            return True
        return False


class _Party:
    def __init__(self, players: list[Player]):
        if not players or not 1 <= len(players) <= 4:
            raise ValueError('Party must have at least 1 and at most 4 players.')

        self.players = players
        self.pre_made_teams: set[Team] = set()

        self.min_relative_rank: float = 0.0
        self.max_relative_rank: float = 0.0
        player_ids = [p.relic_id for p in self.players]
        sum_relative_rank = 0
        for p in self.players:
            # There could be multiple possible pre-made teams per player. For example
            # when players A, B and C with teams (A,B), (B,C) have no team (A,B,
            # C). Which means either player A or C queued alone or the current match
            # is the first match of a new team (A,B,C).
            player_pre_made_teams = []
            max_player_pre_made_team_size = 0
            for team in p.teams:
                is_pre_made_team = all(member in player_ids for member in team.members)
                if is_pre_made_team:
                    pre_made_team_size = len(team.members)
                    if pre_made_team_size > max_player_pre_made_team_size:
                        max_player_pre_made_team_size = pre_made_team_size
                    player_pre_made_teams.append(team)
            for team in player_pre_made_teams:
                if len(team.members) >= max_player_pre_made_team_size:
                    self.pre_made_teams.add(team)

            sum_relative_rank += p.relative_rank
            if p.relative_rank < self.min_relative_rank:
                self.min_relative_rank = p.relative_rank
            if p.relative_rank > self.max_relative_rank:
                self.max_relative_rank = p.relative_rank
        avg_relative_rank = sum_relative_rank / self.size
        LOG.info('Initialized pre-made teams: %s', self.pre_made_teams)
        LOG.info(
            'Initialized (min, max) relative rank: (%f, %f)',
            self.min_relative_rank,
            self.max_relative_rank,
        )

        self.rank_estimates: dict[int, tuple[str, int, int]] = {}
        sum_estimates = (0, 0)
        for p in self.players:
            estimate_rank = p.estimate_rank(avg_relative_rank)
            sum_estimates = tuple(map(add, sum_estimates, estimate_rank[1:]))
            self.rank_estimates[p.relic_id] = estimate_rank
        LOG.info('Initialized rank estimates: %s', self.rank_estimates)

        self.avg_estimated_rank: float = sum_estimates[0] / self.size
        self.avg_estimated_rank_level: float = sum_estimates[1] / self.size
        LOG.info(
            'Initialized average estimated (rank, rank_level): (%f, %f)',
            self.avg_estimated_rank,
            self.avg_estimated_rank_level,
        )

        LOG.info('Initialized %s', cls_name(self))

    @property
    def size(self) -> int:
        return len(self.players)

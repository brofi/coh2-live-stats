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

"""Match and Party."""

import logging
import sys
from operator import add
from typing import TYPE_CHECKING

from coh2_live_stats.util import cls_name

from .player import Player

if TYPE_CHECKING:
    from .team import Team

LOG = logging.getLogger('coh2_live_stats')


class Match:
    """A match manages two ``Party`` objects."""

    MIN_SIZE = 2

    def __init__(self, players: list[Player]) -> None:
        """Initialize a match with the given players.

        The players must have team IDs set, allowing them to be split up into parties.
        :param players: players participating in this match
        """
        if not players or len(players) < self.MIN_SIZE:
            msg = f'No match with less than {self.MIN_SIZE} players.'
            raise ValueError(msg)

        p0 = Party([p for p in players if p.team_id == 0])
        p1 = Party([p for p in players if p.team_id == 1])

        if p0.size != p1.size:
            msg = 'Parties must be of equal size.'
            raise ValueError(msg)

        self.parties: tuple[Party, Party] = p0, p1

        LOG.info('Initialized %s', cls_name(self))

    @property
    def highest_avg_rank_party(self) -> int:
        """The party ID of the party with the highest average rank.

        :return: party ID
        """
        return (
            0
            if self.parties[0].avg_estimated_rank < self.parties[1].avg_estimated_rank
            else 1
        )

    @property
    def highest_avg_rank_level_party(self) -> int:
        """The party ID of the party with the highest average rank level.

        :return: party ID
        """
        return (
            0
            if self.parties[0].avg_estimated_rank_level
            > self.parties[1].avg_estimated_rank_level
            else 1
        )

    @property
    def has_pre_made_teams(self) -> bool:
        """Whether there are any pre-made teams in this match."""
        return (
            len(self.parties[0].pre_made_teams) > 0
            or len(self.parties[1].pre_made_teams) > 0
        )


class Party:
    """A group of players opposing another group of players in a ``Match``.

    A party in CoH2 has at least 1 and at most 4 players (given the match modes 1v1,
    2v2, 3v3 and 4v4). A party can have multiple pre-made teams (groups of players
    searching for a match together). A party holds statistics such as the minimum and
    maximum (relative) ranks of its players as well as their estimated ranks and the
    average estimated rank.
    """

    MIN_SIZE = 1
    MAX_SIZE = 4

    def __init__(self, players: list[Player]) -> None:
        """Initialize a party.

        :param players: players playing together as a ``Party`` in a ``Match``
        """
        if not players or not self.MIN_SIZE <= len(players) <= self.MAX_SIZE:
            msg = f'Party must have at least {self.MIN_SIZE} and at most {self.MAX_SIZE} players.'
            raise ValueError(msg)

        self.players = players
        self.pre_made_teams: set[Team] = set()

        self.min_relative_rank: float = sys.maxsize
        self.max_relative_rank: float = 0.0
        player_ids = [p.relic_id for p in self.players]
        relative_ranks = []
        for p in self.players:
            self._add_player_pre_made_teams(p, player_ids)
            if p.is_ranked:
                relative_ranks.append(p.relative_rank)
                self.min_relative_rank = min(self.min_relative_rank, p.relative_rank)
                self.max_relative_rank = max(self.max_relative_rank, p.relative_rank)

        avg_relative_rank = (
            sum(relative_ranks) / len(relative_ranks) if relative_ranks else 0.0
        )
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

    def _add_player_pre_made_teams(self, p: Player, player_ids: list[int]) -> None:
        # There could be multiple possible pre-made teams per player. For example when
        # players A, B and C with teams (A,B), (B,C) have no team (A,B,C). Which means
        # either player A or C queued alone or the current match is the first match of a
        # new team (A,B,C).
        player_pre_made_teams = []
        max_player_pre_made_team_size = 0
        for team in p.teams:
            is_pre_made_team = all(member in player_ids for member in team.members)
            if is_pre_made_team:
                pre_made_team_size = len(team.members)
                max_player_pre_made_team_size = max(
                    max_player_pre_made_team_size, pre_made_team_size
                )
                player_pre_made_teams.append(team)
        for team in player_pre_made_teams:
            if len(team.members) >= max_player_pre_made_team_size:
                self.pre_made_teams.add(team)

    @property
    def size(self) -> int:
        """Number of players in this party."""
        return len(self.players)

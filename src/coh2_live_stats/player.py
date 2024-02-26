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

from dataclasses import dataclass, field

from .faction import Faction
from .team import Team


@dataclass(eq=False)
class Player:
    # Log data
    id: int
    name: str
    relic_id: int
    team: int
    faction: Faction

    # CoH2 API data
    country: str = ''
    leaderboard_id: int = -1
    rank: int = -1
    rank_total: int = -1
    rank_level: int = -1
    highest_rank: int = -1
    highest_rank_level: int = -1
    teams: list[Team] = field(default_factory=list)

    # Derived data

    # There could be multiple possible pre-made teams. For example when players A, B
    # and C with teams (A,B), (B,C) have no team (A,B,C). Which means either player
    # A or C queued alone or the current match is the first match of a new team
    # (A,B,C).
    pre_made_teams: list[Team] = field(default_factory=list)

    def estimate_rank(self, avg_team_rank=0):
        if (self.rank > 0 and self.rank_level > 0) or self.relic_id <= 0:
            return '', self.rank, self.rank_level
        if self.highest_rank > 0 and self.highest_rank_level > 0:
            return '+', self.highest_rank, self.highest_rank_level
        if avg_team_rank > 0:
            return '?', round(avg_team_rank), self._rank_level_from_rank(avg_team_rank)
        return '?', round(self.rank_total / 2), self._rank_level_from_rank(self.rank_total / 2)

    def _rank_level_from_rank(self, rank):
        if rank <= 0 or self.rank_total <= 0:
            return -1

        lvl = 0
        if 0 < rank <= 2:
            lvl = 20
        elif 2 < rank <= 13:
            lvl = 19
        elif 13 < rank <= 36:
            lvl = 18
        elif 36 < rank <= 80:
            lvl = 17
        elif 80 < rank <= 200:
            lvl = 16
        else:  # build and search the rest of the ranking
            ratio_lvl_1_14 = [6, 8, 6, 5] + 3 * [10] + 2 * [7] + [6] + 4 * [5]
            n_top_200 = min(200, self.rank_total)
            remain = self.rank_total - n_top_200
            ranking = []
            for r in ratio_lvl_1_14:
                n = min(round(self.rank_total * (r / 100)), max(0, remain))
                ranking.append(remain + n_top_200)
                remain -= n
            while rank <= ranking[lvl]:
                lvl += 1
        return lvl

    @staticmethod
    def from_log(player_line):
        s = player_line.split(' ')
        faction = Faction.from_log(s.pop())
        team = int(s.pop())
        relic_id = int(s.pop())
        player_id = int(s.pop(0))
        name = ' '.join(s)
        return Player(player_id, name, relic_id, team, faction)

    def __eq__(self, other):
        if not isinstance(other, Player):
            return NotImplemented
        return self.relic_id == other.relic_id

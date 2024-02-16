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
    rank: int = -1
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

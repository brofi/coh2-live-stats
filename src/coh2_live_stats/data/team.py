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

"""Team module."""

from dataclasses import dataclass, field
from typing import override


@dataclass
class Team:
    """A CoH2 (pre-made) team with its members and stats."""

    id: int = -1
    members: list[int] = field(default_factory=list)
    rank: int = -1
    rank_level: int = -1
    highest_rank: int = -1
    highest_rank_level: int = -1

    @property
    def display_rank(self) -> tuple[str, str]:
        """The team's rank as it should be displayed."""
        if self.rank > 0 and self.rank_level > 0:
            return str(self.rank), str(self.rank_level)
        if self.highest_rank > 0 and self.highest_rank_level > 0:
            return str(self.highest_rank), str(self.highest_rank_level)
        return ('-',) * 2

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Team):
            return NotImplemented
        return self.id == other.id

    @override
    def __hash__(self) -> int:
        return hash(self.id)

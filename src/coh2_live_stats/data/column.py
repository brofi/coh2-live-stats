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

from enum import Enum, auto


class Column(Enum):
    FACTION = auto()
    RANK = auto()
    LEVEL = auto()
    WIN_RATIO = auto()
    DROP_RATIO = auto()
    TEAM = auto()
    TEAM_RANK = auto()
    TEAM_LEVEL = auto()
    COUNTRY = auto()
    NAME = auto()

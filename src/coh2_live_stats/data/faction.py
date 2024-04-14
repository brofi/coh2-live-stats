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

from enum import Enum, IntEnum
from typing import override

from coh2_live_stats.util import cls_name

from .color import Color


class Faction(Enum):
    WM = 0, 'german', 'Wehrmacht', Color.RED
    SU = 1, 'soviet', 'Soviet Union', Color.RED
    OKW = 2, 'west_german', 'Oberkommando West', Color.CYAN
    US = 3, 'aef', 'US Forces', Color.BLUE
    UK = 4, 'british', 'British Forces', Color.YELLOW

    def __init__(self, _id, key_log, full_name, default_color: Color = Color.WHITE):
        self.id = _id
        self.key_log = key_log
        self.full_name = full_name
        self.default_color = default_color

    @property
    def is_axis_faction(self):
        return self in {Faction.WM, Faction.OKW}

    @property
    def is_allies_faction(self):
        return self in {Faction.SU, Faction.US, Faction.UK}

    @classmethod
    def from_log(cls, faction_name):
        for member in cls:
            if member.key_log == faction_name:
                return member
        return None

    @override
    def __repr__(self):
        return f'{cls_name(self)}.{self.name}'

    @override
    def __str__(self):
        return self.full_name


class TeamFaction(IntEnum):
    AXIS = 0
    ALLIES = 1

    @classmethod
    def from_faction(cls, f: Faction):
        return cls(int(f.is_allies_faction))

    @override
    def __repr__(self):
        return f'{cls_name(self)}.{self.name}'

    @override
    def __str__(self):
        return self.name.capitalize()

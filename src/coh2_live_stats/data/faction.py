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

from dataclasses import dataclass

from .color import Color


@dataclass
class Faction:
    id: int
    name: str
    short: str

    @staticmethod
    def from_log(faction_name):
        if faction_name == 'german':
            return Faction(0, 'Wehrmacht', 'WM')
        elif faction_name == 'soviet':
            return Faction(1, 'Soviet Union', 'SU')
        elif faction_name == 'west_german':
            return Faction(2, 'Oberkommando West', 'OKW')
        elif faction_name == 'aef':
            return Faction(3, 'US Forces', 'US')
        elif faction_name == 'british':
            return Faction(4, 'British Forces', 'UK')
        else:
            return None

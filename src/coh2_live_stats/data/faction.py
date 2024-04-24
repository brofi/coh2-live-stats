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

"""Faction and TeamFaction."""

from __future__ import annotations

from enum import Enum, IntEnum
from typing import Self, override

from coh2_live_stats.util import cls_name

from .color import Color


class Faction(Enum):
    """Playable CoH2 factions."""

    WM = 0, 'german', 'Wehrmacht', Color.RED
    SU = 1, 'soviet', 'Soviet Union', Color.RED
    OKW = 2, 'west_german', 'Oberkommando West', Color.CYAN
    US = 3, 'aef', 'US Forces', Color.BLUE
    UK = 4, 'british', 'British Forces', Color.YELLOW

    def __init__(
        self, _id: int, key_log: str, full_name: str, default_color: Color = Color.WHITE
    ) -> None:
        """Initialize a faction.

        :param _id: id as used by Relic
        :param key_log: faction identifier used in the log file
        :param full_name: name of the faction
        :param default_color: default display color of the faction
        """
        self.id = _id
        self.key_log = key_log
        self.full_name = full_name
        self.default_color = default_color

    @property
    def is_axis_faction(self) -> bool:
        """Whether this faction is an Axis faction."""
        return self in self.axis_factions()

    @property
    def is_allies_faction(self) -> bool:
        """Whether this faction is an Allies faction."""
        return self in self.allies_factions()

    @staticmethod
    def allies_factions() -> list[Faction]:
        """Allies factions."""
        return [Faction.SU, Faction.US, Faction.UK]

    @staticmethod
    def axis_factions() -> list[Faction]:
        """Axis factions."""
        return [Faction.WM, Faction.OKW]

    @classmethod
    def from_team_faction(cls, team_faction: TeamFaction) -> list[Faction]:
        """Get factions belonging to given team faction."""
        return (
            cls.axis_factions()
            if team_faction == TeamFaction.AXIS
            else cls.allies_factions()
        )

    @classmethod
    def from_log(cls, faction_name: str) -> Self:
        """Get faction from its log file identifier.

        :param faction_name: the log file identifier
        :return: the faction identified by the given log file identifier
        """
        for member in cls:
            if member.key_log == faction_name:
                return member
        msg = f'Not a log file identifier: {faction_name!r}'
        raise ValueError(msg)

    @override
    def __repr__(self) -> str:
        return f'{cls_name(self)}.{self.name}'

    @override
    def __str__(self) -> str:
        return self.full_name


class TeamFaction(IntEnum):
    """What Relic considers a faction: Axis or Allies."""

    AXIS = 0
    ALLIES = 1

    @classmethod
    def from_faction(cls, f: Faction) -> Self:
        """Get the ``TeamFaction`` from a given ``Faction``.

        :param f: the ``Faction`` for which to get the ``TeamFaction``
        :return: the ``TeamFaction`` the given ``Faction`` belongs to
        """
        return cls(int(f.is_allies_faction))

    @override
    def __repr__(self) -> str:
        return f'{cls_name(self)}.{self.name}'

    @override
    def __str__(self) -> str:
        return self.name.capitalize()

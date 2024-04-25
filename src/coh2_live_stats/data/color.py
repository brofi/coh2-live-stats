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

"""ANSI color."""

from enum import IntEnum
from typing import override

from prettytable.colortable import RESET_CODE, Theme

from coh2_live_stats.util import cls_name


class Color(IntEnum):
    """Available colors with their ANSI codes."""

    BLACK = 30
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    MAGENTA = 35
    CYAN = 36
    WHITE = 37
    BRIGHT_BLACK = 90
    BRIGHT_RED = 91
    BRIGHT_GREEN = 92
    BRIGHT_YELLOW = 93
    BRIGHT_BLUE = 94
    BRIGHT_MAGENTA = 95
    BRIGHT_CYAN = 96
    BRIGHT_WHITE = 97

    @override
    def __repr__(self) -> str:
        return f'{cls_name(self)}.{self.name}'

    @override
    def __str__(self) -> str:
        return ' '.join(self.name.lower().split('_'))

    def colorize(self, s: str) -> str:
        """Wrap the given string in an ANSI escape sequence using this color.

        :param s: string to wrap
        :return: wrapped string
        """
        return Theme.format_code(str(self.value)) + s + RESET_CODE

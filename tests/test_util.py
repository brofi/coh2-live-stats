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

from pathlib import Path
from typing import get_args

import pytest
from coh2_live_stats.settings import Sound
from coh2_live_stats.util import (
    cls_name,
    cls_name_parent,
    play_sound,
    ratio,
    stop_sound,
)


class A:
    def __new__(cls) -> 'B':
        return super().__new__(B)


class B(A):
    pass


@pytest.mark.parametrize(
    ('obj', 'expected'),
    [(A, 'A'), (A(), 'B'), (B, 'B'), (B(), 'B'), (None, 'NoneType'), (0, 'int')],
)
def test_cls_name(obj: type | object, expected: str) -> None:
    assert cls_name(obj) == expected


@pytest.mark.parametrize(
    ('obj', 'expected'),
    [(A, 'object'), (A(), 'A'), (B, 'A'), (B(), 'A'), (None, 'object'), (0, 'object')],
)
def test_cls_name_parent(obj: type | object, expected: str) -> None:
    assert cls_name_parent(obj) == expected


@pytest.mark.parametrize(('x', 'total', 'expected'), [(1, 0, None), (1, 2, 0.5)])
def test_ratio(x: float, total: float, expected: float | None) -> None:
    assert ratio(x, total) == expected


@pytest.mark.parametrize('s', get_args(Sound))
def test_play_sound(s: Sound) -> None:
    assert play_sound(
        Path(__file__)
        .parents[1]
        .joinpath('src', 'coh2_live_stats', 'res', s)
        .with_suffix('.wav')
    )
    stop_sound()

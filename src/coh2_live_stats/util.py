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

import asyncio
import os
import sys
from inspect import isclass

import winsound


def cls_name(obj: type | object) -> str:
    return obj.__name__ if isclass(obj) else type(obj).__name__


def cls_name_parent(obj: type | object) -> str | None:
    return obj.mro()[1].__name__ if isclass(obj) else obj.__class__.mro()[1].__name__


def ratio(x, total) -> float:
    return x / total if total > 0 else 0


def clear():
    if os.name == 'nt':
        _ = os.system('cls')
        print('\b', end='')
    else:
        _ = os.system('clear')


async def progress_start():
    while True:
        for c in '/—\\|':
            print(f'\b{c}', end='', flush=True)
            await asyncio.sleep(0.25)


def progress_stop():
    print('\b \b', end='')


def play_sound(soundfile: str):
    try:
        winsound.PlaySound(None, 0)  # Stop currently playing waveform sound
        winsound.PlaySound(soundfile, winsound.SND_FILENAME | winsound.SND_NODEFAULT | winsound.SND_ASYNC)
    except RuntimeError:
        return False
    return True


def print_error(*values, **kwargs):
    print(*values, file=sys.stderr, **kwargs)

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

"""Utility functions."""

import sys
from contextlib import suppress
from inspect import isclass
from pathlib import Path

if sys.platform == 'win32':
    from winsound import SND_ASYNC, SND_FILENAME, SND_NODEFAULT, PlaySound


def cls_name(obj: type | object) -> str:
    """Get the class name of a class or an instance.

    :param obj: class or instance
    :return: class name
    """
    return obj.__name__ if isclass(obj) else type(obj).__name__


def cls_name_parent(obj: type | object) -> str | None:
    """Get the parent class name of a class or an instance.

    :param obj: class or instance
    :return: class name
    """
    return obj.mro()[1].__name__ if isclass(obj) else obj.__class__.mro()[1].__name__


def ratio(x: float, total: float) -> float | None:
    """X relative to total."""
    try:
        return x / total
    except ZeroDivisionError:
        return None


def stop_sound() -> None:
    """Stop currently playing waveform sound."""
    if sys.platform == 'win32':
        with suppress(RuntimeError):
            PlaySound(None, 0)


def play_sound(soundfile: Path) -> bool:
    """Plays a WAV file on windows.

    :param soundfile: the WAV file to play
    :return: whether the sound was played
    """
    if sys.platform == 'win32':
        # When using SND_ASYNC there is no RuntimeError for non-existing files without a
        # default sound.
        if not (soundfile.is_file() and soundfile.suffix == '.wav'):
            return False

        stop_sound()
        try:
            PlaySound(str(soundfile), SND_FILENAME | SND_NODEFAULT | SND_ASYNC)
        except RuntimeError:
            return False
    return True

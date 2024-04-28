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

"""Common script functions."""

from collections.abc import Sequence
from functools import partial


def wrap(__s: str, __w: str = "'") -> str:
    """Return a given string wrapped with another string.

    >>> wrap('text')
    "'text'"
    >>> wrap('var', '%')
    '%var%'
    """
    return f'{__w}{__s}{__w}'


def bullet(__s: str, __indent: int = 0, __c: str = '*') -> str:
    """Return a bullet point.

    >>> bullet('item')
    '* item'
    >>> bullet('item', 4, '@')
    '    @ item'
    """
    return f"{' ' * __indent}{__c} {__s}"


def list_multi(__seq: Sequence[str], __indent: int = 0) -> str:
    r"""Return a listing for a given sequence.

    >>> list_multi(['a', 'b', 'c'])
    '* a\n* b\n* c'
    >>> list_multi(['a', 'b', 'c'], 4)
    '    * a\n    * b\n    * c'
    """
    return '\n'.join(map(partial(bullet, __indent=__indent), __seq))


def list_single(__seq: Sequence[str], __indent: int = 0) -> str:
    """Return a listing as a single bullet point.

    >>> list_single(['a', 'b', 'c'])
    "* 'a', 'b' or 'c'"
    >>> list_single(['a', 'b', 'c'], 4)
    "    * 'a', 'b' or 'c'"
    """
    return bullet(list_inline(__seq), __indent)


def list_inline(__s: Sequence[str]) -> str:
    """Return a comma-separated list with conjunction.

    >>> list_inline(['a'])
    "'a'"
    >>> list_inline(['a', 'b'])
    "'a' or 'b'"
    >>> list_inline(['a', 'b', 'c'])
    "'a', 'b' or 'c'"
    """
    return (
        ' or '.join((', '.join(wrap(s) for s in __s[:-1]), wrap(__s[-1])))
        if len(__s) > 1
        else str(__s)[1:-1]
    )

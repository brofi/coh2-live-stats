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

"""Output module."""

import asyncio
import logging
from functools import partial
from typing import Any, Final, Protocol, cast, override

from prettytable import PrettyTable
from prettytable.colortable import ColorTable, Theme

from .data.countries import countries
from .data.faction import Faction
from .data.match import Match, Party
from .data.player import Player
from .settings import Settings
from .util import cls_name


class SupportsStr(Protocol):
    """An ABC with one abstract method __str__."""

    @override
    def __str__(self) -> str: ...


RankTableType = tuple[str, int | float, bool, bool]
HighLowTableType = tuple[str, bool, bool]
TableType = Faction | RankTableType | HighLowTableType | int | float | str | None


class _TableTypeError(Exception):
    def __init__(self, value: TableType) -> None:
        self.msg = f'Invalid type for argument: {value!r}'
        super().__init__(self.msg)


LOG = logging.getLogger('coh2_live_stats')


# ruff: noqa: T201
class Output:
    """Provides an interface for outputting ``Match`` data.

    Uses a ``PrettyTable`` to format the data. Heavily relies on user configuration.
    """

    ERR_NO_MATCH: Final[str] = 'Waiting for match...'
    ERR_NO_COLUMNS: Final[str] = 'No table columns to print.'

    def __init__(self, settings: Settings) -> None:
        """Initialize Output.

        :param settings: the user configuration
        """
        self.settings = settings
        self.table = self._create_output_table()
        self._set_formatters()
        LOG.info('Initialized %s', cls_name(self))

    def _create_output_table(self) -> PrettyTable:
        table: PrettyTable
        if self.settings.table.color:
            border_color = str(self.settings.table.colors.border.value)
            table = ColorTable(
                theme=Theme(
                    vertical_color=border_color,
                    horizontal_color=border_color,
                    junction_color=border_color,
                )
            )
        else:
            table = PrettyTable()

        table.border = self.settings.table.border == 'full'
        table.header = self.settings.table.header
        table.preserve_internal_border = self.settings.table.border == 'inner'

        return table

    def _set_field_names(self) -> None:
        cols = self.settings.table.columns
        visible_columns = [
            (c.label, c.align)
            for c in sorted(
                filter(
                    lambda c: c.visible,
                    [getattr(cols, attr) for attr in cols.model_fields],
                ),
                key=lambda c: c.pos,
            )
        ]
        self.table.field_names = [label for label, _ in visible_columns]

        for label, align in visible_columns:
            self.table.align[label] = align

        LOG.info('Output columns: %s', self.table.field_names)

    def _set_formatters(self) -> None:
        cols = self.settings.table.columns
        self.table.custom_format[cols.faction.label] = self._format_faction
        self.table.custom_format[cols.rank.label] = partial(self._format_rank, 2)
        self.table.custom_format[cols.level.label] = partial(self._format_rank, 1)
        self.table.custom_format[cols.streak.label] = self._format_streak
        self.table.custom_format[cols.win_ratio.label] = partial(self._format_ratio, 0)
        self.table.custom_format[cols.drop_ratio.label] = partial(self._format_ratio, 2)
        for c in cols.prestige, cols.country, cols.name:
            self.table.custom_format[c.label] = self._format_high_low

    def _set_column(self, row: list[SupportsStr], col: Any, val: SupportsStr) -> None:  # noqa: ANN401
        if col.visible:
            row[self.get_column_index(col)] = val

    def get_column_index(self, col: Any) -> int:  # noqa: ANN401
        """Return the index into ``PrettyTable`` field names for a given column."""
        return cast(int, self.table.field_names.index(col.label))

    def print_match(self, players: list[Player]) -> None:
        """Print a match.

        :param players: players participating in the match to print
        """
        self._clear()

        if not players:
            print(Output.ERR_NO_MATCH)
            return

        self.init_table(players)
        table = self.table_string()
        if table:
            print(table)
        else:
            LOG.warning(Output.ERR_NO_COLUMNS)

    def table_string(self) -> str:
        """Return string representation of output table."""
        if len(self.table.field_names) > 0:
            if self.settings.table.color:
                return self._custom_header_table()
            return self.table.get_string()
        return ''

    def _custom_header_table(self) -> str:
        # Unfortunately there is no custom header format and altering field
        # names directly would mess with everything that needs them (e.g.
        # formatting).
        table_lines = self.table.get_string().splitlines(keepends=True)
        i = int(self.settings.table.border == 'full')
        for h in self.table.field_names:
            header = ' ' * self.table.padding_width + h + ' ' * self.table.padding_width
            color_header = self.settings.table.colors.label.colorize(header)
            table_lines[i] = table_lines[i].replace(header, color_header)
        return ''.join(table_lines)

    def init_table(self, players: list[Player]) -> None:
        """Initialize output table with match data."""
        match = Match(players)
        self._set_field_names()
        for party_index, party in enumerate(match.parties):
            for player_index, player in enumerate(party.players):
                row = self._create_player_row(party, player)
                LOG.info(
                    'Add row (party=%d,player=%d): %s',
                    party_index,
                    player.relic_id,
                    row,
                )
                self.table.add_row(row, divider=player_index == party.size - 1)

            if self.has_average_row(party):
                avg_row = self._create_average_row(match, party, party_index)
                LOG.info('Add average row: %s', avg_row)
                self.table.add_row(avg_row, divider=True)

        if not self.has_team_columns(match):
            self._remove_team_columns()

    def has_team_columns(self, match: Match) -> bool:
        """Whether to include columns for the team, team rank and team level."""
        return self.settings.table.always_show_team or match.has_pre_made_teams

    def _remove_team_columns(self) -> None:
        cols = self.settings.table.columns
        for col in cols.team, cols.team_rank, cols.team_level:
            if col.visible:
                LOG.info('Deleting column %r', col.label)
                self.table.del_column(col.label)

    def _create_player_row(self, party: Party, player: Player) -> list[SupportsStr]:
        cols = self.settings.table.columns
        row: list[SupportsStr] = [''] * len(self.table.field_names)

        self._set_column(row, cols.faction, player.faction)

        is_high_low_lvl_player = tuple(
            party.size > 1 and player.is_ranked and cond
            for cond in (
                player.relative_rank <= party.min_relative_rank,
                player.relative_rank >= party.max_relative_rank,
            )
        )

        rank_estimate = party.rank_estimates[player.relic_id]
        self._set_column(
            row,
            cols.rank,
            (rank_estimate[0], rank_estimate[1], *is_high_low_lvl_player),
        )
        self._set_column(
            row,
            cols.level,
            (rank_estimate[0], rank_estimate[2], *is_high_low_lvl_player),
        )

        prestige = player.get_prestige_level_stars(
            self.settings.table.prestige_star_char,
            self.settings.table.prestige_half_star_char,
        )
        self._set_column(row, cols.prestige, (prestige, *is_high_low_lvl_player))

        self._set_column(row, cols.streak, player.streak)
        self._set_column(row, cols.wins, player.wins)
        self._set_column(row, cols.losses, player.losses)
        self._set_column(row, cols.win_ratio, player.win_ratio)
        self._set_column(row, cols.drop_ratio, player.drop_ratio)
        self._set_column(row, cols.num_games, player.num_games)

        team_names = []
        display_ranks = []
        for ti, team in enumerate(party.pre_made_teams):
            if player.relic_id in team.members:
                team_names.append(chr(ti + 65))
                display_ranks.append(team.display_rank)
        self._set_column(row, cols.team, ','.join(team_names))
        self._set_column(
            row, cols.team_rank, ','.join(rank for (rank, _) in display_ranks)
        )
        self._set_column(
            row, cols.team_level, ','.join(level for (_, level) in display_ranks)
        )

        self._set_column(row, cols.steam_profile, player.get_steam_profile_url())

        country = countries.get(player.country)
        self._set_column(
            row,
            cols.country,
            (country if country is not None else '', *is_high_low_lvl_player),
        )

        self._set_column(row, cols.name, (player.name, *is_high_low_lvl_player))

        return row

    def has_average_row(self, party: Party) -> bool:
        """Whether an average row should be created for the given ``Party``."""
        cols = self.settings.table.columns
        return (
            self.settings.table.show_average
            and (cols.rank.visible or cols.level.visible)
            and len([p for p in party.players if p.relic_id > 0]) > 1
        )

    def _has_average_row_label(self) -> bool:
        cols = self.settings.table.columns
        return (
            (
                cols.rank.label in self.table.field_names
                and self.get_column_index(cols.rank) > 0
                and cols.level.label not in self.table.field_names
            )
            or (
                cols.level.label in self.table.field_names
                and self.get_column_index(cols.level) > 0
                and cols.rank.label not in self.table.field_names
            )
            or (
                cols.rank.label in self.table.field_names
                and cols.level.label in self.table.field_names
                and self.get_column_index(cols.rank) > 0
                and self.get_column_index(cols.level) > 0
            )
        )

    def _create_average_row(
        self, match: Match, party: Party, party_index: int
    ) -> list[SupportsStr]:
        cols = self.settings.table.columns
        avg_row: list[SupportsStr] = [''] * len(self.table.field_names)

        avg_rank_prefix = '*' if party_index == match.highest_avg_rank_party else ''
        avg_rank_level_prefix = (
            '*' if party_index == match.highest_avg_rank_level_party else ''
        )
        self._set_column(
            avg_row,
            cols.rank,
            (avg_rank_prefix, party.avg_estimated_rank, False, False),
        )
        self._set_column(
            avg_row,
            cols.level,
            (avg_rank_level_prefix, party.avg_estimated_rank_level, False, False),
        )

        if self._has_average_row_label():
            avg_row[0] = 'Avg'

        return avg_row

    def _clear(self) -> None:
        print('\033[2J\033[H\033[3J', end='', flush=True)
        self.table.clear()

    @staticmethod
    async def progress_start() -> None:
        """Print an indeterminate progress bar."""
        while True:
            for c in '/—\\|':
                print(f'\033[D{c}', end='', flush=True)
                await asyncio.sleep(0.25)

    @staticmethod
    def progress_stop() -> None:
        """Remove leftovers from progress bar."""
        print('\033[D\033[K', end='', flush=True)

    def _format_string(self, v: TableType) -> str | None:
        if isinstance(v, str):
            return (
                self.settings.table.colors.label.colorize(v)
                if v and self.settings.table.color
                else v
            )
        return '' if v is None else None

    def _format_faction(self, _: str, v: Faction | str | None) -> str:
        s = self._format_string(v)
        if s is not None:
            return s

        if not isinstance(v, Faction):
            raise _TableTypeError(v)

        return (
            self.settings.table.colors.get_faction_color(v).colorize(v.name)
            if self.settings.table.color
            else v.name
        )

    def _format_rank(self, precision: int, _: str, v: RankTableType) -> str:
        if not isinstance(v, tuple):
            raise _TableTypeError(v)

        v_str = ''
        if isinstance(v[1], float):
            v_str = f'{v[0]}{v[1]:.{precision}f}'
        elif isinstance(v[1], int):
            v_str = f'{v[0]}{v[1]}'
        return self._format_high_low(_, (v_str, v[2], v[3]))

    def _format_ratio(self, precision: int, f: str, v: float | str | None) -> str:
        s = self._format_string(v)
        if s is not None:
            return s

        if not isinstance(v, float):
            raise _TableTypeError(v)

        v_str = f'{v:.{precision}%}'
        if self.settings.table.color:
            if (
                f == self.settings.table.columns.drop_ratio.label
                and v >= self.settings.table.drop_ratio_high_threshold
            ):
                v_str = self.settings.table.colors.player.high_drop_rate.colorize(v_str)
            elif f == self.settings.table.columns.win_ratio.label:
                v_str = self._format_high_low(
                    f,
                    (
                        v_str,
                        v >= self.settings.table.win_ratio_high_threshold,
                        v < self.settings.table.win_ratio_low_threshold,
                    ),
                )
        return v_str

    def _format_high_low(self, _: str, v: HighLowTableType | str | None) -> str:
        s = self._format_string(v)
        if s is not None:
            return s

        if not isinstance(v, tuple):
            raise _TableTypeError(v)

        if self.settings.table.color and v[1] != v[2]:
            color = self.settings.table.colors.player
            if v[1]:
                return color.high.colorize(v[0])
            if v[2]:
                return color.low.colorize(v[0])
        return v[0]

    def _format_streak(self, _: str, v: int | str | None) -> str:
        s = self._format_string(v)
        if s is not None:
            return s

        if not isinstance(v, int):
            raise _TableTypeError(v)

        if self.settings.table.color:
            if v > 0:
                return self.settings.table.colors.player.win_streak.colorize(f'+{v}')
            if v < 0:
                return self.settings.table.colors.player.loss_streak.colorize(str(v))
        return ''

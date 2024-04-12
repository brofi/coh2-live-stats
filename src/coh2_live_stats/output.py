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

import asyncio
import logging
import os
from functools import partial
from typing import Any

from prettytable import PrettyTable
from prettytable.colortable import ColorTable, Theme

from .data.countries import country_set
from .data.faction import Faction
from .data.match import Match
from .data.player import Player
from .settings import Settings
from .util import cls_name

LOG = logging.getLogger('coh2_live_stats')


# ruff: noqa: T201
class Output:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.table = self._create_output_table()
        self._set_formatters()
        LOG.info('Initialized %s', cls_name(self))

    def _create_output_table(self) -> PrettyTable:
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

        table.border = self.settings.table.border
        table.preserve_internal_border = True

        return table

    def _set_field_names(self):
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

    def _set_formatters(self):
        cols = self.settings.table.columns
        self.table.custom_format[cols.faction.label] = self._format_faction
        self.table.custom_format[cols.rank.label] = partial(self._format_rank, 2)
        self.table.custom_format[cols.level.label] = partial(self._format_rank, 1)
        for c in cols.win_ratio, cols.drop_ratio:
            self.table.custom_format[c.label] = self._format_ratio
        for c in cols.prestige, cols.country, cols.name:
            self.table.custom_format[c.label] = self._format_min_max

    def _set_column(self, row, col, val):
        if col.visible:
            row[self._get_column_index(col)] = val

    def _get_column_index(self, col):
        return self.table.field_names.index(col.label)

    def print_match(self, players: list[Player]):
        self._clear()

        if not players:
            print('Waiting for match...')
            return

        match = Match(players)
        self._set_field_names()
        cols = self.settings.table.columns
        for party_index, party in enumerate(match.parties):
            for player_index, player in enumerate(party.players):
                row = [''] * len(self.table.field_names)

                self._set_column(row, cols.faction, player.faction)

                is_high_low_lvl_player = (
                    player.is_ranked
                    and player.relative_rank <= party.min_relative_rank,
                    player.is_ranked
                    and player.relative_rank >= party.max_relative_rank,
                )

                rank_estimate = party.rank_estimates.get(player.relic_id)
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
                self._set_column(
                    row, cols.prestige, (prestige, *is_high_low_lvl_player)
                )

                self._set_column(row, cols.win_ratio, player.win_ratio)
                self._set_column(row, cols.drop_ratio, player.drop_ratio)

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
                    row,
                    cols.team_level,
                    ','.join(level for (_, level) in display_ranks),
                )

                self._set_column(
                    row, cols.steam_profile, player.get_steam_profile_url()
                )

                country: dict = country_set[player.country] if player.country else ''
                self._set_column(
                    row,
                    cols.country,
                    (country['name'] if country else '', *is_high_low_lvl_player),
                )

                self._set_column(row, cols.name, (player.name, *is_high_low_lvl_player))

                LOG.info(
                    'Add row (party=%d,player=%d): %s',
                    party_index,
                    player.relic_id,
                    row,
                )
                self.table.add_row(row, divider=player_index == party.size - 1)

            if (
                self.settings.table.show_average
                and (cols.rank.visible or cols.level.visible)
                and len([p for p in party.players if p.relic_id > 0]) > 1
            ):
                avg_row: list[Any] = [''] * len(self.table.field_names)

                avg_rank_prefix = (
                    '*' if party_index == match.highest_avg_rank_party else ''
                )
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
                    (
                        avg_rank_level_prefix,
                        party.avg_estimated_rank_level,
                        False,
                        False,
                    ),
                )

                if (
                    self._get_column_index(cols.rank) != 0
                    and self._get_column_index(cols.level) != 0
                ):
                    avg_row[0] = 'Avg'

                LOG.info('Add average row: %s', avg_row)
                self.table.add_row(avg_row, divider=True)

        if not self.settings.table.always_show_team and not match.has_pre_made_teams:
            for col in cols.team, cols.team_rank, cols.team_level:
                if col.visible:
                    LOG.info('Deleting column %r', col.label)
                    self.table.del_column(col.label)

        if len(self.table.field_names) > 0:
            if self.settings.table.color:
                # Unfortunately there is no custom header format and altering field
                # names directly would mess with everything that needs them (e.g.
                # formatting).
                table_lines = self.table.get_string().splitlines(keepends=True)
                i = int(self.settings.table.border)
                for h in self.table.field_names:
                    header = (
                        ' ' * self.table.padding_width
                        + h
                        + ' ' * self.table.padding_width
                    )
                    color_header = self.settings.table.colors.label.colorize(header)
                    table_lines[i] = table_lines[i].replace(header, color_header)
                print(''.join(table_lines))
            else:
                print(self.table)
        else:
            LOG.warning('No table columns to print.')

    def _clear(self):
        if os.name == 'nt':
            _ = os.system('cls')
            print('\b', end='')
        else:
            _ = os.system('clear')
        self.table.clear()

    @staticmethod
    async def progress_start():
        while True:
            for c in '/—\\|':
                print(f'\b{c}', end='', flush=True)
                await asyncio.sleep(0.25)

    @staticmethod
    def progress_stop():
        print('\b \b', end='')

    def _format_faction(self, _, v):
        colored = self.settings.table.color
        if isinstance(v, Faction):
            return (
                self.settings.table.colors.get_faction_color(v).colorize(v.name)
                if colored
                else v.name
            )
        return self.settings.table.colors.label.colorize(str(v)) if colored else str(v)

    def _format_rank(self, precision, _, v: any):
        if not v or not isinstance(v, tuple) or len(v) < 4 or v[1] <= 0:
            return ''

        v_str = ''
        if isinstance(v[1], float):
            v_str = f'{v[0]}{v[1]:.{precision}f}'
        elif isinstance(v[1], int):
            v_str = f'{v[0]}{v[1]}'
        return self._format_min_max(_, (v_str, v[2], v[3]))

    def _format_ratio(self, f, v):
        v_str = ''
        colored = self.settings.table.color
        if isinstance(v, float):
            v_str = f'{v:.0%}'
            if (
                colored
                and f == self.settings.table.columns.drop_ratio.label
                and v >= self.settings.table.drop_ratio_high_threshold
            ):
                v_str = self.settings.table.colors.player.high_drop_rate.colorize(v_str)
            elif f == self.settings.table.columns.win_ratio.label:
                v_str = self._format_min_max(
                    f,
                    (
                        v_str,
                        v >= self.settings.table.win_ratio_high_threshold,
                        v < self.settings.table.win_ratio_low_threshold,
                    ),
                )
        return v_str

    def _format_min_max(self, _, v: any):
        if not v or not isinstance(v, tuple) or len(v) < 3:
            return ''

        v_str = str(v[0])
        colored = self.settings.table.color
        if colored:
            if v[1]:
                v_str = self.settings.table.colors.player.high.colorize(v_str)
            if v[2]:
                v_str = self.settings.table.colors.player.low.colorize(v_str)
        return v_str

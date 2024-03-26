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

from dataclasses import dataclass, field
from functools import partial
from typing import Any

from prettytable import PrettyTable
from prettytable.colortable import Theme, ColorTable

from .data.column import Column
from .data.countries import country_set
from .data.faction import Faction
from .settings import Settings, Keys
from .util import avg, clear, colorize


@dataclass
class _TeamData:
    avg_estimated_rank: float = -1
    avg_estimated_rank_level: float = -1
    avg_rank_factor: float = -1
    high_level_players: list[int] = field(default_factory=list)
    low_level_players: list[int] = field(default_factory=list)
    pre_made_team_ids: list[int] = field(default_factory=list)


def _get_team_data(players):
    data = (_TeamData(), _TeamData())

    for team in range(2):
        team_players = [p for p in players if p.relic_id > 0 and p.team == team]

        for p in team_players:
            data[p.team].pre_made_team_ids.extend(
                t.id for t in p.pre_made_teams if t.id not in data[p.team].pre_made_team_ids)
            data[p.team].pre_made_team_ids.sort()

        ranked_players = [p for p in team_players if p.rank > 0]
        if ranked_players:
            rank_factors = [p.rank / p.rank_total for p in ranked_players]
            data[team].high_level_players = [p for p in ranked_players if
                                             p.rank / p.rank_total <= min(rank_factors)]
            data[team].low_level_players = [p for p in ranked_players if p.rank / p.rank_total >= max(rank_factors)]
            data[team].avg_rank_factor = avg(rank_factors)

        rank_estimates = [p.estimate_rank(data[team].avg_rank_factor) for p in team_players]
        if rank_estimates:
            data[team].avg_estimated_rank = avg([rank for (_, rank, _) in rank_estimates])
            data[team].avg_estimated_rank_level = avg([level for (_, _, level) in rank_estimates])

    return data


class Output:

    def __init__(self, settings: Settings):
        self.settings = settings

    def _pretty_player_table(self):
        table: PrettyTable
        if self.settings.get(Keys.Table.KEY_COLOR):
            border_color = str(self.settings.get_as_color(Keys.Table.Colors.KEY_BORDER).value)
            border_theme = Theme(vertical_color=border_color, horizontal_color=border_color,
                                 junction_color=border_color)
            table = ColorTable(theme=border_theme)
        else:
            table = PrettyTable()
        table.border = self.settings.get(Keys.Table.KEY_BORDER)
        table.preserve_internal_border = True

        column_keys = self.settings.get_columns().keys()
        table.field_names = [self.settings.get_column_label(Column[k.upper()]) for k in column_keys]
        self.set_format(table, Column.FACTION, self._format_faction)
        self.set_format(table, Column.RANK, partial(self._format_rank, 2))
        self.set_format(table, Column.LEVEL, partial(self._format_rank, 1))
        self.set_format(table, Column.WIN_RATIO, self._format_ratio)
        self.set_format(table, Column.DROP_RATIO, self._format_ratio)
        self.set_format(table, Column.COUNTRY, self._format_min_max)
        self.set_format(table, Column.NAME, self._format_min_max)

        align = [self.settings.get_column_align(Column[k.upper()]) for k in column_keys]
        assert len(align) == len(table.field_names)
        for ai, a in enumerate(align):
            table.align[table.field_names[ai]] = a

        return table

    def set_format(self, table: PrettyTable, c: Column, formatter):
        label = self.settings.get_column_label(c)
        if label is not None:
            table.custom_format[label] = formatter

    def set_column(self, row: list, c: Column, value):
        idx = self.settings.get_column_index(c)
        if idx >= 0:
            row[idx] = value

    def print_players(self, players):
        clear()

        if not players or len(players) < 2:
            print('No match found.')
            return

        team_data = _get_team_data(players)
        table = self._pretty_player_table()
        for team in range(2):
            team_players = [p for p in players if p.team == team]
            for tpi, player in enumerate(team_players):
                row = [''] * len(table.field_names)

                self.set_column(row, Column.FACTION, player.faction)

                is_high_lvl_player = player in team_data[team].high_level_players
                is_low_lvl_player = player in team_data[team].low_level_players

                rank_estimate = player.estimate_rank(team_data[team].avg_rank_factor)
                self.set_column(row, Column.RANK,
                                (rank_estimate[0], rank_estimate[1], is_high_lvl_player, is_low_lvl_player))
                self.set_column(row, Column.LEVEL,
                                (rank_estimate[0], rank_estimate[2], is_high_lvl_player, is_low_lvl_player))

                num_games = player.wins + player.losses
                self.set_column(row, Column.WIN_RATIO, player.wins / num_games if num_games > 0 else '')
                self.set_column(row, Column.DROP_RATIO, player.drops / num_games if num_games > 0 else '')

                team_ranks = [str(t.rank) for t in player.pre_made_teams]
                team_rank_levels = [str(t.rank_level) for t in player.pre_made_teams]
                for ti, t in enumerate(player.pre_made_teams):
                    if t.rank <= 0 < t.highest_rank:
                        team_ranks[ti] = '+' + str(t.highest_rank)
                    if t.rank_level <= 0 < t.highest_rank_level:
                        team_rank_levels[ti] = '+' + str(t.highest_rank_level)

                self.set_column(row, Column.TEAM, ','.join(map(str, [
                    chr(team_data[player.team].pre_made_team_ids.index(t.id) + 65) for t in player.pre_made_teams])))
                self.set_column(row, Column.TEAM_RANK, ','.join(team_ranks))
                self.set_column(row, Column.TEAM_LEVEL, ','.join(team_rank_levels))

                country: dict = country_set[player.country] if player.country else ''
                self.set_column(row, Column.COUNTRY,
                                (country['name'] if country else '', is_high_lvl_player, is_low_lvl_player))

                self.set_column(row, Column.NAME, (player.name, is_high_lvl_player, is_low_lvl_player))

                table.add_row(row, divider=True if tpi == len(team_players) - 1 else False)

            if (self.settings.get(Keys.Table.KEY_SHOW_AVERAGE)
                    and (self.settings.has_column(Column.RANK) or self.settings.has_column(Column.LEVEL))
                    and len([p for p in team_players if p.relic_id > 0]) > 1):

                avg_rank_prefix = '*' if team_data[team].avg_estimated_rank < team_data[
                    abs(team - 1)].avg_estimated_rank else ''
                avg_rank_level_prefix = '*' if team_data[team].avg_estimated_rank_level > team_data[
                    abs(team - 1)].avg_estimated_rank_level else ''
                avg_row: list[Any] = [''] * len(table.field_names)

                self.set_column(avg_row, Column.RANK,
                                (avg_rank_prefix, team_data[team].avg_estimated_rank, False, False))
                self.set_column(avg_row, Column.LEVEL,
                                (avg_rank_level_prefix, team_data[team].avg_estimated_rank_level, False, False))

                if (self.settings.get_column_index(Column.RANK) != 0
                        and self.settings.get_column_index(Column.LEVEL) != 0):
                    avg_row[0] = 'Avg'

                for c in Column.COUNTRY, Column.NAME:
                    self.set_column(avg_row, c, ('', False, False))

                table.add_row(avg_row, divider=True)

        if (not self.settings.get(Keys.Table.KEY_ALWAYS_SHOW_TEAM)
                and not team_data[0].pre_made_team_ids and not team_data[1].pre_made_team_ids):
            for col in (self.settings.get_column_label(Column.TEAM),
                        self.settings.get_column_label(Column.TEAM_RANK),
                        self.settings.get_column_label(Column.TEAM_LEVEL)):
                if col is not None:
                    table.del_column(col)

        if len(table.field_names) > 0:
            if self.settings.get(Keys.Table.KEY_COLOR):
                # Unfortunately there is no custom header format and altering field names directly would mess with
                # everything that needs them (e.g. formatting).
                table_lines = table.get_string().splitlines(True)
                i = int(self.settings.get(Keys.Table.KEY_BORDER))
                for h in table.field_names:
                    header = ' ' * table.padding_width + h + ' ' * table.padding_width
                    color_header = colorize(self.settings.get_as_color(Keys.Table.Colors.KEY_LABEL), header)
                    table_lines[i] = table_lines[i].replace(header, color_header)
                print(''.join(table_lines))
            else:
                print(table)
        else:
            print('No table columns to print.')

    def _format_faction(self, _, v):
        colored = self.settings.get(Keys.Table.KEY_COLOR)
        if isinstance(v, Faction):
            return colorize(self.settings.get_faction_color(v), v.name) if colored else v.name
        return colorize(self.settings.get_as_color(Keys.Table.Colors.KEY_LABEL), str(v)) if colored else str(v)

    def _format_rank(self, precision, _, v: tuple[str, any, bool, bool]):
        if v[1] <= 0:
            return ''

        v_str = str(v)
        if isinstance(v[1], float):
            v_str = f'{v[0]}{v[1]:.{precision}f}'
        elif isinstance(v[1], int):
            v_str = f'{v[0]}{v[1]}'
        return self._format_min_max(_, (v_str, v[2], v[3]))

    def _format_ratio(self, f, v):
        v_str = ''
        colored = self.settings.get(Keys.Table.KEY_COLOR)
        if isinstance(v, float):
            v_str = f'{v:.0%}'
            if colored and f == self.settings.get_column_label(Column.DROP_RATIO) and v >= 0.1:
                v_str = colorize(self.settings.get_as_color(Keys.Table.Colors.Player.KEY_HIGH_DROP_RATE), v_str)
            elif f == self.settings.get_column_label(Column.WIN_RATIO):
                v_str = self._format_min_max(f, (v_str, v >= 0.6, v < 0.5))
        return v_str

    def _format_min_max(self, _, v: tuple[any, bool, bool]):
        v_str = str(v[0])
        colored = self.settings.get(Keys.Table.KEY_COLOR)
        if colored:
            if v[1]:
                v_str = colorize(self.settings.get_as_color(Keys.Table.Colors.Player.KEY_HIGH), v_str)
            if v[2]:
                v_str = colorize(self.settings.get_as_color(Keys.Table.Colors.Player.KEY_LOW), v_str)
        return v_str

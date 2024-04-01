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

from .data.countries import country_set
from .data.faction import Faction, TeamFaction
from .data.player import Player
from .settings import Settings
from .util import avg, clear, colorize


@dataclass
class _TeamData:
    avg_estimated_rank: float = -1
    avg_estimated_rank_level: float = -1
    avg_rank_factor: float = -1
    high_level_players: list[int] = field(default_factory=list)
    low_level_players: list[int] = field(default_factory=list)
    pre_made_team_ids: list[int] = field(default_factory=list)


def _get_team_data(players: list[Player]):
    data = (_TeamData(), _TeamData())

    for team in TeamFaction:
        team_players = [p for p in players if p.relic_id > 0 and p.team == team]

        for p in team_players:
            data[p.team.value].pre_made_team_ids.extend(
                t.id for t in p.pre_made_teams if t.id not in data[p.team.value].pre_made_team_ids)
            data[p.team.value].pre_made_team_ids.sort()

        ranked_players = [p for p in team_players if p.is_ranked]
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
        self.table = self._create_output_table(settings)

    def _create_output_table(self, settings) -> PrettyTable:
        if settings.table.color:
            border_color = str(settings.table.colors.border.value)
            table = ColorTable(
                theme=Theme(vertical_color=border_color, horizontal_color=border_color, junction_color=border_color))
        else:
            table = PrettyTable()

        table.border = settings.table.border
        table.preserve_internal_border = True

        cols = settings.table.columns
        visible_columns = [(c.label, c.align) for c in sorted(
            filter(lambda c: c.visible, [getattr(cols, attr) for attr in cols.model_fields.keys()]),
            key=lambda c: c.pos)]
        table.field_names = [label for label, _ in visible_columns]

        for label, align in visible_columns:
            table.align[label] = align

        table.custom_format[cols.faction.label] = self._format_faction
        table.custom_format[cols.rank.label] = partial(self._format_rank, 2)
        table.custom_format[cols.level.label] = partial(self._format_rank, 1)
        for c in cols.win_ratio, cols.drop_ratio:
            table.custom_format[c.label] = self._format_ratio
        for c in cols.prestige, cols.country, cols.name:
            table.custom_format[c.label] = self._format_min_max

        return table

    def _set_column(self, row, col, val):
        if col.visible:
            row[self._get_column_index(col)] = val

    def _get_column_index(self, col):
        return self.table.field_names.index(col.label)

    def print_players(self, players):
        clear()

        if not players or len(players) < 2:
            print('Waiting for match...')
            return

        team_data = _get_team_data(players)
        cols = self.settings.table.columns
        for team in TeamFaction:
            team_players = [p for p in players if p.team == team]
            for tpi, player in enumerate(team_players):
                row = [''] * len(self.table.field_names)

                self._set_column(row, cols.faction, player.faction)

                is_high_low_lvl_player = (player in team_data[team].high_level_players,
                                          player in team_data[team].low_level_players)

                rank_estimate = player.estimate_rank(team_data[team].avg_rank_factor)
                self._set_column(row, cols.rank, (rank_estimate[0], rank_estimate[1], *is_high_low_lvl_player))
                self._set_column(row, cols.level, (rank_estimate[0], rank_estimate[2], *is_high_low_lvl_player))

                self._set_column(row, cols.prestige,
                                 (player.get_prestige_level_stars(self.settings.table.prestige_star_char,
                                                                  self.settings.table.prestige_half_star_char),
                                  *is_high_low_lvl_player))

                self._set_column(row, cols.win_ratio, player.win_ratio)
                self._set_column(row, cols.drop_ratio, player.drop_ratio)

                team_ranks = [str(t.rank) for t in player.pre_made_teams]
                team_rank_levels = [str(t.rank_level) for t in player.pre_made_teams]
                for ti, t in enumerate(player.pre_made_teams):
                    if t.rank <= 0:
                        team_ranks[ti] = '+' + str(t.highest_rank) if t.highest_rank > 0 else '-'
                    if t.rank_level <= 0:
                        team_rank_levels[ti] = '+' + str(t.highest_rank_level) if t.highest_rank_level > 0 else '-'

                self._set_column(row, cols.team, ','.join(map(str, [
                    chr(team_data[player.team.value].pre_made_team_ids.index(t.id) + 65)
                    for t in player.pre_made_teams])))
                self._set_column(row, cols.team_rank, ','.join(team_ranks))
                self._set_column(row, cols.team_level, ','.join(team_rank_levels))

                self._set_column(row, cols.steam_profile, player.get_steam_profile_url())

                country: dict = country_set[player.country] if player.country else ''
                self._set_column(row, cols.country, (country['name'] if country else '', *is_high_low_lvl_player))

                self._set_column(row, cols.name, (player.name, *is_high_low_lvl_player))

                self.table.add_row(row, divider=True if tpi == len(team_players) - 1 else False)

            if (self.settings.table.show_average and (cols.rank.visible or cols.level.visible)
                    and len([p for p in team_players if p.relic_id > 0]) > 1):

                avg_rank_prefix = '*' if team_data[team].avg_estimated_rank < team_data[
                    abs(team - 1)].avg_estimated_rank else ''
                avg_rank_level_prefix = '*' if team_data[team].avg_estimated_rank_level > team_data[
                    abs(team - 1)].avg_estimated_rank_level else ''
                avg_row: list[Any] = [''] * len(self.table.field_names)

                self._set_column(avg_row, cols.rank,
                                 (avg_rank_prefix, team_data[team].avg_estimated_rank, False, False))
                self._set_column(avg_row, cols.level,
                                 (avg_rank_level_prefix, team_data[team].avg_estimated_rank_level, False, False))

                if self._get_column_index(cols.rank) != 0 and self._get_column_index(cols.level) != 0:
                    avg_row[0] = 'Avg'

                self.table.add_row(avg_row, divider=True)

        if (not self.settings.table.always_show_team
                and not team_data[0].pre_made_team_ids and not team_data[1].pre_made_team_ids):
            for col in (cols.team, cols.team_rank, cols.team_level):
                if col.visible:
                    self.table.del_column(col.label)

        if len(self.table.field_names) > 0:
            if self.settings.table.color:
                # Unfortunately there is no custom header format and altering field names directly would mess with
                # everything that needs them (e.g. formatting).
                table_lines = self.table.get_string().splitlines(True)
                i = int(self.settings.table.border)
                for h in self.table.field_names:
                    header = ' ' * self.table.padding_width + h + ' ' * self.table.padding_width
                    color_header = colorize(self.settings.table.colors.label, header)
                    table_lines[i] = table_lines[i].replace(header, color_header)
                print(''.join(table_lines))
            else:
                print(self.table)
        else:
            print('No table columns to print.')

    def _format_faction(self, _, v):
        colored = self.settings.table.color
        if isinstance(v, Faction):
            return colorize(self.settings.table.colors.get_faction_color(v), v.name) if colored else v.name
        return colorize(self.settings.table.colors.label, str(v)) if colored else str(v)

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
            if (colored and f == self.settings.table.columns.drop_ratio.label
                    and v >= self.settings.table.drop_ratio_high_threshold):
                v_str = colorize(self.settings.table.colors.player.high_drop_rate, v_str)
            elif f == self.settings.table.columns.win_ratio.label:
                v_str = self._format_min_max(f, (v_str, v >= self.settings.table.win_ratio_high_threshold,
                                                 v < self.settings.table.win_ratio_low_threshold))
        return v_str

    def _format_min_max(self, _, v: any):
        if not v or not isinstance(v, tuple) or len(v) < 3:
            return ''

        v_str = str(v[0])
        colored = self.settings.table.color
        if colored:
            if v[1]:
                v_str = colorize(self.settings.table.colors.player.high, v_str)
            if v[2]:
                v_str = colorize(self.settings.table.colors.player.low, v_str)
        return v_str

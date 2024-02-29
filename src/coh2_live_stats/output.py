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

from prettytable import PrettyTable
from prettytable.colortable import Theme, ColorTable

from .data.color import Color
from .data.countries import country_set
from .data.faction import Faction
from .settings import Settings
from .util import avg, clear, colorize

_COL_FACTION = 'Fac'
_COL_RANK = 'Rank'
_COL_LEVEL = 'Lvl'
_COL_WIN_RATIO = 'W%'
_COL_DROP_RATIO = 'D%'
_COL_TEAM = 'Team'
_COL_TEAM_RANK = 'T_Rank'
_COL_TEAM_LEVEL = 'T_Lvl'
_COL_COUNTRY = 'Country'
_COL_NAME = 'Name'


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
        if self.settings.get('table.color'):
            border_color = str(self.settings.get_as_color('table.colors.border').value)
            border_theme = Theme(vertical_color=border_color, horizontal_color=border_color,
                                 junction_color=border_color)
            table = ColorTable(theme=border_theme)
        else:
            table = PrettyTable()
        table.border = self.settings.get('table.border')
        table.preserve_internal_border = True
        table.field_names = [_COL_FACTION, _COL_RANK, _COL_LEVEL, _COL_WIN_RATIO, _COL_DROP_RATIO, _COL_TEAM,
                             _COL_TEAM_RANK, _COL_TEAM_LEVEL, _COL_COUNTRY, _COL_NAME]
        table.custom_format[_COL_FACTION] = self._format_faction
        table.custom_format[_COL_RANK] = partial(self._format_rank, 2)
        table.custom_format[_COL_LEVEL] = partial(self._format_rank, 1)
        table.custom_format[_COL_WIN_RATIO] = self._format_ratio
        table.custom_format[_COL_DROP_RATIO] = self._format_ratio
        table.custom_format[_COL_COUNTRY] = self._format_min_max
        table.custom_format[_COL_NAME] = self._format_min_max
        align = ['l', 'r', 'r', 'r', 'r', 'c', 'r', 'r', 'l', 'l']
        assert len(align) == len(table.field_names)
        for ai, a in enumerate(align):
            table.align[table.field_names[ai]] = a
        return table

    def print_players(self, players):
        clear()

        if len(players) < 1:
            print('No players found.')
            return
        if len(players) < 2:
            print('Not enough players.')
            return

        team_data = _get_team_data(players)
        table = self._pretty_player_table()
        for team in range(2):
            team_players = [p for p in players if p.team == team]
            for tpi, player in enumerate(team_players):
                row = [player.faction]

                rank_estimate = player.estimate_rank(team_data[team].avg_rank_factor)
                is_high_lvl_player = player in team_data[team].high_level_players
                is_low_lvl_player = player in team_data[team].low_level_players
                row.append((rank_estimate[0], rank_estimate[1], is_high_lvl_player, is_low_lvl_player))
                row.append((rank_estimate[0], rank_estimate[2], is_high_lvl_player, is_low_lvl_player))

                num_games = player.wins + player.losses
                row.append(player.wins / num_games if num_games > 0 else '')
                row.append(player.drops / num_games if num_games > 0 else '')

                team_ranks = [str(t.rank) for t in player.pre_made_teams]
                team_rank_levels = [str(t.rank_level) for t in player.pre_made_teams]
                for ti, t in enumerate(player.pre_made_teams):
                    if t.rank <= 0 < t.highest_rank:
                        team_ranks[ti] = '+' + str(t.highest_rank)
                    if t.rank_level <= 0 < t.highest_rank_level:
                        team_rank_levels[ti] = '+' + str(t.highest_rank_level)
                row.append(','.join(map(str, [chr(team_data[player.team].pre_made_team_ids.index(t.id) + 65) for t in
                                              player.pre_made_teams])))
                row.append(','.join(team_ranks))
                row.append(','.join(team_rank_levels))
                country: dict = country_set[player.country] if player.country else ''
                row.append((country['name'] if country else '', is_high_lvl_player, is_low_lvl_player))
                row.append((player.name, is_high_lvl_player, is_low_lvl_player))

                table.add_row(row, divider=True if tpi == len(team_players) - 1 else False)

            if len([p for p in team_players if p.relic_id > 0]) > 1:
                avg_rank_prefix = '*' if team_data[team].avg_estimated_rank < team_data[
                    abs(team - 1)].avg_estimated_rank else ''
                avg_rank_level_prefix = '*' if team_data[team].avg_estimated_rank_level > team_data[
                    abs(team - 1)].avg_estimated_rank_level else ''
                avg_row = (['Avg', (avg_rank_prefix, team_data[team].avg_estimated_rank, False, False),
                           (avg_rank_level_prefix, team_data[team].avg_estimated_rank_level, False, False)] +
                           [''] * 5 + [('', False, False)] * 2)
                table.add_row(avg_row, divider=True)

        if not team_data[0].pre_made_team_ids and not team_data[1].pre_made_team_ids:
            for col in (_COL_TEAM, _COL_TEAM_RANK, _COL_TEAM_LEVEL):
                table.del_column(col)

        if self.settings.get('table.color'):
            # Unfortunately there is no custom header format and altering field names directly would mess with
            # everything that needs them (e.g. formatting).
            table_lines = table.get_string().splitlines(True)
            for h in table.field_names:
                header = ' ' * table.padding_width + h + ' ' * table.padding_width
                color_header = colorize(self.settings.get_as_color('table.colors.label'), header)
                table_lines[0] = table_lines[0].replace(header, color_header)
            print(''.join(table_lines))
        else:
            print(table)

    def _format_faction(self, _, v):
        colored = self.settings.get('table.color')
        if isinstance(v, Faction):
            return colorize(self._get_faction_color(v), v.short) if colored else v.short
        return colorize(self.settings.get_as_color('table.colors.label'), str(v)) if colored else str(v)

    def _get_faction_color(self, faction: Faction):
        for c in self.settings.get('table.colors.faction'):
            if faction.short.lower() == c:
                return self.settings.get_as_color(f'table.colors.faction.{c}')
        return Color.WHITE

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
        colored = self.settings.get('table.color')
        if isinstance(v, float):
            v_str = f'{v:.0%}'
            if colored and f == _COL_DROP_RATIO and v >= 0.1:
                v_str = colorize(self.settings.get_as_color('table.colors.player.high_drop_rate'), v_str)
            elif f == _COL_WIN_RATIO:
                v_str = self._format_min_max(f, (v_str, v >= 0.6, v < 0.5))
        return v_str

    def _format_min_max(self, _, v: tuple[any, bool, bool]):
        v_str = str(v[0])
        colored = self.settings.get('table.color')
        if colored:
            if v[1]:
                v_str = colorize(self.settings.get_as_color('table.colors.player.high'), v_str)
            if v[2]:
                v_str = colorize(self.settings.get_as_color('table.colors.player.low'), v_str)
        return v_str

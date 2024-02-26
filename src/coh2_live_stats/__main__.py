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
import concurrent.futures
import os
import sys
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path

from httpx import AsyncClient, RequestError, HTTPStatusError
from prettytable.colortable import ColorTable, Theme, RESET_CODE
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer

# Either use relative imports and run the project as a module from IDE Run/Debug Config (same as python -module) or
# use these absolute imports and run it as a script, but then the package needs to be installed.
# See: Solution 1/3 in https://stackoverflow.com/a/28154841.
# Since the creation of a virtual environment this somehow works without the project being installed.
from coh2_live_stats.countries import country_set
from coh2_live_stats.faction import Faction
from coh2_live_stats.leaderboard import Leaderboard
from coh2_live_stats.player import Player
from coh2_live_stats.team import Team

TIMEOUT = 60

logfile = Path.home().joinpath('Documents', 'My Games', 'Company of Heroes 2', 'warnings.log')
url_leaderboards = 'https://coh2-api.reliclink.com/community/leaderboard/getAvailableLeaderboards'
url_leaderboard = 'https://coh2-api.reliclink.com/community/leaderboard/getleaderboard2'
url_player = 'https://coh2-api.reliclink.com/community/leaderboard/GetPersonalStat'
http_client: AsyncClient
current_players = []
players_changed = False
leaderboards: [Leaderboard] = []


async def init_leaderboards():
    global leaderboards
    progress_indicator = asyncio.create_task(progress_start())
    try:
        r1 = await get_leaderboards_from_api()
        if r1:
            r2 = await asyncio.gather(
                *(get_leaderboard_from_api(lb['id']) for lb in r1['leaderboards'] if lb['isranked'] == 1))
            if r2:
                leaderboards = [Leaderboard(j1['id'], j1['name'], j2['rankTotal']) for (j1, j2) in
                                zip(r1['leaderboards'], r2)]
    except RequestError as e:
        print(f"An error occurred while requesting {e.request.url!r}.")
    except HTTPStatusError as e:
        print(f"Error response {e.response.status_code} while requesting {e.request.url!r}.")
    finally:
        progress_indicator.cancel()
        progress_stop()


async def get_leaderboards_from_api():
    r = await http_client.get(url_leaderboards, params={'title': 'coh2'}, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


async def get_leaderboard_from_api(leaderboard_id):
    params = {'title': 'coh2', 'count': 1, 'leaderboard_id': f'{leaderboard_id}'}
    r = await http_client.get(url_leaderboard, params=params, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


async def get_players():
    global current_players
    global players_changed
    players_changed = False
    players = get_players_from_log()
    if players and players != current_players:
        clear()
        progress_indicator = asyncio.create_task(progress_start())
        r = None
        try:
            r = await asyncio.gather(*(get_player_from_api(p) for p in players))
        except RequestError as e:
            print(f"An error occurred while requesting {e.request.url!r}.")
        except HTTPStatusError as e:
            print(f"Error response {e.response.status_code} while requesting {e.request.url!r}.")
        finally:
            progress_indicator.cancel()
            progress_stop()

        if r:
            game_mode = (len(players) // 2) - 1
            players = [init_player(p, game_mode, j) for (p, j) in zip(players, r)]
            derive_pre_made_teams(players)

            current_players = players
            players_changed = True
    return current_players


def get_players_from_log():
    player_lines = []
    # Get human player lines from log
    with open(logfile, encoding='utf-8') as f:
        lines = f.readlines()
    for line in lines:
        for sep in ['GAME -- Human Player:', 'GAME -- AI Player:']:
            player_line = line.partition(sep)[2]
            if player_line:
                player_lines.append(player_line.strip())

    if player_lines:
        latest_match_player_count = int(player_lines[len(player_lines) - 1].split(' ')[0]) + 1
        # Keep only player lines of latest match
        player_lines = player_lines[len(player_lines) - latest_match_player_count:]
        return [Player.from_log(player_line) for player_line in player_lines]
    return []


async def progress_start():
    while True:
        for c in '/—\\|':
            print(f'\b{c}', end='', flush=True)
            await asyncio.sleep(0.25)


def progress_stop():
    print('\b \b', end='')


async def get_player_from_api(player):
    if player.relic_id <= 0:
        return {}

    params = {'title': 'coh2', 'profile_ids': f'[{player.relic_id}]'}
    r = await http_client.get(url_player, params=params, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def init_player(player: Player, game_mode: int, json):
    player.leaderboard_id = get_leaderboard_id(game_mode, player)
    set_player_stats_from_json(player, json)
    set_country_from_json(player, json)
    set_teams_from_json(player, json)
    return player


def set_player_stats_from_json(player: Player, json):
    if not json:
        return

    for s in json['leaderboardStats']:
        if s['leaderboard_id'] == player.leaderboard_id:
            player.rank = s['rank']
            player.rank_level = s['ranklevel']
            player.rank_total = s['ranktotal']
            if player.rank_total <= 0:
                for lb in leaderboards:
                    if lb == player.leaderboard_id:
                        player.rank_total = lb.rank_total
                        break
            player.highest_rank = s['highestrank']
            player.highest_rank_level = s['highestranklevel']
            return


# game mode: 1v1: 0, 2v2: 1, 3v3: 2, 4v4: 3
def get_leaderboard_id(game_mode: int, player):
    if player.faction.id == 4:
        lid = 51 + game_mode
    else:
        # leaderboard_id 0..3 -> AI Games
        lid = 4 + (game_mode * 4) + player.faction.id
    return lid


def set_country_from_json(player: Player, json):
    if not json:
        return

    for g in json['statGroups']:
        for m in g['members']:
            if m['profile_id'] == player.relic_id:
                player.country = m['country']
                return


def set_teams_from_json(player: Player, json):
    if not json:
        return

    # TODO we gather all teams but only init those with the correct type
    for g in json['statGroups']:
        t = Team(g['id'])
        for m in g['members']:
            t.members.append(m['profile_id'])
        for s in json['leaderboardStats']:
            if s['statgroup_id'] == t.id and s['leaderboard_id'] == get_team_leaderboard_id(g['type'], player):
                t.rank = s['rank']
                t.rank_level = s['ranklevel']
                t.highest_rank = s['highestrank']
                t.highest_rank_level = s['highestranklevel']
        player.teams.append(t)


def get_team_leaderboard_id(num_team_members, player):
    leaderboard_id = -1
    if num_team_members > 1:
        leaderboard_id = 20 + (num_team_members - 2) * 2
        if is_team_allies(player):
            leaderboard_id += 1
    return leaderboard_id


def derive_pre_made_teams(players):
    if len(players) < 4:
        return

    for player in players:
        pre_made_teams = []
        max_team_size = -1
        for team in player.teams:
            if len(team.members) > 1:
                isvalid = True
                for member in team.members:
                    if member not in [p.relic_id for p in players if p.team == player.team]:
                        isvalid = False
                        break
                if isvalid:
                    team_size = len(team.members)
                    if team_size > max_team_size:
                        max_team_size = team_size
                    pre_made_teams.append(team)
        pre_made_teams.sort(key=lambda x: x.id)
        for team in pre_made_teams:
            if len(team.members) >= max_team_size:
                player.pre_made_teams.append(team)


def clear():
    if os.name == 'nt':
        _ = os.system('cls')
        print('\b', end='')
    else:
        _ = os.system('clear')


def print_players(players):
    if len(players) < 1:
        print('No players found.')
        return
    if len(players) < 2:
        print('Not enough players.')
        return

    team_data = get_team_data(players)
    table = pretty_player_table()
    for team in range(2):
        team_players = [p for p in players if p.team == team]
        for tpi, player in enumerate(team_players):
            row = [player.faction]

            rank_estimate = player.estimate_rank(team_data[team].avg_rank)
            is_high_lvl_player = 0 < rank_estimate[1] == team_data[team].max_rank
            is_low_lvl_player = 0 < rank_estimate[1] == team_data[team].min_rank
            row.append((rank_estimate[0], rank_estimate[1], is_high_lvl_player, is_low_lvl_player))
            row.append((rank_estimate[0], rank_estimate[2], is_high_lvl_player, is_low_lvl_player))

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
            avg_rank_prefix = '*' if team_data[team].avg_rank < team_data[abs(team - 1)].avg_rank else ''
            avg_rank_level_prefix = '*' if team_data[team].avg_rank_level > team_data[
                abs(team - 1)].avg_rank_level else ''
            avg_row = ['Avg', (avg_rank_prefix, team_data[team].avg_rank, False, False),
                       (avg_rank_level_prefix, team_data[team].avg_rank_level, False, False)] + [''] * 3 + [
                          ('', False, False)] * 2
            table.add_row(avg_row, divider=True)

    if not team_data[0].pre_made_team_ids and not team_data[1].pre_made_team_ids:
        for col in (col_team, col_team_rank, col_team_level):
            table.del_column(col)

    # Unfortunately there is no custom header format and altering field names directly would mess with everything
    # that needs them (e.g. formatting).
    table_lines = table.get_string().splitlines(True)
    for h in table.field_names:
        header = ' ' * table.padding_width + h + ' ' * table.padding_width
        table_lines[0] = table_lines[0].replace(header, colorize(90, header))
    print(''.join(table_lines))


@dataclass
class TeamData:
    min_rank: int = -1
    max_rank: int = sys.maxsize
    min_rank_level: int = sys.maxsize
    max_rank_level: int = -1
    avg_rank: float = -1
    avg_rank_level: float = -1
    pre_made_team_ids: list[int] = field(default_factory=list)


def get_team_data(players):
    data = (TeamData(), TeamData())

    for team in range(2):
        team_players = [p for p in players if p.relic_id > 0 and p.team == team]

        for p in team_players:
            data[p.team].pre_made_team_ids.extend(
                t.id for t in p.pre_made_teams if t.id not in data[p.team].pre_made_team_ids)
            data[p.team].pre_made_team_ids.sort()

        ranks = [p.rank for p in team_players if p.rank > 0]
        if ranks:
            data[team].min_rank = max(ranks)
            data[team].max_rank = min(ranks)
            data[team].avg_rank = avg(ranks)

        rank_levels = [p.rank_level for p in team_players if p.rank_level > 0]
        if rank_levels:
            data[team].min_rank_level = min(rank_levels)
            data[team].max_rank_level = max(rank_levels)

        rank_estimates = [p.estimate_rank(data[team].avg_rank) for p in team_players]
        if rank_estimates:
            data[team].avg_rank = avg([rank for (_, rank, _) in rank_estimates])
            data[team].avg_rank_level = avg([level for (_, _, level) in rank_estimates])

    return data


def avg(c):
    if not c:
        raise ValueError('Cannot calculate average of empty list.')
    return sum(c) / len(c)


col_faction = 'Fac'
col_rank = 'Rank'
col_level = 'Lvl'
col_team = 'Team'
col_team_rank = 'T_Rank'
col_team_level = 'T_Lvl'
col_country = 'Country'
col_name = 'Name'


def pretty_player_table():
    darker_borders = Theme(vertical_color="90", horizontal_color="90", junction_color="90")
    table = ColorTable(theme=darker_borders)
    table.border = False
    table.preserve_internal_border = True
    table.field_names = [col_faction, col_rank, col_level, col_team, col_team_rank, col_team_level, col_country,
                         col_name]
    table.float_format = '.2'
    table.custom_format[col_faction] = format_faction
    table.custom_format[col_rank] = partial(format_rank, 2)
    table.custom_format[col_level] = partial(format_rank, 1)
    table.custom_format[col_country] = format_min_max
    table.custom_format[col_name] = format_min_max
    align = ['l', 'r', 'r', 'c', 'r', 'r', 'l', 'l']
    assert len(align) == len(table.field_names)
    for ai, a in enumerate(align):
        table.align[table.field_names[ai]] = a
    return table


def format_min_max(_, v: tuple[any, bool, bool]):
    v_str = str(v[0])
    if v[1]:
        v_str = colorize(97, v_str)
    if v[2]:
        v_str = colorize(90, v_str)
    return v_str


def format_rank(precision, _, v: tuple[str, any, bool, bool]):
    if v[1] <= 0:
        return ''

    v_str = str(v)
    if isinstance(v[1], float):
        v_str = f'{v[0]}{v[1]:.{precision}f}'
    elif isinstance(v[1], int):
        v_str = f'{v[0]}{v[1]}'
    return format_min_max(_, (v_str, v[2], v[3]))


def format_faction(_, v):
    if isinstance(v, Faction):
        return colorize(v.color, v.short)
    return colorize(90, str(v))


def is_team_axis(player):
    return player.faction.id == 0 or player.faction.id == 2


def is_team_allies(player):
    return not is_team_axis(player)


def colorize(c, s):
    return Theme.format_code(str(c)) + s + RESET_CODE


class LogFileEventHandler(FileSystemEventHandler):

    def __init__(self, loop):
        self.loop = loop

    def on_modified(self, event: FileSystemEvent) -> None:
        if event.is_directory or event.src_path != str(logfile):
            return

        future_players: concurrent.futures.Future = asyncio.run_coroutine_threadsafe(get_players(), self.loop)
        # Don't block for future result here, since the Observer thread might need to be stopped
        future_players.add_done_callback(on_players_gathered)

    def on_deleted(self, event: FileSystemEvent) -> None:
        super().on_deleted(event)


def on_players_gathered(future_players):
    if players_changed:
        try:
            print_players(future_players.result())
        except concurrent.futures.CancelledError:
            pass


async def main():
    global http_client
    http_client = AsyncClient()
    observer = Observer()

    try:
        # Initial requests
        await init_leaderboards()
        print_players(await get_players())
        # Watch log files
        observer.schedule(LogFileEventHandler(asyncio.get_running_loop()), str(logfile.parent))
        observer.start()
        while True:
            # Force CoH2 to write out its collected log
            with open(logfile, mode="rb", buffering=0):
                await asyncio.sleep(1)
    # In asyncio `Ctrl-C` cancels the main task, which raises a Cancelled Error
    except asyncio.CancelledError:
        observer.stop()
        raise
    finally:
        if observer.is_alive():
            observer.join()
        await http_client.aclose()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except asyncio.CancelledError:
        pass
    except KeyboardInterrupt:
        pass

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
import time
from functools import partial
from pathlib import Path

import httpx
from prettytable.colortable import ColorTable, Theme, RESET_CODE
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer

# Either use relative imports and run the project as a module from IDE Run/Debug Config (same as python -module) or
# use these absolute imports and run it as a script, but then the package needs to be installed.
# See: Solution 1/3 in https://stackoverflow.com/a/28154841.
# Since the creation of a virtual environment this somehow works without the project being installed.
from coh2_live_stats.countries import country_set
from coh2_live_stats.player import Player
from coh2_live_stats.team import Team

logfile = Path.home().joinpath('Documents', 'My Games', 'Company of Heroes 2', 'warnings.log')
request_url = "https://coh2-api.reliclink.com/community/leaderboard/GetPersonalStat?title=coh2&profile_ids=[{}]"
current_players = []
players_changed = False


async def get_players():
    global current_players
    global players_changed
    players_changed = False
    players = get_players_from_log()
    if players and players != current_players:
        clear()
        # TODO maybe reuse for watcher
        #  but then don't close in finally?
        http_aclient = httpx.AsyncClient()
        url = 'https://coh2-api.reliclink.com/community/leaderboard/GetPersonalStat'
        progress_indicator = asyncio.create_task(progress_start())
        r = None
        try:
            r = await asyncio.gather(*(get_player_from_api(http_aclient, url, p) for p in players))
        except httpx.RequestError as e:
            print(f"An error occurred while requesting {e.request.url!r}.")
        except httpx.HTTPStatusError as e:
            print(f"Error response {e.response.status_code} while requesting {e.request.url!r}.")
        finally:
            await http_aclient.aclose()
            progress_indicator.cancel()
            # TODO in case of error we don't delete the correct char
            await progress_stop()

        if r:
            game_mode = (len(players) // 2) - 1
            players = [init_player_from_json(p, game_mode, j) for (p, j) in zip(players, r)]
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
        player_line = line.partition('GAME -- Human Player:')[2]
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
            print(f'\r{c}', end='', flush=True)
            await asyncio.sleep(0.25)


async def progress_stop():
    print('\b', end='')


async def get_player_from_api(client, url, player):
    params = {'title': 'coh2', 'profile_ids': f'[{player.relic_id}]'}
    r = await client.get(url, params=params, timeout=60)
    r.raise_for_status()
    return r.json()


def init_player_from_json(player: Player, game_mode: int, json):
    set_player_stats_from_json(player, game_mode, json)
    set_country_from_json(player, json)
    set_teams_from_json(player, json)
    return player


def set_player_stats_from_json(player: Player, game_mode: int, json):
    leaderboard_id = get_leaderboard_id(game_mode, player)
    for s in json['leaderboardStats']:
        if s['leaderboard_id'] == leaderboard_id:
            player.rank = s['rank']
            player.rank_level = s['ranklevel']
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
    for g in json['statGroups']:
        for m in g['members']:
            if m['profile_id'] == player.relic_id:
                player.country = m['country']
                return


def set_teams_from_json(player: Player, json):
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
    if len(players) <= 2:
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
    if len(players) <= 1:
        print('Not enough players.')
        return

    pre_made_teams = [[], []]
    for player in players:
        pre_made_teams[player.team].extend(
            t.id for t in player.pre_made_teams if t.id not in pre_made_teams[player.team])

    table = pretty_player_table()
    for team in range(2):
        pre_made_teams[team].sort()

        rank_sum = 0
        rank_level_sum = 0

        team_players = [p for p in players if p.team == team]
        for tpi, player in enumerate(team_players):
            row = [Theme.format_code('31' if is_team_axis(player) else '34') + player.faction.short + RESET_CODE]

            rank = player.rank
            rank_str = str(rank)
            if rank <= 0 < player.highest_rank:
                rank = player.highest_rank
                rank_str = '+' + str(player.highest_rank)
            row.append(rank_str)
            rank_sum += rank if rank > 0 else 1500  # TODO get avg rank in mode

            rank_level = player.rank_level
            rank_level_str = str(rank_level)
            if rank_level <= 0 < player.highest_rank_level:
                rank_level = player.highest_rank_level
                rank_level_str = '+' + str(player.highest_rank_level)
            row.append(rank_level_str)
            rank_level_sum += rank_level if rank_level > 0 else 6  # TODO get avg level in mode

            team_ranks = [str(t.rank) for t in player.pre_made_teams]
            team_rank_levels = [str(t.rank_level) for t in player.pre_made_teams]
            for ti, t in enumerate(player.pre_made_teams):
                if t.rank <= 0 < t.highest_rank:
                    team_ranks[ti] = '+' + str(t.highest_rank)
                if t.rank_level <= 0 < t.highest_rank_level:
                    team_rank_levels[ti] = '+' + str(t.highest_rank_level)

            row.append(
                ','.join(map(str, [chr(pre_made_teams[player.team].index(t.id) + 65) for t in player.pre_made_teams])))
            row.append(','.join(team_ranks))
            row.append(','.join(team_rank_levels))
            country = country_set[player.country]
            row.append(country['name'] if country else 'unknown')
            row.append(player.name)

            table.add_row(row, divider=True if tpi == len(team_players) - 1 else False)

        if len(players) > 2:
            team_size = len(players) / 2
            avg_rank = rank_sum / team_size
            avg_rank_level = rank_level_sum / team_size
            avg_row = [colorize(90, 'Avg'), avg_rank, avg_rank_level]
            table.add_row(avg_row + ([''] * (len(table.field_names) - len(avg_row))), divider=True)

    if not pre_made_teams[0] and not pre_made_teams[1]:
        for col in (col_team, col_team_rank, col_team_level):
            table.del_column(col)

    # Colorize fields last so column indices can still be used. If passing field names via `get_string(fields={})`
    # validation will fail.
    table.field_names = map(partial(colorize, 90), table.field_names)
    print(table.get_string())


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
    align = ['l', 'r', 'r', 'c', 'r', 'r', 'l', 'l']
    assert len(align) == len(table.field_names)
    for ai, a in enumerate(align):
        table.align[table.field_names[ai]] = a
    return table


def is_team_axis(player):
    return player.faction.id == 0 or player.faction.id == 2


def is_team_allies(player):
    return not is_team_axis(player)


def colorize(c, s):
    return Theme.format_code(str(c)) + s + RESET_CODE


async def watch_log_file():
    observer = Observer()
    observer.schedule(LogFileEventHandler(asyncio.get_running_loop()), str(logfile.parent))
    observer.start()
    # TODO maybe just hold it open
    try:
        while True:
            await asyncio.sleep(5)
            # Force CoH2 to write out its collected log
            with open(logfile):
                pass
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


class LogFileEventHandler(FileSystemEventHandler):

    def __init__(self, loop):
        self.loop = loop

    def on_modified(self, event: FileSystemEvent) -> None:
        if event.is_directory or event.src_path != str(logfile):
            return
        players = asyncio.run_coroutine_threadsafe(get_players(), self.loop).result()
        if players_changed:
            print_players(players)

    def on_deleted(self, event: FileSystemEvent) -> None:
        super().on_deleted(event)


async def main():
    players = await get_players()
    print_players(players)
    await watch_log_file()


if __name__ == '__main__':
    asyncio.run(main())

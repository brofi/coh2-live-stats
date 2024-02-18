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

import time
from pathlib import Path

import requests
from tabulate import tabulate
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer

# Either use relative imports and run the project as a module from IDE Run/Debug Config (same as python -module) or
# use these absolute imports and run it as a script, but then the package needs to be installed.
# See: Solution 1/3 in https://stackoverflow.com/a/28154841.
# Since the creation of a virtual environment this somehow works without the project being installed.
from coh2_live_stats.player import Player
from coh2_live_stats.team import Team

logfile = Path.home().joinpath('Documents', 'My Games', 'Company of Heroes 2', 'warnings.log')
request_url = "https://coh2-api.reliclink.com/community/leaderboard/GetPersonalStat?title=coh2&profile_ids=[{}]"
current_players = []
players_changed = False


def get_players():
    global current_players
    global players_changed
    players_changed = False
    players = get_players_from_log()
    if players and players != current_players:
        init_players_from_api(players)
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


def init_players_from_api(players):
    print('Getting player data fom CoH2 API...')
    for player in players:
        leaderboard_id = get_leaderboard_id((len(players) // 2) - 1, player)
        r = requests.get(request_url.format(player.relic_id))
        stats = r.json()['leaderboardStats']
        groups = r.json()['statGroups']
        for d in stats:
            if d['leaderboard_id'] == leaderboard_id:
                player.rank = d['rank']
                player.rank_level = d['ranklevel']
                player.highest_rank = d['highestrank']
                player.highest_rank_level = d['highestranklevel']
                break

        for g in groups:
            t = Team(g['id'])
            for m in g['members']:
                t.members.append(m['profile_id'])
            for d in stats:
                if d['statgroup_id'] == t.id and d['leaderboard_id'] == get_team_leaderboard_id(g['type'], player):
                    t.rank = d['rank']
                    t.rank_level = d['ranklevel']
                    t.highest_rank = d['highestrank']
                    t.highest_rank_level = d['highestranklevel']
            player.teams.append(t)

    # Derive player data
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


# game mode: 1v1: 0, 2v2: 1, 3v3: 2, 4v4: 3
def get_leaderboard_id(game_mode, player):
    if player.faction.id == 4:
        lid = 51 + game_mode
    else:
        # leaderboard_id 0..3 -> AI Games
        lid = 4 + (game_mode * 4) + player.faction.id
    return lid


def get_team_leaderboard_id(num_team_members, player):
    leaderboard_id = -1
    if num_team_members > 1:
        leaderboard_id = 20 + (num_team_members - 2) * 2
        if is_team_allies(player):
            leaderboard_id += 1
    return leaderboard_id


def is_team_axis(player):
    return player.faction.id == 0 or player.faction.id == 2


def is_team_allies(player):
    return not is_team_axis(player)


def print_players(players):
    if len(players) <= 1:
        print('Not enough players.')
        return

    team_size = len(players) / 2
    headers = ['Fac', 'Rank', 'Lvl', 'Team', 'T_Rank', 'T_Lvl', 'Name']

    # TODO if team 1 add row, if team 0 expand row
    for team in range(2):
        print()
        table = []
        rank_sum = 0
        rank_level_sum = 0

        pre_made_teams = []
        for player in (p for p in players if p.team == team):
            pre_made_teams.extend(t.id for t in player.pre_made_teams if t.id not in pre_made_teams)
        pre_made_teams.sort()

        for player in (p for p in players if p.team == team):
            row = [player.faction.short]

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
            for i, t in enumerate(player.pre_made_teams):
                if t.rank <= 0 < t.highest_rank:
                    team_ranks[i] = '+' + str(t.highest_rank)
                if t.rank_level <= 0 < t.highest_rank_level:
                    team_rank_levels[i] = '+' + str(t.highest_rank_level)

            row.append(','.join(map(str, [chr(pre_made_teams.index(t.id) + 65) for t in player.pre_made_teams])))
            row.append(','.join(team_ranks))
            row.append(','.join(team_rank_levels))
            row.append(player.name)

            table.append(row)

        avg_rank = rank_sum / team_size
        avg_rank_level = rank_level_sum / team_size
        table.append([] * len(headers))
        avg_row = ['Avg', avg_rank, avg_rank_level]
        table.append(avg_row + ([] * (len(headers) - len(avg_row))))

        print(tabulate(table,
                       headers=headers,
                       tablefmt='pretty',
                       colalign=('left', 'right', 'right', 'center', 'right', 'right', 'left')))


def watch_log_file():
    observer = Observer()
    observer.schedule(LogFileEventHandler(), str(logfile.parent))
    observer.start()
    try:
        while True:
            time.sleep(5)
            # Force CoH2 to write out its collected log
            with open(logfile):
                pass
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


class LogFileEventHandler(FileSystemEventHandler):
    def on_modified(self, event: FileSystemEvent) -> None:
        if event.is_directory or event.src_path != str(logfile):
            return
        players = get_players()
        if players_changed:
            print_players(players)

    def on_deleted(self, event: FileSystemEvent) -> None:
        super().on_deleted(event)


def run():
    print_players(get_players())
    watch_log_file()


if __name__ == '__main__':
    run()

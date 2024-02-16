import time
from pathlib import Path

from tabulate import tabulate

import requests
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer

from player import Player

logfile = Path.home().joinpath('Documents', 'My Games', 'Company of Heroes 2', 'warnings.log')
request_url = "https://coh2-api.reliclink.com/community/leaderboard/GetPersonalStat?title=coh2&profile_ids=[{}]"


def get_players():
    players = get_players_from_log()
    if players:
        init_players_from_api(players)
    return players


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
        leaderboard_id = get_leaderboard_id((len(players) / 2) - 1, player)
        r = requests.get(request_url.format(player.relic_id))
        for d in r.json()['leaderboardStats']:
            if d['leaderboard_id'] == leaderboard_id:
                player.rank = d['rank']
                player.rank_level = d['ranklevel']
                player.highest_rank = d['highestrank']
                player.highest_rank_level = d['highestranklevel']
                break

        for d in r.json()['statGroups']:
            t = list()
            for m in d['members']:
                t.append(m['profile_id'])
            player.teams.append(t)

    # Derive player data
    possible_teams = [[], []]
    for player in players:
        for team in player.teams:
            if len(team) > 1 and team not in possible_teams[player.team]:
                isvalid = True
                for member in team:
                    if member not in [p.relic_id for p in players if p.team == player.team]:
                        isvalid = False
                        break
                if isvalid:
                    possible_teams[player.team].append(team)

    # Only keep the biggest teams
    for tid, pt in enumerate(possible_teams):
        possible_teams[tid] = [t for t in pt if len(t) >= max(map(len, pt))]

    for player in players:
        for i, t in enumerate(possible_teams[player.team]):
            if player.relic_id in t:
                player.pre_made_team.append(i)


# game mode: 1v1: 0, 2v2: 1, 3v3: 2, 4v4: 3
def get_leaderboard_id(game_mode, player):
    if player.faction.id == 4:
        lid = 51 + game_mode
    else:
        # leaderboard_id 0..3 -> AI Games
        lid = 4 + (game_mode * 4) + player.faction.id
    return lid


def print_players(players):
    team_size = len(players) / 2
    headers = ['Fac', 'Rank', 'Level', 'Team', 'Name']

    # TODO if team 1 add row, if team 0 expand row
    for team in range(2):
        print()
        table = []
        rank_sum = 0
        rank_level_sum = 0

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

            row.append(','.join(map(str, player.pre_made_team)))
            row.append(player.name)

            table.append(row)

        avg_rank = rank_sum / team_size
        avg_rank_level = rank_level_sum / team_size
        table.append([] * len(headers))
        table.append(['Avg', avg_rank, avg_rank_level, '', ''])

        print(tabulate(table,
                       headers=headers,
                       tablefmt='pretty',
                       colalign=('left', 'right', 'right', 'center', 'left')))


def watch_log_file():
    observer = Observer()
    observer.schedule(LogFileEventHandler(), str(logfile.parent))
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


class LogFileEventHandler(FileSystemEventHandler):
    def on_modified(self, event: FileSystemEvent) -> None:
        if event.is_directory or event.src_path != str(logfile):
            return

        print_players(get_players())

    def on_deleted(self, event: FileSystemEvent) -> None:
        super().on_deleted(event)


if __name__ == '__main__':
    print_players(get_players())
    watch_log_file()

import time
from pathlib import Path

import time
from pathlib import Path

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

    # TODO team ranks
    # get id from statsGroup entry, query the leaderboardStats for given id
    # result is either 1 (allies or axis) or 2 (allies and axis) entries'
    # TODO test
    # case: player 1 has team (1,2), player 2 has team (2,3) and there is no team (1,2,3). So did (1,2) or (2,3) queue?
    # test with roy, aldo, schnugge
    for player in players:
        for i, t in enumerate(possible_teams[player.team]):
            if player.relic_id in t:
                player.pre_made_team = i


# game mode: 1v1: 0, 2v2: 1, 3v3: 2, 4v4: 3
def get_leaderboard_id(game_mode, player):
    if player.faction.id == 4:
        lid = 51 + game_mode
    else:
        # leaderboard_id 0..3 -> AI Games
        lid = 4 + (game_mode * 4) + player.faction.id
    return lid


def print_players(players):
    print()
    row = '| {} | {} | {} | {} | {} '
    sep = ('+ ' + '-' * 3 + ' + ' + '-' * 5 + ' + ' + '-' * 5 + ' + ' + '-' * 4 + ' + ' + '-' * 32 + ' ') * 2 + '+'
    team_size = len(players) / 2
    print(sep)
    print(row.format('Fac', 'Rank'.ljust(5), 'Level', 'Team', 'Name'.ljust(32)) * 2 + '|')
    print(sep)
    rank_sums = [0, 0]
    rank_level_sums = [0, 0]

    # Print player data
    for player in players:
        rank = player.rank
        rank_str = str(rank)
        if rank <= 0 < player.highest_rank:
            rank = player.highest_rank
            rank_str = '+' + str(player.highest_rank)
        rank_sums[player.team] += rank if rank > 0 else 1500  # TODO get avg rank in mode

        rank_level = player.rank_level
        rank_level_str = str(rank_level)
        if rank_level <= 0 < player.highest_rank_level:
            rank_level = player.highest_rank_level
            rank_level_str = '+' + str(player.highest_rank_level)
        rank_level_sums[player.team] += rank_level if rank_level > 0 else 6  # TODO get avg level in mode

        # TODO if only 1 player don't forget \n
        s = row.format(player.faction.short.ljust(3), rank_str.rjust(5), rank_level_str.rjust(5),
                       ('' if player.pre_made_team < 0 else str(player.pre_made_team)).rjust(4),
                       player.name.ljust(32))
        print(s, end='') if player.team == 0 else print(s + '|')

    print(sep)
    avg_row = 'Avg | {}{:>4.0f} | {}{:.1f} | '
    avg_rank_0 = rank_sums[0] / team_size
    avg_rank_level_0 = rank_level_sums[0] / team_size
    avg_rank_1 = rank_sums[1] / team_size
    avg_rank_level_1 = rank_level_sums[1] / team_size
    print('| ' +
          avg_row.format('*' if avg_rank_0 < avg_rank_1 else ' ', avg_rank_0,
                         '*' if avg_rank_level_0 > avg_rank_level_1 else ' ', avg_rank_level_0) +
          ' ' * 4 + ' | ' + (' ' * 32) + ' | ' +
          avg_row.format('*' if avg_rank_1 < avg_rank_0 else ' ', avg_rank_1,
                         '*' if avg_rank_level_1 > avg_rank_level_0 else ' ', avg_rank_level_1) +
          ' ' * 4 + ' | ' + (' ' * 32) + ' | ')
    print(sep)


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

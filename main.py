from pathlib import Path
from typing import NamedTuple

import requests


class Faction(NamedTuple):
    id: int
    name: str
    short: str


def faction_from_log(log):
    if log == 'german':
        return Faction(0, 'Wehrmacht', 'WM')
    elif log == 'soviet':
        return Faction(1, 'Soviet Union', 'SU')
    elif log == 'west_german':
        return Faction(2, 'Oberkommando West', 'OKW')
    elif log == 'aef':
        return Faction(3, 'US Forces', 'US')
    elif log == 'british':
        return Faction(4, 'British Forces', 'UK')
    else:
        return None


class Player(NamedTuple):
    id: int
    name: str
    relic_id: int
    team: int
    faction: Faction
    rank: int
    rank_level: int
    highest_rank: int
    highest_rank_level: int


logfile = Path.home().joinpath('Documents', 'My Games', 'Company of Heroes 2', 'warnings.log')
with open(logfile, encoding='utf-8') as f:
    lines = f.readlines()

player_lines = []
for line in lines:
    player_line = line.partition('GAME -- Human Player:')[2]
    if player_line:
        player_lines.append(player_line.strip())

# TODO watch file
if not player_lines:
    print('No player data found.')
    exit(0)

latest_match_player_count = int(player_lines[len(player_lines) - 1].split(' ')[0]) + 1
# 1v1: 0, 2v2: 1, 3v3: 2, 4v4: 3
game_mode = (latest_match_player_count / 2) - 1
# Keep only players of latest match
player_lines = player_lines[len(player_lines) - latest_match_player_count:]

players = []
request_url = "https://coh2-api.reliclink.com/community/leaderboard/GetPersonalStat?title=coh2&profile_ids=[{}]"

leaderboard_id = -1
for player_line in player_lines:
    # Get player data from log file
    s = player_line.split(' ')
    faction = faction_from_log(s.pop())
    team = int(s.pop())
    relic_id = int(s.pop())
    player_id = int(s.pop(0))
    name = ' '.join(s)
    rank = -1
    rank_level = -1
    highest_rank = -1
    highest_rank_level = -1

    # Request player data from CoH2 API
    if faction.id == 4:
        leaderboard_id = 51 + game_mode
    else:
        # leaderboard_id 0..3 -> AI Games
        leaderboard_id = 4 + (game_mode * 4) + faction.id

    r = requests.get(request_url.format(relic_id))
    for d in r.json()['leaderboardStats']:
        if d['leaderboard_id'] == leaderboard_id:
            rank = d['rank']
            rank_level = d['ranklevel']
            highest_rank = d['highestrank']
            highest_rank_level = d['highestranklevel']
            break

    players.append(Player(player_id, name, relic_id, team, faction, rank, rank_level, highest_rank, highest_rank_level))

row = '| {} | {} | {} | {}'
sep = ('+ ' + '-' * 3 + ' + ' + '-' * 5 + ' + ' + '-' * 3 + ' + ' + '-' * 32) * 2 + ' +'
print(sep)
print(row.format('Fac', 'Rank'.ljust(5), 'Lvl', 'Name'.ljust(32)) * 2 + ' |')
print(sep)
for player in players:
    rank = str(player.rank)
    if player.rank <= 0 < player.highest_rank:
        rank = '+' + str(player.highest_rank)

    rank_level = str(player.rank_level)
    if player.rank_level <= 0 < player.highest_rank_level:
        rank_level = '+' + str(player.highest_rank_level)

    s = row.format(player.faction.short.ljust(3), rank.rjust(5), rank_level.rjust(3), player.name.ljust(32))
    print(s, end='') if player.team == 0 else print(s + ' |')
print(sep)

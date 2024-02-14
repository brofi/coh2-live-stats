from pathlib import Path
from typing import NamedTuple
import requests

# TODO get data from log


class Faction(NamedTuple):
    id: int
    name: str


def faction_from_log(log):
    if log == 'german':
        return Faction(0, 'Wehrmacht')
    elif log == 'soviet':
        return Faction(1, 'Soviet Union')
    elif log == 'west_german':
        return Faction(2, 'Oberkommando West')
    elif log == 'aef':
        return Faction(3, 'US Forces')
    elif log == 'british':
        return Faction(4, 'British Forces')
    else:
        return None


class Player(NamedTuple):
    id: int
    name: str
    relic_id: int
    team: int
    faction: Faction


logfile = Path.home().joinpath('Documents', 'My Games', 'Company of Heroes 2', 'warnings.log')
with open(logfile, encoding='utf-8') as f:
    lines = f.readlines()

player_lines = []
for line in lines:
    player_line = line.partition('GAME -- Human Player:')[2]
    if player_line:
        player_lines.append(player_line.strip())

last_match_player_count = int(player_lines[len(player_lines) - 1].split(' ')[0]) + 1
player_lines = player_lines[len(player_lines) - last_match_player_count:]

players = []
for player_line in player_lines:
    s = player_line.split(' ')
    faction = faction_from_log(s.pop())
    team = int(s.pop())
    relic_id = int(s.pop())
    player_id = int(s.pop(0))
    name = ' '.join(s)
    players.append(Player(player_id, name, relic_id, team, faction))

api = "https://coh2-api.reliclink.com/community/leaderboard/GetPersonalStat?title=coh2&profile_ids="

# TODO make single request for all players
# request_url = api + '['
# for player in players:
#     request_url += str(player.relic_id) + ','
# request_url += ']'
# print(request_url)

# 1v1: 0, 2v2: 1, 3v3: 2, 4v4: 3
game_mode = (last_match_player_count / 2) - 1

for player in players:
    leaderboard_id = -1
    if player.faction.id == 4:
        leaderboard_id = 51 + game_mode
    else:
        # leaderboard_id 0..3 -> AI Games
        leaderboard_id = 4 + (game_mode * 4) + player.faction.id

    r_url = api + '[' + str(player.relic_id) + ']'
    r = requests.get(r_url)

    for d in r.json()['leaderboardStats']:
        if d['leaderboard_id'] == leaderboard_id:
            print('#' + str(d['rank']) + ' (' + str(d['ranklevel']) + ') ' + player.name)
            break

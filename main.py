from pathlib import Path
from typing import NamedTuple


# TODO get data from log

class Player(NamedTuple):
    id: int
    name: str
    relic_id: int
    team: int
    faction: str


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
    faction = s.pop()
    team = int(s.pop())
    relic_id = int(s.pop())
    player_id = int(s.pop(0))
    name = ' '.join(s)
    players.append(Player(player_id, name, relic_id, team, faction))

print(players)

api = "https://coh2-api.reliclink.com/community/leaderboard/GetPersonalStat?title=coh2&profile_ids=[profile_ids]"
# TODO make request

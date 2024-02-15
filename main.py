from pathlib import Path

import requests

from player import Player

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
# Keep only player lines of latest match
player_lines = player_lines[len(player_lines) - latest_match_player_count:]

# Initialize players from log
players = [Player.from_log(player_line) for player_line in player_lines]

request_url = "https://coh2-api.reliclink.com/community/leaderboard/GetPersonalStat?title=coh2&profile_ids=[{}]"
# 1v1: 0, 2v2: 1, 3v3: 2, 4v4: 3
game_mode = (latest_match_player_count / 2) - 1
leaderboard_id = -1

# Gather player data from CoH2 API
for player in players:
    if player.faction.id == 4:
        leaderboard_id = 51 + game_mode
    else:
        # leaderboard_id 0..3 -> AI Games
        leaderboard_id = 4 + (game_mode * 4) + player.faction.id

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

row = '| {} | {} | {} | {} | {} '
sep = ('+ ' + '-' * 3 + ' + ' + '-' * 5 + ' + ' + '-' * 5 + ' + ' + '-' * 4 + ' + ' + '-' * 32 + ' ') * 2 + '+'
team_size = latest_match_player_count / 2
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

    # TODO team ranks
    # get id from statsGroup entry, query the leaderboardStats for given id
    # result is either 1 (allies or axis) or 2 (allies and axis) entries'
    # TODO test
    # case: player 1 has team (1,2), player 2 has team (2,3) and there is no team (1,2,3). So did (1,2) or (2,3) queue?
    # test with roy, aldo, schnugge
    team = -1
    for i, t in enumerate(possible_teams[player.team]):
        if player.relic_id in t:
            team = i

    s = row.format(player.faction.short.ljust(3), rank_str.rjust(5), rank_level_str.rjust(5),
                   ('' if team < 0 else str(team)).rjust(4), player.name.ljust(32))
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

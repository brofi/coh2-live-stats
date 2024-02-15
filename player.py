from dataclasses import dataclass, field

from faction import Faction


@dataclass
class Player:
    # Log data
    id: int
    name: str
    relic_id: int
    team: int
    faction: Faction

    # CoH2 API data
    rank: int = -1
    rank_level: int = -1
    highest_rank: int = -1
    highest_rank_level: int = -1
    teams: list[list[int]] = field(default_factory=list)

    # Derived data

    # There could be multiple possible pre-made teams. For example when players A, B
    # and C with teams (A,B), (B,C) have no team (A,B,C). Which means either player
    # A or C queued alone or the current match is the first match of a new team
    # (A,B,C).
    pre_made_team: list[int] = field(default_factory=list)

    @staticmethod
    def from_log(player_line):
        s = player_line.split(' ')
        faction = Faction.from_log(s.pop())
        team = int(s.pop())
        relic_id = int(s.pop())
        player_id = int(s.pop(0))
        name = ' '.join(s)
        return Player(player_id, name, relic_id, team, faction)

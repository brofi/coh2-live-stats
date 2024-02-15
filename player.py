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
    pre_made_team: int = -1

    @staticmethod
    def from_log(player_line):
        s = player_line.split(' ')
        faction = Faction.from_log(s.pop())
        team = int(s.pop())
        relic_id = int(s.pop())
        player_id = int(s.pop(0))
        name = ' '.join(s)
        return Player(player_id, name, relic_id, team, faction)

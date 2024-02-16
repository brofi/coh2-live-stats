from dataclasses import dataclass, field


@dataclass
class Team:
    id: int = -1
    members: list[int] = field(default_factory=list)
    rank: int = -1
    rank_level: int = -1
    highest_rank: int = -1
    highest_rank_level: int = -1

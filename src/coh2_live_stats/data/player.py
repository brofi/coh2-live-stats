#  Copyright (C) 2024 Andreas Becker.
#
#  This file is part of CoH2LiveStats.
#
#  CoH2LiveStats is free software: you can redistribute it and/or modify it under the
#  terms of the GNU General Public License as published by the Free Software
#  Foundation, either version 3 of the License, or (at your option) any later version.
#
#  CoH2LiveStats is distributed in the hope that it will be useful, but WITHOUT ANY
#  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
#  PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with
#  CoH2LiveStats. If not, see <https://www.gnu.org/licenses/>.

"""Player module."""

from dataclasses import dataclass, field
from typing import override

from coh2_live_stats.util import ratio

from .faction import Faction, TeamFaction
from .team import Team


@dataclass(eq=False)
class Player:
    """A CoH2 player.

    Player data either stems from the CoH2 log file or the API.
    The following properties are specific to a match mode for the player's faction :
    ``wins``, ``losses``, ``drops``, ``rank``, ``rank_total``, ``rank_level``,
    ``highest_rank``, ``highest_rank_level``, ``relative_rank``, ``num_games``,
    ``win_ratio``, ``drop_ratio``.
    """

    # Log data
    id: int
    name: str
    relic_id: int
    team_id: int
    faction: Faction

    # CoH2 API data
    # Player data
    steam_profile: str = ''
    prestige: int = -1
    country: str = ''
    # Player stats
    wins: int = 0
    losses: int = 0
    streak: int = 0
    drops: int = 0
    rank: int = -1
    rank_total: int = -1
    rank_level: int = -1
    highest_rank: int = -1
    highest_rank_level: int = -1
    # Pre-made teams
    teams: list[Team] = field(default_factory=list)

    @property
    def team_faction(self) -> TeamFaction:
        """The ``TeamFaction`` this player belongs to."""
        # Log file team ID can't be used to determine the team faction (always 0 for
        # user's team)
        return TeamFaction.from_faction(self.faction)

    @property
    def is_ranked(self) -> bool:
        """Whether this player currently has a rank."""
        return self.rank > 0 and self.rank_level > 0

    @property
    def has_highest_rank(self) -> bool:
        """Whether this player has a past highest rank."""
        return self.highest_rank > 0 and self.highest_rank_level > 0

    @property
    def relative_rank(self) -> float:
        """Player's rank relative to the total number of ranked players."""
        return self.rank / self.rank_total if self.is_ranked else 0.0

    @property
    def num_games(self) -> int:
        """Player's total number of played games."""
        return self.wins + self.losses

    @property
    def win_ratio(self) -> float | None:
        """Player's wins relative to the number of played games."""
        return ratio(self.wins, self.num_games)

    @property
    def drop_ratio(self) -> float | None:
        """Player's drops relative to the number of played games."""
        return ratio(self.drops, self.num_games)

    def get_steam_profile_url(self) -> str:
        """Player's steam profile URL."""
        return 'https://steamcommunity.com' + self.steam_profile.replace(
            'steam', 'profiles'
        )

    def get_prestige_level_stars(self, star: str = '*', half_star: str = '~') -> str:
        """Player's prestige level measured in stars."""
        return star * int(self.prestige / 100) + half_star * round(
            (self.prestige / 100) % 1
        )

    def estimate_rank(self, avg_relative_rank: float = 0) -> tuple[str, int, int]:
        """Player's estimate rank.

        The player's estimate rank is either their current rank, their past highest
        rank (+), their team's average rank (?) or the middle of the leaderboard (?).
        :param avg_relative_rank: team average rank
        :return: estimated rank
        """
        if self.is_ranked or self.relic_id <= 0:
            return '', self.rank, self.rank_level
        if self.highest_rank > 0 and self.highest_rank_level > 0:
            return '+', self.highest_rank, self.highest_rank_level
        if avg_relative_rank > 0:
            avg_rank = round(avg_relative_rank * self.rank_total)
            return '?', avg_rank, self.rank_level_from_rank(avg_rank, self.rank_total)
        avg_rank = round(self.rank_total / 2)
        return '?', avg_rank, self.rank_level_from_rank(avg_rank, self.rank_total)

    @staticmethod
    def rank_level_from_rank(rank: int, rank_total: int) -> int:
        """Calculate the corresponding level for the given rank."""
        if rank <= 0 or rank_total <= 0:
            return -1

        lvl = 0
        if 0 < rank <= 2:  # noqa: PLR2004
            lvl = 20
        elif 2 < rank <= 13:  # noqa: PLR2004
            lvl = 19
        elif 13 < rank <= 36:  # noqa: PLR2004
            lvl = 18
        elif 36 < rank <= 80:  # noqa: PLR2004
            lvl = 17
        elif 80 < rank <= 200:  # noqa: PLR2004
            lvl = 16
        else:  # build and search the rest of the ranking
            ratio_lvl_1_14 = [6, 8, 6, 5] + 3 * [10] + 2 * [7] + [6] + 4 * [5]
            n_top_200 = min(200, rank_total)
            remain = rank_total - n_top_200
            ranking = []
            for r in ratio_lvl_1_14:
                n = min(round(rank_total * (r / 100)), max(0, remain))
                ranking.append(remain + n_top_200)
                remain -= n
            while lvl < len(ranking) and rank <= ranking[lvl]:
                lvl += 1
        return lvl

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Player):
            return NotImplemented
        return self.relic_id == other.relic_id

    @override
    def __hash__(self) -> int:
        return hash(self.relic_id)

from dataclasses import dataclass


@dataclass
class Faction:
    id: int
    name: str
    short: str

    @staticmethod
    def from_log(faction_name):
        if faction_name == 'german':
            return Faction(0, 'Wehrmacht', 'WM')
        elif faction_name == 'soviet':
            return Faction(1, 'Soviet Union', 'SU')
        elif faction_name == 'west_german':
            return Faction(2, 'Oberkommando West', 'OKW')
        elif faction_name == 'aef':
            return Faction(3, 'US Forces', 'US')
        elif faction_name == 'british':
            return Faction(4, 'British Forces', 'UK')
        else:
            return None

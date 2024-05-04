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

"""Logfile mocking used in GitHub Actions."""

import os
from pathlib import Path


def run() -> None:
    """Create an empty CoH2 logfile at the correct location depending on OS."""
    logfile = Path().home()
    if os.name == 'nt':
        logfile = logfile.joinpath('Documents', 'My Games', 'Company of Heroes 2')
    else:
        logfile = logfile.joinpath(
            '.local', 'share', 'feral-interactive', 'CompanyOfHeroes2', 'AppData'
        )
    logfile.mkdir(parents=True, exist_ok=True)
    logfile /= 'warnings.log'
    logfile.touch()


if __name__ == '__main__':
    run()

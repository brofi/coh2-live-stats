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

"""Virtual environment activation used in GitHub Actions."""

import os
from pathlib import Path


def run() -> None:
    """Set up env variables for a python venv in the GitHub environment files."""
    virtual_env = Path('.venv').resolve()
    path = virtual_env.joinpath('Scripts' if os.name == 'nt' else 'bin').resolve()
    with Path(os.environ['GITHUB_PATH']).open('a+') as f:
        f.write(f'\n{path}' if f.read() else str(path))
    with Path(os.environ['GITHUB_ENV']).open('a+') as f:
        v = f'VIRTUAL_ENV={virtual_env}'
        f.write(f'\n{v}' if f.read() else str(v))


if __name__ == '__main__':
    run()
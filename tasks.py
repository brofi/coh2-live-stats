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

import json
import sys
from glob import glob
from pathlib import Path
from shutil import rmtree

from invoke import Collection, Context, Result, task

type Package = dict[str, str]

_pkg = 'coh2_live_stats'
_pycmd = [sys.executable, '-m']
_pipcmd = _pycmd + ['pip', '--isolated', '--require-virtualenv']

_build_dir = Path(__file__).with_name('build')
_dist_dir = Path(__file__).with_name('dist')


def _run(c: Context, *args, **kwargs) -> Result | None:
    return c.run(' '.join(args), **kwargs)


def _success(res: Result) -> bool:
    return res is not None and res.return_code == 0


@task
def _activate(c: Context) -> bool:
    return _success(c.run('.\\venv\\Scripts\\activate.bat'))


def _is_editable(p: Package) -> bool:
    return p.get('editable_project_location') is not None


@task(pre=[_activate], help={'name': 'Name of the package to get.'})
def _get_pkg(c: Context, name='') -> Package | None:
    """Returns given package from pip or all if none is given."""

    res: Result = _run(c, *_pipcmd, 'list', '--format json')
    packages = list(filter(lambda p: p['name'] == name, json.loads(res.stdout)))
    assert len(packages) <= 1
    return packages[0] if packages else None


@task(pre=[_activate])
def _install(c: Context) -> bool:
    wheels = glob(f'{_pkg}-*.whl', root_dir=_dist_dir)
    wheels.sort(reverse=True)
    if wheels:
        return _success(
            _run(c, *_pipcmd, 'install', str(_dist_dir.joinpath(wheels[0])))
        )
    return False


@task(_activate)
def _install_editable(c: Context, force=False, dev=False) -> bool:
    cmd = [*_pipcmd, 'install']
    if force:
        cmd += ['--force-reinstall']
    cmd += ['-e .[build,dev]'] if dev else ['-e .']
    return _success(_run(c, *cmd))


def _clean() -> bool:
    if _build_dir.is_dir():
        rmtree(_build_dir)
    if _dist_dir.is_dir():
        rmtree(_dist_dir)
    return True


@task(
    pre=[_activate],
    help={
        'clean': 'Remove build and distribution directories',
        'pyinstaller_only': 'Skip setuptools build.',
    },
)
def build(c: Context, clean=False, pyinstaller_only=False) -> None:
    """Build wheel and source distribution."""

    # Don't fail install on first time setup
    from scripts import pyinstaller_setup, settings_generator

    if clean:
        _clean()

    settings_generator.default()
    if not pyinstaller_only:
        _run(c, *_pycmd, 'build', hide=False)
    pyinstaller_setup.bundle()


@task(
    _activate,
    help={
        'normal_mode': "Don't install in editable mode.",
        'dev': 'Install additional build and development dependencies (editable only).',
    },
)
def install(c: Context, normal_mode=False, dev=False) -> bool:
    """Install project in editable (default) or non-editable mode."""

    if normal_mode:
        print(f'Installing {_pkg} in non-editable mode...')
        return _install(c)

    pkg = _get_pkg(c, _pkg)
    if pkg is None:
        print(f'Installing {_pkg} in editable mode...')
        return _install_editable(c, False, dev)
    if not _is_editable(pkg):
        print(f'Reinstalling {_pkg} in editable mode...')
        return _install_editable(c, True, dev)
    print(f'{_pkg} is up to date.')
    return True


namespace = Collection(build, install)

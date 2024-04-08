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
import logging
import sys
from pathlib import Path
from shutil import rmtree

from coh2_live_stats.logging_conf import LoggingConf
from invoke import Collection, Context, Result, task

type Package = dict[str, str]

_pkg = 'coh2_live_stats'
_pycmd = [sys.executable, '-m']
_pipcmd = _pycmd + ['pip', '--isolated', '--require-virtualenv']

_build_dir = Path(__file__).with_name('build')
_dist_dir = Path(__file__).with_name('dist')

_logging = LoggingConf(Path('build.log'), stdout=True)
LOG = logging.getLogger('coh2_live_stats_build')
LOG.setLevel(logging.INFO)
_logging.start()


@task
def stop_logging(_):
    _logging.stop()


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
    wheels = list(_dist_dir.glob(f'{_pkg}-*.whl'))
    if wheels:
        wheels.sort(reverse=True)
        return _success(
            _run(c, *_pipcmd, 'install', str(_dist_dir.joinpath(wheels[0])))
        )
    return False


@task(_activate)
def _install_editable(c: Context, *, force=False, dev=False) -> bool:
    cmd = [*_pipcmd, 'install']
    if force:
        cmd += ['--force-reinstall']
    cmd += ['-e .[build,dev]'] if dev else ['-e .']
    return _success(_run(c, *cmd))


def _clean() -> bool:
    def err(_, path, __):
        LOG.error('Failed to remove %s', path)

    for d in _build_dir, _dist_dir:
        if d.is_dir():
            rmtree(d, onexc=err)
    return True


@task(
    pre=[_activate],
    post=[stop_logging],
    help={
        'clean': 'Remove build and distribution directories',
        'pyinstaller_only': 'Skip setuptools build.',
    },
)
def build(c: Context, *, clean=False, pyinstaller_only=False) -> None:
    """Build wheel and source distribution."""

    # Don't fail install on first time setup
    from scripts import pyinstaller_setup, settings_generator

    if clean:
        _clean()
        return

    settings_generator.default()
    if not pyinstaller_only:
        _run(c, *_pycmd, 'build', hide=False)
    pyinstaller_setup.bundle()


@task(
    pre=[_activate],
    post=[stop_logging],
    help={
        'normal_mode': "Don't install in editable mode.",
        'dev': 'Install additional build and development dependencies (editable only).',
    },
)
def install(c: Context, *, normal_mode=False, dev=False) -> bool:
    """Install project in editable (default) or non-editable mode."""

    if normal_mode:
        LOG.info('Installing %s in non-editable mode...', _pkg)
        return _install(c)

    pkg = _get_pkg(c, _pkg)
    if pkg is None:
        LOG.info('Installing %s in editable mode...', _pkg)
        return _install_editable(c, force=False, dev=dev)
    if not _is_editable(pkg):
        LOG.info('Reinstalling %s in editable mode...', _pkg)
        return _install_editable(c, force=True, dev=dev)
    LOG.info('%s is up to date.', _pkg)
    return True


namespace = Collection(build, install)

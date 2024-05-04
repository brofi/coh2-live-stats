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

"""A build script based on PyInvoke."""

import json
import logging
import os
import sys
from collections.abc import Callable
from pathlib import Path
from shutil import rmtree
from typing import Any, Final

from invoke import Collection, Context, Result, task

# Conditional imports and mypy - see: https://github.com/python/mypy/issues/1297

try:
    # noinspection PyUnresolvedReferences
    from coh2_live_stats.logging_conf import LoggingConf as _LoggingConf
except ImportError:
    LoggingConf = None
else:
    LoggingConf = _LoggingConf

try:
    # noinspection PyUnresolvedReferences
    from coh2_live_stats.version import version_tuple as _version_tuple
except ImportError:
    version_tuple = None
else:
    version_tuple = _version_tuple

try:
    # noinspection PyUnresolvedReferences
    from scripts import settings_generator as _settings_generator
except ImportError:
    settings_generator = None
else:
    settings_generator = _settings_generator

try:
    # noinspection PyUnresolvedReferences
    from scripts import pyinstaller_setup as _pyinstaller_setup
except ImportError:
    pyinstaller_setup = None
else:
    pyinstaller_setup = _pyinstaller_setup


Package = dict[str, str]

_VERSION_LEN: Final[int] = 3

_pkg = 'coh2_live_stats'
_pycmd = [sys.executable, '-m']
_pipcmd = [*_pycmd, 'pip', '--isolated', '--require-virtualenv']
_ruff_cmd = [*_pycmd, 'ruff', 'check', '.']
_mypy_cmd = [*_pycmd, 'mypy', 'src', 'tests', 'scripts', 'tasks.py']
_pytest_cmd = [*_pycmd, 'pytest', '--verbose', '--no-header', '--no-summary', '--tb=no']

_gen_dirs = [Path(__file__).with_name(n) for n in ('dist', 'dist_bundle', 'build')]
_dist_dir = _gen_dirs[0]

_logging = None
if LoggingConf is not None:
    _logging = LoggingConf(Path('build.log'), stdout=True)
    _logging.start()

LOG = logging.getLogger('coh2_live_stats_build')
LOG.setLevel(logging.INFO)

logging.getLogger('PyInstaller').setLevel(logging.INFO)
logging.getLogger('PyInstaller.__main__').setLevel(logging.INFO)


@task
def _stop_logging(_: Context) -> None:
    if _logging is not None:
        _logging.stop()


def _run(c: Context, *args: str, **kwargs: Any) -> Result | None:  # noqa: ANN401
    return c.run(' '.join(args), **kwargs)


@task
def _run_check(c: Context, *cmd: str) -> bool:
    res = _run(c, *cmd, echo=True, hide=False, warn=True)
    if res is None:
        msg = f'Failed to run check: {' '.join(cmd)!r}'
        raise RuntimeError(msg)
    return res.return_code == 0


def _success(res: Result | None) -> bool:
    return res is not None and res.return_code == 0


@task
def _activate(c: Context) -> bool:
    venv = Path(__file__).with_name('venv')
    cmd = (
        str(venv.joinpath('Scripts', 'activate.bat'))
        if os.name == 'nt'
        else f'. {venv.joinpath('bin', 'activate')}'
    )
    return _success(c.run(cmd))


def _is_editable(p: Package) -> bool:
    return p.get('editable_project_location') is not None


@task(pre=[_activate], help={'name': 'Name of the package to get.'})
def _get_pkg(c: Context, name: str) -> Package | None:
    """Return the given package from pip."""
    res = _run(c, *_pipcmd, 'list', '--format json')
    packages: list[Package] = []
    if res is not None:
        packages = list(filter(lambda p: p['name'] == name, json.loads(res.stdout)))
        if len(packages) > 1:
            msg = f'Multiple packages {name!r} detected.'
            raise ValueError(msg)
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
def _install_editable(c: Context, *, force: bool = False, dev: bool = False) -> bool:
    cmd = [*_pipcmd, 'install']
    if force:
        cmd += ['--force-reinstall']
    cmd += ['-e .[build,dev]'] if dev else ['-e .']
    return _success(_run(c, *cmd, hide=False))


def _clean() -> bool:
    def err(_: Callable[[str], Any], path: str, __: Exception) -> None:
        LOG.error('Failed to remove %s', path)

    for d in _gen_dirs:
        if d.is_dir():
            rmtree(d, onexc=err)
    return True


@task(pre=[_activate], post=[_stop_logging])
def check(c: Context) -> bool:
    """Run checks (ruff, mypy, pytest)."""
    if not _run_check(c, *_ruff_cmd):
        LOG.error('Ruff found errors.')
        return False
    if not _run_check(c, *_mypy_cmd):
        LOG.error('Mypy found errors.')
        return False
    if not _run_check(c, *_pytest_cmd):
        LOG.error('Running tests failed. Run pytest for more info.')
        return False
    return True


@task(
    pre=[_activate],
    post=[_stop_logging],
    help={'clean': 'Remove build and distribution directories'},
)
def build(c: Context, *, clean: bool = False) -> None:
    """Build wheel and source distribution."""
    if clean:
        _clean()
        return

    if not check(c):
        return

    if settings_generator is not None:
        settings_generator.write_default()

    _run(c, *_pycmd, 'build', hide=False)

    if pyinstaller_setup is not None:
        pyinstaller_setup.bundle()


@task(
    pre=[_activate],
    post=[_stop_logging],
    help={
        'normal_mode': "Don't install in editable mode.",
        'dev': 'Install additional build and development dependencies (editable only).',
    },
)
def install(c: Context, *, normal_mode: bool = False, dev: bool = False) -> bool:
    """Install project in editable (default) or non-editable mode."""
    installed = True
    if normal_mode:
        LOG.info('Installing %s in non-editable mode...', _pkg)
        installed = _install(c)
    else:
        pkg = _get_pkg(c, _pkg)
        if pkg is None:
            LOG.info('Installing %s in editable mode...', _pkg)
            installed = _install_editable(c, force=False, dev=dev)
        elif not _is_editable(pkg):
            LOG.info('Reinstalling %s in editable mode...', _pkg)
            installed = _install_editable(c, force=True, dev=dev)
        else:
            LOG.info('%s is up to date.', _pkg)
    return installed


@task
def publish(c: Context) -> None:
    """Upload package to PyPI."""
    if version_tuple is None:
        LOG.error('Package coh2_live_stats not installed.')
        return
    if len(version_tuple) != _VERSION_LEN or not all(
        isinstance(x, int) for x in version_tuple[:_VERSION_LEN]
    ):
        LOG.error("Don't publish development versions.")
        return

    base = f'coh2_live_stats-{'.'.join(map(str, version_tuple))}'
    dist_files = [
        str(Path(_dist_dir).joinpath(f'{base}.tar.gz')),
        str(next(Path(_dist_dir).glob(f'{base}*.whl'))),
    ]

    if not _success(_run(c, *_pycmd, 'twine', 'check', *dist_files)):
        LOG.error('Twine failed to check distribution files.')
        return

    _run(c, *_pycmd, 'twine', 'upload', *dist_files, hide=False)


namespace = Collection(check, build, install, publish)

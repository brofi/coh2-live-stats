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

"""Script for bundling *coh2_live_stats* using *PyInstaller*."""

import shutil
import sys
from pathlib import Path

import PyInstaller.__main__
from coh2_live_stats.logging_conf import LoggingConf
from coh2_live_stats.settings import CONFIG_FILE_DEV

if sys.platform == 'win32':
    # noinspection PyUnresolvedReferences
    from PyInstaller.utils.win32.versioninfo import (  # type: ignore[attr-defined]
        FixedFileInfo,
        StringFileInfo,
        StringStruct,
        StringTable,
        VarFileInfo,
        VarStruct,
        VSVersionInfo,
    )

app_name = 'CoH2LiveStats'
license_file_name = 'COPYING'
exec_name = f'{app_name}.exe'
contents_dir_name = 'lib'
content_root = Path(__file__).parents[1]
dist_path = content_root.joinpath('dist_bundle')
build_path = content_root.joinpath('build')
module_path = content_root.joinpath('src', 'coh2_live_stats')
res_path = module_path.joinpath('res')
version_file = build_path.joinpath('file_version_info.txt')


def bundle() -> None:
    """Create a one-folder bundle of *coh2_live_stats* using *PyInstaller*."""
    from coh2_live_stats.version import version, version_tuple  # noqa: PLC0415

    cmd: list[str] = []
    build_path.mkdir(exist_ok=True)

    if sys.platform == 'win32':
        ffi_version = (
            *tuple(x if isinstance(x, int) else 0 for x in version_tuple[:3]),
            0,
        )
        # see: https://learn.microsoft.com/en-us/windows/win32/menurc/vs-versioninfo
        version_info = VSVersionInfo(
            # see:
            # https://learn.microsoft.com/en-us/windows/win32/api/VerRsrc/ns-verrsrc-vs_fixedfileinfo
            ffi=FixedFileInfo(filevers=ffi_version, prodvers=ffi_version, date=(0, 0)),
            kids=[
                # see:
                # https://learn.microsoft.com/en-us/windows/win32/menurc/stringfileinfo
                StringFileInfo(
                    [
                        # see (szKey, Children):
                        # https://learn.microsoft.com/en-us/windows/win32/menurc/stringtable
                        StringTable(
                            '040904b0',  # Change with Translation (1200_10 = 04b0_16)
                            # see (szKey, Value):
                            # https://learn.microsoft.com/en-us/windows/win32/menurc/string-str
                            [
                                StringStruct('CompanyName', ''),
                                StringStruct('FileDescription', app_name),
                                StringStruct('FileVersion', version),
                                StringStruct('InternalName', exec_name),
                                StringStruct(
                                    'LegalCopyright',
                                    'Copyright (C) 2024 Andreas Becker.',
                                ),
                                StringStruct('OriginalFilename', exec_name),
                                StringStruct('ProductName', app_name),
                                StringStruct('ProductVersion', version),
                            ],
                        )
                    ]
                ),
                # see:
                # https://learn.microsoft.com/en-us/windows/win32/menurc/varfileinfo-block
                VarFileInfo([VarStruct('Translation', [0x0409, 1200])]),
            ],
        )
        version_file.write_text(str(version_info))
        cmd.extend(['--version-file', str(version_file)])

    cmd.extend(
        [
            '--distpath',
            str(dist_path),
            '--workpath',
            str(build_path),
            '--noconfirm',
            '--specpath',
            str(build_path),
            '--name',
            app_name,
            '--contents-directory',
            contents_dir_name,
            '--add-data',
            f'{content_root.joinpath(license_file_name)}:.',
            '--add-data',
            f'{CONFIG_FILE_DEV}:.',
            '--add-data',
            f'{LoggingConf.CONF_PATH}:.',
            '--add-data',
            f'{res_path.joinpath('horn.wav')}:./res',
            '--add-data',
            f'{res_path.joinpath('horn_subtle.wav')}:./res',
            '--add-data',
            f'{res_path.joinpath('horn_epic.wav')}:./res',
            '--icon',
            str(res_path.joinpath('coh2_live_stats.ico')),
            str(module_path.joinpath('__main__.py')),
        ]
    )
    PyInstaller.__main__.run(cmd)

    # Move license and config next to executable
    app_path = dist_path.joinpath(app_name)
    app_path.joinpath(contents_dir_name, license_file_name).replace(
        app_path.joinpath(license_file_name + '.txt')
    )
    app_path.joinpath(contents_dir_name, CONFIG_FILE_DEV.name).replace(
        app_path.joinpath(CONFIG_FILE_DEV.name)
    )

    # Create distribution archive
    shutil.make_archive(
        str(dist_path.joinpath(f'{app_name}-bundle-{version}')),
        'zip',
        dist_path,
        app_name,
    )


if __name__ == '__main__':
    bundle()

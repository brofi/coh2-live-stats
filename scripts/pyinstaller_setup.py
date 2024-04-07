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

import os
import shutil
from contextlib import suppress
from pathlib import Path

import PyInstaller.__main__
from coh2_live_stats import __version__, __version_tuple__
from coh2_live_stats.logging_conf import LoggingConf
from coh2_live_stats.settings import CONFIG_FILE_DEV

# noinspection PyUnresolvedReferences
from PyInstaller.utils.win32.versioninfo import (
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
dist_path = content_root.joinpath('dist')
build_path = content_root.joinpath('build')
module_path = content_root.joinpath('src', 'coh2_live_stats')
res_path = module_path.joinpath('res')
version_file = build_path.joinpath('file_version_info.txt')

ffi_version = (
    *__version_tuple__[:2],
    __version_tuple__[2] if isinstance(__version_tuple__[2], int) else 0,
    0,
)
# see: https://learn.microsoft.com/en-us/windows/win32/menurc/vs-versioninfo
version_info = VSVersionInfo(
    # see:
    # https://learn.microsoft.com/en-us/windows/win32/api/VerRsrc/ns-verrsrc-vs_fixedfileinfo
    ffi=FixedFileInfo(filevers=ffi_version, prodvers=ffi_version, date=(0, 0)),
    kids=[
        # see: https://learn.microsoft.com/en-us/windows/win32/menurc/stringfileinfo
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
                        StringStruct('FileVersion', __version__),
                        StringStruct('InternalName', exec_name),
                        StringStruct(
                            'LegalCopyright', 'Copyright (C) 2024 Andreas Becker.'
                        ),
                        StringStruct('OriginalFilename', exec_name),
                        StringStruct('ProductName', app_name),
                        StringStruct('ProductVersion', __version__),
                    ],
                )
            ]
        ),
        # see: https://learn.microsoft.com/en-us/windows/win32/menurc/varfileinfo-block
        VarFileInfo([VarStruct('Translation', [0x0409, 1200])]),
    ],
)


def bundle():
    with suppress(FileExistsError):
        os.mkdir(build_path)

    with open(version_file, 'w') as f:
        f.write(str(version_info))

    PyInstaller.__main__.run(
        [
            '--distpath',
            str(dist_path),
            '--workpath',
            str(build_path),
            '--noconfirm',
            '--specpath',
            str(content_root),
            '--name',
            app_name,
            '--contents-directory',
            contents_dir_name,
            '--add-data',
            f'{license_file_name}:.',
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
            '--version-file',
            str(version_file),
            str(module_path.joinpath('__main__.py')),
        ]
    )

    # Move license and config next to executable
    app_path = dist_path.joinpath(app_name)
    os.replace(
        app_path.joinpath(contents_dir_name, license_file_name),
        app_path.joinpath(license_file_name + '.txt'),
    )
    os.replace(
        app_path.joinpath(contents_dir_name, CONFIG_FILE_DEV.name),
        app_path.joinpath(CONFIG_FILE_DEV.name),
    )

    # Create distribution archive
    shutil.make_archive(str(app_path), 'zip', dist_path, app_name)


if __name__ == '__main__':
    bundle()

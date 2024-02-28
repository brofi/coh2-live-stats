#  Copyright (C) 2024 Andreas Becker.
#
#  This file is part of CoH2LiveStats.
#
#  CoH2LiveStats is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any
#  later version.
#
#  Foobar is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
#  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with Foobar. If not,
#  see <https://www.gnu.org/licenses/>.

import os
import shutil
from pathlib import Path

import PyInstaller.__main__
# noinspection PyUnresolvedReferences
from PyInstaller.utils.win32.versioninfo import StringFileInfo, StringTable, StringStruct, VarFileInfo, VarStruct
from PyInstaller.utils.win32.versioninfo import VSVersionInfo, FixedFileInfo

from coh2_live_stats.version import __version__, __version_info__

license_file_name = 'COPYING'
app_name = 'CoH2LiveStats'
exec_name = f'{app_name}.exe'
contents_dir_name = 'lib'
content_root = Path(__file__).parents[1]
dist_path = content_root.joinpath('dist')
build_path = content_root.joinpath('build')
module_path = content_root.joinpath('src', 'coh2_live_stats')
res_path = module_path.joinpath('res')
version_file = build_path.joinpath('file_version_info.txt')

# see: https://learn.microsoft.com/en-us/windows/win32/menurc/vs-versioninfo
version_info = VSVersionInfo(
    # see: https://learn.microsoft.com/en-us/windows/win32/api/VerRsrc/ns-verrsrc-vs_fixedfileinfo
    ffi=FixedFileInfo(
        filevers=__version_info__ + (0,),
        prodvers=__version_info__ + (0,),
        date=(0, 0)
    ),
    kids=[
        # see: https://learn.microsoft.com/en-us/windows/win32/menurc/stringfileinfo
        StringFileInfo(
            [
                # see (szKey, Children): https://learn.microsoft.com/en-us/windows/win32/menurc/stringtable
                StringTable(
                    '040904b0',  # Change with Translation (1200_10 = 04b0_16)
                    # see (szKey, Value): https://learn.microsoft.com/en-us/windows/win32/menurc/string-str
                    [StringStruct('CompanyName', ''),
                     StringStruct('FileDescription', app_name),
                     StringStruct('FileVersion', __version__),
                     StringStruct('InternalName', exec_name),
                     StringStruct('LegalCopyright', 'Copyright (C) 2024 Andreas Becker.'),
                     StringStruct('OriginalFilename', exec_name),
                     StringStruct('ProductName', app_name),
                     StringStruct('ProductVersion', __version__)])
            ]),
        # see: https://learn.microsoft.com/en-us/windows/win32/menurc/varfileinfo-block
        VarFileInfo([VarStruct('Translation', [0x0409, 1200])])
    ]
)

try:
    os.mkdir(build_path)
except FileExistsError:
    pass

with open(version_file, 'w') as f:
    f.write(str(version_info))

PyInstaller.__main__.run([
    '--distpath', str(dist_path),
    '--workpath', str(build_path),
    '--noconfirm',
    '--specpath', str(content_root),
    '--name', app_name,
    '--contents-directory', contents_dir_name,
    '--add-data', f'{license_file_name}:.',
    '--add-data', f'{res_path.joinpath('notify.wav')}:./res',
    '--icon', str(res_path.joinpath('coh2_live_stats.ico')),
    '--version-file', str(version_file),
    str(module_path.joinpath('__main__.py'))
])

# Move license next to executable
app_path = dist_path.joinpath(app_name)
os.replace(app_path.joinpath(contents_dir_name, license_file_name), app_path.joinpath(license_file_name + '.txt'))

# Create distribution archive
res = shutil.make_archive(str(app_path), 'zip', dist_path, app_name)

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
from pathlib import Path
import shutil

import PyInstaller.__main__

license_file_name = 'COPYING'
app_name = 'CoH2LiveStats'
contents_dir_name = 'lib'
content_root = Path().cwd().parent
dist_path = content_root.joinpath('dist')

PyInstaller.__main__.run([
    '--distpath', str(dist_path),
    '--workpath', str(content_root.joinpath('build')),
    '--noconfirm',
    '--specpath', str(content_root),
    '--name', app_name,
    '--contents-directory', contents_dir_name,
    '--add-data', '{}:.'.format(license_file_name),
    '--icon', str(content_root.joinpath('res', 'coh2_live_stats.ico')),
    str(content_root.joinpath('src', 'coh2_live_stats', '__main__.py'))
])

# Move license next to executable
app_path = dist_path.joinpath(app_name)
os.replace(app_path.joinpath(contents_dir_name, license_file_name), app_path.joinpath(license_file_name + '.txt'))

# Create distribution archive
res = shutil.make_archive(str(app_path), 'zip', dist_path, app_name)

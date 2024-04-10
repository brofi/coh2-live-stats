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

import asyncio
import concurrent.futures
import logging.config
import os
import re
from contextlib import suppress
from functools import partial
from hashlib import file_digest
from logging import ERROR, INFO
from pathlib import Path
from sys import exit
from tomllib import TOMLDecodeError
from typing import TYPE_CHECKING, override

from httpx import HTTPStatusError, RequestError
from pydantic import ValidationError
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

# Either use relative imports and run the project as a module from IDE Run/Debug
# config (same as python -module) or use these absolute imports and run it as a
# script, but then the package needs to be installed.
# See: Solution 1/3 in https://stackoverflow.com/a/28154841.
# Since the creation of a virtual environment this somehow works without the project
# being installed.
from coh2_live_stats.coh2api import CoH2API
from coh2_live_stats.data.faction import Faction
from coh2_live_stats.data.player import Player
from coh2_live_stats.logging_conf import (
    HiddenOutputFilter,
    LoggingConf,
    LoggingConfError,
)
from coh2_live_stats.output import Output
from coh2_live_stats.settings import Settings, SettingsFactory
from coh2_live_stats.util import (
    cls_name,
    cls_name_parent,
    is_running_in_pyinstaller,
    play_sound,
)

if TYPE_CHECKING:
    from io import BytesIO

LOG = logging.getLogger('coh2_live_stats')

API_TIMEOUT = 30
EXIT_STATUS = 0

PLAYER_PATTERN = re.compile(
    'GAME -- (?:Human|AI) Player: '
    '(?P<id>\\d) (?P<name>.*) (?P<relic_id>\\d+) (?P<team>\\d) '
    f'(?P<faction>{'|'.join([f.key_log for f in Faction])})$'
)

last_player_line = 0
new_match_found = False
new_match_notified = True


def get_players_from_log(settings: Settings, *, notify=True) -> list[Player]:
    global last_player_line
    global new_match_found
    global new_match_notified

    with settings.logfile.open(encoding='utf-8') as f:
        lines = f.readlines()

    pl = 0
    player_matches = []
    for i, line in enumerate(lines):
        m = PLAYER_PATTERN.search(line)
        if m is not None:
            if int(m.group('id')) == 0:
                player_matches.clear()
            player_matches.append(m)
            pl = i

    new_match_found = pl != last_player_line
    last_player_line = pl

    players = []
    for m in player_matches:
        p = Player(
            int(m.group('id')),
            m.group('name'),
            int(m.group('relic_id')),
            int(m.group('team')),
            Faction.from_log(m.group('faction')),
        )
        LOG.info('Found player: %s', p)
        players.append(p)

    if notify:
        # If a multiplayer match is detected (no replay, no local AI game) and it's a
        # new match -> notify.
        # If a multiplayer match is detected, and it's not a new match,
        # but we haven't played a sound before -> notify.
        # The latter can happen if the playing status is written late.
        if new_match_found:
            new_match_notified = False
        is_mp = (
            'Party::SetStatus - S_PLAYING' in lines[pl + 1]
            if pl < len(lines) - 1
            else False
        )
        if not new_match_notified and is_mp:
            LOG.info('Notify new match')
            if settings.notification.play_sound and not play_sound(
                settings.notification.sound
            ):
                LOG.warning('Failed to play sound: %s', settings.notification.sound)

            new_match_notified = True

    return players


class LogFileEventHandler(FileSystemEventHandler):
    def __init__(self, loop, api: CoH2API, settings: Settings, output: Output):
        self.loop = loop
        self.api = api
        self.settings = settings
        self.output = output
        self.last_hash = None
        LOG.info('Initialized %s(%s)', cls_name(self), cls_name_parent(self))

    @override
    def on_modified(self, event: FileSystemEvent) -> None:
        if event.is_directory or event.src_path != str(self.settings.logfile):
            return

        f: BytesIO
        with Path(event.src_path).open('rb', buffering=0) as f:
            h = file_digest(f, 'sha256').hexdigest()

        # Getting multiple modified events on every other file write, so make sure
        # the file contents have really changed.
        # See: https://github.com/gorakhargosh/watchdog/issues/346
        if self.last_hash != h:
            LOG.info('Logfile %s: %s', event.event_type, event.src_path)
            future_players: concurrent.futures.Future = (
                asyncio.run_coroutine_threadsafe(
                    get_players(self.api, self.settings), self.loop
                )
            )
            # Don't block for future result here, since the Observer thread might
            # need to be stopped
            future_players.add_done_callback(partial(on_players_gathered, self.output))
            self.last_hash = h


def on_players_gathered(output: Output, future_players):
    if new_match_found:
        with suppress(concurrent.futures.CancelledError):
            output.print_match(future_players.result())


async def init_leaderboards(api: CoH2API):
    progress_indicator = asyncio.create_task(Output.progress_start())
    try:
        await api.init_leaderboards()
    finally:
        progress_indicator.cancel()
        Output.progress_stop()


async def get_players(api: CoH2API, settings: Settings, *, notify=True):
    players = get_players_from_log(settings, notify=notify)
    if new_match_found:
        progress_indicator = asyncio.create_task(Output.progress_start())
        try:
            return await api.get_players(players)
        finally:
            progress_indicator.cancel()
            Output.progress_stop()
    return None


async def main():
    global EXIT_STATUS

    _logging = None
    api = CoH2API(API_TIMEOUT)
    observer = Observer()

    try:
        _logging = LoggingConf()
        _logging.start()
        settings = SettingsFactory.create_settings()
        output = Output(settings)
        # Initial requests
        await init_leaderboards(api)
        output.print_match(await get_players(api, settings, notify=False))
        # Watch log files
        handler = LogFileEventHandler(asyncio.get_running_loop(), api, settings, output)
        logfile_dir = str(settings.logfile.parent)
        LOG.info('Scheduling %s for: %s', cls_name(handler), logfile_dir)
        observer.schedule(handler, logfile_dir)
        LOG.info('Starting observer: %s[name=%s]', cls_name(observer), observer.name)
        observer.start()
        while True:
            # Force CoH2 to write out its collected log
            with settings.logfile.open(mode="rb", buffering=0):
                await asyncio.sleep(1)
    except LoggingConfError as e:
        logging.exception(e.args[0])
        EXIT_STATUS = 1
    except TOMLDecodeError as e:
        # Should only occur if pydantic settings model is given an invalid TOML config
        LOG.exception(
            'Failed to parse TOML file: %s\n\tCause: %s'.expandtabs(4),
            settings.model_config.get('toml_file'),
            e.args[0],
        )
        EXIT_STATUS = 1
    except ValidationError as e:
        # Pydantic model validation errors
        n = e.error_count()
        msg = '%d validation error%s for %s:'
        args = n, 's' if n > 1 else '', e.title
        for err in e.errors():
            msg += '\n\t[%s]: %s'.expandtabs(4)
            args += '.'.join(err['loc']), err['msg']
        LOG.exception(msg, *args)
        EXIT_STATUS = 1
    except RequestError as e:
        LOG.exception('An error occurred while requesting %s.', repr(e.request.url))
        EXIT_STATUS = 1
    except HTTPStatusError as e:
        LOG.exception(
            "Error response %d while requesting %s.",
            e.response.status_code,
            repr(e.request.url),
        )
        EXIT_STATUS = 1
    # In asyncio `Ctrl-C` cancels the main task, which raises a Cancelled Error
    except asyncio.CancelledError:
        raise
    except Exception:
        msg = 'Unexpected error. Consult the log for more information'
        LOG.exception(
            '%s: %s', msg, _logging.logfile
        ) if _logging else logging.exception('%s.', msg)
        EXIT_STATUS = 1
        raise
    finally:
        if observer:
            LOG.info(
                'Stopping observer: %s[name=%s]', cls_name(observer), observer.name
            )
            observer.stop()
            if observer.is_alive():
                observer.join()
        await api.close()
        LOG.log(
            INFO if EXIT_STATUS == 0 else ERROR,
            'Exit with code: %d\n',
            EXIT_STATUS,
            **HiddenOutputFilter.KWARGS,
        )
        if _logging:
            _logging.stop()

        if EXIT_STATUS > 0 and os.name == 'nt' and is_running_in_pyinstaller():
            os.system('pause')


def run():
    with suppress(asyncio.CancelledError, KeyboardInterrupt, Exception):
        asyncio.run(main())
    exit(EXIT_STATUS)


if __name__ == '__main__':
    run()

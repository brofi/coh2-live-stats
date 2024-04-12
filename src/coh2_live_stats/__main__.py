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
import logging.config
import os
import re
import time
from asyncio import AbstractEventLoop, Queue
from contextlib import suppress
from dataclasses import dataclass
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


@dataclass
class LogInfo:
    players: list[Player]
    is_new_match: bool
    is_multiplayer_match: bool


class LogFileEventHandler(FileSystemEventHandler):
    PLAYER_PATTERN = re.compile(
        'GAME -- (?:Human|AI) Player: '
        '(?P<id>\\d) (?P<name>.*) (?P<relic_id>\\d+) (?P<team>\\d) '
        f'(?P<faction>{'|'.join([f.key_log for f in Faction])})$'
    )

    def __init__(
        self, queue: Queue[LogInfo], loop: AbstractEventLoop, settings: Settings
    ):
        self.queue = queue
        self.loop = loop
        self.settings = settings
        self._last_hash = None
        self._last_player_line = 0
        LOG.info('Initialized %s(%s)', cls_name(self), cls_name_parent(self))
        self.produce()  # kickstart

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
        if self._last_hash != h:
            self.produce()
            self._last_hash = h

    def produce(self):
        self.loop.call_soon_threadsafe(self.queue.put_nowait, self.parse_log())

    def parse_log(self) -> LogInfo:
        with self.settings.logfile.open(encoding='utf-8') as f:
            lines = f.readlines()

        pl = 0
        player_matches = []
        for i, line in enumerate(lines):
            m = self.PLAYER_PATTERN.search(line)
            if m is not None:
                if int(m.group('id')) == 0:
                    player_matches.clear()
                player_matches.append(m)
                pl = i

        is_new_match = pl != self._last_player_line
        self._last_player_line = pl

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

        is_multiplayer_match = (
            'Party::SetStatus - S_PLAYING' in lines[pl + 1]
            if pl < len(lines) - 1
            else False
        )

        return LogInfo(players, is_new_match, is_multiplayer_match)


async def init_leaderboards(api: CoH2API):
    progress_indicator = asyncio.create_task(Output.progress_start())
    try:
        await api.init_leaderboards()
    finally:
        progress_indicator.cancel()
        Output.progress_stop()


async def get_players(api: CoH2API, players: list[Player]):
    progress_indicator = asyncio.create_task(Output.progress_start())
    try:
        return await api.get_players(players)
    finally:
        progress_indicator.cancel()
        Output.progress_stop()


def notify_match(settings: Settings):
    LOG.info('Notify new match')
    if settings.notification.play_sound and not play_sound(settings.notification.sound):
        LOG.warning('Failed to play sound: %s', settings.notification.sound)


def tickle_logfile(settings: Settings):
    while True:
        with settings.logfile.open(mode='rb', buffering=0):
            time.sleep(0.1)


async def main():
    global EXIT_STATUS

    _logging = None
    api = CoH2API(API_TIMEOUT)
    observer = Observer()

    try:
        _logging = LoggingConf()
        _logging.start()

        await init_leaderboards(api)

        settings = SettingsFactory.create_settings()
        output = Output(settings)

        queue: Queue[LogInfo] = Queue()
        handler = LogFileEventHandler(queue, asyncio.get_running_loop(), settings)
        logfile_dir = str(settings.logfile.parent)
        LOG.info('Scheduling %s for: %s', cls_name(handler), logfile_dir)
        observer.schedule(handler, logfile_dir)
        LOG.info('Starting observer: %s[name=%s]', cls_name(observer), observer.name)
        observer.start()

        notified = False
        is_first_item = True
        # Force CoH2 to write out its collected log
        asyncio.get_running_loop().run_in_executor(None, tickle_logfile, settings)
        while observer.is_alive():
            log_info = await queue.get()
            if log_info.is_new_match:
                notified = False
                players = await get_players(api, log_info.players)
                output.print_match(players)
            if not notified and log_info.is_multiplayer_match and not is_first_item:
                # When the logfile playing status is written late, there are multiplayer
                # matches that are not new but haven't been notified before.
                notify_match(settings)
                notified = True
            queue.task_done()
            is_first_item = False
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

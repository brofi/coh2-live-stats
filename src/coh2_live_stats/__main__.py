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

"""Main module."""

import asyncio
import logging.config
import re
import time
from asyncio import AbstractEventLoop, Event, Queue
from contextlib import suppress
from dataclasses import dataclass
from hashlib import file_digest
from logging import ERROR, INFO
from pathlib import Path
from sys import exit
from typing import Any, override

from colorama import just_fix_windows_console
from httpx import HTTPStatusError, RequestError
from pydantic import ValidationError
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer
from watchdog.observers.api import BaseObserver

# Either use relative imports and run the project as a module from IDE Run/Debug
# config (same as python -module) or use these absolute imports and run it as a
# script, but then the package needs to be installed.
# See: Solution 1/3 in https://stackoverflow.com/a/28154841.
# Since the creation of a virtual environment this somehow works without the project
# being installed.
from coh2_live_stats.coh2api import CoH2API
from coh2_live_stats.data.faction import Faction
from coh2_live_stats.data.player import Player
from coh2_live_stats.logging_conf import HiddenOutputFilter, LoggingConf
from coh2_live_stats.output import Output
from coh2_live_stats.settings import Settings, TomlSettings
from coh2_live_stats.util import cls_name, cls_name_parent, play_sound

LOG = logging.getLogger('coh2_live_stats')


@dataclass
class LogInfo:
    """Data parsed from a CoH2 log file."""

    players: list[Player]
    is_new_match: bool
    is_multiplayer_match: bool


class LogFileEventHandler(FileSystemEventHandler):
    """A handler scheduled with a *watchdog* observer.

    This handler parses a CoH2 log file upon change and puts the resulting ``LogInfo``
    in its ``Queue`` for consumers to process.
    """

    PLAYER_PATTERN = re.compile(
        'GAME -- (?:Human|AI) Player: '
        '(?P<id>\\d) (?P<name>.*) (?P<relic_id>\\d+) (?P<team>\\d) '
        f'(?P<faction>{'|'.join([f.key_log for f in Faction])})$'
    )

    def __init__(
        self, loop: AbstractEventLoop, queue: Queue[LogInfo], logfile: Path
    ) -> None:
        """Initialize a logfile handler.

        :param loop: the ``async`` event loop to run queue operations on
        :param queue: the ``async`` queue to store parsed log file information in
        :param logfile: the log file to watch
        """
        self.queue = queue
        self.loop = loop
        self.logfile = logfile
        self._last_hash = ''
        self._last_player_line = -1
        LOG.info('Initialized %s(%s)', cls_name(self), cls_name_parent(self))
        self._produce()  # kickstart

    @override
    def on_modified(self, event: FileSystemEvent) -> None:
        if event.is_directory or event.src_path != str(self.logfile):
            return

        f: Any
        with Path(event.src_path).open('rb', buffering=0) as f:
            h = file_digest(f, 'sha256').hexdigest()

        # Getting multiple modified events on every other file write, so make sure
        # the file contents have really changed.
        # See: https://github.com/gorakhargosh/watchdog/issues/346
        if self._last_hash != h:
            self._produce()
            self._last_hash = h

    def _produce(self) -> None:
        self.loop.call_soon_threadsafe(self.queue.put_nowait, self._parse_log())

    def _parse_log(self) -> LogInfo:
        with self.logfile.open(encoding='utf-8', errors='replace') as f:
            lines = f.readlines()

        pl = 0
        player_matches: list[re.Match[str]] = []
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


async def _init_leaderboards(api: CoH2API) -> None:
    progress_indicator = asyncio.create_task(Output.progress_start())
    try:
        await api.init_leaderboards()
    finally:
        progress_indicator.cancel()
        Output.progress_stop()


async def _get_players(api: CoH2API, players: list[Player]) -> list[Player]:
    progress_indicator = asyncio.create_task(Output.progress_start())
    try:
        return await api.get_players(players)
    finally:
        progress_indicator.cancel()
        Output.progress_stop()


def _notify_match(settings: Settings) -> None:
    LOG.info('Notify new match')
    if settings.notification.play_sound and not play_sound(settings.notification.sound):
        LOG.warning('Failed to play sound: %s', settings.notification.sound)


def _tickle_logfile(logfile: Path, cancel_event: Event) -> None:
    while not cancel_event.is_set():
        with logfile.open(mode='rb', buffering=0):
            time.sleep(0.1)


def _log_validation_error(e: ValidationError) -> None:
    n = e.error_count()
    msg = '%d validation error%s for %s:'
    args: tuple[Any, ...] = n, 's' if n > 1 else '', e.title
    for err in e.errors():
        msg += '\n\t[%s]: %s'.expandtabs(4)
        args += '.'.join(map(str, err['loc'])), err['msg']
    LOG.exception(msg, *args)


def _start_logfile_observer(queue: Queue[LogInfo], logfile: Path) -> BaseObserver:
    observer = Observer()
    handler = LogFileEventHandler(asyncio.get_running_loop(), queue, logfile)
    LOG.info('Scheduling %s for: %s', cls_name(handler), str(logfile.parent))
    observer.schedule(handler, str(logfile.parent))  # type: ignore[no-untyped-call]
    LOG.info('Starting observer: %s[name=%s]', cls_name(observer), observer.name)
    observer.start()  # type: ignore[no-untyped-call]
    return observer


def _stop_logfile_observer(observer: BaseObserver) -> None:
    if observer:
        LOG.info('Stopping observer: %s[name=%s]', cls_name(observer), observer.name)
        observer.stop()  # type: ignore[no-untyped-call]
        observer.join()


async def main() -> int:
    """Set up and run the *coh2_live_stats* main loop."""
    exit_status = 0
    just_fix_windows_console()

    _logging = LoggingConf()
    _logging.start()

    try:
        settings = TomlSettings()
        LOG.info(
            'Loaded %s[file=%s]',
            cls_name(settings),
            settings.model_config.get('toml_file'),
        )
    except ValidationError as e:
        _log_validation_error(e)
        return 1

    api = CoH2API()
    output = Output(settings)

    queue: Queue[LogInfo] = Queue()
    observer = _start_logfile_observer(queue, settings.logfile)

    # Force CoH2 to write out its collected log
    tickle_cancel_event = Event()
    tickle_future = asyncio.get_running_loop().run_in_executor(
        None, _tickle_logfile, settings.logfile, tickle_cancel_event
    )

    try:
        await _init_leaderboards(api)
        notified = False
        is_first_item = True
        while observer.is_alive():
            log_info = await queue.get()
            if log_info.is_new_match:
                notified = False
                players = await _get_players(api, log_info.players)
                output.print_match(players)
            if not notified and log_info.is_multiplayer_match and not is_first_item:
                # When the logfile playing status is written late, there are multiplayer
                # matches that are not new but haven't been notified before.
                _notify_match(settings)
                notified = True
            queue.task_done()
            is_first_item = False
    except RequestError as e:
        LOG.exception('An error occurred while requesting %s.', repr(e.request.url))
        exit_status = 1
    except HTTPStatusError as e:
        LOG.exception(
            'Error response %d while requesting %s.',
            e.response.status_code,
            repr(e.request.url),
        )
        exit_status = 1
    except Exception:
        LOG.exception('Unexpected error:')
        raise
    finally:
        tickle_future.cancel()
        tickle_cancel_event.set()
        _stop_logfile_observer(observer)
        await api.close()
        LOG.log(
            INFO if exit_status == 0 else ERROR,
            'Exit with code: %d\n',
            exit_status,
            extra=HiddenOutputFilter.EXTRA,
        )
        if _logging:
            _logging.stop()

    return exit_status


def run() -> None:
    """Run the event loop. Main entry point."""
    # In asyncio `Ctrl-C` cancels the main task, which raises a Cancelled Error
    with suppress(asyncio.CancelledError, KeyboardInterrupt):
        exit(asyncio.run(main()))


if __name__ == '__main__':
    run()

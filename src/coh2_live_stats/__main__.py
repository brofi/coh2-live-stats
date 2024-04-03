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

import asyncio
import atexit
import concurrent.futures
import logging
import logging.config
import sys
import tomllib
from contextlib import suppress
from hashlib import file_digest
from io import BytesIO
from logging import INFO, WARNING, ERROR, CRITICAL
from pathlib import Path
from sys import exit
from tomllib import TOMLDecodeError

from httpx import RequestError, HTTPStatusError
from pydantic import ValidationError
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer

# Either use relative imports and run the project as a module from IDE Run/Debug Config (same as python -module) or
# use these absolute imports and run it as a script, but then the package needs to be installed.
# See: Solution 1/3 in https://stackoverflow.com/a/28154841.
# Since the creation of a virtual environment this somehow works without the project being installed.
from coh2_live_stats.coh2api import CoH2API
from coh2_live_stats.data.match import Match
from coh2_live_stats.data.player import Player
from coh2_live_stats.output import Output
from coh2_live_stats.settings import SettingsFactory, Settings
from coh2_live_stats.util import progress_start, progress_stop, play_sound, clear

# When running in PyInstaller bundle:
# getattr(sys, '_MEIPASS', __file__): ... \CoH2LiveStats\dist\CoH2LiveStats\lib                 (_MEIPASS)
# __file__:                           ... \CoH2LiveStats\dist\CoH2LiveStats\lib\__main__.py
# When running in a normal Python process:
# getattr(sys, '_MEIPASS', __file__): ... \CoH2LiveStats\src\coh2_live_stats\__main__.py        (getattr default)
# __file__:                           ... \CoH2LiveStats\src\coh2_live_stats\__main__.py

LOGGING_CONF = Path(getattr(sys, '_MEIPASS', str(Path(__file__).parents[2]))).joinpath('logging.toml')
LOG = logging.getLogger('coh2_live_stats')

API_TIMEOUT = 30
EXIT_STATUS = 0
api: CoH2API
settings: Settings
output: Output
last_player_line = 0
new_match_found = False
new_match_notified = True


def get_players_from_log(notify=True):
    global last_player_line
    global new_match_found
    global new_match_notified
    player_lines = []
    # Get human player lines from log
    with open(settings.logfile, encoding='utf-8') as f:
        lines = f.readlines()
    pl = 0
    for i, line in enumerate(lines):
        for sep in ['GAME -- Human Player: ', 'GAME -- AI Player: ']:
            player_line = line.partition(sep)[2]
            if player_line:
                if player_line.split(' ')[0] == str(0):
                    player_lines.clear()
                player_lines.append(player_line.strip())
                pl = i

    new_match_found = pl != last_player_line
    last_player_line = pl

    for p in player_lines:
        LOG.info('Found player: %s', p)

    if notify:
        # If a multiplayer match is detected (no replay, no local AI game) and it's a new match -> notify.
        # If a multiplayer match is detected, and it's not a new match, but we haven't played a sound before -> notify.
        # The latter can happen if the playing status is written late.
        if new_match_found:
            new_match_notified = False
        is_mp = 'Party::SetStatus - S_PLAYING' in lines[pl + 1] if pl < len(lines) - 1 else False
        if not new_match_notified and is_mp:
            LOG.info('Notify new match')
            if settings.notification.play_sound and not play_sound(settings.notification.sound):
                LOG.warning('Failed to play sound: %s', settings.notification.sound)

            new_match_notified = True

    return [Player.from_log(player_line) for player_line in player_lines] if player_lines else []


class LogFileEventHandler(FileSystemEventHandler):

    def __init__(self, loop):
        self.last_hash = None
        self.loop = loop
        LOG.info('Initialized %s(%s)', self.__class__.__name__, self.__class__.__mro__[1].__name__)

    def on_modified(self, event: FileSystemEvent) -> None:
        if event.is_directory or event.src_path != str(settings.logfile):
            return

        f: BytesIO
        with open(event.src_path, 'rb', buffering=0) as f:
            h = file_digest(f, 'sha256').hexdigest()

        # Getting multiple modified events on every other file write, so make sure the file contents have really
        # changed. See: https://github.com/gorakhargosh/watchdog/issues/346
        if self.last_hash != h:
            LOG.info('Logfile %s: %s', event.event_type, event.src_path)
            future_players: concurrent.futures.Future = asyncio.run_coroutine_threadsafe(get_players(), self.loop)
            # Don't block for future result here, since the Observer thread might need to be stopped
            future_players.add_done_callback(on_players_gathered)
            self.last_hash = h


def on_players_gathered(future_players):
    if new_match_found:
        try:
            print_match(future_players.result())
        except concurrent.futures.CancelledError:
            pass


async def init_leaderboards():
    progress_indicator = asyncio.create_task(progress_start())
    try:
        await api.init_leaderboards()
    finally:
        progress_indicator.cancel()
        progress_stop()


async def get_players(notify=True):
    players = get_players_from_log(notify)
    if new_match_found:
        progress_indicator = asyncio.create_task(progress_start())
        try:
            return await api.get_players(players)
        finally:
            progress_indicator.cancel()
            progress_stop()


def print_match(players: list[Player]):
    if not players:
        print('Waiting for match...')
    else:
        clear()
        output.print_match(Match(players))


def print_error(*values, **kwargs):
    print(*values, file=sys.stderr, **kwargs)


def setup_logging():
    with open(LOGGING_CONF, 'rb') as f:
        try:
            conf = tomllib.load(f)
        except TOMLDecodeError as e:
            print_error('Error: Invalid TOML in logging configuration')
            print_error(f'\tFile: {LOGGING_CONF}')
            print_error(f'\tCause: {e.args[0]}')
            exit(1)

    with suppress(KeyError):
        filename = str(Path(conf['handlers']['file']['filename']).name)
        conf['handlers']['file']['filename'] = str(
            Path(getattr(sys, '_MEIPASS', str(Path(__file__).parents[1]))).with_name(filename))

    logging.config.dictConfig(conf)
    logging.addLevelName(WARNING, 'WARN')
    logging.addLevelName(CRITICAL, 'CRIT')
    logging.logThreads = False
    logging.logProcesses = False
    logging.logMultiprocessing = False

    queue_handler = logging.getHandlerByName('queue_handler')
    if queue_handler is not None:
        queue_handler.listener.start()
        atexit.register(queue_handler.listener.stop)

    LOG.info('Configured logging with: %s', LOGGING_CONF)


async def main():
    global api
    global settings
    global output
    global EXIT_STATUS

    setup_logging()
    api = CoH2API(API_TIMEOUT)
    observer = Observer()

    try:
        settings = SettingsFactory.create_settings()
        output = Output(settings)
        # Initial requests
        await init_leaderboards()
        print_match(await get_players(notify=False))
        # Watch log files
        handler = LogFileEventHandler(asyncio.get_running_loop())
        logfile_dir = str(settings.logfile.parent)
        LOG.info('Scheduling %s for: %s', handler.__class__.__name__, logfile_dir)
        observer.schedule(handler, logfile_dir)
        LOG.info('Starting observer: %s[name=%s]', observer.__class__.__name__, observer.name)
        observer.start()
        while True:
            # Force CoH2 to write out its collected log
            with open(settings.logfile, mode="rb", buffering=0):
                await asyncio.sleep(1)
    except TOMLDecodeError as e:
        # Should only occur if pydantic settings model is given an invalid TOML config
        LOG.error('Failed to parse TOML file: %s', settings.model_config.get('toml_file'))
        LOG.error('Invalid TOML: %s', e.args[0])
        EXIT_STATUS = 1
    except ValidationError as e:
        # Pydantic model validation errors
        n = e.error_count()
        LOG.error('%d validation error%s for %s:', n, 's' if n > 1 else '', e.title)
        for err in e.errors():
            LOG.error('\t[%s]: %s'.expandtabs(4), '.'.join(err['loc']), err['msg'])
        EXIT_STATUS = 1
    except RequestError as e:
        LOG.error('An error occurred while requesting %s.', repr(e.request.url))
        EXIT_STATUS = 1
    except HTTPStatusError as e:
        LOG.error("Error response %d while requesting %s.", e.response.status_code, repr(e.request.url))
        EXIT_STATUS = 1
    # In asyncio `Ctrl-C` cancels the main task, which raises a Cancelled Error
    except asyncio.CancelledError:
        raise
    finally:
        if observer:
            LOG.info('Stopping observer: %s[name=%s]', observer.__class__.__name__, observer.name)
            observer.stop()
            if observer.is_alive():
                observer.join()
        await api.close()
        LOG.log(INFO if EXIT_STATUS == 0 else ERROR, 'Exit with code: %d\n', EXIT_STATUS)


def run():
    try:
        asyncio.run(main())
        exit(EXIT_STATUS)
    except asyncio.CancelledError:
        pass
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    run()

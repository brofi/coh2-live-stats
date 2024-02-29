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
import concurrent.futures
from hashlib import file_digest
from io import BytesIO
from pathlib import Path
from sys import exit
from tomllib import TOMLDecodeError

from httpx import RequestError, HTTPStatusError
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer

# Either use relative imports and run the project as a module from IDE Run/Debug Config (same as python -module) or
# use these absolute imports and run it as a script, but then the package needs to be installed.
# See: Solution 1/3 in https://stackoverflow.com/a/28154841.
# Since the creation of a virtual environment this somehow works without the project being installed.
from coh2_live_stats.coh2api import CoH2API
from coh2_live_stats.data.player import Player
from coh2_live_stats.output import Output
from coh2_live_stats.settings import Settings
from coh2_live_stats.util import progress_start, progress_stop, play_sound

API_TIMEOUT = 30
EXIT_STATUS = 0
res = Path(__file__).with_name('res')
soundfile = res.joinpath('notify.wav')
api: CoH2API
settings: Settings
output: Output
current_players = []
players_changed = False


def get_players_from_log():
    player_lines = []
    # Get human player lines from log
    with open(settings.get_logfile_path(), encoding='utf-8') as f:
        lines = f.readlines()
    for line in lines:
        for sep in ['GAME -- Human Player:', 'GAME -- AI Player:']:
            player_line = line.partition(sep)[2]
            if player_line:
                player_lines.append(player_line.strip())

    if player_lines:
        latest_match_player_count = int(player_lines[len(player_lines) - 1].split(' ')[0]) + 1
        # Keep only player lines of latest match
        player_lines = player_lines[len(player_lines) - latest_match_player_count:]
        return [Player.from_log(player_line) for player_line in player_lines]
    return []


class LogFileEventHandler(FileSystemEventHandler):

    def __init__(self, loop):
        self.last_hash = None
        self.loop = loop

    def on_modified(self, event: FileSystemEvent) -> None:
        if event.is_directory or event.src_path != str(settings.get_logfile_path()):
            return

        f: BytesIO
        with open(event.src_path, 'rb', buffering=0) as f:
            h = file_digest(f, 'sha256').hexdigest()

        # Getting multiple modified events on every other file write, so make sure the file contents have really
        # changed. See: https://github.com/gorakhargosh/watchdog/issues/346
        if self.last_hash != h:
            future_players: concurrent.futures.Future = asyncio.run_coroutine_threadsafe(get_players(), self.loop)
            # Don't block for future result here, since the Observer thread might need to be stopped
            future_players.add_done_callback(on_players_gathered)
            self.last_hash = h


def on_players_gathered(future_players):
    if players_changed:
        if not play_sound(str(soundfile)):
            print('Match found!')
        try:
            output.print_players(future_players.result())
        except concurrent.futures.CancelledError:
            pass


async def init_leaderboards():
    progress_indicator = asyncio.create_task(progress_start())
    try:
        await api.init_leaderboards()
    finally:
        progress_indicator.cancel()
        progress_stop()


async def get_players():
    global current_players
    global players_changed
    players_changed = False
    players = get_players_from_log()
    if players and players != current_players:
        progress_indicator = asyncio.create_task(progress_start())
        try:
            current_players = await api.get_players(players)
            players_changed = True
        finally:
            progress_indicator.cancel()
            progress_stop()

    return current_players


async def main():
    global api
    global settings
    global output
    global EXIT_STATUS

    api = CoH2API(API_TIMEOUT)
    observer = Observer()

    try:
        settings = Settings()
        output = Output(settings)
        # Initial requests
        await init_leaderboards()
        output.print_players(await get_players())
        # Watch log files
        observer.schedule(LogFileEventHandler(asyncio.get_running_loop()), str(settings.get_logfile_path().parent))
        observer.start()
        while True:
            # Force CoH2 to write out its collected log
            with open(settings.get_logfile_path(), mode="rb", buffering=0):
                await asyncio.sleep(1)
    except TOMLDecodeError as e:
        print(e.args[0])
        EXIT_STATUS = 1
    except FileNotFoundError as e:
        print(f'No logfile: "{e.filename}"')
        EXIT_STATUS = 1
    except RequestError as e:
        print(f"An error occurred while requesting {e.request.url!r}.")
        EXIT_STATUS = 1
    except HTTPStatusError as e:
        print(f"Error response {e.response.status_code} while requesting {e.request.url!r}.")
        EXIT_STATUS = 1
    # In asyncio `Ctrl-C` cancels the main task, which raises a Cancelled Error
    except asyncio.CancelledError:
        raise
    finally:
        if observer:
            observer.stop()
            if observer.is_alive():
                observer.join()
        await api.close()


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

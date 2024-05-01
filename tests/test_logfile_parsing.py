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
from asyncio import Queue
from collections.abc import AsyncGenerator, Generator, Iterable
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from coh2_live_stats.__main__ import LogFileEventHandler, LogInfo
from coh2_live_stats.data.player import Player
from watchdog.observers import Observer


@pytest.fixture(scope='module')
def logfile() -> Generator[Path, Any, None]:
    watchdir = Path(__file__).with_name('watch')
    watchdir.mkdir(exist_ok=True)
    logfile = watchdir.joinpath('warnings.log')
    logfile.touch()
    yield logfile
    logfile.unlink()
    watchdir.rmdir()


@pytest_asyncio.fixture(scope='module')
async def queue(logfile: Path) -> AsyncGenerator[Queue[LogInfo], Any]:  # noqa: RUF029 (need loop)
    queue: Queue[LogInfo] = Queue()
    observer = Observer()
    observer.schedule(
        LogFileEventHandler(asyncio.get_running_loop(), queue, logfile),
        str(logfile.parent),
    )  # type: ignore[no-untyped-call]
    observer.start()  # type: ignore[no-untyped-call]
    yield queue
    observer.stop()  # type: ignore[no-untyped-call]
    observer.join()


@pytest.fixture
def now() -> str:
    # intentionally naive (like in CoH2 log file)
    return datetime.now().strftime('%H:%M:%S.%f')[:-4]  # noqa: DTZ005


def log_match(
    logfile: Path, now: str, players: Iterable[Player], mode: str = 'w'
) -> None:
    log = (
        f'{now}   GAME -- Scenario: DATA:'
        'scenarios\\mp\\8p_redball_express\\8p_redball_express\n'
        f'{now}   GAME -- Win Condition Qualified Name: '
        '00000000000000000000000000000000:16123440\n'
        f'{now}   GAME -- Win Condition Name: victory_point\n'
    )
    for i, p in enumerate(players):
        log += (
            f'{now}   GAME -- Human Player: '
            f'{i} {p.name} {p.relic_id} {p.team_id} {p.faction.key_log}\n'
        )
    with logfile.open(mode=mode) as f:
        f.write(log)


@pytest.fixture
def _log_playing(logfile: Path, now: str) -> None:
    log = f'{now}   Party::SetStatus - S_PLAYING'
    with logfile.open(mode='a') as f:
        f.write(log)


def test_initial_parse(queue: Queue[LogInfo]) -> None:
    assert queue.qsize() == 1


@pytest.mark.asyncio(scope='module')
async def test_initial_parse_empty(queue: Queue[LogInfo]) -> None:
    log_info: LogInfo = await queue.get()
    queue.task_done()
    assert log_info == LogInfo([], is_new_match=True, is_multiplayer_match=False)


@pytest.mark.asyncio(scope='module')
@pytest.mark.usefixtures('_equality')
async def test_parse_new_match(
    queue: Queue[LogInfo], logfile: Path, now: str, players1: list[Player]
) -> None:
    log_match(logfile, now, players1, mode='a')
    log_info: LogInfo = await queue.get()
    queue.task_done()
    assert log_info == LogInfo(players1, is_new_match=True, is_multiplayer_match=False)


@pytest.mark.asyncio(scope='module')
@pytest.mark.usefixtures('_equality')
async def test_parse_next_match(
    queue: Queue[LogInfo], logfile: Path, now: str, players2: list[Player]
) -> None:
    log_match(logfile, now, players2, mode='a')
    log_info: LogInfo = await queue.get()
    queue.task_done()
    assert log_info == LogInfo(players2, is_new_match=True, is_multiplayer_match=False)


@pytest.mark.asyncio(scope='module')
@pytest.mark.usefixtures('_equality', '_log_playing')
async def test_parse_now_playing_match(
    queue: Queue[LogInfo], players2: list[Player]
) -> None:
    log_info: LogInfo = await queue.get()
    queue.task_done()
    assert log_info == LogInfo(players2, is_new_match=False, is_multiplayer_match=True)

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

"""Custom logging configuration with custom handlers, formatters and filters."""

import copy
import logging.config
import sys
import time
import tomllib
from logging import CRITICAL, WARNING, Filter, Formatter, Handler, LogRecord
from logging.handlers import QueueHandler, QueueListener
from pathlib import Path
from queue import Queue
from tomllib import TOMLDecodeError
from typing import TYPE_CHECKING, Any, Final, override

if TYPE_CHECKING:
    from coh2_live_stats.__main__ import LogInfo


class LoggingConfError(Exception):
    """Raised when an error occurred while configuring custom logging."""


class LoggingConf:
    """Custom logging configuration.

    The custom logging configuration is initialized from the logging configuration file.
    What cannot be done in the configuration file is done in its initialization.
    """

    CONF_PATH = Path(getattr(sys, '_MEIPASS', str(Path(__file__).parent))).joinpath(
        '_logging.toml'
    )

    def __init__(self, logfile: Path | None = None, *, stdout: bool = False) -> None:
        """Initialize the custom logging configuration.

        :param logfile: the logging configuration file
        :param stdout: whether to add a stdout handler
        """
        try:
            with self.CONF_PATH.open('rb') as f:
                self.log_conf = tomllib.load(f)
        except FileNotFoundError as e:
            msg = f'{e.strerror}: {e.filename}'
            raise LoggingConfError(msg) from e
        except TOMLDecodeError as e:
            msg = (
                'Invalid TOML in logging configuration'
                f'\n\tFile: {self.CONF_PATH}'
                f'\n\tCause: {e.args[0]}'
            ).expandtabs(4)
            raise LoggingConfError(msg) from e

        try:
            if logfile is None:
                logfile = Path(self.log_conf['handlers']['file']['filename'])
                logfile = Path(
                    getattr(sys, '_MEIPASS', str(Path(__file__).parents[1]))
                ).with_name(logfile.name)
            self.log_conf['handlers']['file']['filename'] = str(logfile)
        except KeyError as e:
            msg = f'Failed to patch handler filename in {self.CONF_PATH}'
            raise LoggingConfError(msg) from e

        self.logfile = logfile

        logging.config.dictConfig(self.log_conf)
        logging.addLevelName(WARNING, 'WARN')
        logging.addLevelName(CRITICAL, 'CRIT')
        logging.logThreads = False
        logging.logProcesses = False
        logging.logMultiprocessing = False

        # Setup custom queue handler
        que: Queue[LogInfo] = Queue(-1)
        queue_handler = CustomQueueHandler(que)
        logging.getLogger().addHandler(queue_handler)
        # Listener needs to be created manually, unlike when configuring the default
        # queue handler with dictConfig
        handlers: tuple[Handler, ...] = (
            self._get_handler_by_name('stderr'),
            self._get_handler_by_name('file'),
        )
        if stdout:
            handlers += (self._get_handler_by_name('stdout'),)
        self.listener = QueueListener(que, *handlers, respect_handler_level=True)

    @staticmethod
    def _get_handler_by_name(name: str) -> Handler:
        handler = logging.getHandlerByName(name)
        if handler is None:
            msg = f'Not a handler: {name!r}.'
            raise LoggingConfError(msg)
        return handler

    def start(self) -> None:
        """Start custom logging."""
        self.listener.start()
        logger = logging.getLogger('coh2_live_stats')
        logger.info(
            'Started logging with: %s', self.CONF_PATH, extra=HiddenOutputFilter.EXTRA
        )

    def stop(self) -> None:
        """Stop custom logging."""
        self.listener.stop()


class CustomQueueHandler(QueueHandler):
    """A custom ``QueueHandler``.

    This ``QueueHandler`` doesn't mess with the original record and doesn't add in
    exception data before any custom formatter has the chance to do so. It discards the
    exception info but keeps the exception text string for use with custom formatters.
    """

    @override
    def prepare(self, record: LogRecord) -> Any:
        # Don't edit original record
        r = copy.copy(record)
        # If record contains exception info ...
        if record.exc_info:
            # ... call formatter on the record copy which sets the exception text to
            # exc_text and discard the returned message which would also contain
            # exception data.
            _ = self.format(r)
            # Save the formatted exception text ...
            et = r.exc_text
            # ... and reset to original record.
            r = copy.copy(record)
            # Now remove the exception info before ...
            r.exc_info = None
            # ... calling the formatter again to get the message without exception data.
            msg = self.format(r)
            # Add saved exception text after(!) generating the message to get a
            # normal record message with its exception string saved in exc_text.
            r.exc_text = et
        else:
            # Easy without exception info
            msg = self.format(r)
        # Set msg and message which now have the args merged in - so remove them
        r.msg = msg
        r.message = msg
        r.args = None
        return r


class SimpleFormatter(Formatter):
    """A simple formatter that ignores exception data."""

    @override
    def format(self, record: LogRecord) -> str:
        # Save the exception text
        et = record.exc_text
        # Don't let parent formatter add exception text. Exception info was already
        # removed in CustomQueueHandler.prepare(), so parent formatter won't create
        # the exception text again.
        record.exc_text = None
        s = super().format(record)
        # Restore exception text for other formatters that want to use it (e.g.
        # DetailedFormatter).
        record.exc_text = et
        return s


class DetailedFormatter(Formatter):
    """A formatter that puts the milliseconds before the timezone."""

    @override
    def formatTime(self, record: LogRecord, datefmt: str | None = None) -> str:
        ct = self.converter(record.created)
        if datefmt:
            # Replace %f (only supported by datetime) with milliseconds
            s = time.strftime(datefmt.replace('%f', f'{record.msecs:03.0f}'), ct)
        else:
            s = time.strftime(self.default_time_format, ct)
            if self.default_msec_format:
                s = self.default_msec_format % (s, record.msecs)
        return s


class ErrorFilter(Filter):
    """A filter that only keeps warnings and errors."""

    @override
    def filter(self, record: LogRecord) -> bool | LogRecord:
        return record.levelno < WARNING


class HiddenOutputFilter(Filter):
    """A filter that removes records explicitly marked as hidden via extra data."""

    KEY_EXTRA_HIDE: Final[str] = 'hide'
    EXTRA: Final[dict[str, bool]] = {KEY_EXTRA_HIDE: True}

    @override
    def filter(self, record: LogRecord) -> bool | LogRecord:
        return not getattr(record, self.KEY_EXTRA_HIDE, False)

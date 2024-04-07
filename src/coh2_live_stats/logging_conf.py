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

import copy
import logging
import queue
import sys
import time
import tomllib
from logging import CRITICAL, WARNING, Filter, Formatter, LogRecord
from logging.handlers import QueueHandler, QueueListener
from pathlib import Path
from tomllib import TOMLDecodeError
from typing import override

from .util import cls_name, print_error


class LoggingConfError(Exception):
    pass


class LoggingConf:
    CONF_PATH = Path(getattr(sys, '_MEIPASS', str(Path(__file__).parent))).joinpath(
        '_logging.toml'
    )

    def __init__(self):
        try:
            with open(self.CONF_PATH, 'rb') as f:
                self.log_conf = tomllib.load(f)
        except FileNotFoundError as e:
            raise LoggingConfError(f'{e.strerror}: {e.filename}') from e
        except TOMLDecodeError as e:
            print_error('Invalid TOML in logging configuration')
            print_error(f'\tFile: {self.CONF_PATH}')
            print_error(f'\tCause: {e.args[0]}')
            raise LoggingConfError(
                f'Failed to initialize {cls_name(self)} with {self.CONF_PATH}'
            ) from e

        file_handler_conf_name = 'file'
        try:
            filename = str(
                Path(self.log_conf['handlers'][file_handler_conf_name]['filename']).name
            )
            self.log_file_path = Path(
                getattr(sys, '_MEIPASS', str(Path(__file__).parents[1]))
            ).with_name(filename)
            self.log_conf['handlers'][file_handler_conf_name]['filename'] = str(
                self.log_file_path
            )
        except KeyError as e:
            raise LoggingConfError(
                f'Failed to patch filename for handler named '
                f'{file_handler_conf_name!r} in {self.CONF_PATH}'
            ) from e

        logging.config.dictConfig(self.log_conf)
        logging.addLevelName(WARNING, 'WARN')
        logging.addLevelName(CRITICAL, 'CRIT')
        logging.logThreads = False
        logging.logProcesses = False
        logging.logMultiprocessing = False

        # Setup custom queue handler
        que = queue.Queue(-1)
        queue_handler = CustomQueueHandler(que)
        logging.getLogger().addHandler(queue_handler)
        # Listener needs to be created manually, unlike when configuring the default
        # queue handler with dictConfig
        stderr_handler = logging.getHandlerByName('stderr')
        file_handler = logging.getHandlerByName('file')
        self.listener = QueueListener(
            que, stderr_handler, file_handler, respect_handler_level=True
        )

    def start(self):
        self.listener.start()
        logger = logging.getLogger('coh2_live_stats')
        logger.info('Started logging with: %s', self.CONF_PATH)

    def stop(self):
        self.listener.stop()


# Custom Queue Handler that doesn't mess with the original record and doesn't add in
# exception data before any custom formatter has the chance to do so. It discards the
# exception info but keeps the exception text string for use with custom formatters.
class CustomQueueHandler(QueueHandler):
    @override
    def prepare(self, record):
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
    @override
    def format(self, record):
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
    @override
    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            # Replace %f (only supported by datetime) with milliseconds
            s = time.strftime(datefmt.replace('%f', f'{record.msecs:03.0f}'), ct)
        else:
            s = time.strftime(self.default_time_format, ct)
            if self.default_msec_format:
                s = self.default_msec_format % (s, record.msecs)
        return s


class StderrHiddenFilter(Filter):
    KEY_EXTRA_HIDE = 'hide_from_stderr'
    KWARGS = {'extra': {KEY_EXTRA_HIDE: True}}

    @override
    def filter(self, record: LogRecord):
        return not getattr(record, self.KEY_EXTRA_HIDE, False)

import sys
import os
import logging
import pathlib

_simple_format = logging.Formatter('{asctime} [{levelname:7s}] {name} {message}',
                                   datefmt='%Y-%m-%d %H:%M:%S',
                                   style='{')

_initialized = False


def setup(debug=False):
    global _initialized
    ch = logging.StreamHandler(sys.stderr)
    ch.setLevel(logging.DEBUG if debug else logging.INFO)
    ch.setFormatter(_simple_format)

    root = logging.getLogger()
    root.addHandler(ch)
    root.setLevel(logging.INFO)

    logging.getLogger('dvc').setLevel(logging.ERROR)
    logging.getLogger('lenskit').setLevel(logging.DEBUG)
    logging.getLogger('bookgender').setLevel(logging.DEBUG)
    root.debug('log system configured')
    _initialized = True


def start_script(file, debug=False):
    """
    Initialize logging and get a logger for a script.

    Args:
        file(str): The ``__file__`` of the script being run.
        debug(bool): whether to enable debug logging to the console
    """

    if not _initialized:
        setup(debug)

    name = pathlib.Path(file).stem
    logger = logging.getLogger(name)
    try:
        logger.info('starting script on %s', os.uname().nodename)
    except AttributeError:
        logger.info('starting script')

    return logger


def _logfile(file):
    fh = logging.FileHandler(file, mode='w', encoding='utf-8')
    fmt = logging.Formatter('{asctime} ({process}) [{levelname:7}] {name}: {message}', style='{')
    fh.setFormatter(fmt)
    fh.setLevel(logging.DEBUG)
    return fh


def set_logfile(file):
    fh = _logfile(file)
    logging.getLogger().addHandler(fh)


class LogFile:
    "Context manager to add a log file to the system."

    def __init__(self, file):
        self.file = file
        self.fh = None

    def __enter__(self):
        self.fh = _logfile(self.file)
        logging.getLogger().addHandler(self.fh)
        logging.getLogger(__name__).info('activated log file %s', self.file)


    def __exit__(self, *args, **kwargs):
        logging.getLogger(__name__).info('deactivating log file %s', self.file)
        logging.getLogger().removeHandler(self.fh)

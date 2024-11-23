import logging
import os
import sys
from pathlib import Path
import datetime
import locale
from threading import Lock

from colorlog import ColoredFormatter
from dask.distributed import get_worker

import kiele as ROOT_PACKAGE


ROOT_PACKAGE_NAME = str(Path(ROOT_PACKAGE.__file__).parent.name)
LOCALE, LOCALE_ENCODING = locale.getlocale()

__lock = Lock()  # thread 並列されたタスクがアクセスする場合に備えて


# ===== set dask worker prefix to ``ROOT`` logger =====

def _get_dask_worker_name():
    name = '(Main)'
    try:
        worker = get_worker()
        if isinstance(worker.name, str):  # local なら index, cluster なら tcp address
            name = f'({worker.name}) '
        else:
            name = f'(Sub{worker.name}) '
    except ValueError:
        pass
    return name


class _DaskLogRecord(logging.LogRecord):
    def getMessage(self):
        msg = str(self.msg)
        if self.args:
            msg = msg % self.args
        msg = _get_dask_worker_name() + ' ' + msg
        return msg


logging.setLogRecordFactory(_DaskLogRecord)


# ===== format config =====

def __create_formatter(colored=True):

    if colored:
        header = "%(log_color)s" + "[%(name)s %(levelname).4s]" + "%(reset)s"

        formatter = ColoredFormatter(
            f"{header} %(message)s",
            datefmt=None,
            reset=True,
            log_colors={
                "DEBUG": "purple",
                "INFO": "cyan",
                "WARNING": "yellow",
                "ERROR": "light_red",
                "CRITICAL": "red",
            },
        )

    else:
        header = "[%(name)s %(levelname).4s]"
        formatter = logging.Formatter(
            f"{header} %(message)s",
            datefmt=None,
        )

    return formatter


# ===== handler config =====

STDOUT_HANDLER_NAME = 'stdout-handler'


def __get_stdout_handler():
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.set_name(STDOUT_HANDLER_NAME)
    stdout_handler.setFormatter(__create_formatter(colored=True))
    return stdout_handler


def __has_stdout_handler(logger=None):
    if logger is None:
        logger = get_root_package_logger()

    return any([handler.get_name() != STDOUT_HANDLER_NAME for handler in logger.handlers])


def set_stdout_output(logger=None, level=logging.INFO):

    if logger is None:
        logger = get_root_package_logger()

    if not __has_stdout_handler(logger):
        logger.addHandler(__get_stdout_handler())

    logger.setLevel(level)


def remove_stdout_output(logger=None):
    if logger is None:
        logger = get_root_package_logger()

    if __has_stdout_handler(logger):
        logger.removeHandler(__get_stdout_handler())


def add_file_output(logger=None, filepath=None, level=logging.INFO) -> str:
    """Add FileHandler to the logger.

    Returns:
        str: THe name of the added handler.
        Its format is f'filehandler-{os.path.basename(filepath)}'

    """

    # module logger or package logger
    if logger is None:
        logger = get_root_package_logger()

    # cirtify filepath
    if filepath is None:
        filepath = datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + f'_{logger.name}.log'

    # add file handler
    file_handler = logging.FileHandler(filename=filepath, encoding=LOCALE_ENCODING)
    file_handler.set_name(f'filehandler-{os.path.basename(filepath)}')
    file_handler.setFormatter(__create_formatter(colored=False))
    logger.addHandler(file_handler)

    # set (default) log level
    logger.setLevel(level)

    return file_handler.get_name()


def remove_file_output(logger=None, filepath=None):
    """Removes FileHandler from the logger.

    If filepath is None, remove all FileHandler.
    """

    if logger is None:
        logger = get_root_package_logger()

    if filepath is None:
        for handler in logger.handlers:
            if 'filehandler-' in handler.name:
                logger.removeHandler(handler)

    else:
        handler_name = f'filehandler-{os.path.basename(filepath)}'
        for handler in logger.handlers:
            if handler_name == handler.name:
                logger.removeHandler(handler)


def remove_all_output(logger=None):
    if logger is None:
        logger = get_root_package_logger()

    for handler in logger.handlers:
        logger.removeHandler(handler)

    logger.addHandler(logging.NullHandler())


# ===== root-package logger =====

def _root_package_logger_condig():
    with __lock:

        # get root package logger
        logger = logging.getLogger(ROOT_PACKAGE_NAME)

        # add stdout handler
        set_stdout_output(logger)


def get_root_package_logger() -> logging.Logger:
    _root_package_logger_condig()
    return logging.getLogger(ROOT_PACKAGE_NAME)


# ===== module logger =====

def __get_module_tree_name(module_path: str or None = None) -> str:
    """Get the string like ``ROOT_PACKAGE.subpackage.submodule`` from its __file__."""
    library_root = Path(ROOT_PACKAGE.__file__).parent
    if module_path:
        me = Path(module_path).absolute()
    else:
        me = Path(__file__)
    buff: str = me.relative_to(library_root).as_posix()  # subpackage/submodule.py
    buff = buff.rstrip('.py')  # subpackage/submodule
    return ROOT_PACKAGE_NAME + '.' + buff.replace('/', '.')


def get_module_logger(module_path: str) -> logging.Logger:
    """Return the module-level logger.

    The format is defined in the package_root_logger.

    Args:
        module_path (str): __file__ of the module(.py) file.

    Returns:
        logging.Logger:
            The logger its name is ``root_package.subpackage.module``.
            child level logger's signal propagates to the parent logger
            and is shown in the parent(s)'s hander(s).

    """
    logger_name = __get_module_tree_name(module_path)
    return logging.getLogger(logger_name)


if __name__ == '__main__':
    root_logger = get_root_package_logger()
    module_logger = get_module_logger(__file__)

    root_logger.info("This is root logger's info.")
    module_logger.info("This is module logger's info.")

    add_file_output(module_logger, 'test-module-log.log', level=logging.DEBUG)
    module_logger.debug('debugging...')
    remove_file_output(module_logger, 'test-module-log.log')

    module_logger.info('debug is finished.')

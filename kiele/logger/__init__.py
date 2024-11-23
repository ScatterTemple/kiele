from ._logging import get_root_package_logger as get_kiele_logger
from ._logging import (
    get_module_logger,
    add_file_output,
    set_stdout_output,
    remove_file_output,
    remove_stdout_output,
    remove_all_output,
)


def get_dask_logger():
    import logging
    return logging.getLogger('distributed')


def get_optuna_logger():
    import optuna
    return optuna.logging.get_logger('optuna')


def get_dash_logger():
    import logging
    return logging.getLogger('werkzeug')
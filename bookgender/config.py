import os
import sys
from pathlib import Path
import logging
import psycopg2
from configparser import ConfigParser

__all__ = [
    'db_uri', 'proc_count', 'have_gpu',
    'work_dir',
    'data_dir'
]

_log = logging.getLogger(__name__)

_cpu_sources = [
    ('LK_NUM_PROCS', None),
    ('SLURM_CPUS_ON_NODE', None),
    ('CPU count', os.cpu_count)
]

_config_file = None


def _config_section(section):
    global _config_file

    if _config_file is None:
        # read config file
        _config_file = ConfigParser()
        _config_file.read('config.ini')

    if _config_file.has_section(section):
        return _config_file[section]
    else:
        return {}


def db_uri():
    url = os.environ.get('DB_URL', None)

    if not url:
        url = _config_section('database').get('url', None)

    if url:
        return url
    else:
        raise Exception("No database URL configured")


def proc_count():
    cpus = None
    cpu_src = None
    for src, fun in _cpu_sources:
        if fun is None:
            cpus = os.environ.get(src, None)
        else:
            cpus = fun()
        if cpus is not None:
            cpus = int(cpus)
            _log.info('configured for %d cpus (by %s)', cpus, src)
            return cpus


def isolate_search():
    res = os.environ.get('ISOLATE_SEARCH', False)
    if res:
        return res != 'no'
    else:
        return sys.platform == 'linux'


def have_gpu():
    return os.environ.get('SLURM_JOB_PARTITION', None) == 'gpuq'


work_dir = Path('work')
data_dir = Path('data')
step_dir = Path('steps')
scratch_dir = Path('scratch')

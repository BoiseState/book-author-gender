import os
import sys
from pathlib import Path
import logging
from configparser import ConfigParser
import toml
import numpy as np
import git

__all__ = [
    'db_uri', 'proc_count', 'have_gpu',
    'root_dir',
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


def rng_seed():
    "Get the initial random seed"
    cfg = Path('random.toml')
    seed = None
    if cfg.exists():
        obj = toml.loads(cfg.read_text())
        seed = obj.get('initial_seed', None)

    if seed is None:
        _log.warn('no random seed specified')
        return np.random.SeedSequence()
    else:
        return np.random.SeedSequence(int(seed))


def db_uri():
    "Get the URL to connect to the database."
    if 'DB_URL' in os.environ:
        return os.environ['DB_URL']

    repo = git.Repo(search_parent_directories=True)

    cfg = ConfigParser()
    _log.debug('reading config from db.cfg')
    cfg.read([repo.working_tree_dir + '/db.cfg'])

    branch = repo.head.reference.name
    _log.info('reading database config for branch %s', branch)

    if branch in cfg:
        section = cfg[branch]
    else:
        _log.debug('No configuration for branch %s, using default', branch)
        section = cfg['DEFAULT']

    host = section.get('host', 'localhost')
    port = section.get('port', None)
    db = section.get('database', None)
    user = section.get('user', None)
    pw = section.get('password', None)

    if db is None:
        _log.error('No database specified for branch %s', branch)
        raise RuntimeError('no database specified')

    url = 'postgresql://'
    if user:
        url += user
        if pw:
            url += ':' + pw
        url += '@'
    url += host
    if port:
        url += ':' + port
    url += '/' + db
    return url


def proc_count():
    cpus = None
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


root_dir = Path(__file__).parent.parent
work_dir = Path('work')
data_dir = Path('data')
step_dir = Path('steps')
scratch_dir = Path('scratch')

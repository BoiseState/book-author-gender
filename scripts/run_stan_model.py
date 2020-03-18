"""
Runs one of the STAN models.

Usage:
    run_stan_model.py [options] <model> [<instance>...]

Options:
    --iter N
        The number of iterations to run [default: 5000].
    --chains N
        The number of chains to run [default: 4].
    -P <prop>=<val>
        A property to pass.
    <model>
        The name of the model to run (in `bookgender.models`).
    <instance>
        The instance(s) to run.
"""

from docopt import docopt
from os import fspath
from hashlib import md5
from importlib import import_module
from pathlib import Path
import pickle

from bookgender.logutils import start_script
from bookgender.config import scratch_dir

_log = start_script(__file__)
mod_dir = Path('models')

import pystan


def load_model(options):
    name = options['<model>']
    _log.info('loading stat model %s', name)
    return import_module(f'bookgender.models.{name}')


def compile_model(mod):
    sfile = mod_dir / mod.stan_file
    name = mod.__name__.split('.')[-1]
    m_hash = md5(sfile.read_bytes()).hexdigest()
    cache_file = scratch_dir / 'stan' / f'stan-{name}-{m_hash}.pkl'

    if cache_file.exists():
        _log.info('loading cached STAN model from %s', cache_file)
        with cache_file.open('rb') as cf:
            return pickle.load(cf)

    else:
        _log.info('loading and compiling STAN model %s', sfile)
        model = pystan.StanModel(file=fspath(sfile), model_name=name)
        _log.info('saving STAN model to cache')
        cache_file.parent.mkdir(exist_ok=True, parents=True)
        with cache_file.open('wb') as cf:
            pickle.dump(model, cf)
        return model


def instances(mod, options):
    vars = options['<instance>']
    if vars:
        return vars
    else:
        return mod.instances


def load_data(mod, vars):
    return mod.load_data(vars)


def run_model(mod, model, data, inst, options):
    cfg = {
        'iter': int(options['--iter']),
        'chains': int(options['--chains'])
    }
    params = {}
    if options['-P']:
        k, v = options['-P'].split('=', 1)
        params[k] = v
    _log.info('running with %d iterations and %d chains', cfg['iter'], cfg['chains'])
    mod.run_model(model, data, inst, cfg, **params)


if __name__ == '__main__':
    options = docopt(__doc__)
    mod = load_model(options)
    model = compile_model(mod)

    for var in instances(mod, options):
        data = load_data(mod, var)
        run_model(mod, model, data, var, options)

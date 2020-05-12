"""
Carry out hyperparameter search for a model.

Usage:
  search-model.py [--drop-ratings] [--out-name NAME] <dataset> <algorithm>
  search-model.py --inspect <file>

Options:
    --drop-ratings
        Drop rating values from data prior to training and evaluation.
    --out-name NAME
        Use output name NAME instead of the algorithm name.
    --inspect <file>
        Inspect the optimization results in <file>.
"""

from docopt import docopt
import importlib
import json

from bookgender.logutils import start_script, LogFile
from bookgender.config import data_dir, rng_seed
import bookgender.datatools as dt
from bookgender.eval import OptEvaluator, ImprovementStopper

from lenskit.util import init_rng

import skopt

import pandas as pd
import numpy as np

_log = start_script(__file__)


def job_template(data, var):
    ofn = var
    if var.endswith('-imp'):
        opt = f' --drop-ratings --out-name {ofn}'
        var = var.replace('-imp', '')
    else:
        opt = ''
    a_mod = dt.pyname(var)
    a_fn = dt.afname(var)
    return f'data/{data}/tuning/{ofn}-search.dvc', {
        'cmd': f'python -m scripts.search-model{opt} {data} {a_fn}',
        'wdir': '../../..',
        'deps': [
            {'path': 'scripts/search-model.py'},
            {'path': f'data/{data}/ratings.parquet'},
            {'path': f'data/{data}/tuning/test-ratings.parquet'},
            {'path': f'bookgender/algorithms/{a_mod}.py'},
            {'path': 'random.toml'}
        ],
        'outs': [
            {'path': f'data/{data}/tuning/{ofn}.opt'},
            {'path': f'data/{data}/tuning/{ofn}.json',
             'metric': True, 'cache': False},
        ]
    }


def setup(data, algo, implicit):
    amn = dt.pyname(algo)

    ddir = data_dir / data
    tdir = ddir / 'tuning'

    algo_mod = importlib.import_module(f'bookgender.algorithms.{amn}')
    _log.info('reading test ratings')
    test = pd.read_parquet(tdir / 'test-ratings.parquet')
    if implicit and 'rating' in test.columns:
        test = test.drop(columns=['rating'])

    _log.info('reading original ratings')
    train = pd.read_parquet(ddir / 'ratings.parquet')
    if implicit and 'rating' in train.columns:
        train = train.drop(columns=['rating'])
    train_mask = pd.Series(True, index=train.index)
    train_mask.loc[test.index] = False
    train = train[train_mask].copy()

    return OptEvaluator(algo_mod, train, test)


def run_search(data, algo, out_name, evaluate):
    opts = dict()
    algo_mod = evaluate.module
    opts.update(getattr(algo_mod, 'options', {}))

    afn = dt.afname(algo)
    if not out_name:
        out_name = afn
    ddir = data_dir / data
    tdir = ddir / 'tuning'
    ofile = tdir / f'{out_name}.opt'
    cpfile = tdir / f'{out_name}.cp'

    if cpfile.exists():
        _log.info('loading checkpoint file %s', cpfile)
        initial = skopt.load(cpfile)
        opts['x0'] = initial.x_iters
        opts['y0'] = initial.func_vals
        opts['n_random_starts'] = max(0, 10-len(initial.x_iters))
        opts['n_calls'] = 100 - len(initial.x_iters)
        _log.info('checkpoint has %d iterations', len(initial.x_iters))

    saver = skopt.callbacks.CheckpointSaver(cpfile)
    stopper = ImprovementStopper(0.01, min_runs=20)
    timer = skopt.callbacks.TimerCallback()

    with LogFile(tdir / f'{afn}-search.log'):
        res = skopt.gp_minimize(evaluate, algo_mod.dimensions,
                                callback=[timer, saver, stopper],
                                **opts)
        _log.info('%s: optimal MRR of %f at %s after %d searches',
                  algo, -res.fun, res.x, len(res.x_iters))

    res.iter_time = timer.iter_time
    _log.info('writing results to %s', ofile)
    skopt.dump(res, ofile)
    with (tdir / f'{out_name}.json').open('w') as jsf:
        json.dump({
            'params': [x.item() for x in res.x],
            'iters': len(res.x_iters),
            'MRR': -res.fun
        }, jsf)

    _log.info('removing checkpoint file %s', cpfile)
    if cpfile.exists():
        cpfile.unlink()


def inspect(file):
    _log.info('loading file %s', file)
    opt = skopt.load(file)
    n = len(opt.x_iters)
    print('iterations:', n)
    print('optimal HR:', -opt.fun)
    for i in range(n):
        x = opt.x_iters[i]
        nhr = opt.func_vals[i]
        if hasattr(opt, 'iter_time'):
            time = opt.iter_time[i]
        else:
            time = np.nan
        print('iter[{}]: {!r} -> {:f} ({:.1f}s)'.format(i, x, -nhr, time))


if __name__ == '__main__':
    options = docopt(__doc__)
    insp_file = options['--inspect']
    if insp_file:
        inspect(insp_file)
    else:
        seed = init_rng(rng_seed(), 'search-model', options['<dataset>'], options['--out-name'])
        _log.info('using random seed %s', seed)
        eval = setup(options['<dataset>'], options['<algorithm>'], options['--drop-ratings'])
        run_search(options['<dataset>'], options['<algorithm>'], options['--out-name'],
                   eval)

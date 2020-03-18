"""
Train a model

Usage:
    train_model.py [options] DATA ALGO

Options:
    --drop-ratings
        Drop rating values prior to training
    --default
        Use algorithm defaults instead of reading optimization data.
    --train-data SRC
        Use training data from SRC [default: all].
    -N, --name NAME
        Use NAME instead of ALGO as the name for input & output files.
"""

import json

from bookgender.logutils import start_script, LogFile
from bookgender.config import data_dir
from bookgender.util import OptionReader, get_opt
import bookgender.datatools as dt
from bookgender.rec_ops import get_algorithm

from lenskit.algorithms import Recommender
from lenskit.util import Stopwatch

import pandas as pd

_log = start_script(__file__)


class TrainOptions(OptionReader):
    data = get_opt('DATA')
    algo = get_opt('ALGO')
    drop_ratings = get_opt('--drop-ratings')
    default = get_opt('--default')
    name = get_opt('--name')
    train_data = get_opt('--train-data')

    @property
    def algo_fn(self):
        afn = self.name
        if not afn:
            afn = dt.afname(self.algo)
        return afn


def job_template(data, algo):
    ashort = algo.replace('-imp', '')
    algo_mod = dt.pyname(ashort)
    algo_fn = dt.afname(algo)
    algo_name = dt.afname(ashort)
    fn = f'data/{data}/models/{algo_fn}.dvc'
    opts = ''
    if algo_fn.endswith('-imp'):
        opts = f' --drop-ratings -N {algo_fn}'

    return fn, {
        'cmd': f'python -m scripts.train_model{opts} {data} {algo_name}',
        'wdir': '../../..',
        'deps': [
            {'path': f'bookgender/algorithms/{algo_mod}.py'},
            {'path': f'data/{data}/tuning/{algo_fn}.json'},
            {'path': f'data/{data}/ratings.parquet'}
        ],
        'outs': [
            {'path': f'data/{data}/models/{algo_fn}.model'}
        ]
    }


def eval_template(data, algo):
    ashort = algo.replace('-imp', '')
    algo_mod = dt.pyname(ashort)
    algo_fn = dt.afname(algo)
    algo_name = dt.afname(ashort)
    fn = f'data/{data}/eval/{algo_fn}-train.dvc'
    opts = ''
    if algo_fn.endswith('-imp'):
        opts = f' --drop-ratings -N {algo_fn}'

    return fn, {
        'cmd': f'python -m scripts.train_model{opts} --train-data eval {data} {algo_name}',
        'wdir': '../../..',
        'deps': [
            {'path': f'bookgender/algorithms/{algo_mod}.py'},
            {'path': f'data/{data}/tuning/{algo_fn}.json'},
            {'path': f'data/{data}/eval/train-ratings.parquet'}
        ],
        'outs': [
            {'path': f'data/{data}/eval/{algo_fn}.model'}
        ]
    }


def train(options: TrainOptions):
    ddir = data_dir / options.data
    if options.train_data == 'all':
        mdir = ddir / 'models'
        rating_file = ddir / 'ratings.parquet'
    elif options.train_data == 'eval':
        mdir = ddir / 'eval'
        rating_file = ddir / 'eval' / 'train-ratings.parquet'
    else:
        raise ValueError(f'unknown training data {options.train_data}')

    mdir.mkdir(parents=True, exist_ok=True)
    mfn = mdir / f'{options.algo_fn}.model'
    if options.default:
        _log.warn('Using default settings')
        opt_fn = None
    else:
        opt_fn = ddir / 'tuning' / f'{options.algo_fn}.json'
        _log.info('Using algorithm optimization results %s', opt_fn)

    with LogFile(mdir / f'{options.algo_fn}.log'):
        _log.info('reading ratings from %s', rating_file)
        ratings = pd.read_parquet(rating_file)
        if options.drop_ratings and 'rating' in ratings.columns:
            _log.info('dropping rating column')
            ratings = ratings.drop(columns=['rating'])
        implicit = 'rating' not in ratings.columns

        _log.info('loading algorithm %s for %s in %s mode', options.data, options.algo,
                  'implicit' if implicit else 'explicit')
        algo = get_algorithm(options.data, options.algo, opt_fn, implicit)
        algo = Recommender.adapt(algo)

        _log.info('training %s on %s ratings', algo, len(ratings))
        timer = Stopwatch()
        model = algo.fit(ratings)
        timer.stop()
        _log.info('trained in %s', timer)
        _log.info('saving model to %s', mfn)
        with open(mfn, 'wb') as f:
            p = dt.CompactingPickler(f, protocol=4)
            p.dump(model)


if __name__ == '__main__':
    opts = TrainOptions(__doc__)
    train(opts)

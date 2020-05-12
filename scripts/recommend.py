"""
Generate recommendations

Usage:
    recommend.py [options] <dataset> <algorithm>

Options:
    -n N
        Recommend N items per user [default: 100].
"""

import pickle
import json

from bookgender.logutils import start_script, LogFile
from bookgender.config import data_dir, proc_count
from bookgender.util import OptionReader, get_opt
import bookgender.datatools as dt

from lenskit import batch
from lenskit.util import Stopwatch

import pandas as pd

_log = start_script(__file__)


def job_template(data, algo):
    algo_fn = dt.afname(algo)
    fn = f'data/{data}/recs/{algo_fn}.dvc'
    return fn, {
        'cmd': f'python -m scripts.recommend {data} {algo_fn}',
        'wdir': '../../..',
        'deps': [
            {'path': 'scripts/recommend.py'},
            {'path': f'data/{data}/sample-users.csv'},
            {'path': f'data/{data}/models/{algo_fn}.model'}
        ],
        'outs': [
            {'path': f'data/{data}/recs/{algo_fn}.parquet'},
            {'path': f'data/{data}/recs/{algo_fn}.csv.gz'},
            {'path': f'data/{data}/recs/{algo_fn}.json', 'metric': True}
        ]
    }


class RecOptions(OptionReader):
    "Options for the recommend script"

    data = get_opt('<dataset>')
    algo = get_opt('<algorithm>')
    n = get_opt('-n', int)


def run_recs(opts):
    ddir = data_dir / opts.data
    afn = dt.afname(opts.algo)
    mfn = ddir / 'models' / f'{afn}.model'
    with LogFile(ddir / 'recs' / f'{afn}.log'):
        _log.info('loading model for %s', opts.algo)
        with open(mfn, 'rb') as f:
            model = pickle.load(f)

        _log.info('loading users for %s', opts.data)
        users = pd.read_csv(ddir / 'sample-users.csv')

        _log.info('producing recs for %d users', len(users))
        timer = Stopwatch()
        recs = batch.recommend(model, users.user, opts.n,
                               nprocs=max(proc_count() // 2, 1))
        timer.stop()
        _log.info('finished in %s', timer)

        _log.info('saving recommendations')
        recs.to_parquet(ddir / 'recs' / f'{afn}.parquet', index=False, compression='brotli')
        recs.to_csv(ddir / 'recs' / f'{afn}.csv.gz', index=False)

        metrics = ddir / 'recs' / f'{afn}.json'
        with metrics.open('w') as jsf:
            json.dump({'rec_time': timer.elapsed()}, jsf)


if __name__ == '__main__':
    opts = RecOptions(__doc__)
    run_recs(opts)

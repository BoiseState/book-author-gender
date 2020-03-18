"""
Generate recommendations

Usage:
  recommend.py <dataset> <algorithm>
"""
from docopt import docopt
import pickle
import json

from bookgender.logutils import start_script, LogFile
from bookgender.config import data_dir, proc_count
import bookgender.datatools as dt
from bookgender.rec_ops import get_algorithm

from lenskit import batch
from lenskit.util import Stopwatch

import pandas as pd

LIST_SIZE = 100

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


def run_recs(data, algo):
    ddir = data_dir / data
    afn = dt.afname(algo)
    mfn = ddir / 'models' / f'{afn}.model'
    with LogFile(ddir / 'recs' / f'{afn}.log'):
        _log.info('loading model for %s', algo)
        with open(mfn, 'rb') as f:
            model = pickle.load(f)

        _log.info('loading users for %s', data)
        users = pd.read_csv(ddir / 'sample-users.csv')

        _log.info('producing recs for %d users', len(users))
        timer = Stopwatch()
        recs = batch.recommend(model, users.user, LIST_SIZE,
                               nprocs=max(proc_count() // 2, 1))
        timer.stop()
        _log.info('finished in %s', timer)

        _log.info('saving recommendations')
        recs.to_parquet(ddir / 'recs' / f'{afn}.parquet', index=False)
        recs.to_csv(ddir / 'recs' / f'{afn}.csv.gz', index=False)

        metrics = ddir / 'recs' / f'{afn}.json'
        with metrics.open('w') as jsf:
            json.dump({'rec_time': timer.elapsed()}, jsf)


if __name__ == '__main__':
    args = docopt(__doc__)
    run_recs(args['<dataset>'], args['<algorithm>'])

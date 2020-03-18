"""
Aggregate data from experimental runs into unified files to ease analysis.

Usage:
  aggregate.py --users
  aggregate.py --recs [--skip-missing]
  aggregate.py --rec-perf
  aggregate.py --rec-tune
  aggregate.py --rec-rerank
"""

import sys
from docopt import docopt
import importlib
import json

from bookgender.logutils import start_script
from bookgender.config import data_dir
import bookgender.datatools as dt
from bookgender.algorithms import data_algos

import pandas as pd
import numpy as np

_log = start_script(__file__)


def _datasets():
    yield from dt.datasets.keys()


def _rec_lists():
    for ds, algos in data_algos.items():
        for a in algos:
            yield ds, a


def agg_users():
    u_dfs = {}
    r_dfs = {}

    for ds in _datasets():
        dir = data_dir / ds
        _log.info('reading users from %s', dir)
        u_dfs[ds] = pd.read_csv(dir / 'sample-users.csv').set_index('user')
        _log.info('reading ratings from %s', dir)
        rates = pd.read_csv(dir / 'sample-ratings.csv')
        if 'rating' not in rates.columns:
            rates = rates.assign(rating=np.nan)
        r_dfs[ds] = rates.set_index(['user', 'item'])

    users = pd.concat(u_dfs, names=['dataset']).reset_index()
    users.to_csv(data_dir / 'study-users.csv', index=False)

    ratings = pd.concat(r_dfs, names=['dataset']).reset_index()
    ratings.to_csv(data_dir / 'study-ratings.csv', index=False)


def agg_recs(skip):
    all_recs = {}

    for ds, algo in _rec_lists():
        rec_fn = data_dir / ds / 'recs' / f'{algo}.parquet'
        if not rec_fn.exists():
            if skip:
                _log.warning('%s does not exist', rec_fn)
                continue
            else:
                _log.error('%s does not exist', rec_fn)
                sys.exit(2)

        _log.info('reading recs from %s on %s from %s', ds, algo, rec_fn)
        recs = pd.read_parquet(rec_fn)
        all_recs[(ds, algo)] = recs

    all_recs = pd.concat(all_recs, names=['dataset', 'algorithm'])
    all_recs = all_recs.reset_index(['dataset', 'algorithm'])
    all_recs = all_recs.reset_index(drop=True)
    all_recs.to_csv(data_dir / 'study-recs.csv.gz', index=False)
    all_recs.to_parquet(data_dir / 'study-recs.parquet')


def agg_perf():
    records = []
    for ds, algo in _rec_lists():
        m_fn = data_dir / ds / 'eval' / f'{algo}-metrics.json'
        with m_fn.open('r') as jsf:
            rec = json.load(jsf)
        rec['DataSet'] = ds
        rec['Algorithm'] = algo
        records.append(rec)

    _log.info('writing %d records', len(records))
    pd.DataFrame.from_records(records).to_csv(data_dir / 'rec-perf.csv', index=False)


def agg_rerank_perf():
    records = []
    for ds, algo in _rec_lists():
        m_fn = data_dir / ds / 'eval' / f'{algo}-rerank.csv'
        if not m_fn.exists():
            _log.error('%s does not exist', m_fn)
            continue
        rec = pd.read_csv(m_fn)
        rec['DataSet'] = ds
        rec['Algorithm'] = algo
        records.append(rec)

    _log.info('writing %d records', len(records))
    pd.concat(records).to_csv(data_dir / 'rerank-perf.csv', index=False)


def agg_tune():
    records = []
    for ds, algo in _rec_lists():
        jfn = data_dir / ds / 'tuning' / f'{algo}.json'
        with jfn.open('r') as jsf:
            rec = json.load(jsf)
        rec['DataSet'] = ds
        rec['Algorithm'] = algo
        records.append(rec)

    _log.info('writing %d records', len(records))
    with open(data_dir / 'rec-tune.json', 'w', encoding='utf-8') as f:
        for r in records:
            print(json.dumps(r), file=f)


def user_step():
    deps = (data_dir / ds / f'sample-{part}.csv' for ds in _datasets() for part in ['users', 'ratings'])
    deps = [{'path': d.as_posix()} for d in deps]
    deps.append({'path': 'scripts/aggregate.py'})

    return 'steps/sample-users.dvc', {
        'cmd': 'python -m scripts.aggregate --users',
        'wdir': '..',
        'outs': [
            {'path': 'data/study-users.csv'},
            {'path': 'data/study-ratings.csv'}
        ],
        'deps': deps
    }


def rec_step():
    deps = (data_dir / ds / 'recs' / f'{algo}.parquet' for (ds, algo) in _rec_lists())
    deps = [{'path': d.as_posix()} for d in deps]
    deps.append({'path': 'scripts/aggregate.py'})

    return 'steps/recommend.dvc', {
        'cmd': 'python -m scripts.aggregate --recs',
        'wdir': '..',
        'outs': [
            {'path': 'data/study-recs.csv.gz'},
            {'path': 'data/study-recs.parquet'}
        ],
        'deps': deps
    }


def perf_step():
    deps = (data_dir / ds / 'eval' / f'{algo}-metrics.json' for (ds, algo) in _rec_lists())
    deps = [{'path': d.as_posix()} for d in deps]
    deps.append({'path': 'scripts/aggregate.py'})

    return 'steps/perf-results.dvc', {
        'cmd': 'python -m scripts.aggregate --rec-perf',
        'wdir': '..',
        'outs': [
            {'path': 'data/rec-perf.csv'}
        ],
        'deps': deps
    }


def tune_step():
    deps = (data_dir / ds / 'tuning' / f'{algo}.json' for (ds, algo) in _rec_lists())
    deps = [{'path': d.as_posix()} for d in deps]
    deps.append({'path': 'scripts/aggregate.py'})

    return 'steps/tuning-results.dvc', {
        'cmd': 'python -m scripts.aggregate --rec-tune',
        'wdir': '..',
        'outs': [
            {'path': 'data/rec-tune.json'}
        ],
        'deps': deps
    }


def rerank_step():
    deps = (data_dir / ds / 'eval' / f'{algo}-rerank.csv' for (ds, algo) in _rec_lists())
    deps = [{'path': d.as_posix()} for d in deps]
    deps.append({'path': 'scripts/aggregate.py'})

    return 'steps/rerank-results.dvc', {
        'cmd': 'python -m scripts.aggregate --rec-rerank',
        'wdir': '..',
        'outs': [
            {'path': 'data/rerank-perf.csv'}
        ],
        'deps': deps
    }


if __name__ == '__main__':
    args = docopt(__doc__)
    if args['--users']:
        agg_users()
    elif args['--recs']:
        agg_recs(args['--skip-missing'])
    elif args['--rec-perf']:
        agg_perf()
    elif args['--rec-tune']:
        agg_tune()
    elif args['--rec-rerank']:
        agg_rerank_perf()

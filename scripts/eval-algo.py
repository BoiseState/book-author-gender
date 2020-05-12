"""
Measure the effectiveness of an algorithm.

Usage:
    eval-algo.py [options] <dataset> <algorithm>

Options:
    -n N    The number of recommendations to use [default: 100]
    -N, --name NAME
            Use NAME as the algorithm file name.
    -t, --time TIME
            Evaluate ratings for TIME.
    --drop-ratings
            Drop the 'rating' column and run in implicit feedback mode.
    --default
            Use the algorithm's default configuration.
    --pretrained
            Use a pre-trained model.
    --rerank
            Run rerankers in the output.
    --output-format
            Ouptut format [default: json].
    --tuning-data
            Use the tuning data instead of eval.
"""

import json
import pickle

from bookgender.logutils import start_script, LogFile
from bookgender.config import data_dir, proc_count, rng_seed
from bookgender.util import OptionReader, get_opt
import bookgender.datatools as dt
from bookgender.rec_ops import get_algorithm
import bookgender.rerank
from bookgender.rerank.rerankUtil import getBookGender

from lenskit import batch, topn
from lenskit.util import Stopwatch, init_rng
from lenskit.algorithms import Recommender


import pandas as pd

_log = start_script(__file__)


class EvalOptions(OptionReader):
    data = get_opt('<dataset>')
    algo = get_opt('<algorithm>')
    drop_ratings = get_opt('--drop-ratings')
    name = get_opt('--name')
    n = get_opt('-n', int)
    time = get_opt('--time')
    default = get_opt('--default')
    tuning = get_opt('--tuning-data')
    pretrained = get_opt('--pretrained')
    rerank = get_opt('--rerank')
    output_format = get_opt('--output-format')

    @property
    def algo_fn(self):
        afn = self.name
        if not afn:
            afn = dt.afname(self.algo)
        return afn


def job_template(data, algo):
    "Job template for setting up algorithm evaluation."
    algo_fn = dt.afname(algo)
    fn = f'data/{data}/eval/{algo_fn}.dvc'
    if algo_fn.endswith('-imp'):
        opt = f' --drop-ratings -N {algo_fn}'
        aname = algo_fn.replace('-imp', '')
    else:
        opt = ''
        aname = algo_fn

    return fn, {
        'cmd': f'python -m scripts.eval-algo{opt} --pretrained {data} {aname}',
        'deps': [
            {'path': 'scripts/eval-algo.py'},
            {'path': f'data/{data}/eval/{algo_fn}.model'},
            {'path': f'data/{data}/ratings.parquet'},
            {'path': f'data/{data}/eval/test-ratings.parquet'},
            {'path': f'data/{data}/tuning/{algo_fn}.json'}
        ],
        'outs': [
            {'path': f'data/{data}/eval/{algo_fn}-recs.parquet'},
            {'path': f'data/{data}/eval/{algo_fn}-metrics.json',
             'metric': True}
        ],
        'wdir': '../../..'
    }


def rerank_template(data, algo):
    "Job template for setting up algorithm rerank evaluation."
    algo_fn = dt.afname(algo)
    fn = f'data/{data}/eval/{algo_fn}-rerank.dvc'
    if algo_fn.endswith('-imp'):
        opt = f' --drop-ratings -N {algo_fn}'
        aname = algo_fn.replace('-imp', '')
    else:
        opt = ''
        aname = algo_fn

    return fn, {
        'cmd': f'python -m scripts.eval-algo{opt} --pretrained --rerank {data} {aname}',
        'deps': [
            {'path': 'scripts/eval-algo.py'},
            {'path': f'data/{data}/eval/{algo_fn}.model'},
            {'path': f'data/{data}/ratings.parquet'},
            {'path': f'data/{data}/eval/test-ratings.parquet'},
            {'path': f'data/{data}/tuning/{algo_fn}.json'}
        ],
        'outs': [
            {'path': f'data/{data}/eval/{algo_fn}-rerank-recs.parquet'},
            {'path': f'data/{data}/eval/{algo_fn}-rerank.csv'}
        ],
        'wdir': '../../..'
    }


def _load_ratings(options):
    dir = data_dir / options.data
    if options.tuning:
        dir = dir / 'tuning'
    else:
        dir = dir / 'eval'

    test_fn = dir / 'test-ratings.parquet'
    _log.info('reading test ratings from from %s', test_fn)
    test = pd.read_parquet(test_fn)

    rate_fn = data_dir / options.data / 'ratings.parquet'
    _log.info('reading original ratings from from %s', rate_fn)
    ratings = pd.read_parquet(rate_fn)

    if options.drop_ratings:
        _log.info('dropping rating column')
        test = test.drop(columns=['rating'])
        ratings = ratings.drop(columns=['rating'])

    _log.info('creating training mask')
    train_mask = pd.Series(True, index=ratings.index)
    train_mask.loc[test.index] = False
    assert train_mask.sum() + len(test) == len(ratings)

    train = ratings[train_mask].copy()  # copy to disconnect and ensure contiguious
    _log.info('loaded %d test and %d train ratings', len(test), len(train))
    return train, test


def _load_time_ratings(options):
    dir = data_dir / options.data
    filename = dir / 'ratings.parquet'
    _log.info('reading ratings from %s', filename)
    ratings = pd.read_parquet(filename)
    _log.info('loaded %d ratings', len(ratings))
    dso = dt.datasets[options.data]

    if options.drop_ratings:
        ratings = ratings.drop(columns=['rating'])

    tsc = dso.ts_column
    ratings[tsc] = pd.to_datetime(ratings[tsc], unit='s')
    ratings.set_index(tsc, inplace=True)

    _log.info('splitting for time %s', options.time)

    test = ratings[options.time]
    train = ratings[:pd.Period(options.time).start_time - pd.Timedelta('1us')]

    return train, test


def _train_algo(data, algo, ratings):
    algo = Recommender.adapt(algo)
    _log.info('training algorithm %s', algo)
    timer = Stopwatch()
    algo.fit(ratings)
    timer.stop()
    _log.info('trained %s in %s', algo, timer)
    return algo


def _gen_recs(algo, test, n):
    users = test['user'].unique()
    _log.info('recommending for %d users with %s', len(users), algo)
    recs = batch.recommend(algo, users, n, n_jobs=max(proc_count() // 2, 1))
    return recs


def _measure_recs(recs, test):
    rla = topn.RecListAnalysis()
    rla.add_metric(topn.recall)
    rla.add_metric(topn.recip_rank)
    rla.add_metric(topn.ndcg)

    return rla.compute(recs[['user', 'item', 'score']], test, include_missing=True)


def _measure_raw(algo, test, n, afn):
    recs = _gen_recs(algo, test, n)
    if options.time:
        rfile = data_dir / options.data / 'eval' / f'{afn}-{options.time}-recs.parquet'
        mfile = data_dir / options.data / 'eval' / f'{afn}-{options.time}-metrics.json'
    else:
        rfile = data_dir / options.data / 'eval' / f'{afn}-recs.parquet'
        mfile = data_dir / options.data / 'eval' / f'{afn}-metrics.json'
    _log.info('saving recommendations to %s', rfile)
    recs.to_parquet(rfile, compression='brotli', index=False)

    metrics = _measure_recs(recs, test)

    if options.tuning:
        mfile = mfile.with_suffix('.tuning.json')
    agg_metrics = {
        'MRR': metrics['recip_rank'].fillna(0).mean(),
        'HR': metrics['recall'].fillna(0).mean(),
        'NDCG': metrics['ndcg'].fillna(0).mean()
    }
    _log.info('saving metrics to %s: %s', mfile, agg_metrics)
    mfile.write_text(json.dumps(agg_metrics))


def _measure_rerank(algo, train, test, n, afn, gender):
    rfile = data_dir / options.data / 'eval' / f'{afn}-rerank-recs.parquet'
    mfile = data_dir / options.data / 'eval' / f'{afn}-rerank.csv'

    all_recs = []
    all_metrics = []

    if hasattr(algo, 'predictor'):
        algo = algo.predictor

    for rr in bookgender.rerank.__all__:
        _log.info('applying reranker %s', rr)
        wrapper = getattr(bookgender.rerank, rr)
        w_algo = wrapper(algo, gender)
        w_algo.fit(train, fit_pred=False)
        recs = _gen_recs(w_algo, test, n)
        all_recs.append(recs.assign(Strategy=rr))
        metrics = _measure_recs(recs, test)
        all_metrics.append({
            'Strategy': rr,
            'MRR': metrics['recip_rank'].fillna(0).mean(),
            'HR': metrics['recall'].fillna(0).mean(),
            'NDCG': metrics['ndcg'].fillna(0).mean()
        })

    pd.concat(all_recs, ignore_index=True).to_parquet(rfile)
    pd.DataFrame.from_records(all_metrics).to_csv(mfile, index=False)


def measure_algo(options: OptionReader):
    afn = options.algo_fn
    lfile = data_dir / options.data / 'eval' / f'{afn}.log'
    opt = data_dir / options.data / 'tuning' / f'{afn}.json'

    seed = init_rng(rng_seed(), 'eval-algo', options.data, options.algo)
    _log.info('using random seed %s', seed)

    with LogFile(lfile):
        if options.time:
            train, test = _load_time_ratings(options)
        else:
            train, test = _load_ratings(options)
        if options.pretrained:
            mfn = data_dir / options.data / 'eval' / f'{afn}.model'
            _log.info('loading model from %s', mfn)
            with mfn.open('rb') as f:
                algo = pickle.load(f)
        else:
            implicit = 'rating' not in train.columns
            algo = get_algorithm(options.data, options.algo,
                                 None if options.default else opt,
                                 implicit)
            algo = _train_algo(options.data, algo, train)

        if options.rerank:
            gender = getBookGender()
            _measure_rerank(algo, train, test, options.n, afn, gender)
        else:
            _measure_raw(algo, test, options.n, afn)


if __name__ == '__main__':
    options = EvalOptions(__doc__)
    measure_algo(options)

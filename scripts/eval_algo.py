"""
Measure the effectiveness of an algorithm.

Usage:
    eval_algo.py [options] <dataset> <algorithm>

Options:
    -n N    The number of recommendations to use [default: 100]
    -N, --name NAME
            Use NAME as the algorithm file name.
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
import importlib

from bookgender.logutils import start_script, LogFile
from bookgender.config import data_dir, proc_count
from bookgender.util import OptionReader, get_opt
import bookgender.datatools as dt
from bookgender.rec_ops import get_algorithm
import bookgender.rerank
from bookgender.rerank.rerankUtil import getBookGender

from lenskit import batch, topn
from lenskit.util import Stopwatch
from lenskit.algorithms import Recommender


import pandas as pd

_log = start_script(__file__)


class EvalOptions(OptionReader):
    data = get_opt('<dataset>')
    algo = get_opt('<algorithm>')
    drop_ratings = get_opt('--drop-ratings')
    name = get_opt('--name')
    n = get_opt('-n', int)
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
        'cmd': f'python -m scripts.eval_algo{opt} --pretrained {data} {aname}',
        'deps': [
            {'path': 'scripts/eval_algo.py'},
            {'path': f'data/{data}/eval/{algo_fn}.model'},
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
        'cmd': f'python -m scripts.eval_algo{opt} --pretrained --rerank {data} {aname}',
        'deps': [
            {'path': 'scripts/eval_algo.py'},
            {'path': f'data/{data}/eval/{algo_fn}.model'},
            {'path': f'data/{data}/eval/test-ratings.parquet'},
            {'path': f'data/{data}/tuning/{algo_fn}.json'}
        ],
        'outs': [
            {'path': f'data/{data}/eval/{algo_fn}-rerank-recs.parquet'},
            {'path': f'data/{data}/eval/{algo_fn}-rerank.csv'}
        ],
        'wdir': '../../..'
    }


def _load_ratings(options, mode):
    dir = data_dir / options.data
    if options.tuning:
        dir = dir / 'tuning'
    else:
        dir = dir / 'eval'

    filename = dir / f'{mode}-ratings.parquet'
    _log.info('reading ratings from from %s', filename)
    ratings = pd.read_parquet(filename)
    if options.drop_ratings:
        _log.info('dropping rating column')
        ratings = ratings.drop(columns=['rating'])
    _log.info('%s contained %d ratings', filename, len(ratings))
    return ratings


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
    rfile = data_dir / options.data / 'eval' / f'{afn}-recs.parquet'
    _log.info('saving recommendations to %s', rfile)
    recs.to_parquet(rfile, compression='snappy', index=False)

    metrics = _measure_recs(recs, test)
    mfile = data_dir / options.data / 'eval' / f'{afn}-metrics.json'
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

    with LogFile(lfile):
        train = _load_ratings(options, 'train')
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
        test = _load_ratings(options, 'test')

        if options.rerank:
            gender = getBookGender()
            _measure_rerank(algo, train, test, options.n, afn, gender)
        else:
            _measure_raw(algo, test, options.n, afn)


if __name__ == '__main__':
    options = EvalOptions(__doc__)
    measure_algo(options)

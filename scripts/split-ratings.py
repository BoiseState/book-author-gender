"""
Split rating data into train and test sets.


This script only saves the test data, but it preserves the indexes from the original
input file.  Code that loads train-test pairs should use that index to get the ratings
from the original ratings file!

Usage:
    split-ratings.py [options] DATASET

Options:
    --test-users N
        The number of test users to sample [default: 5000]
    --min-ratings N
        The minimum number of ratings per testuser [default: 5]
    -d, --subdir DIR
        The subdirectory to use [default: tuning]
    DATASET
        The name of the data set to prepare.
"""

from bookgender.logutils import start_script
from bookgender.config import data_dir, rng_seed
from bookgender.util import OptionReader, get_opt
import bookgender.datatools as dt

import pandas as pd
from lenskit.util import init_rng, rng

_log = start_script(__file__)


def job_template(data, var):
    "Job template for setting up data splitting."
    fn = f'data/{data}/{var}/split.dvc'

    return fn, {
        'cmd': f'python -m scripts.split-ratings -d {var} {data}',
        'deps': [
            {'path': 'scripts/split-ratings.py'},
            {'path': f'data/{data}/ratings.parquet'},
            {'path': 'random.toml'}
        ],
        'outs': [
            {'path': f'data/{data}/{var}/test-ratings.parquet'}
        ],
        'wdir': '../../..'
    }


class SplitOptions(OptionReader):
    data = get_opt('DATASET')
    test_users = get_opt('--test-users', int)
    min_ratings = get_opt('--min-ratings', int)
    subdir = get_opt('--subdir')


def split(opts: OptionReader):
    data = dt.fname(opts.data)
    ddir = data_dir / data
    tdir = ddir / opts.subdir

    seed = init_rng(rng_seed(), 'split-ratings', data, opts.subdir)
    _log.info('using random seed %s', seed)

    _log.info('reading ratings')
    ratings = pd.read_parquet(ddir / 'ratings.parquet')
    _log.info('counting users in %d ratings', len(ratings))
    users = ratings.groupby('user')['item'].count()
    candidates = users[users >= opts.min_ratings]

    _log.info('selecting %d of %d candidate users (%d total)',
              opts.test_users, len(candidates), len(users))
    sample = candidates.sample(opts.test_users, random_state=rng(legacy=True))

    _log.info('selecting test ratings')
    u_rates = ratings[ratings['user'].isin(sample.index)]
    test = u_rates.groupby('user').apply(lambda df: df.sample(1))
    test.reset_index('user', drop=True, inplace=True)

    _log.info('writing %d test ratings', len(test))
    test.to_parquet(tdir / 'test-ratings.parquet', compression='snappy')


if __name__ == '__main__':
    opts = SplitOptions(__doc__)
    split(opts)

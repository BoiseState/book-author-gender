"""
Split rating data into train and test sets.

Usage:
    split_ratings.py [options] DATASET

Options:
    --test-users N
        The number of test users to sample [default: 5000]
    -d, --subdir DIR
        The subdirectory to use [default: tuning]
    DATASET
        The name of the data set to prepare.
"""

from docopt import docopt

from bookgender.logutils import start_script
from bookgender.config import data_dir
import bookgender.datatools as dt

import pandas as pd

SAMPLE_MIN_RATINGS = 5

_log = start_script(__file__)


def split(dataset, test_users, sub):
    data = dt.fname(dataset)
    ddir = data_dir / data
    tdir = ddir / sub

    _log.info('reading ratings')
    ratings = pd.read_parquet(ddir / 'ratings.parquet')
    _log.info('counting users in %d ratings', len(ratings))
    users = ratings.groupby('user')['item'].count()
    candidates = users[users >= SAMPLE_MIN_RATINGS]

    _log.info('selecting %d of %d candidate users (%d total)',
              test_users, len(candidates), len(users))
    sample = candidates.sample(test_users)

    _log.info('selecting test ratings')
    u_rates = ratings[ratings['user'].isin(sample.index)]
    test = u_rates.groupby('user').apply(lambda df: df.sample(1))
    test.reset_index('user', drop=True, inplace=True)
    
    _log.info('selecting train ratings')
    ratings['test'] = False
    ratings.loc[test.index, 'test'] = True
    assert sum(ratings['test']) == len(test)
    train = ratings[~ratings['test']]
    train = train.drop(columns=['test'])
    assert len(train) + len(test) == len(ratings)

    _log.info('writing %d training ratings', len(train))
    train.to_parquet(tdir / 'train-ratings.parquet', compression='snappy',
                     index=False)
    train.to_csv(tdir / 'train-ratings.csv.gz', index=False)

    _log.info('writing %d test ratings', len(test))
    test.to_parquet(tdir / 'test-ratings.parquet', compression='snappy',
                    index=False)
    test.to_csv(tdir / 'test-ratings.csv.gz', index=False)


if __name__ == '__main__':
    args = docopt(__doc__)
    split(args['DATASET'], int(args['--test-users']), args['--subdir'])

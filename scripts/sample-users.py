"""
Sample users, and write the sampled users along with their ratings to the data file.

Usage:
    sample-users.py [options] DATASET

Options:
    -n N
        the number of users to sample [default: 5000].
    --min N
        the minimum number of ratings per viable user [default: 5].
"""

import json

from bookgender.logutils import start_script
from bookgender import datatools as dt
from bookgender.config import db_uri, data_dir, rng_seed
from bookgender.util import OptionReader, get_opt

import pandas as pd
from lenskit.util import init_rng, rng

_log = start_script(__file__)


class SampleOptions(OptionReader):
    data = get_opt('DATASET')
    sample_size = get_opt('-n', int)
    min_ratings = get_opt('--min', int)


def sample(options):
    data = dt.fname(options.data)

    seed = init_rng(rng_seed(), 'sample-users', data)
    _log.info('using random seed %s', seed)

    ds = dt.datasets[data]

    kr_query = f'''
        SELECT r.user_id AS user, COUNT(book_id) AS profile_size
        FROM {ds.table} r
        JOIN cluster_first_author_gender g ON g.cluster = r.book_id
        WHERE gender = 'male' OR gender = 'female'
        GROUP BY r.user_id
        HAVING COUNT(book_id) >= {options.min_ratings}
    '''

    _log.info('loading users for %s', data)
    valid_users = pd.read_sql(kr_query, db_uri())
    _log.info('found %d viable profiles, sampling %d',
              len(valid_users), options.sample_size)
    sample = valid_users.sample(options.sample_size, random_state=rng(legacy=True))

    ddir = data_dir / data

    u_fn = ddir / 'sample-users.csv'
    _log.info('writing %s', u_fn)
    sample.to_csv(ddir / 'sample-users.csv', index=False)

    ratings = pd.read_parquet(ddir / 'ratings.parquet')
    ratings = pd.merge(sample[['user']], ratings)
    r_fn = ddir / 'sample-ratings.csv'
    _log.info('writing %d ratings to %s', len(ratings), r_fn)
    ratings.to_csv(r_fn, index=False)

    s_fn = ddir / 'sample-stats.json'
    _log.info('writing stats to %s', s_fn)
    s_fn.write_text(json.dumps({
        'viable': len(valid_users),
        'sampled': options.sample_size,
        'ratings': len(ratings)
    }))


if __name__ == '__main__':
    sample(SampleOptions(__doc__))

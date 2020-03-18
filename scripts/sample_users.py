"""
Sample users, and write the sampled users along with their ratings to the data file.

Usage:
  sample_users.py <dataset>
"""
import logging
import json

from docopt import docopt

from bookgender.logutils import start_script
from bookgender import datatools as dt
from bookgender.config import db_uri, data_dir

import pandas as pd

SAMPLE_SIZE = 1000
SAMPLE_MIN_RATINGS = 5

_log = start_script(__file__)


def sample(data):
    data = dt.fname(data)
    ds = dt.datasets[data]

    kr_query = f'''
        SELECT r.user_id AS user, COUNT(book_id) AS profile_size
        FROM {ds.table} r
        JOIN cluster_first_author_gender g ON g.cluster = r.book_id
        WHERE gender = 'male' OR gender = 'female'
        GROUP BY r.user_id
        HAVING COUNT(book_id) >= {SAMPLE_MIN_RATINGS}
    '''

    _log.info('loading users for %s', data)
    valid_users = pd.read_sql(kr_query, db_uri())
    _log.info('found %d viable profiles, sampling %d', 
              len(valid_users), SAMPLE_SIZE)
    sample = valid_users.sample(SAMPLE_SIZE)

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
    s_fn.write_text(json.dumps({'viable': len(valid_users), 'sampled': SAMPLE_SIZE, 'ratings': len(ratings)}))


if __name__ == '__main__':
    args = docopt(__doc__)
    sample(args['<dataset>'])
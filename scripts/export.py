"""
Export general data from the database.

Usage:
    export.py --authors
    export.py --book-hashes
    export.py --ratings DATASET
    export.py --loc-books
"""

from docopt import docopt
import pandas as pd

from bookgender.logutils import start_script
from bookgender.config import data_dir, db_uri
import bookgender.datatools as dt

_log = start_script(__file__)


def export_authors():
    query = f'''
        SELECT cluster AS item, gender
        FROM cluster_first_author_gender
        ORDER BY cluster
    '''
    _log.info('reading author genders')
    gender = pd.read_sql(query, db_uri())
    csv_fn = data_dir / 'author-gender.csv.gz'
    pq_fn = data_dir / 'author-gender.parquet'
    _log.info('writing CSV to %s', csv_fn)
    gender.to_csv(csv_fn, index=False)
    _log.info('writing parquet to %s', pq_fn)
    gender.to_parquet(pq_fn, index=False, compression='snappy')


def export_book_hashes():
    query = f'''
        SELECT cluster AS item, COUNT(isbn) AS nisbns,
            MD5(STRING_AGG(isbn, '|' ORDER BY isbn))
        FROM isbn_cluster JOIN isbn_id USING (isbn_id)
        GROUP BY cluster
    '''
    _log.info('reading book ID hashes')
    gender = pd.read_sql(query, db_uri())
    csv_fn = data_dir / 'book-hash.csv.gz'
    pq_fn = data_dir / 'book-hash.parquet'
    _log.info('writing CSV to %s', csv_fn)
    gender.to_csv(csv_fn, index=False)
    _log.info('writing parquet to %s', pq_fn)
    gender.to_parquet(pq_fn, index=False, compression='snappy')


def export_ratings(data):
    "export ratings"
    data = dt.fname(data)
    ds = dt.datasets[data]
    path = data_dir / data / 'ratings'
    columns = ', '.join(ds.columns)

    order = f'{ds.ts_column}, user, item' if ds.ts_column else 'user, item'

    query = f'''
        SELECT user_id AS user, book_id AS item, {columns}
        FROM {ds.table}
        ORDER BY {order}
    '''
    _log.info('reading ratings from %s', ds.table)
    ratings = dt.load_table(query, dtype={
        'user': 'i4',
        'item': 'i4',
        'rating': 'f4',
        'nactions': 'i4'
    })

    path.parent.mkdir(parents=True, exist_ok=True)
    pqf = path.with_suffix('.parquet')
    _log.info('writing ratings to %s', pqf)
    ratings.to_parquet(pqf, index=False)


def export_loc_books():
    "export LOC books"
    query = f'''
        SELECT DISTINCT cluster AS item
        FROM locmds.book_rec_isbn JOIN isbn_cluster USING (isbn_id)
    '''
    _log.info('reading LOC books')
    books = pd.read_sql(query, db_uri())
    csv_fn = data_dir / 'loc-books.csv.gz'
    pq_fn = data_dir / 'loc-books.parquet'
    _log.info('writing CSV to %s', csv_fn)
    books.to_csv(csv_fn, index=False)
    _log.info('writing parquet to %s', pq_fn)
    books.to_parquet(pq_fn, index=False, compression='snappy')


args = docopt(__doc__)

if args['--authors']:
    export_authors()
elif args['--book-hashes']:
    export_book_hashes()
elif args['--ratings']:
    export_ratings(args['DATASET'])
elif args['--loc-books']:
    export_loc_books()

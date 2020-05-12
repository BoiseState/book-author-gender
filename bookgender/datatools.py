"""
Functions for accessing & exporting data.
"""

import sys
import os
import threading
from collections import namedtuple
from contextlib import contextmanager
import logging
import pickle
import copyreg
import zstandard as zstd
import blosc

import numpy as np
import pandas as pd
from psycopg2 import sql, connect

from .config import db_uri

_log = logging.getLogger(__name__)

DS = namedtuple('DS', ['table', 'columns', 'ts_column'])

datasets = {
    'AZ': DS('az.rating', ['rating', 'timestamp'], 'timestamp'),
    'BX-E': DS('bx.rating', ['rating'], None),
    'BX-I': DS('bx.add_action', ['nactions'], None),
    'GR-E': DS('gr.rating', ['rating', 'timestamp'], 'timestamp'),
    'GR-I': DS('gr.add_action', ['nactions', 'first_time', 'last_time'], 'first_time')
}


def fname(name):
    "Normalize a data set name for file path use."
    return name.upper()


def pyname(name):
    "Normalize a data set name for use as a Python object name."
    return name.lower().replace('-', '_')


def afname(name):
    "Normalize an algorithm name for use in a file path"
    return name.replace('_', '-')


@contextmanager
def zstd_write(fn):
    zs = zstd.ZstdCompressor()
    with open(fn, 'wb') as rawf:
        with zs.stream_writer(rawf) as zf:
            yield zf


@contextmanager
def zstd_read(fn):
    zs = zstd.ZstdDecompressor()
    with open(fn, 'rb') as rawf:
        with zs.stream_reader(rawf) as zf:
            yield zf


def np_f64(array):
    return np.require(array, 'float64')


def np_rebuild(blocks, axis, dtype):
    blocks = [blosc.unpack_array(b) for b in blocks]
    if len(blocks) == 1:
        array = blocks[0]
    else:
        array = np.concatenate(blocks, axis=axis)
    if dtype:
        return np.require(array, dtype)
    else:
        return array


def _split_array(array, axis, blocks=None):
    lim = 2048 * 1024 * 512
    if blocks is None:
        blocks = []

    if array.nbytes > lim:
        for piece in np.array_split(array, 2, axis=axis):
            _split_array(piece, axis, blocks)
    else:
        blocks.append(array)
    return blocks


def numpy_reduce(array):
    _log.debug('saving array of shape %s', (array.shape,))
    dtype = None
    if array.dtype == 'float64':
        dtype = 'float64'
        array = array.astype('float32')

    axis = 0
    for ax in range(1, array.ndim):
        if array.shape[ax] > array.shape[axis]:
            axis = ax
    blocks = _split_array(array, axis)

    def pack(a):
        ac = blosc.pack_array(a, 5, cname='zstd')
        _log.debug('compressed %d -> %d (%.2f)', a.nbytes, len(ac), len(ac) / a.nbytes * 100)
        return ac

    blocks = [pack(b) for b in blocks]
    return (np_rebuild, (blocks, axis, dtype))


class CompactingPickler(pickle.Pickler):
    dispatch_table = copyreg.dispatch_table.copy()
    dispatch_table[np.ndarray] = numpy_reduce


class _LoadThread(threading.Thread):
    """
    Thread worker for copying database results to a stream we can read.
    """
    def __init__(self, dbc, query, dir='out'):
        super().__init__()
        self.database = dbc
        self.query = query
        rfd, wfd = os.pipe()
        self.reader = os.fdopen(rfd)
        self.writer = os.fdopen(wfd, 'w')
        self.chan = self.writer if dir == 'out' else self.reader

    def run(self):
        with self.chan, self.database.cursor() as cur:
            cur.copy_expert(self.query, self.chan)


def load_table(query, **kwargs):
    """
    Load a table from PostgreSQL using the CSV reader.  This is often more
    efficient than using Pandas read_sql().
    """
    cq = sql.SQL('COPY ({}) TO STDOUT WITH CSV HEADER')
    q = sql.SQL(query)
    dbc = connect(db_uri())
    try:
        dbc.autocommit = True
        thread = _LoadThread(dbc, cq.format(q))
        thread.start()
        data = pd.read_csv(thread.reader, **kwargs)
        thread.join()
    finally:
        dbc.close()
    return data

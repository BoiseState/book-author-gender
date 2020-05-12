from os import fspath
import logging

import tables
from lenskit.util.random import derive_seed

_log = logging.getLogger(__name__)


def write_samples(path, samples, title=None, **extra):
    path = fspath(path)

    _log.info('saving samples to %s', path)
    with tables.File(path, 'w', title=title) as h5:
        sg = h5.create_group(h5.root, 'samples')
        comp = tables.Filters(complib='blosc:snappy')
        for k, v in samples.items():
            h5.create_carray(sg, k, obj=v, filters=comp)

        for k, v in extra.items():
            h5.create_array(h5.root, k, obj=v)


def stan_seed(*keys):
    seed = derive_seed(*keys)
    stan_seed = seed.generate_state(1)[0] & 0x80000000  # put in range of int
    _log.info('using random seed %s (from %s)', stan_seed, seed)

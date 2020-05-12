"""
Inspect a model file.

Usage:
    inspect-model.py [options] FILE

Options:
    -v, --verbose
        Print debug-level log messages.
"""

from pathlib import Path
import logging
from docopt import docopt
from natural.size import binarysize
import pickle
import pickle5
import gc
import resource
import zlib
import msgpack
import blosc
import struct

import numcodecs as nc
import numpy as np

from lenskit.util import Stopwatch

from bookgender.logutils import start_script
from bookgender.util import OptionReader, get_opt


class InspectOpts(OptionReader):
    verbose = get_opt('--verbose')
    path = get_opt('FILE', Path)


class PBJar:
    SLICE_SIZE = 1024 * 1024 * 1024

    def __init__(self):
        self.buffers = []
        self.encoded = []

    def __call__(self, buf):
        rb = buf.raw()
        blen = rb.nbytes
        _log.info('pickling buffer of size %s (%s)', blen, binarysize(blen))
        _log.debug('obj: %s', type(rb.obj))
        if hasattr(rb.obj, 'dtype'):
            _log.debug('dtype: %s', rb.obj.dtype)
        if hasattr(rb.obj, 'shape'):
            _log.debug('shape: %s', rb.obj.shape)
        _log.debug('itemsize: %d', rb.itemsize)
        self.buffers.append(buf)

        sz = rb.itemsize
        if hasattr(rb.obj, 'dtype'):
            sz = rb.obj.dtype.itemsize

        p = msgpack.Packer(autoreset=False)
        starts = list(range(0, blen, self.SLICE_SIZE))
        p.pack_array_header(len(starts))
        for start in starts:
            end = min(start + self.SLICE_SIZE, blen)
            comp = blosc.compress(rb[start:end], typesize=sz, clevel=5, cname='zstd', shuffle=blosc.BITSHUFFLE)
            p.pack(comp)

        enc = p.bytes()
        _log.info('encoded to %d bytes (%s)', len(enc), binarysize(len(enc)))
        self.encoded.append(enc)

    def codecs(self, obj):
        codecs = []
        if obj.dtype == np.float64:
            codecs.append(nc.AsType('f4', 'f8'))
        codecs.append(nc.Blosc('zstd', 5))
        return codecs

    def total_size(self):
        return sum(b.raw().nbytes for b in self.buffers)

    def encoded_size(self):
        return sum(len(b) for b in self.encoded)


def inspect(opts):
    _log.info('inspecting file %s', opts.path)
    stat = opts.path.stat()
    _log.info('file size: %s (%s)', stat.st_size, binarysize(stat.st_size))

    timer = Stopwatch()
    with opts.path.open('rb') as f:
        model = pickle.load(f)
    timer.stop()
    gc.collect()
    res = resource.getrusage(resource.RUSAGE_SELF)
    _log.info('loaded model in %s', timer)
    _log.info('max RSS %s', binarysize(res.ru_maxrss * 1024))

    bufs = PBJar()
    timer = Stopwatch()
    p_bytes = pickle5.dumps(model, protocol=5, buffer_callback=bufs)
    timer.stop()
    bsize = bufs.total_size()
    _log.info('pickled to %d bytes in %s', len(p_bytes), timer)
    _log.info('with %d bytes of buffers', bsize)
    _log.info('total size: %s', binarysize(len(p_bytes) + bsize))
    _log.info('compresses to: %s', binarysize(len(p_bytes) + bufs.encoded_size()))


if __name__ == '__main__':
    opts = InspectOpts(__doc__)
    _log = start_script(__file__, opts.verbose)
    inspect(opts)
else:
    _log = logging.getLogger(__name__)

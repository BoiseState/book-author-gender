"""
Recommender operations for the project.
"""

import logging
import importlib
import json

from . import datatools as dt

_log = logging.getLogger(__name__)


def get_algorithm(data, algo, opt_f=None, implicit=False):
    algo = dt.pyname(algo)
    amod = importlib.import_module(f'bookgender.algorithms.{algo}')

    if opt_f:
        _log.info('reading opt results from %s', opt_f)
        ores = json.loads(opt_f.read_text())
        return amod.instantiate(ores['params'], implicit)
    else:
        _log.info('using default algorithm %s', amod.default(implicit))
        return amod.default(implicit)

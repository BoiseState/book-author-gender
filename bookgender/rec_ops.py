"""
Recommender operations for the project.
"""

import logging
import importlib
from pathlib import Path
import pickle
import json

import pystache

import numpy as np
import pandas as pd

from lenskit import batch, topn
from lenskit.algorithms import Recommender
from . import datatools as dt
from . import config, logutils, util

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

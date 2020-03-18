"""
Code for optimizing the item-item algorithm.
"""

import sys
import os
import logging
from copy import copy
import tempfile

import pathlib
from skopt.space import Integer, Real

import numpy as np
import joblib

from lenskit.matrix import CSR
from lenskit import util
from lenskit.algorithms.item_knn import ItemItem
from lenskit.algorithms.basic import TopN, UnratedItemCandidateSelector

_log = logging.getLogger(__name__)

dimensions = [Integer(5, 250), Real(0, 0.1)]


def instantiate(opts, implicit):
    nnbrs, smin = opts
    if implicit:
        return ItemItem(nnbrs, min_sim=smin, save_nbrs=10000,
                        aggregate='sum', center=False)
    else:
        return ItemItem(nnbrs, min_sim=smin, save_nbrs=10000)


def default(implicit):
    if implicit:
        return ItemItem(20, save_nbrs=10000,
                        aggregate='sum', center=False)
    else:
        return ItemItem(20, save_nbrs=10000)


class Retrainer:
    """
    Exploit internal model structures and relationships to reduce retrain cost for item-item k-NN
    search process.
    """
    def __init__(self, implicit):
        self.initial = default(implicit)
        self.initialized = False
        self.selector = UnratedItemCandidateSelector()

    def fit_initial(self, ratings):
        _log.info('fitting initial model %s', self.initial)
        self.initial.fit(ratings)
        fd, path = tempfile.mkstemp(prefix='lkpy-predict', suffix='.pkl',
                                    dir=util.scratch_dir(joblib=True))
        self.path = pathlib.Path(path)
        os.close(fd)

        del self.initial._sim_inv_
        _log.info('persisting initial model file to shared memory')
        joblib.dump(self.initial.sim_matrix_, path)
        self.initial.sim_matrix_ = joblib.load(path)

        self.selector.fit(ratings)
        self.initialized = True

    def instantiate(self, opts):
        nnbrs, smin = opts
        model = copy(self.initial)
        _log.info('updating model to use %d sims', nnbrs)
        model.nnbrs = nnbrs

        keep = model.sim_matrix_.values >= smin

        _log.info('trimming model to keep %d sims', np.sum(keep))
        model.sim_matrix_ = model.sim_matrix_.filter_nnzs(keep)
        model._sim_inv_ = model.sim_matrix_.transpose()

        return TopN(model, self.selector)

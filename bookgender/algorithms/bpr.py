"""
Code for optimizing the item-item algorithm.
"""

from skopt.space import Integer, Real
from lenskit.algorithms.implicit import BPR
from bookgender.config import have_gpu

dimensions = [Integer(5, 250), Real(0, 0.25), Real(0, 0.1)]


def instantiate(opts, implicit):
    feats, reg, lrate = opts
    return BPR(feats, regularization=reg, learning_rate=lrate)


def default(implicit):
    return BPR(50)


update = None


sweep_points = [BPR(factors=nf, use_gpu=have_gpu()) for nf in range(25, 250, 25)]
sweep_attrs = ['factors']

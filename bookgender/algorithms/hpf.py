"""
Code for optimizing the item-item algorithm.
"""

from skopt.space import Integer, Real
from lenskit.algorithms.hpf import HPF
from bookgender.config import have_gpu


dimensions = [Integer(5, 500), Real(0.01,1), Real(0.01,1), Real(0.01,1), Real(0.01,1)]


def instantiate(opts, implicit):
    feats, a, ap, c, cp = opts
    feats = int(feats)
    return HPF(feats, a=a, a_prime=ap, c=c, c_prime=cp)


update = None

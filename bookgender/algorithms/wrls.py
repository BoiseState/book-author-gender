"""
Code for optimizing the implicit ALS algorithm.
"""

from skopt.space import Integer, Real
from lenskit.algorithms.als import ImplicitMF

dimensions = [Integer(5, 500), Real(1.0e-6, 5), Real(1.0e-6, 5), Real(1, 50)]


def instantiate(opts, implicit):
    feats, ureg, ireg, weight = opts
    return ImplicitMF(feats, reg=(ureg, ireg), weight=weight)


def default(implicit):
    return ImplicitMF(50)


update = None

sweep_points = [ImplicitMF(nf) for nf in range(25, 250, 25)]
sweep_attrs = ['features']

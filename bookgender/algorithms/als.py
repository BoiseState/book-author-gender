"""
Code for optimizing the explicit ALS algorithm.
"""

from skopt.space import Integer, Real
from lenskit.algorithms.als import BiasedMF

dimensions = [Integer(5, 300), Real(1.0e-6, 5), Real(1.0e-6, 5), Real(0, 25)]


def instantiate(opts, implicit):
    feats, ureg, ireg, damp = opts
    return BiasedMF(feats, reg=(ureg, ireg), damping=damp)


def default(implicit):
    return BiasedMF(50)


update = None

sweep_points = [BiasedMF(nf) for nf in range(25, 250, 25)]
sweep_attrs = ['features']

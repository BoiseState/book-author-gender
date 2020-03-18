"""
Code for a gender balanced  explicit ALS algorithm.
"""

from skopt.space import Integer, Real
from lenskit.algorithms.als import BiasedMF

from bookgender.rerank.GenderCalibratedRecommender import GenderCalibratedRecommender
from bookgender.rerank.fastForceGenderBalanceRecommender import FastForceGenderBalanceRecommender
from bookgender.rerank.rerankUtil import getBookGender
from bookgender.rerank.slowForceGenderBalanceRecommender import SlowForceGenderBalanceRecommender
from bookgender.rerank.slowForceGenderTargetRecommender import SlowForceGenderTargetRecommender

dimensions = [Integer(5, 300), Real(1.0e-6, 5), Real(1.0e-6, 5), Real(0, 25)]


def instantiate(opts, implicit):
    feats, ureg, ireg, damp = opts
    return GenderCalibratedRecommender(BiasedMF(feats, reg=(ureg, ireg), damping=damp), getBookGender(), 0.5)
    #return SlowForceGenderTargetRecommender(BiasedMF(feats, reg=(ureg, ireg), damping=damp), getBookGender())


update = None

sweep_points = [BiasedMF(nf) for nf in range(25, 250, 25)]
sweep_attrs = ['features']

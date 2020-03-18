"""
Code for optimizing the item-item algorithm.
"""

from skopt.space import Integer, Real
from lenskit.algorithms.user_knn import UserUser

dimensions = [Integer(5, 500), Real(0, 0.1)]


def instantiate(opts, implicit):
    nnbrs, smin = opts
    if implicit:
        return UserUser(nnbrs, min_sim=smin,
                        aggregate='sum', center=False)
    else:
        return UserUser(nnbrs, min_sim=smin)


def default(implicit):
    if implicit:
        return UserUser(30, aggregate='sum', center=False)
    else:
        return UserUser(30)


update = None

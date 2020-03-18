from .fastForceGenderBalanceRecommender import FastForceGenderBalanceRecommender
from .slowForceGenderBalanceRecommender import SlowForceGenderBalanceRecommender
from .slowForceGenderTargetRecommender import SlowForceGenderTargetRecommender
from .GenderCalibratedRecommender import GenderCalibratedRecommender

__all__ = ['SingleEQ', 'GreedyEQ', 'GreedyReflect']


def SingleEQ(predictor, genders):
    return FastForceGenderBalanceRecommender(predictor, genders)


def GreedyEQ(predictor, genders):
    return SlowForceGenderBalanceRecommender(predictor, genders)


def GreedyReflect(predictor, genders):
    return SlowForceGenderTargetRecommender(predictor, genders)


def CALIBRATE(predictor, genders):
    return GenderCalibratedRecommender(predictor, genders, 0.85)

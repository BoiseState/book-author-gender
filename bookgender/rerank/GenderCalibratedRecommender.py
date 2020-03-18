import time
from math import log

from lenskit.algorithms import Predictor, Recommender, CandidateSelector
from lenskit.algorithms.basic import UnratedItemCandidateSelector
import pandas as pd
import numpy as np

MALE = "male"
FEMALE = "female"
UNKNOWN = "unknown"

class GenderCalibratedRecommender(Recommender):
    """
    Recommends TopN Items such that each gender has (within +/- 1 of the exact same number of recommendations)
    This is done in O(k) passes of the scored items garunteeing that the top-ranked male- and female-authored books are returned

    Args:
        predictor(Predictor):
            The underlying predictor.
        selector(CandidateSelector):
            The candidate selector.  If ``None``, uses :class:`UnratedItemCandidateSelector`.
        genders(Pandas Series, index is items, values is gender strings.)
            A data structure for looking up gender categories for items.
    """

    def __init__(self, predictor, genders, calibrationFactor, alpha=0.1, selector=None):
        self.predictor = predictor
        self.genders = genders
        self.genders.name = 'gender'
        self.genders.index.name = 'item'
        self.genders.sort_index(inplace=True)
        self.calibrationFactor = calibrationFactor
        self.alpha = alpha
        self.inputGenderBalance = None

        self.selector = selector if selector is not None else UnratedItemCandidateSelector()

    def fit(self, ratings, *args, fit_pred=True, **kwargs):
        """
        Fit the recommender.
        Args:
            ratings(pandas.DataFrame):
                The rating or interaction data.  Passed changed to the predictor and
                candidate selector. This class itself does not need fitting, if the base predictor and selector are fit,
                this does not need to be called.
            args, kwargs:
                Additional arguments for the predictor to use in its training process.
        """
        self.inputGenderBalance = self._computeInputGenderBalance(ratings)
        if fit_pred:
            self.predictor.fit(ratings, *args, **kwargs)
        self.selector.fit(ratings)
        return self

    def recommend(self, user, n=None, candidates=None, ratings=None):
        if candidates is None:
            candidates = self.selector.candidates(user, ratings)

        scores = self.predictor.predict_for_user(user, candidates, ratings)

        if n is None:
            # TODO: Probably not the right error. However, this recommender is 100% meaningless in "recommend all movies" context.
            raise NotImplementedError()

        scores.sort_index(inplace=True)
        scores.name = 'score'
        scores.index.name = 'item'
        scores = pd.DataFrame({'score': scores}).join(self.genders, how='left')
        # scores = pd.concat([scores, self.genders], axis=1).reset_index()

        # remove na
        # scores = scores.to_frame()
        scores.dropna(subset=["score"], inplace=True)
        # insert unknowns for gender if necisary
        scores.fillna(UNKNOWN, inplace=True)
        # sort by score
        scores.sort_values("score", ascending=False, inplace=True)

        keepers = []
        u=0
        m=0
        f=0
        userRow = self._getRowforUser(user)

        while len(keepers) < n:
            next = self.pickNext(scores, keepers, userRow, m, f, u)
            keepers.append(next)
            gender = scores['gender'].at[next]
            if MALE == gender:
                m = m + 1
            elif FEMALE == gender:
                f = f + 1
            else:
                u = u + 1
        return scores.loc[keepers].reset_index()

    def __str__(self):
        return 'SlowForceGenderTarget/' + str(self.predictor)

    def __getstate__(self):
        return {
            'predictor': self.predictor,
            'selector': self.selector,
            'g_idx': self.genders.index.values,
            'g_vals': self.genders.values,
            'ifb': self.inputGenderBalance.to_dict(),
            'calFact': self.calibrationFactor,
            'alpha': self.alpha
        }

    def __setstate__(self, state):
        self.predictor = state['predictor']
        self.selector = state['selector']
        self.calibrationFactor = state['calFact']
        self.alpha = state['alpha']

        # disconnect from underlying read-only storage because yuck
        self.genders = pd.Series(state['g_vals'].copy(), index=state['g_idx'].copy())
        self.genders.name = 'gender'
        self.genders.index.name = 'item'

        self.inputGenderBalance = pd.DataFrame.from_dict(state['ifb'])

    def pickNext(self, scores, keepers, userRow, nm, nf, nu):
        pmu = userRow['pMale']
        pfu = userRow['pFemale']
        puu = userRow['pUnknonw']

        scores['lnm'] = nm
        scores['lnf'] = nf
        scores['lnu'] = nu
        scores.loc[scores['gender'] == MALE, 'lnm'] += 1
        scores.loc[scores['gender'] == FEMALE, 'lnf'] += 1
        scores.loc[scores['gender'] == UNKNOWN, 'lnu'] +=1

        scores['qmu'] = scores['lnm']/(nm+nf+nu+1)
        scores['qfu'] = scores['lnf']/(nm+nf+nu+1)
        scores['quu'] = scores['lnu']/(nm+nf+nu+1)

        scores['calibrationM'] = pmu * np.log(pmu / ((1-self.alpha) * scores['qmu'] + self.alpha * pmu))
        scores['calibrationF'] = pfu * np.log(pfu / ((1-self.alpha) * scores['qfu'] + self.alpha * pfu))
        scores['calibrationU'] = puu * np.log(puu / ((1-self.alpha) * scores['quu'] + self.alpha * puu))
        scores['calibration'] = self.calibrationFactor * (scores['calibrationM'] + scores['calibrationF'] + scores['calibrationU'])

        scores['weight'] = (1 - self.calibrationFactor)*scores['score'] - scores['calibration']

        bestitem = 0
        bestScore = -np.infty
        for row in scores.itertuples():
            item = row.Index
            if item in keepers:
                continue
            score = row.score
            if score > bestScore:
                bestScore = score
                bestitem = item
        return bestitem

    def _getRowforUser(self, user):
        return self.inputGenderBalance.loc[user]

    def _computeInputGenderBalance(self, ratings):
        # Ratings is a dataframe. Must have at least `user`, `item`, and `rating` columns.
        ratings.sort_index(inplace=True)
        ratings = ratings.join(self.genders, on='item', how="left")
        ratings.fillna({'gender':UNKNOWN}, inplace=True)

        ratings = ratings.loc[:,['user', 'gender']].pivot_table(index='user', columns="gender", aggfunc=len, fill_value=0)
        ratings.columns = pd.Index(list(ratings.columns))

        # add a pseudo-count of 1 to each count, this damps towards 1/3, 1/3, 1/3, like a dirlichet([1,1,1]) prior
        # important for numerical stability
        ratings[MALE] = ratings[MALE] + 1
        ratings[FEMALE] = ratings[FEMALE] + 1
        ratings[UNKNOWN] = ratings[UNKNOWN] + 1

        ratings['total'] = ratings[FEMALE] + ratings[MALE] + ratings[UNKNOWN]
        ratings['pMale'] = ratings[MALE] / ratings['total']
        ratings['pFemale'] = ratings[FEMALE] / ratings['total']
        ratings['pUnknonw'] = ratings[UNKNOWN] / ratings['total']
        return ratings

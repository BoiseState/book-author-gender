import time

from lenskit.algorithms import Predictor, Recommender, CandidateSelector
from lenskit.algorithms.basic import UnratedItemCandidateSelector
import pandas as pd

MALE = "male"
FEMALE = "female"
UNKNOWN = "unknown"

class FastForceGenderBalanceRecommender(Recommender):
    """
    Recommends TopN Items such that each gender has (within +/- 1 of the exact same number of recommendations)
    This is done in a single pass of the scored items list by discarding any items in ranked order that lead to a major gender imbalance

    Args:
        predictor(Predictor):
            The underlying predictor.
        selector(CandidateSelector):
            The candidate selector.  If ``None``, uses :class:`UnratedItemCandidateSelector`.
        genders(Pandas Series, index is items, values is gender strings.)
            A data structure for looking up gender categories for items.
    """

    def __init__(self, predictor, genders, selector=None):
        self.predictor = predictor
        self.genders = genders
        self.genders.name = 'gender'
        self.genders.index.name = 'item'
        self.genders.sort_index(inplace=True)

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
        if fit_pred:
            self.predictor.fit(ratings, *args, **kwargs)
        self.selector.fit(ratings)
        return self

    def recommend(self, user, n=None, candidates=None, ratings=None):
        #print("ENTERING recommend    "+str(time.time()))
        if candidates is None:
            candidates = self.selector.candidates(user, ratings)

        scores = self.predictor.predict_for_user(user, candidates, ratings)

        if n is None:
            #TODO: Probably not the right error. However, this recommender is 100% meaningless in "recommend all movies" context.
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
        m=0
        f=0

        for row in scores.itertuples():

            item = row.Index
            gender = row.gender
            if MALE == gender and m <= f:
                m = m + 1
                keepers.append(item)
            elif FEMALE == gender and f <= m:
                f = f + 1
                keepers.append(item)
            elif UNKNOWN == gender:
                keepers.append(item)

            if len(keepers) >= n:
                break
        return scores.loc[keepers].reset_index()

    def __str__(self):
        return 'FastForceGenderBalance/' + str(self.predictor)

    def __getstate__(self):
        return {
            'predictor': self.predictor,
            'selector': self.selector,
            'g_idx': self.genders.index.values,
            'g_vals': self.genders.values
        }

    def __setstate__(self, state):
        self.predictor = state['predictor']
        self.selector = state['selector']

        # disconnect from underlying read-only storage because yuck
        self.genders = pd.Series(state['g_vals'].copy(), index=state['g_idx'].copy())
        self.genders.name = 'gender'
        self.genders.index.name = 'item'


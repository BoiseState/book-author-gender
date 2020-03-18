import sys
import os
import logging
from importlib import import_module
import pickle

import pandas as pd
import numpy as np
import skopt

from lenskit.util import Stopwatch
from lenskit import topn, batch
from lenskit.algorithms import Recommender

from .config import proc_count, isolate_search

_log = logging.getLogger(__name__)


class ImprovementStopper(skopt.callbacks.EarlyStopper):
    def __init__(self, frac, n_best=5, min_runs=15):
        self.fraction = frac
        self.n_best = n_best
        self.min_runs = min_runs

    def _criterion(self, result):
        if len(result.func_vals) >= self.min_runs:
            nb = np.sort(result.func_vals)[-self.n_best:]
            b = nb[-1]
            check = nb[0]
            _log.debug('checking %d runs: best=%f, upper=%f', len(result.func_vals), b, check)
            # is it within fraction?
            range = check - b
            return range < np.abs(b) * self.fraction
        else:
            return None


class OptEvaluator:
    def __init__(self, algo_mod, train, test, n=1000):
        self.module = algo_mod
        self.n_jobs = max(proc_count() // 2, 1)
        self.train = train
        self.test = test
        self.n_recs = n
        self.explicit = 'rating' in self.train.columns
        if hasattr(algo_mod, 'Retrainer'):
            self.retrainer = algo_mod.Retrainer(not self.explicit)
        else:
            self.retrainer = None

    def __call__(self, params):
        if isolate_search() and not self.retrainer:
            rd, wr = os.pipe()
            pid = os.fork()
            if pid:
                # we are the parent
                _log.info('evaluating in subprocess %d', pid)
                os.close(wr)
                with open(rd, 'rb') as rd2:
                    rv = pickle.load(rd2)
                _, status = os.waitpid(pid, 0)
                if status:
                    _log.info('child failed with code %d', status)
                return rv
            else:
                # we are the child
                os.close(rd)
                with open(wr, 'wb') as wr2:
                    rv = self._run_eval(params)
                    pickle.dump(rv, wr2)
                sys.exit(0)

        else:
            return self._run_eval(params)

    def _run_eval(self, params):
        timer = Stopwatch()

        _log.info('evaluating at %s', params)

        if self.retrainer:
            if not self.retrainer.initialized:
                self.retrainer.fit_initial(self.train)
            algo = self.retrainer.instantiate(params)
        else:
            algo = self.module.instantiate(params, not self.explicit)
            algo = Recommender.adapt(algo)
            _log.info('[%s] train %s', timer, algo)
            algo.fit(self.train)

        _log.info('[%s] recommend %s', timer, algo)
        users = self.test['user'].unique()
        recs = batch.recommend(algo, users, self.n_recs, n_jobs=self.n_jobs)

        if len(recs) == 0:
            _log.info('[%s] %s produced no recommendations', timer, algo)
            return 0

        _log.info('[%s] evaluate %s', timer, algo)
        rla = topn.RecListAnalysis()
        rla.add_metric(topn.recip_rank)
        rla.add_metric(topn.recall)
        scores = rla.compute(recs, self.test, include_missing=True)
        assert len(scores) == len(self.test)
        mrr = scores['recip_rank'].fillna(0).mean()
        hr = scores['recall'].fillna(0).mean()
        _log.info('%s had MRR of %.3f', algo, mrr)
        _log.info('%s had hit rate of %.3f', algo, hr)
        return -mrr

    def __getstate__(self):
        return {'n_jobs': self.n_jobs, 'module': self.module.__name__}

    def __setstate__(self, state):
        self.n_jobs = state['n_jobs']
        self.module = import_module(state['module'])

"""
The full integrated profile / list model.
"""

import logging
from collections import namedtuple

import pandas as pd
import numpy as np

from lenskit.util import Stopwatch

from .. import datatools as dt
from . import write_samples, stan_seed
from ..config import data_dir

_log = logging.getLogger(__name__)

stan_file = 'full.stan'

DataEnv = namedtuple('DataEnv', ['profiles', 'lists'])

instances = dt.datasets.keys()


def load_data(inst):
    ps = pd.read_pickle(data_dir / 'profile-data.pkl')
    rs = pd.read_pickle(data_dir / 'rec-data.pkl')
    return DataEnv(ps.loc[inst, :], rs.loc[inst, :])


def run_model(model, data, inst, cfg, *, var='gender'):
    """
    Run a STAN model.
    """

    seed = stan_seed(inst, var)

    users = data.profiles.assign(unum=np.arange(len(data.profiles), dtype='i4') + 1)

    lists = data.lists.reset_index()
    lists['Algorithm'] = lists['Algorithm'].astype('category')
    algos = lists['Algorithm'].cat.categories

    lists = lists.join(users[['unum']], on='user')

    _log.info('running full model on %d profiles and %d lists (%d algorithms) for %s',
              len(data.profiles), len(data.lists), len(algos), inst)
    timer = Stopwatch()

    stan_data = {
        'A': len(algos),
        'J': len(users),
        'NL': len(lists),
        'ru': lists['unum'],
        'ra': lists['Algorithm'].cat.codes + 1,
    }
    if var == 'gender':
        stan_data['n'] = users['Known']
        stan_data['y'] = users['female']
        stan_data['rn'] = lists['Known']
        stan_data['ry'] = lists['female']
        out_pfx = 'full'
    elif var == 'dcode':
        stan_data['n'] = users['dcknown']
        stan_data['y'] = users['dcyes']
        stan_data['rn'] = lists['dcknown']
        stan_data['ry'] = lists['dcyes']
        out_pfx = 'full-dcode'
    else:
        raise ValueError(f'unknown variant {var}')

    fit = model.sampling(stan_data, seed=seed, check_hmc_diagnostics=True, **cfg)
    _log.info('full-model sampling for %s finished in %s', inst, timer)
    summary = fit.stansummary(pars=["mu", "sigma", "nMean", "nDisp", "recB", "recS", "recV"])
    print(summary)
    (data_dir / inst / f'{out_pfx}-model.txt').write_text(summary)

    _log.info('extracting samples')
    samples = fit.extract(permuted=True)
    write_samples(data_dir / inst / f'{out_pfx}-samples.h5', samples, algo_names=list(algos))

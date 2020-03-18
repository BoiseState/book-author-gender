"""
The user-profile model.
"""

import logging
from collections import namedtuple
import pickle

import pandas as pd

from lenskit.util import Stopwatch

from .. import datatools as dt
from ..config import data_dir
from . import write_samples

_log = logging.getLogger(__name__)

stan_file = 'profile.stan'

DataEnv = namedtuple('DataEnv', ['profiles'])

instances = dt.datasets.keys()


def load_data(inst):
    return DataEnv(pd.read_pickle(data_dir / 'profile-data.pkl'))


def run_model(model, env, inst, cfg, *, var='gender'):
    """
    Run a STAN model.
    """

    data = env.profiles.loc[inst, :]

    _log.info('running profile model on %d profiles for %s', len(data), inst)
    timer = Stopwatch()

    stan_data = {'J': len(data)}
    if var == 'gender':
        stan_data['n'] = data['Known']
        stan_data['y'] = data['female']
        out_pfx = 'profile'
    elif var == 'dcode':
        stan_data['n'] = data['dcknown']
        stan_data['y'] = data['dcyes']
        out_pfx = 'profile-dcode'
    else:
        raise ValueError(f'unknown variant {var}')

    fit = model.sampling(stan_data, **cfg)
    _log.info('profile sample for %s finished in %s', inst, timer)
    summary = fit.stansummary(pars=["mu", "sigma", "thetaP", "nP", "yP"])
    print(summary)
    (data_dir / inst / f'{out_pfx}-model.txt').write_text(summary)

    _log.info('extracting samples')
    samples = fit.extract(permuted=True)

    write_samples(data_dir / inst / f'{out_pfx}-samples.h5', samples)

    _log.info('pickling model and fit')
    with dt.zstd_write(data_dir / inst / f'{out_pfx}-fit.pkl.zstd') as ff:
        pickle.dump((model, fit), ff, protocol=4)

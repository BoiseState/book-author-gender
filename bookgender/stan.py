"""
Stan utility functions.
"""

import os
import shutil
import logging
import platform
import subprocess as sp
from pathlib import Path

import toml
import cmdstanpy
import zarr
import numcodecs as nc
import pandas as pd
import numpy as np
from scipy.special import logsumexp

from bookgender.config import root_dir

_log = logging.getLogger(__name__)

cfg_file = root_dir / 'stan.toml'
stan_dir = root_dir / 'cmdstan'
tbb_dir = stan_dir / 'stan' / 'lib' / 'stan_math' / 'lib' / 'tbb'
_local_make = stan_dir / 'make' / 'local'

stan_config = '''
CXX_TYPE = gcc
'''

def _coalesce(*args):
    for a in args:
        if a is not None:
            return a


def sample_options(seed, opts):
    stan_seed = seed.generate_state(1)[0] & ~0x80000000  # put in range of int
    _log.info('using random seed %s (from %s)', stan_seed, seed)

    cfg = {}
    if cfg_file.exists():
        _log.info('loading %s', cfg_file)
        cfg = toml.loads(cfg_file.read_text())

    return {
        'seed': int(stan_seed),
        'iter_warmup': _coalesce(getattr(opts, 'warmup', None), cfg.get('warmup', None), 1000),
        'iter_sampling': _coalesce(getattr(opts, 'iters', None), cfg.get('iters', None), 1000),
        'chains': _coalesce(getattr(opts, 'chains', None), cfg.get('chains', None), 4)
    }


def init():
    "Initialize CmdStan and CmdStanPy"
    readme = stan_dir / 'README.md'
    if not readme.exists():
        _log.error('CmdStan not found, is it checked out?')
        _log.info('Try running: git submodule update --init --recursive')
        raise RuntimeError('CmdStan not available')

    _log.info('initializing local settings')
    _local_make.write_text(stan_config)

    stanc = stan_dir / 'bin' / 'stanc'
    make = 'make'
    if platform.system() == 'Windows':
        stanc = stanc.with_suffix('.exe')
        make = 'mingw32-make'  # STAN is picky

    _log.info('making sure CmdStan is compiled')
    sp.run([make, '-j4', 'build'], cwd=stan_dir, check=True)

    res = sp.run([os.fspath(stanc), '--version'], capture_output=True, check=True)
    _log.info('built Stan version %s', res.stdout.decode('utf8').strip())
    cmdstanpy.set_cmdstan_path(os.fspath(stan_dir))


def compile(file, log=None):
    if log is None:
        log = _log
    _log.info('preparing Stan model %s', file)
    mod = cmdstanpy.CmdStanModel(file.stem, file, logger=log, cpp_options={'STAN_THREADS': 'yes'})
    return mod


def save_samples(path, mcmc, title=None):
    path = os.fspath(path)

    names = pd.Series(mcmc.column_names).str.replace(r'\.\d+$', '').unique()
    _log.info('saving %d draws of %d variables to %s',
              mcmc.chains * mcmc.draws, len(names), path)

    comp = nc.Blosc('zstd', 9, shuffle=nc.blosc.BITSHUFFLE)
    with zarr.ZipStore(path) as store:
        g = zarr.group(store)
        for name in names:
            if name.startswith('_') or name == 'log_lik':
                continue  # we don't save names prefixed with _
            draws = mcmc.get_drawset([name])
            nrows, ncols = draws.shape
            if ncols > 1:
                _log.info('saving %d draws of %d-dimensional vector %s', nrows, ncols, name)
                arr = draws.to_numpy()
            else:
                _log.info('saving %d draws of scalar %s', nrows, name)
                arr = draws.to_numpy().reshape(nrows)
            g.array(name, arr, compressor=comp)

        if 'log_lik' in names:
            _log.info('computing LPPD')
            ll = mcmc.get_drawset(['log_lik'])
            draws, dims = ll.shape
            ll_exp = logsumexp(ll, axis=0) - np.log(draws)
            ll_var = np.var(ll, axis=0)
            lppd = np.sum(ll_exp)
            pwaic = np.sum(ll_var)
            _log.info('LPPD=%.2f, pWAIC=%.2f, WAIC=%.2f',
                      lppd, pwaic, -2 * (lppd - pwaic))
            g.array('ll_exp', ll_exp, compressor=comp)
            g.array('ll_var', ll_var, compressor=comp)


def start_compression(out_dir):
    "Start compressing the CSV output files from a STAN run."
    compressors = {}
    for sfile in out_dir.glob('*.csv'):
        compressors[sfile.name] = sp.Popen(['zstd', '-9', '-q', os.fspath(sfile)])
    return compressors


def finish_compression(out_dir, compressors):
    "Finish compressing and clean up."

    for fn, proc in compressors.items():
        _log.debug('waiting for %s', fn)
        proc.wait()
        if proc.returncode != 0:
            _log.error('compression of %s failed with code %d', fn, proc.returncode)
            raise RuntimeError('zstd subprocess failed with code {}'.format(proc.returncode))
        # successfully compressed - remove file
        sfile = out_dir / fn
        _log.debug('removing compressed file %s', sfile)
        sfile.unlink()

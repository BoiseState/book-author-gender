"""
Compiles and runs a STAN model.

Usage:
    stan.py --init
    stan.py --compile MODEL
    stan.py [options] MODEL DATA
    stan.py [options] --joint MODEL

Options:
    --init
        Only initialize, don't do anything else.
    --compile
        Compile the model but don't do anything else.
    -v, --var VARIANT
        The variant to use.
    --chains N
        The number of chains to run.
    -n, --iters N
        The number of iterations to run.
    --warmup N
        The number of warmup iterations to run.
    --input FILE
        The input file to use (defaults to MODEL-inputs.json).

    MODEL
        The model to use.
    DATA
        The data set to operate on.
"""

import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from lenskit.util.random import derive_seed

from bookgender import stan
from bookgender.logutils import start_script
from bookgender.config import data_dir
from bookgender.util import OptionReader, get_opt

_log = start_script(__file__)
mod_dir = Path('models')


class STANOptions(OptionReader):
    init_only = get_opt('--init')
    compile_only = get_opt('--compile')
    joint = get_opt('--joint')
    variant = get_opt('--var')

    chains = get_opt('--chains', int)
    iters = get_opt('--iters', int)
    warmup = get_opt('--warmup', int)
    input = get_opt('--input')

    model = get_opt('MODEL')
    data = get_opt('DATA')

    @property
    def basename(self):
        v = self.variant
        if v:
            return f'{self.model}-{v}'
        else:
            return self.model


def job_template(ds, model, var=None):
    "Step, to be run with --data-args"
    if var is None or var == 'gender':
        base = model
        v_cmd = ''
    else:
        base = f'{model}-{var}'
        v_cmd = ' -v ' + var

    return f'data/{ds}/inference/{base}.dvc', {
        'cmd': f'python -m scripts.stan{v_cmd} {model} {ds}',
        'wdir': '../../..',
        'deps': [
            {'path': 'scripts/stan.py'},
            {'path': 'random.toml'},
            {'path': 'stan.toml'},
            {'path': f'models/{model}.stan'},
            {'path': f'data/{ds}/inference/{base}-inputs.json'}
        ],
        'outs': [
            {'path': f'data/{ds}/inference/{base}'},
            {'path': f'data/{ds}/inference/{base}-summary.csv'},
            {'path': f'data/{ds}/inference/{base}-diag.txt'}
        ]
    }


def joint_template(model):
    "Joint inference step, to be run without arguments"
    return f'data/joint-inference/{model}.dvc', {
        'cmd': f'python -m scripts.stan --joint {model}',
        'wdir': '../..',
        'deps': [
            {'path': 'scripts/stan.py'},
            {'path': 'random.toml'},
            {'path': 'stan.toml'},
            {'path': f'models/joint-{model}.stan'},
            {'path': f'data/joint-inference/{model}-inputs.json'}
        ],
        'outs': [
            {'path': f'data/joint-inference/{model}'},
            {'path': f'data/joint-inference/{model}-summary.csv'},
            {'path': f'data/joint-inference/{model}-diag.txt'}
        ]
    }


def main(opts: STANOptions):
    stan.init()
    if opts.init_only:
        return  # we're done

    keys = ['stan', opts.model]

    if opts.joint:
        inf_dir = data_dir / 'joint-inference'
        mfile = mod_dir / f'joint-{opts.model}.stan'
    else:
        if opts.data:
            inf_dir = data_dir / opts.data / 'inference'
        mfile = mod_dir / f'{opts.model}.stan'
        keys.append(opts.data)

    model = stan.compile(mfile)
    if opts.compile_only:
        return  # we're done

    _log.info('sampling %s on %s (variant %s)', opts.model, opts.data, opts.variant)

    seed = derive_seed(*keys)
    sample_args = stan.sample_options(seed, opts)

    if opts.input:
        input = inf_dir / opts.input
    else:
        input = inf_dir / (opts.basename + '-inputs.json')
    output = inf_dir / opts.basename
    sum_file = inf_dir / (opts.basename + '-summary.csv')
    dia_file = inf_dir / (opts.basename + '-diag.txt')
    draw_file = output / 'samples.zarr'

    _log.info('running %d chains with %d warmup and %d sampling iterations',
              sample_args['chains'], sample_args['iter_warmup'], sample_args['iter_sampling'])
    output.mkdir(exist_ok=True)

    mcmc = model.sample(os.fspath(input), output_dir=os.fspath(output),
                        **sample_args)

    _log.info('starting sample compression')
    comp = stan.start_compression(output)

    with ThreadPoolExecutor() as pool:
        _log.info('spawning summarization process')
        summary = pool.submit(lambda m: m.summary(), mcmc)
        _log.info('spawning diagnostic process')
        diag = pool.submit(lambda m: m.diagnose(), mcmc)

        _log.info('saving model samples')
        stan.save_samples(draw_file, mcmc)

        _log.info('waiting for summary results')
        summary = summary.result()
        _log.info('saving model summary')
        summary.to_csv(sum_file, index=True)

        _log.info('waiting for diagnostic results')
        diag = diag.result()
        _log.info('saving diagnostics')
        dia_file.write_text(diag)

    _log.info('finalizing sample compression')
    stan.finish_compression(output, comp)


if __name__ == '__main__':
    opts = STANOptions(__doc__)
    main(opts)

"""
Bulk-create step files for a script.

Usage:
    make-steps.py --data-algos [options] <script>
    make-steps.py --data-variants [options] <script> <var>...
    make-steps.py [options] <script>

Options:
    --data-algos
        Generate steps for data-algorithm pairs
    --data-variants
        Generate steps for variants for a data set.
    -t, --template <template>
        The name of the template function to use [default: job_template].
    --force
        Overwrite existing step files
"""

from pathlib import Path
import importlib
import yaml

from docopt import docopt

from bookgender import datatools as dt, algorithms
from bookgender.logutils import start_script

_log = start_script(__file__)


def _override_setup(logger=None):
    pass


def _load_template(script, name):
    smod = importlib.import_module(script)
    _log.info('getting template %s.%s', script, name)
    return getattr(smod, name)


def data_steps(data, tmpl, force):
    for algo in algorithms.data_algos[data]:
        fn, step = tmpl(data, algo)
        fn = Path(fn)
        if fn.exists() and not force:
            _log.info('%s already exists', fn)
        else:
            _log.info('writing %s', fn)
            fn.parent.mkdir(exist_ok=True)
            fn.write_text(yaml.dump(step))


def data_algo_steps(template, force):
    for ds in dt.datasets.keys():
        data_steps(ds, template, force)


def data_var_steps(template, force, variants):
    for ds in dt.datasets.keys():
        for var in variants:
            fn, step = template(ds, var)
            fn = Path(fn)
            if fn.exists() and not force:
                _log.info('%s already exists', fn)
            else:
                _log.info('writing %s', fn)
                fn.parent.mkdir(exist_ok=True)
                fn.write_text(yaml.dump(step))


def single_step(template, force):
    fn, step = template()
    fn = Path(fn)
    if fn.exists() and not force:
        _log.info('%s already exists', fn)
    else:
        _log.info('writing %s', fn)
        fn.write_text(yaml.dump(step))


if __name__ == '__main__':
    options = docopt(__doc__)

    if options['--data-algos']:
        template = _load_template(options['<script>'], options['--template'])
        data_algo_steps(template, options['--force'])
    elif options['--data-variants']:
        template = _load_template(options['<script>'], options['--template'])
        data_var_steps(template, options['--force'], options['<var>'])
    else:
        template = _load_template(options['<script>'], options['--template'])
        single_step(template, options['--force'])

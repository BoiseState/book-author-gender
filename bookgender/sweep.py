from pathlib import Path
from os import fspath
import string
import logging

import nbformat
import nbconvert

from . import datatools as dt

_log = logging.getLogger(__name__)


def analyze_sweep(work_dir, name, implicit):
    prefix = 'imp' if implicit else 'exp'
    full_name = f'{prefix}-{name}'
    aname = dt.pyname(name)

    if implicit:
        from .algorithms import implicit_algos as algo_mod
        sfx = '-imp'
    else:
        from .algorithms import explicit_algos as algo_mod
        sfx = ''

    props = {'title': full_name}
    attrs = getattr(algo_mod, f'{aname}_attrs', [])

    _log.info('reading source notebook')
    nbf = nbformat.read('sweep-results/SweepAccuracy.ipynb', as_version=4)
    for cell in nbf.cells:
        lkv = cell.metadata.get('lk_var', None)
        if 'lk_template' in cell.metadata:
            tmpl = string.Template(cell.source)
            cell.source = tmpl.safe_substitute(props)
        elif lkv == 'sweep_name':
            _log.info('using sweep name %s', full_name)
            cell.source = f"sweep_name = '{full_name}'"
        elif lkv == 'attrs':
            _log.info('using attributes %s', attrs)
            cell.source = f"attrs = {repr(attrs)}"
        elif lkv == 'data_sfx':
            cell.source = f"data_sfx = '{sfx}'"

    fn = Path(f'sweep-results/sweep-{full_name}.ipynb')
    _log.info('writing %s', fn)
    nbformat.write(nbf, fspath(fn))

    nbexec = nbconvert.preprocessors.ExecutePreprocessor(timeout=600, kernel_name='python3')
    _log.info('executing notebook %s', fn)
    nbexec.preprocess(nbf, {'metadata': {'path': 'work/'}})
    _log.info('writing executed notebook %s', fn)
    nbformat.write(nbf, fspath(fn))
    
    html_fn = fn.with_suffix('.html')
    _log.info('exporting html to %s', html_fn)
    html_e = nbconvert.HTMLExporter()
    html_e.template_file = 'full'
    body, resources = html_e.from_notebook_node(nbf)
    html_fn.write_text(body)
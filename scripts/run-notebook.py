"""
Re-run a notebook.  This is provided as a convenient wrapper around the
Jupyter APIs.

Usage:
    run-notebook.py [options] FILE

Options:
    --overwrite
            Overwrite the input file with the executed results.
    -p, --param-json FILE
            Load parameters from JSON file FILE
    -o, --output FILE
            Write HTML output to FILE
    -v, --variant VARIANT
            Set the environment variable NB_VARIANT to VARIANT when running
    FILE    The notebook file to run.
"""

from docopt import docopt
import os
from pathlib import Path
import json

import nbformat
from nbconvert.exporters import HTMLExporter

import papermill as pm

from bookgender.logutils import start_script

_log = start_script(__file__)

args = docopt(__doc__)
nbfile = Path(args['FILE'])
tmp_nbf = nbfile.with_suffix('.temp.ipynb')

try:
    pfile = args['--param-json']
    if pfile:
        with open(pfile, 'r') as pf:
            params = json.load(pf)
    else:
        params = {}

    _log.info('executing notebook')
    pm.execute_notebook(os.fspath(nbfile), os.fspath(tmp_nbf), params)

    _log.info('loading %s', tmp_nbf)

    with tmp_nbf.open() as nbf:
        nb = nbformat.read(nbf, as_version=4)

    if args['--output']:
        htmlfile = Path(args['--output'])
    else:
        htmlfile = nbfile.with_suffix('.html')
    _log.info('saving HTML %s', htmlfile)
    htmle = HTMLExporter()
    htmle.template_file = 'full'
    (body, resources) = htmle.from_notebook_node(nb)
    htmlfile.write_text(body)

    if args['--overwrite']:
        _log.info('overwriting %s', nbfile)
        if nbfile.exists():
            nbfile.unlink()
        tmp_nbf.rename(nbfile)

finally:
    if tmp_nbf.exists():
        tmp_nbf.unlink()

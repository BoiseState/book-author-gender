"""
Make a work tree for running experiments.

Usage:
    make_tree.py [-b BRANCH] <tree>

Options:
    -b BRANCH
        The branch to base off of
"""

from docopt import docopt
import logging
import os
import pathlib
import subprocess

from bookgender.logutils import start_script


def init_tree(tree, branch=None):
    repo = pathlib.Path.cwd().absolute()
    _log.info('initializing worktree at %s', tree)
    wt_cmd = ['git', 'worktree', 'add', tree]
    if branch:
        wt_cmd.append(branch)
    subprocess.run(wt_cmd, check=True)
    os.chdir(tree)
    _log.info('using DVC cache from %s', repo)
    subprocess.run(['dvc', 'cache', 'dir', '--local', repo / '.dvc' / 'cache'], check=True)
    subprocess.run(['dvc', 'config', '--local', 'cache.type', 'symlink'], check=True)
    _log.info('checking out DVC results')
    subprocess.run(['dvc', 'checkout'], check=True)


if __name__ == '__main__':
    _log = start_script(__file__)
    options = docopt(__doc__)
    init_tree(options['<tree>'], options['-b'])
else:
    _log = logging.getLogger(__name__)

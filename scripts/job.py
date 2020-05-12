"""
Job runner for batch runs.

Usage:
    job.py [options] ARGS...

Options:
    --no-slack
        Do not post to Slack when completed.
    --retry-dvc
        Re-run DVC if it fails (once).
    --random-sleep
        Randomly sleep before starting (to avoid lock contention)
    --commit
        Commit results to Git when completed.
    -t, --threading LAYER
        Use threading layer LAYER for MKL and Numba.
    --tree-dir DIR
        Run job in separate worktree under DIR. Must not already exist.
"""

import os
import sys
import pathlib
import subprocess
import resource
import requests
import random
import time
from textwrap import dedent
import natural.date

from docopt import docopt

from bookgender.logutils import start_script
from bookgender.config import proc_count
from scripts.make_tree import init_tree

_log = start_script(__file__)


class Notifier:
    def __init__(self, opts):
        self.options = opts
        self.hook_url = os.environ.get('SLACK_WEBHOOK_URL', None)
        self.active = self.hook_url is not None and not opts['--no-slack']
        self.channel = os.environ.get('SLACK_CHANNEL', None)
        self.username = os.environ.get('SLACK_USERNAME', None)
        self.emoji = os.environ.get('SLACK_EMOJI', None)
        self.notify_user = os.environ.get('SLACK_NOTIFY_USER', None)
        if self.notify_user:
            self.tag = f'<{self.notify_user}>, '
        else:
            self.tag = ''
        self.job_name = os.environ.get('SLURM_JOB_NAME', '<unnamed>')
        self.job_id = os.environ.get('SLURM_JOB_ID', '?')

    def notify_start(self, command):
        if not self.active:
            return
        _log.info('posting startup message to Slack')
        requests.post(self.hook_url, json={
            'text': dedent(f'''
                :rocket: {self.tag} we are starting job {self.job_id} ({self.job_name}):
                ```
                {" ".join(command)}
                ```
            '''),
            'channel': self.channel,
            'icon_emoji': self.emoji,
            'username': self.username
        })

    def notify_finish(self):
        if not self.active:
            return
        _log.info('posting completion message to Slack')
        requests.post(self.hook_url, json={
            'text': f':tada: {self.tag} job {self.job_id} ({self.job_name}) completed!',
            'channel': self.channel,
            'icon_emoji': self.emoji,
            'username': self.username
        })

    def notify_fail(self):
        if not self.active:
            return
        _log.info('posting completion message to Slack')
        requests.post(self.hook_url, json={
            'text': f':skull: {self.tag} job {self.job_id} ({self.job_name}) failed',
            'channel': self.channel,
            'icon_emoji': self.emoji,
            'username': self.username
        })


def set_limit(res, soft):
    old_s, old_h = resource.getrlimit(res)
    _log.info('resource %s has soft limit %s (hard %s)', res, old_s, old_h)
    _log.info('changing soft to %s', soft)
    resource.setrlimit(res, (soft, old_h))


def set_limits(options):
    _log.info('setting resource limits')
    set_limit(resource.RLIMIT_AS, resource.RLIM_INFINITY)
    set_limit(resource.RLIMIT_NPROC, 1024)
    # set_limit(resource.RLIMIT_STACK, 64 * 1024 * 1024)


def set_threads(options):
    if 'MKL_NUM_THREADS' not in os.environ:
        _log.info('setting MKL thread count')
        os.environ['MKL_NUM_THREADS'] = str(proc_count())

    if 'NUMBA_NUM_THREADS' not in os.environ:
        _log.info('setting Numba thread count')
        os.environ['NUMBA_NUM_THREADS'] = str(proc_count())

    thread_layer = options['--threading']
    if thread_layer:
        os.environ['MKL_THREADING_LAYER'] = thread_layer
        os.environ['NUMBA_THREADING_LAYER'] = thread_layer


def treeify(options):
    tree_root = options['--tree-dir']
    if tree_root:
        name = os.environ.get('SLURM_JOB_NAME', 'unnamed')
        jid = os.environ.get('SLURM_JOB_ID', 'unknown')
        tree = pathlib.Path(tree_root) / f'{name}-{jid}'
        init_tree(tree)


def run(options, slack):
    cmd = options['ARGS']

    slack.notify_start(cmd)
    start = time.time()
    try:
        _log.info('running command %s', cmd)
        subprocess.run(cmd, check=True)
        _log.info('job succeeded')
        finish = time.time()
        elapsed = finish - start
        use = resource.getrusage(resource.RUSAGE_CHILDREN)
        _log.info('CPU time: %s', natural.date.compress(use.ru_utime + use.ru_stime))
        _log.info('Wall time: %s', natural.date.compress(elapsed))
        slack.notify_finish()
    except subprocess.CalledProcessError as e:
        _log.error('job failed with code %d', e.returncode)
        slack.notify_fail()
        sys.exit(e.returncode)


def commit(options):
    if options['--commit']:
        subprocess.run(['git', 'commit', '-am', f'ran job {os.environ.get("SLURM_JOB_NAME")}'],
                       check=True)


def main():
    options = docopt(__doc__, options_first=True)
    slack = Notifier(options)

    set_limits(options)
    set_threads(options)
    treeify(options)
    if options['--random-sleep']:
        s = random.randint(10, 120)
        _log.info('sleeping for %d seconds', s)
        time.sleep(s)
    run(options, slack)
    commit(options)


if __name__ == '__main__':
    main()

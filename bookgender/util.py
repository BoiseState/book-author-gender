import pathlib
from docopt import docopt

import numpy as np
import pandas as pd


def mtimes(files):
    files = [pathlib.Path(f) for f in files]

    mtimes = [(p.stat().st_mtime if p.exists() else None) for p in files]
    return pd.Series(mtimes, name='mtime', index=files)


class OptionReader:
    def __init__(self, doc):
        self.options = docopt(doc)


def get_opt(key, xf=None):
    def read(self):
        v = self.options[key]
        if xf and v is not None:
            v = xf(v)
        return v
    read.__doc__ = f'Read option {key}'
    return property(read)

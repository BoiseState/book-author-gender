"""
Utility functions for notebooks.
"""

from pathlib import Path
import plotnine as pn

_fig_root = Path('figures')
_fig_dir = _fig_root


class theme_paper(pn.theme_minimal):
    def __init__(self):
        pn.theme_minimal.__init__(self, base_family='Open Sans')
        self.add_theme(pn.theme(
            axis_title=pn.element_text(size=10),
            axis_title_y=pn.element_text(margin={'r': 12}),
            panel_border=pn.element_rect(color='gainsboro', size=1, fill=None)
        ), inplace=True)


def init_figs(name):
    global _fig_dir
    _fig_dir = _fig_root / name
    print('using figure dir', _fig_dir)
    _fig_dir.mkdir(exist_ok=True)
    return _fig_dir


def make_plot(data, aes, *args, file=None, height=5, width=7, theme=theme_paper(), **kwargs):
    plt = pn.ggplot(data, aes)
    for a in args:
        plt = plt + a
    plt = plt + theme + pn.theme(**kwargs)
    if file is not None:
        plt.save(_fig_dir / file, height=height, width=width)
    return plt

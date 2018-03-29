from matplotlib import figure
from matplotlib import axes

import os


def axes_object(ax):
    """ Checks if a value if an Axes. If None, a new one is created.
    Both the figure and axes are returned (in that order).

    """
    if ax is None:
        fig = figure.Figure()
        ax = fig.add_subplot(1, 1, 1)
    elif isinstance(ax, axes.Axes):
        fig = ax.figure
    else:
        msg = "`ax` must be a matplotlib Axes instance or None"
        raise ValueError(msg)

    return fig, ax


def source(source):
    """ checks that a *source* value is valid """
    if source.lower() not in ('wunderground', 'asos', 'wunder_nonairport'):
        raise ValueError('source must be one of "wunderground" or "asos"')
    return source.lower()


def step(step):
    """ checks that a *step* value is valid """
    if step.lower() not in ('raw', 'flat', 'compile'):
        raise ValueError('step must be one of "raw" or "flat"')
    return step.lower()


def file_status(filename):
    """ confirms that a raw file isn't empty """
    if os.path.exists(filename):
        with open(filename, 'r') as testfile:
            line = testfile.readline()

        if line:
            status = 'ok'
        else:
            status = 'bad'

    else:
        status = 'not there'

    return status


def progress_bar(pbar):
    if not pbar:
        def pbar(x):
            return x
    return pbar

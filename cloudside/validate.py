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
    if source.lower() in ("wunderground", "wunder_nonairport"):
        raise NotImplementedError("wunderground support is borked")
    elif source.lower() not in ("asos",):
        raise ValueError('source must now be "asos"')
    return source.lower()


def step(step):
    """ checks that a *step* value is valid """
    if step.lower() not in ("raw", "flat", "compile"):
        raise ValueError('step must be one of "raw" or "flat"')
    return step.lower()


def file_status(filename):
    """ confirms that a raw file isn't empty """
    if os.path.exists(filename):
        with open(filename, "r") as testfile:
            line = testfile.readline()

        if line:
            status = "ok"
        else:
            status = "bad"

    else:
        status = "not there"

    return status


def progress_bar(pbar_fxn, sequence, **kwargs):
    if not pbar_fxn:
        return sequence
    else:
        pbar = pbar_fxn(sequence, **kwargs)
    return pbar


def unique_index(df):
    if df.index.is_unique:
        return df
    else:
        raise ValueError("index is not unique")

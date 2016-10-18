import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import matplotlib.dates as dates
import pandas
import seaborn

__all__ = [
    'hyetograph',
    'rainClock',
    'windRose',
    'psychromograph',
    'temperaturePlot'
]


def _resampler(dataframe, col, freq, how='sum', fillna=None):
    rules = {
        '5min': ('5Min', 'line'),
        '5 min': ('5Min', 'line'),
        '5-min': ('5Min', 'line'),
        '5 minute': ('5Min', 'line'),
        '5-minute': ('5Min', 'line'),
        '15min': ('15Min', 'line'),
        '15 min': ('15Min', 'line'),
        '15-min': ('15Min', 'line'),
        '15 minute': ('15Min', 'line'),
        '15-minute': ('15Min', 'line'),
        '30min': ('30Min', 'line'),
        '30 min': ('30Min', 'line'),
        '30-min': ('30Min', 'line'),
        '30 minute': ('30Min', 'line'),
        '30-minute': ('30Min', 'line'),
        'hour': ('H', 'line'),
        'hourly': ('H', 'line'),
        'day': ('D', 'line'),
        'daily': ('D', 'line'),
        'week': ('W', 'line'),
        'weekly': ('W', 'line'),
        'month': ('M', 'line'),
        'monthly': ('M', 'line')
    }

    if freq not in list(rules.keys()):
        m = ("freq should be in ['5-min', '15-min', 'hourly', 'daily',"
             "'weekly', 'monthly']")
        raise ValueError(m)

    rule = rules[freq.lower()][0]
    plotkind = rules[freq.lower()][1]
    data = dataframe[col].resample(how=how, rule=rule)
    if fillna is not None:
        data.fillna(value=fillna, inplace=True)

    return data, rule, plotkind


def _plotter(dataframe, col, ylabel, freq='hourly', how='sum',
             ax=None, downward=False, fname=None, fillna=None):

    if not hasattr(dataframe, col):
        raise ValueError('input `dataframe` must have a `%s` column' % col)

    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.figure

    data, rule, plotkind = _resampler(dataframe, col, freq=freq, how=how)

    data.plot(ax=ax, kind=plotkind)
    if rule == 'A':
        xformat = dates.DateFormatter('%Y')
        ax.xaxis.set_major_formatter(xformat)
    elif rule == 'M':
        xformat = dates.DateFormatter('%Y-%m')
        ax.xaxis.set_major_formatter(xformat)

    ax.tick_params(axis='x', labelsize=8)
    ax.set_xlabel('Date')
    ax.set_ylabel(ylabel)
    if downward:
        ax.invert_yaxis()

    if fname is not None:
        fig.tight_layout()
        fig.savefig(fname, dpi=300, bbox_inches='tight')

    return fig


def hyetograph(dataframe, freq='hourly', ax=None, downward=True, col='Precip', fname=None):
    ylabel = '%s Rainfall Depth (in)' % freq.title()
    fig = _plotter(dataframe, col, ylabel, freq=freq, fillna=0,
                       how='sum', ax=ax, downward=downward, fname=fname)
    return fig


def psychromograph(dataframe, freq='hourly', ax=None, col='AtmPress', fname=None):
    ylabel = '%s Barometric Pressure (in Hg)' % freq.title()
    fig = _plotter(dataframe, col, ylabel, freq=freq,
                       how='mean', ax=ax, fname=fname)
    return fig


def temperaturePlot(dataframe, freq='hourly', ax=None, col='Temp', fname=None):
    ylabel = u'%s Temperature (\xB0C)' % freq.title()
    fig = _plotter(dataframe, col, ylabel, freq=freq,
                       how='mean', ax=ax, fname=fname)
    return fig


def rainClock(dataframe, raincol='Precip', fname=None):
    '''
    Mathematically dubious representation of the likelihood of rain at
    at any hour given that will rain.
    '''
    if not hasattr(dataframe, raincol):
        raise ValueError('input `dataframe` must have a `%s` column' % raincol)

    rainfall = dataframe[raincol]
    am_hours = np.arange(0, 12)
    am_hours[0] = 12
    rainhours = rainfall.index.hour
    rain_by_hour = []
    for hr in np.arange(24):
        selector = (rainhours == hr)
        total_depth = rainfall[selector].sum()
        num_obervations = rainfall[selector].count()
        rain_by_hour.append(total_depth/num_obervations)

    bar_width = 2*np.pi/12 * 0.8
    fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=(7, 3),
                                   subplot_kw=dict(polar=True))
    theta = np.arange(0.0, 2*np.pi, 2*np.pi/12)
    ax1.bar(theta + 2*np.pi/12 * 0.1, rain_by_hour[:12],
            bar_width, color='DodgerBlue', linewidth=0.5)
    ax2.bar(theta + 2*np.pi/12 * 0.1, rain_by_hour[12:],
            bar_width, color='Crimson', linewidth=0.5)
    ax1.set_title('AM Hours')
    ax2.set_title('PM Hours')
    for ax in [ax1, ax2]:
        ax.set_theta_zero_location("N")
        ax.set_theta_direction('clockwise')
        ax.set_xticks(theta)
        ax.set_xticklabels(am_hours)
        ax.set_yticklabels([])

    if fname is not None:
        fig.tight_layout()
        fig.savefig(fname, dpi=300, bbox_inches='tight')

    return fig


def _speed_labels(bins, units=None):
    if units is None:
        units = ''

    labels = []
    for left, right in zip(bins[:-1], bins[1:]):
        if left == bins[0]:
            labels.append('calm'.format(right))
        elif np.isinf(right):
            labels.append('>{} {}'.format(left, units))
        else:
            labels.append('{} - {} {}'.format(left, right, units))

    return list(labels)


def _dir_degrees_to_radins(directions):
    N = directions.shape[0]
    barDir = directions * np.pi/180. - np.pi/N
    barWidth = 2 * np.pi / N
    return barDir, barWidth


def _compute_windrose(dataframe, speedcol='WindSpd', dircol='WindDir',
                      spd_bins=None, spd_labels=None, spd_units=None,
                      calmspeed=0.1, bin_width=15):

    total_count = dataframe.shape[0]
    calm_count = dataframe[dataframe[speedcol] <= calmspeed].shape[0]

    if spd_bins is None:
        spd_bins = [-1, 0, 5, 10, 20, 30, np.inf]

    if spd_labels is None:
        spd_labels = _speed_labels(spd_bins, units=spd_units)

    dir_bins = np.arange(-0.5 * bin_width, 360 + bin_width * 0.5, bin_width)
    dir_labels = (dir_bins[:-1] + dir_bins[1:]) / 2

    rose = (
        dataframe
            .assign(Spd_bins=pandas.cut(dataframe[speedcol], bins=spd_bins, labels=spd_labels, right=True))
            .assign(Dir_bins=pandas.cut(dataframe[dircol], bins=dir_bins, labels=dir_labels, right=False))
            .replace({'Dir_bins': {360: 0}})
            .groupby(by=['Spd_bins', 'Dir_bins'])
            .size()
            .unstack(level='Spd_bins')
            .fillna(0)
            .assign(calm=lambda df: calm_count / df.shape[0])
            .sort_index(axis=1)
            .applymap(lambda x: x / total_count)
    )

    return rose


def _plot_windrose(rose, ax=None, palette=None, show_legend=True, **other_opts):
    dir_degrees = np.array(rose.index.tolist())
    dir_rads, dir_width = _dir_degrees_to_radins(dir_degrees)

    palette = seaborn.color_palette(palette=palette, n_colors=rose.shape[1])

    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    else:
        fig = ax.figure

    ax.set_theta_direction('clockwise')
    ax.set_theta_zero_location('N')
    ax.yaxis.set_major_formatter(FuncFormatter(_pct_fmt))

    for n, (c1, c2) in enumerate(zip(rose.columns[:-1], rose.columns[1:])):
        if n == 0:
            # first column only
            ax.bar(dir_rads, rose[c1].values,
                   width=dir_width,
                   color=palette[0],
                   edgecolor='none',
                   label=c1,
                   linewidth=0,
                   **other_opts)

        # all other columns
        ax.bar(dir_rads, rose[c2].values,
               width=dir_width,
               bottom=rose.cumsum(axis=1)[c1].values,
               color=palette[n+1],
               edgecolor='none',
               label=c2,
               linewidth=0,
               **other_opts)

    if show_legend:
        leg = ax.legend(
            loc=(0.9, -0.1),
            ncol=1,
            fontsize=8,
            frameon=False
        )
    xtl = ax.set_xticklabels(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'])

    return fig


def windRose(dataframe, speedcol='WindSpd', dircol='WindDir',
             spd_bins=None, spd_labels=None, spd_units=None,
             calmspeed=0.1, bin_width=15, ax=None,
             palette='Blues', show_legend=True, **bar_opts):

    rose = _compute_windrose(dataframe, speedcol=speedcol, dircol=dircol,
                             spd_bins=spd_bins, spd_labels=spd_labels,
                             spd_units=spd_units, calmspeed=calmspeed,
                             bin_width=bin_width)

    return _plot_windrose(rose, ax=ax, palette=palette, show_legend=show_legend, **bar_opts)


def _pct_fmt(x, pos=0):
    return '%0.1f%%' % (100*x)


def _convert_dir_to_left_radian(directions):
    N = directions.shape[0]
    barDir = directions * np.pi/180. - np.pi/N
    barWidth = [2 * np.pi / N]*N
    return barDir, barWidth

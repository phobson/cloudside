import numpy
from matplotlib import pyplot
from matplotlib.ticker import FuncFormatter
from matplotlib.dates import DateFormatter
import pandas


__all__ = [
    'hyetograph',
    'rainClock',
    'windRose',
    'psychromograph',
    'temperaturePlot'
]

DEEPCOLORS = [
    (0.29803921568627451, 0.44705882352941179, 0.69019607843137254),
    (0.33333333333333331, 0.6588235294117647, 0.40784313725490196),
    (0.7686274509803922, 0.30588235294117649, 0.32156862745098042),
    (0.50588235294117645, 0.44705882352941179, 0.69803921568627447),
    (0.80000000000000004, 0.72549019607843135, 0.45490196078431372),
    (0.39215686274509803, 0.70980392156862748, 0.80392156862745101)
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
    data = dataframe[col].resample(rule=rule).apply(how)
    if fillna is not None:
        data.fillna(value=fillna, inplace=True)

    return data, rule, plotkind


def _plotter(dataframe, col, ylabel, freq='hourly', how='sum',
             ax=None, downward=False, fname=None, fillna=None):

    if not hasattr(dataframe, col):
        raise ValueError('input `dataframe` must have a `%s` column' % col)

    if ax is None:
        fig, ax = pyplot.subplots()
    else:
        fig = ax.figure

    data, rule, plotkind = _resampler(dataframe, col, freq=freq, how=how)

    data.plot(ax=ax, kind=plotkind)
    if rule == 'A':
        xformat = DateFormatter('%Y')
        ax.xaxis.set_major_formatter(xformat)
    elif rule == 'M':
        xformat = DateFormatter('%Y-%m')
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
    am_hours = numpy.arange(0, 12)
    am_hours[0] = 12
    rainhours = rainfall.index.hour
    rain_by_hour = []
    for hr in numpy.arange(24):
        selector = (rainhours == hr)
        total_depth = rainfall[selector].sum()
        num_obervations = rainfall[selector].count()
        rain_by_hour.append(total_depth / num_obervations)

    bar_width = 2 * numpy.pi / 12 * 0.8
    fig, (ax1, ax2) = pyplot.subplots(nrows=1, ncols=2, figsize=(7, 3),
                                   subplot_kw=dict(polar=True))
    theta = numpy.arange(0.0, 2 * numpy.pi, 2 * numpy.pi / 12)
    ax1.bar(theta + 2 * numpy.pi / 12 * 0.1, rain_by_hour[:12],
            bar_width, color='DodgerBlue', linewidth=0.5)
    ax2.bar(theta + 2 * numpy.pi / 12 * 0.1, rain_by_hour[12:],
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
        elif numpy.isinf(right):
            labels.append('>{} {}'.format(left, units))
        else:
            labels.append('{} - {} {}'.format(left, right, units))

    return list(labels)


def _dir_degrees_to_radins(directions):
    N = directions.shape[0]
    barDir = (directions * numpy.pi / 180.) - (numpy.pi / N)
    barWidth = 2 * numpy.pi / N
    return barDir, barWidth


def _compute_windrose(dataframe, speedcol='WindSpd', dircol='WindDir',
                      spd_bins=None, spd_labels=None, spd_units=None,
                      calmspeed=0.1, bin_width=15):

    total_count = dataframe.shape[0]
    calm_count = dataframe[dataframe[speedcol] <= calmspeed].shape[0]

    if spd_bins is None:
        spd_bins = [-1, 0, 5, 10, 20, 30, numpy.inf]

    if spd_labels is None:
        spd_labels = _speed_labels(spd_bins, units=spd_units)

    dir_bins = numpy.arange(-0.5 * bin_width, 360 + bin_width * 0.5, bin_width)
    dir_labels = (dir_bins[:-1] + dir_bins[1:]) / 2

    raw_rose = (
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

    # short data records might not be able to fill out all of the speed
    # and direction bins. So we have to make a "complete" template
    # to poputate with the results that we do have
    _rows = pandas.CategoricalIndex(
        data=raw_rose.index.categories.values,
        categories=raw_rose.index.categories,
        ordered=True, name='Dir_bins',
    )
    _cols = pandas.CategoricalIndex(
        data=raw_rose.columns.categories.values,
        categories=raw_rose.columns.categories,
        ordered=True, name='Spd_bins',
    )

    # we'll fill this this template with all zeroes so that we can
    # just add it to out computed rose data.
    rose_template = pandas.DataFrame(0, index=_rows, columns=_cols)

    # .add returns NA where both elements don't exists, so we
    # can just fill all of those with zeros again
    return rose_template.add(raw_rose, fill_value=0)


def _plot_windrose(rose, ax=None, palette=None, show_calm=True, show_legend=True, **other_opts):
    dir_degrees = numpy.array(rose.index.tolist())
    dir_rads, dir_width = _dir_degrees_to_radins(dir_degrees)
    palette = palette or DEEPCOLORS

    if ax is None:
        fig, ax = pyplot.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    else:
        fig = ax.figure

    ax.set_theta_direction('clockwise')
    ax.set_theta_zero_location('N')
    ax.yaxis.set_major_formatter(FuncFormatter(_pct_fmt))

    for n, (c1, c2) in enumerate(zip(rose.columns[:-1], rose.columns[1:])):
        if n == 0 and show_calm:
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
               color=palette[n + 1],
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


def windRose(dataframe, ax=None, speedcol='WindSpd', dircol='WindDir',
             spd_bins=None, spd_labels=None, spd_units=None,
             calmspeed=0.1, bin_width=15, palette=None,
             show_legend=True, show_calm=True, **bar_opts):

    rose = _compute_windrose(dataframe, speedcol=speedcol, dircol=dircol,
                             spd_bins=spd_bins, spd_labels=spd_labels,
                             spd_units=spd_units, calmspeed=calmspeed,
                             bin_width=bin_width)

    fig = _plot_windrose(rose, ax=ax, palette=palette, show_legend=show_legend,
                         show_calm=show_calm, **bar_opts)
    return fig, rose


def _pct_fmt(x, pos=0):
    return '%0.1f%%' % (100 * x)


def _convert_dir_to_left_radian(directions):
    N = directions.shape[0]
    barDir = (directions * numpy.pi / 180.) - (numpy.pi / N)
    barWidth = [2 * numpy.pi / N] * N
    return barDir, barWidth

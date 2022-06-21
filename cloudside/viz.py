import numpy
from matplotlib import figure
from matplotlib import ticker
from matplotlib.ticker import FuncFormatter
from matplotlib.dates import DateFormatter
import pandas

from . import validate


__all__ = ["hyetograph", "rain_clock", "rose", "psychromograph", "temperature"]

DEEPCOLORS = [
    (0.29803921568627451, 0.44705882352941179, 0.69019607843137254),
    (0.33333333333333331, 0.6588235294117647, 0.40784313725490196),
    (0.7686274509803922, 0.30588235294117649, 0.32156862745098042),
    (0.50588235294117645, 0.44705882352941179, 0.69803921568627447),
    (0.80000000000000004, 0.72549019607843135, 0.45490196078431372),
    (0.39215686274509803, 0.70980392156862748, 0.80392156862745101),
]


def _resampler(dataframe, col, freq, how="sum", fillna=None):
    rules = {
        "5min": ("5Min", "line"),
        "5 min": ("5Min", "line"),
        "5-min": ("5Min", "line"),
        "5 minute": ("5Min", "line"),
        "5-minute": ("5Min", "line"),
        "15min": ("15Min", "line"),
        "15 min": ("15Min", "line"),
        "15-min": ("15Min", "line"),
        "15 minute": ("15Min", "line"),
        "15-minute": ("15Min", "line"),
        "30min": ("30Min", "line"),
        "30 min": ("30Min", "line"),
        "30-min": ("30Min", "line"),
        "30 minute": ("30Min", "line"),
        "30-minute": ("30Min", "line"),
        "hour": ("H", "line"),
        "hourly": ("H", "line"),
        "day": ("D", "line"),
        "daily": ("D", "line"),
        "week": ("W", "line"),
        "weekly": ("W", "line"),
        "month": ("M", "line"),
        "monthly": ("M", "line"),
    }

    if freq not in list(rules.keys()):
        m = (
            "freq should be in ['5-min', '15-min', 'hourly', 'daily',"
            "'weekly', 'monthly']"
        )
        raise ValueError(m)

    rule = rules[freq.lower()][0]
    plotkind = rules[freq.lower()][1]
    data = dataframe[col].resample(rule=rule).apply(how)
    if fillna is not None:
        data.fillna(value=fillna, inplace=True)

    return data, rule, plotkind


def _plotter(
    dataframe,
    col,
    ylabel,
    freq="hourly",
    how="sum",
    ax=None,
    downward=False,
    fillna=None,
):

    if not hasattr(dataframe, col):
        raise ValueError("input `dataframe` must have a `%s` column" % col)

    fig, ax = validate.axes_object(ax)

    data, rule, plotkind = _resampler(dataframe, col, freq=freq, how=how)

    data.plot(ax=ax, kind=plotkind)
    if rule == "A":
        xformat = DateFormatter("%Y")
        ax.xaxis.set_major_formatter(xformat)
    elif rule == "M":
        xformat = DateFormatter("%Y-%m")
        ax.xaxis.set_major_formatter(xformat)

    ax.tick_params(axis="x", labelsize=8)
    ax.set_xlabel("Date")
    ax.set_ylabel(ylabel)
    if downward:
        ax.invert_yaxis()

    return fig


def hyetograph(dataframe, col="precipitation", freq="hourly", ax=None, downward=True):
    """Plot showing rainfall depth over time.

    Parameters
    ----------
    dataframe : pandas.DataFrame
        Must have a datetime index.
    col : string, optional (default = 'precip')
        The name of the column in *dataframe* that contains the
        rainall series.
    freq : str, optional (default = 'hourly')
        The frequency to which the rainfall depth should be
        accumulated.
    ax : matplotlib.Axes object, optional
        The Axes on which the plot will be placed. If not provided,
        a new Figure and Axes will be created.
    downward : bool, optional (default = True)
        Inverts the y-axis to show the rainfall depths "falling"
        from the top.

    Returns
    -------
    fig : matplotlib.Figure

    """

    ylabel = "%s Rainfall Depth (in)" % freq.title()
    fig = _plotter(
        dataframe, col, ylabel, freq=freq, fillna=0, how="sum", ax=ax, downward=downward
    )
    return fig


def psychromograph(dataframe, col="air_pressure", freq="hourly", how="mean", ax=None):
    """Plot showing barometric pressure over time.

    Parameters
    ----------
    dataframe : pandas.DataFrame
        Must have a datetime index.
    col : string, optional (default = 'precip')
        The name of the column in *dataframe* that contains the
        barometric pressure series.
    freq : str, optional (default = 'hourly')
        The frequency to which the barometrix pressure should be
        aggregated.
    how : {'mean', 'max', 'min'}, optional (default = 'mean')
        Specifies how the data will be aggregted.
    ax : matplotlib.Axes object, optional
        The Axes on which the plot will be placed. If not provided,
        a new Figure and Axes will be created.

    Returns
    -------
    fig : matplotlib.Figure

    """

    ylabel = "%s Barometric Pressure (in Hg)" % freq.title()
    fig = _plotter(dataframe, col, ylabel, freq=freq, how=how, ax=ax)
    return fig


def temperature(dataframe, col="temperature", freq="hourly", how="mean", ax=None):
    """Plot showing temperature over time.

    Parameters
    ----------
    dataframe : pandas.DataFrame
        Must have a datetime index.
    col : string, optional (default = 'precip')
        The name of the column in *dataframe* that contains the
        temperature series.
    freq : str, optional (default = 'hourly')
        The frequency to which the rainfall depth should be
        accumulated.
    how : {'mean', 'max', 'min'}, optional (default = 'mean')
        Specifies how the data will be aggregted.
    ax : matplotlib.Axes object, optional
        The Axes on which the plot will be placed. If not provided,
        a new Figure and Axes will be created.

    Returns
    -------
    fig : matplotlib.Figure

    """

    ylabel = "%s Temperature (\xB0C)" % freq.title()
    fig = _plotter(dataframe, col, ylabel, freq=freq, how=how, ax=ax)
    return fig


def rain_clock(dataframe, raincol="precip"):
    """Mathematically dubious representation of the likelihood of rain at
    at any hour given that will rain.

    Parameters
    ----------
    dataframe : pandas.DataFrame
    raincol : string, optional (default = 'precip')
        The name of the column in *dataframe* that contains the
        rainfall series.

    Returns
    -------
    fig : matplotlib.Figure

    """

    if not hasattr(dataframe, raincol):
        raise ValueError("input `dataframe` must have a `%s` column" % raincol)

    rainfall = dataframe[raincol]
    am_hours = numpy.arange(0, 12)
    am_hours[0] = 12
    rainhours = rainfall.index.hour
    rain_by_hour = []
    for hr in numpy.arange(24):
        selector = rainhours == hr
        total_depth = rainfall[selector].sum()
        num_obervations = rainfall[selector].count()
        rain_by_hour.append(total_depth / num_obervations)

    bar_width = 2 * numpy.pi / 12 * 0.8

    fig = figure.Figure(figsize=(7, 3))
    ax1 = fig.add_subplot(1, 2, 1, polar=True)
    ax2 = fig.add_subplot(1, 2, 2, polar=True)
    theta = numpy.arange(0.0, 2 * numpy.pi, 2 * numpy.pi / 12)
    ax1.bar(
        theta,
        rain_by_hour[:12],
        bar_width,
        align="center",
        color="DodgerBlue",
        linewidth=0.5,
    )
    ax2.bar(
        theta,
        rain_by_hour[12:],
        bar_width,
        align="center",
        color="Crimson",
        linewidth=0.5,
    )
    ax1.set_title("AM Hours\n")
    ax2.set_title("PM Hours\n")
    for ax in [ax1, ax2]:
        ax.set_theta_zero_location("N")
        ax.set_theta_direction("clockwise")
        ax.set_xticks(theta)
        ax.set_xticklabels(am_hours)
        ax.set_yticklabels([])

    return fig


def _speed_labels(bins, units=None):
    if units is None:
        units = ""

    labels = []
    for left, right in zip(bins[:-1], bins[1:]):
        if left == bins[0]:
            labels.append("calm")
        elif numpy.isinf(right):
            labels.append(">{} {}".format(left, units))
        else:
            labels.append("{} - {} {}".format(left, right, units))

    return list(labels)


def _dir_degrees_to_radins(directions):
    N = directions.shape[0]
    barDir = numpy.deg2rad(directions)
    barWidth = 2 * numpy.pi / N
    return barDir, barWidth


def _compute_rose(
    dataframe,
    magcol,
    dircol,
    spd_bins=None,
    spd_labels=None,
    spd_units=None,
    calmspeed=0.1,
    dir_bins=None,
    bin_width=15,
    dir_labels=None,
    total_count=None,
):

    total_count = total_count or dataframe.shape[0]
    calm_count = dataframe[dataframe[magcol] <= calmspeed].shape[0]

    if spd_bins is None:
        spd_bins = [-1, 0, 5, 10, 20, 30, numpy.inf]

    if spd_labels is None:
        spd_labels = _speed_labels(spd_bins, units=spd_units)

    if dir_bins is None:
        dir_bins = numpy.arange(-0.5 * bin_width, 360 + bin_width * 0.5, bin_width)

    if dir_labels is None:
        dir_labels = (dir_bins[:-1] + dir_bins[1:]) / 2

    raw_rose = (
        dataframe.assign(
            Spd_bins=pandas.cut(
                dataframe[magcol], bins=spd_bins, labels=spd_labels, right=True
            )
        )
        .assign(
            Dir_bins=pandas.cut(
                dataframe[dircol], bins=dir_bins, labels=dir_labels, right=False
            )
        )
        .replace({"Dir_bins": {360: 0}})
        .groupby(by=["Spd_bins", "Dir_bins"])
        .size()
        .unstack(level="Spd_bins")
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
        ordered=True,
        name="Dir_bins",
    )
    _cols = pandas.CategoricalIndex(
        data=raw_rose.columns.categories.values,
        categories=raw_rose.columns.categories,
        ordered=True,
        name="Spd_bins",
    )

    # .add returns NA where both elements don't exists, so we
    # can just fill all of those with zeros again
    return raw_rose.reindex(index=_rows, columns=_cols, fill_value=0.0)


def _draw_rose(
    rose, ax=None, palette=None, show_calm=True, show_legend=True, **other_opts
):
    dir_degrees = numpy.array(rose.index.tolist())
    dir_rads, dir_width = _dir_degrees_to_radins(dir_degrees)
    palette = palette or DEEPCOLORS

    fig, ax = validate.axes_object(ax, polar=True)

    ax.set_theta_direction("clockwise")
    ax.set_theta_zero_location("N")
    ax.yaxis.set_major_formatter(FuncFormatter(_pct_fmt))

    for n, (c1, c2) in enumerate(zip(rose.columns[:-1], rose.columns[1:])):
        if n == 0 and show_calm:
            # first column only
            ax.bar(
                dir_rads,
                rose[c1].values,
                width=dir_width,
                color=palette[0],
                edgecolor="none",
                label=c1,
                linewidth=0,
                align="center",
                **other_opts
            )

        # all other columns
        ax.bar(
            dir_rads,
            rose[c2].values,
            width=dir_width,
            bottom=rose.cumsum(axis=1)[c1].values,
            color=palette[n + 1],
            edgecolor="none",
            label=c2,
            linewidth=0,
            align="center",
            **other_opts
        )

    if show_legend:
        ax.legend(loc=(0.9, -0.1), ncol=1, fontsize=8, frameon=False)

    thetas = numpy.linspace(0, 2 * numpy.pi, 8, endpoint=False)
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    ax.xaxis.set_major_locator(ticker.FixedLocator(thetas))
    ax.xaxis.set_major_formatter(ticker.FixedFormatter(directions))

    return fig


def rose(
    dataframe,
    magcol,
    dircol,
    spd_bins=None,
    spd_labels=None,
    spd_units=None,
    calmspeed=0.1,
    dir_bins=None,
    bin_width=15,
    dir_labels=None,
    palette=None,
    show_legend=True,
    show_calm=True,
    ax=None,
    total_count=None,
    **bar_opts
):
    """Draw a rose diagram

    Parameters
    ----------
    dataframe : pandas.DataFrame
    magcol, dircol : str
        The names of the columns that contain the magnitude and direction,
        respectively.
    spd_bins : sequence of floats, optional
        The bin edges to be used in catgorizing the wind speeds.
    spd_labels : sequence of strings, optional
        The labels for each speed category. Length of this sequence should
        be one less than the length of *spd_bins*.
    spd_units : str, optional
        The units of measure of the wind speed.
    calmspeed : float (default = 0.1)
        The wind speed below which conditions are considered "calm"
    dir_bins : sequence of floats, optional
        The bin edges to be used in catgorizing the wind directions.
    dir_labels : sequence of strings, optional
        The labels for each direction category. Length of this sequence should
        be one less than the length of *dir_bins*.
    ax : matplotlib.Axes object, optional
        The Axes on which the plot will be placed. If not provided,
        a new Figure and Axes will be created.
    palette : sequence of matplotlin colors, optional
        The color palette for the polar bars. Length of this sequence should be
        the same as *dir_labels*.
    show_legend : bool, optional, (default = True)
        Toggles the placement of a legend on the figure. If the default
        placement interferes with the plot, set to False and add the legend
        manually (see example).
    show_calm : bool, optional (default = True)
        Toggles the inclusion of the "calm" circle in the plot.
    ax : matplotlib.Axes object, optional
        The Axes on which the plot will be placed. If not provided,
        a new Figure and Axes will be created.
    total_count = int (optional)
        Defaults to the number of rows in the dataframe. Used to normalize the
        counts of the binned values to a percetage of the total.

    Other Parameters
    ----------------
    All other keyword arguments passed will be sent directly to the plotting
    method that creates the bars (``matplotlib.Axes.bar``).


    Returns
    -------
    fig : matplotlib.Figure
    rose : pandas.DataFrame
        Dataframe containing the relative frequencies within each
        direction and speed bin.

    Example
    -------
    >>> from matplotlib import pyplot
    >>> from tqdm import tqdm
    >>> from cloudside import asos, viz, tests
    >>> csvfile = tests.get_test_file("data_for_viz_tests.csv")
    >>> data = pandas.read_csv(csvfile, parse_dates=True, index_col=0)
    >>> fig, ax = pyplot.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    >>> # use show_legend = False since the legend might overlap tick labels
    >>> fig, rose = viz.rose(data, "WindSpd", "WindDir",ax=ax, show_legend=False)
    >>> # add legend ourselves in a position further away from the Axes
    >>> leg = ax.legend(loc='lower right', bbox_to_anchor=(1.5, 0.25))

    """

    rose = _compute_rose(
        dataframe,
        magcol=magcol,
        dircol=dircol,
        spd_bins=spd_bins,
        spd_labels=spd_labels,
        spd_units=spd_units,
        calmspeed=calmspeed,
        bin_width=bin_width,
        total_count=total_count,
    )

    fig = _draw_rose(
        rose,
        ax=ax,
        palette=palette,
        show_legend=show_legend,
        show_calm=show_calm,
        **bar_opts
    )
    return fig, rose


@numpy.deprecate
def windRose(dataframe, spdcol="wind_speed", dircol="wind_dir", **kwargs):
    return rose(dataframe, spdcol, dircol, **kwargs)


def _pct_fmt(x, pos=0):
    return "%0.1f%%" % (100 * x)


def _convert_dir_to_left_radian(directions):
    N = directions.shape[0]
    barDir = (directions * numpy.pi / 180.0) - (numpy.pi / N)
    barWidth = [2 * numpy.pi / N] * N
    return barDir, barWidth

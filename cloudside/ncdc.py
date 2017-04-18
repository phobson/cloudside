# standard library models
from __future__ import division, print_function
import datetime
import sys
import os

# third-party modules
import numpy

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec
import matplotlib.colorbar as colorbar

import pandas


def remove_bad_rain_values(df, raincol='hpcp', threshold=500):
    """ Filters invalid rainfall values and returns a new series.

    NCDC use 99999 1/100th of inch for invalid/missing values.
    We downloaded the data in mm so NCDC coverted that value to
    25399 mm. However, we default the invalid threshold value to
    500 mm since 12 inches of rain in an hour is equally
    unreasonable.
    """
    return numpy.where(df[raincol] > threshold, numpy.nan, df[raincol])


def get_percent_available(grid, coopid):
    status = grid.unstack()
    groups = status.groupby(level='Yr')
    pct_avail = groups.apply(
        lambda x:
            x.value_counts().to_dict().get(0, 0) / float(x.count()) * 100
    )
    pct_avail.name = coopid
    return pandas.DataFrame(pct_avail)


@mticker.FuncFormatter
def xdates(x, pos):
    day = x / 24.
    date = mdates.num2date(1 + day)
    date2 = datetime.datetime(1900, date.month, date.day)
    return date2.strftime('%m-%d')


def set_status(dataframe, opener, closer, flagval, flagcol='flag',
               raincol='precip', statuscol='status'):
    if statuscol not in dataframe.columns:
        dataframe = dataframe.assign(**{statuscol: 0})

    df = (
        dataframe
            .assign(_open=lambda df: (df[flagcol] == opener).cumsum())
            .assign(_close=lambda df: (df[flagcol] == closer).cumsum() + 1)
            .assign(**{statuscol: lambda df: numpy.where(
                (df['_close'] == df['_open']) | (df[flagcol] == closer),
                flagval, df[statuscol]
            )})
            .drop(['_open', '_close'], axis='columns')
    )
    return df


def setup_station_data(dataframe, coopid, dumpcsv=False, datecol='DATE',
                       stationcol='STATION', stanamecol='STATION_NAME',
                       precipcol='HPCP', qualcol='Measurement Flag',
                       baseyear=1947):
    # get the name of the station
    stationname = dataframe[stanamecol][dataframe[stationcol] == coopid].iloc[0]

    # standard column names
    colnames = {precipcol: 'precip', qualcol: 'flag'}

    # set the row labels, pull out data just for this station,
    # also rename some columns and just keep precip and flag
    station_data = dataframe.set_index([stationcol, datecol]) \
                            .xs(coopid, level=stationcol) \
                            .rename(columns=colnames)[['precip', 'flag']]

    origin_date = datetime.datetime(baseyear, 10, 1)
    start_date = station_data.index[0] - datetime.timedelta(hours=1)
    end_date = station_data.index[-1] + datetime.timedelta(hours=1)
    future_date = datetime.datetime(2015, 12, 31, 23)

    # pad the start of the data
    station_data.loc[origin_date, 'flag'] = '['
    station_data.loc[start_date, 'flag'] = ']'

    # pad the end of the data
    station_data.loc[end_date, 'flag'] = '['
    station_data.loc[future_date, 'flag'] = ']'

    # sort the now chaotic index
    station_data.sort_index(inplace=True)

    cooptxt = coopid.replace(':', '')

    if dumpcsv:
        station_data.to_csv('{}.csv'.format(cooptxt))

    # generate the full index (every hour, ever day)
    fulldates = pandas.DatetimeIndex(freq=pandas.offsets.Hour(1),
                                     start=origin_date,
                                     end=future_date)
    station_data = station_data.reindex(index=fulldates)

    # create a status column, default to 0 (available)
    station_data['status'] = 0

    # sometime the initial 'a' flags are missing. this inserts them:
    missing_flag_locs = (station_data.flag == ' ') & \
                        (station_data.precip > 10000)
    station_data.loc[missing_flag_locs, 'flag'] = 'a'

    # set the status for accumulated (aA), deleted ({}), and missing ([])
    station_data = set_status(station_data, 'a', 'A', 1)
    station_data = set_status(station_data, '{', '}', 2)
    station_data = set_status(station_data, '[', ']', 3)

    return station_data, stationname


def waterYear(dateval):
    october = 10
    if dateval.month >= october:
        return dateval.year + 1
    else:
        return dateval.year


def summarizeStorms(stormdata, stormcol='storm', units='in',
                    intensityfactor=1, datename=None):
    def timediff(row, t2, t1, asdays=False):
        secperhr = 60. * 60.
        hrperday = 24

        if asdays:
            conversion = secperhr * hrperday
        else:
            conversion = secperhr
        if pandas.isnull(row[t2]) or pandas.isnull(row[t1]):
            return numpy.nan
        else:
            return (row[t2] - row[t1]).total_seconds() / conversion

    if datename is None:
        datename = stormdata.index.names[0]

    stormdata = stormdata[stormdata[stormcol] > 0].reset_index()
    groups = stormdata.groupby(by=stormcol)

    # basic dictionary of how to rename the columns
    column_names = {
        datename: 'Start Date',
        'precip': 'Total',
        datename + '_max': 'End Date',
        'precip_max': 'Max Inten.'
    }

    # aggregate the total precip, min (start) date, and then join it
    # to an aggrecation of the max precip and max (end) date and then
    # rename the columns
    aggfxns = {datename: 'max', 'precip': 'max'}
    summary = (
        groups.agg({'precip': 'sum', datename: 'min'})
              .join(groups.agg(aggfxns), rsuffix='_max')
              .rename(columns=column_names)
    )

    if summary.shape[0] > 1:
        secperhr = 60. * 60.
        # compute storm durations
        summary['Duration Hours'] = summary.apply(
            lambda row: timediff(row, 'End Date', 'Start Date', asdays=False),
            axis=1
        )

        # fill in end date of previous storm
        summary['Previous Storm End'] = summary['End Date'].shift(1)

        # compute antecedant duration
        summary['Antecedent Days'] = summary.apply(
            lambda row: timediff(row, 'Start Date', 'Previous Storm End', asdays=True),
            axis=1
        )

        summary['Avg Inten.'] = (
            summary['Total'] / summary['Duration Hours'] * intensityfactor
        )

        summary.loc[:, 'Max Inten.'] = summary['Max Inten.'] * intensityfactor

        # keep only our favorite columns
        final_columns = [
            'Antecedent Days', 'Previous Storm End',
            'Start Date', 'End Date', 'Duration Hours',
            'Total', 'Avg Inten.', 'Max Inten.'
        ]
        return summary[final_columns]


def availabilityByStation(stationdata, stationname, coopid, baseyear=1947,
                          figsize=None):

    cooptxt = coopid.replace(':', '')

    # reset in the index and compute year and month-day-hour representations of the date
    stationdata = stationdata.reset_index()[['index', 'status']]
    stationdata['Yr'] = stationdata['index'].apply(
        lambda d: d.strftime('%Y')
    )
    stationdata['MoDayHr'] = stationdata['index'].apply(
        lambda d: d.strftime('%m-%d-%H:%M')
    )

    # set those as the index, pull out only status data
    stationdata = stationdata.set_index(['Yr', 'MoDayHr'])

    # pivot so that month-hour-years are columns
    grid = stationdata.unstack(level='MoDayHr')['status']

    # plotting
    if not figsize:
        figsize = (6.5, 7.25)

    fig = plt.figure(figsize=figsize)
    gs = gridspec.GridSpec(nrows=2, ncols=1, height_ratios=[20, 1])
    ax = fig.add_subplot(gs[0])
    cax = fig.add_subplot(gs[1])

    mycolors = [
        (0.75871830080126179, 0.79220693354743377, 0.95438612219134034),
        (0.81462453291982828, 0.49548316572322215, 0.57525259364168568),
        (0.32927729263408284, 0.47628455565843819, 0.18371555497583281),
        (0.086056336005814082, 0.23824692404211989, 0.30561236308077167)
    ]
    cmap = mpl.colors.ListedColormap(mycolors)
    cmap.set_bad(mycolors[-1])
    bounds = [-0.5, 0.5, 1.5, 2.5, 3.5]
    norm = mpl.colors.BoundaryNorm(bounds, cmap.N)

    img = ax.pcolorfast(grid, cmap=cmap, norm=norm)
    ax.set_aspect(grid.shape[1] / grid.shape[0])

    ax.set_yticks(numpy.arange(grid.shape[0]) + 0.5)
    ax.set_yticklabels(grid.index.tolist(), fontsize=7)

    months = pandas.DatetimeIndex(freq=pandas.offsets.MonthBegin(n=1),
                                  start='1900-01-01', end='1900-12-31')
    ax.set_xticks([(month.dayofyear * 24) - 24 for month in months.tolist()])

    ax.invert_yaxis()
    ax.xaxis.set_major_formatter(xdates)

    cbar = colorbar.ColorbarBase(cax, cmap=cmap, norm=norm, orientation='horizontal')
    cbar.set_ticks([0, 1, 2, 3])
    cbar.set_ticklabels(['Good', 'Accumulated', 'Deleted', 'Missing'])
    cbar.ax.set_title('Precipitation Data Status')

    ax.set_title('{1}\n({0})'.format(coopid, stationname), fontsize=10)
    ax.set_ylabel('Year')
    ax.set_xlabel('Month and Day')
    ax.xaxis.tick_bottom()
    ax.yaxis.tick_left()
    fig.tight_layout()

    return fig, grid


def dataAvailabilityHeatmap(data, figsize=None):
    if not figsize:
        figsize = (6.8, 7.0)

    bounds = numpy.arange(10., 101.0, 10.0)
    mycolors = [
        (0.89788543476777916, 0.93903883485233086, 0.97736255421357998),
        (0.8288812097381143, 0.89376394327949071, 0.95472510842715996),
        (0.75063438625896683, 0.84784314632415769, 0.92821223034578215),
        (0.63252597346025352, 0.79764707088470455, 0.88687428586623251),
        (0.49176471712542513, 0.72196849023594578, 0.85477893983616549),
        (0.36159939310129952, 0.64273742998347561, 0.81657825007158169),
        (0.24816610374871423, 0.56189160382046421, 0.77098040580749516),
        (0.15072665197007795, 0.4644521408221301, 0.72078433036804201),
        (0.074817382149836603, 0.37325644738533914, 0.65520955534542313),
        (0.031372550874948502, 0.28161477242030347, 0.55826222487524446)
    ]
    cmap = mpl.colors.ListedColormap(mycolors)
    cmap.set_under('1.0')
    cmap.set_bad('1.0')
    norm = mpl.colors.BoundaryNorm(bounds, cmap.N, clip=True)

    fig = plt.figure(figsize=figsize)
    gs = gridspec.GridSpec(nrows=2, ncols=1, height_ratios=[1, 20])

    mdata = numpy.ma.masked_less(data.values, 1)

    ax = fig.add_subplot(gs[1])
    img = ax.pcolorfast(mdata, cmap=cmap)
    ax.set_xlabel('Year')
    ax.set_ylabel('Precipitation Gauge')
    ax.xaxis.tick_bottom()
    ax.yaxis.tick_left()

    yearstep = 4
    ax.set_yticks(numpy.arange(data.shape[0]) + 0.5)
    ax.set_yticks(numpy.arange(data.shape[0]), minor=True)
    ax.set_yticklabels(data.index.tolist())
    ax.set_xticks(numpy.arange(0, data.shape[1], yearstep) + 0.5)
    ax.set_xticks(numpy.arange(0, data.shape[1], 1), minor=True)
    ax.set_xticklabels(data.columns[::yearstep], rotation=45)
    ax.tick_params(axis='both', which='minor', length=0)
    ax.xaxis.grid(True, zorder=10, lw=0.5, which='minor', linestyle='-', color='0.5', alpha=0.5)
    ax.yaxis.grid(True, zorder=10, lw=0.5, which='minor', linestyle='-', color='0.5', alpha=0.5)

    cax = fig.add_subplot(gs[0])
    cbar = colorbar.ColorbarBase(cax, cmap=cmap, norm=norm, orientation='horizontal', extend='min')
    cax.invert_xaxis()
    cax.xaxis.tick_top()
    cax.xaxis.set_label_position('top')
    cax.set_xlabel('Percent of data available', fontsize=10)
    fig.tight_layout()

    return fig


if __name__ == '__main__':

    def _parser(x):
        return datetime.datetime.strptime(x, '%Y%m%d %H:%M')

    data_1hr = pandas.read_csv(filepath, sep=sep, na_values=['unknown', 99999],
                               parse_dates=['DATE'], date_parser=_parser)

    COOPIDS = pandas.unique(data_1hr['STATION'])
    COOPIDS.sort()

    station_info = []

    for n, coopid in enumerate(COOPIDS):
        cooptxt = coopid.replace(':', '')
        station_data, station_name = setup_station_data(data_1hr, coopid)
        summary = summarizeStorms(station_data, coopid)
        station_info.append({
            'name': station_name,
            'coop': coopid,
            'data': station_data,
            'storms': summary
        })

    for n, sta in enumerate(station_info):
        fig, grid = availabilityByStation(sta['data'], sta['name'], sta['coop'])

        if n == 0:
            pct_avail = get_percent_available(grid, sta['coop'])
        else:
            pct_avail = pct_avail.join(get_percent_available(grid, sta['coop']), how='outer')

        pct_avail.to_csv('GaugeAvailabily.csv', na_rep=0, float_format='%0.1f')

    pct_avail_grid = pct_avail.T
    pct_avail_grid.sort_index(inplace=True, ascending=False)
    fig = rainfall.dataAvailabilityHeatmap(pct_avail_grid)

import numpy
import pandas


SEC_PER_MINUTE = 60.0
MIN_PER_HOUR = 60.0
HOUR_PER_DAY = 24.0
SEC_PER_HOUR = SEC_PER_MINUTE * MIN_PER_HOUR
SEC_PER_DAY = SEC_PER_HOUR * HOUR_PER_DAY


def _wet_first_row(df, wetcol, diffcol):
    # make sure that if the first record is associated with the first
    # storm if it's wet
    firstrow = df.iloc[0]
    if firstrow[wetcol]:
        df.loc[firstrow.name, diffcol] = 1

    return df


def _wet_window_diff(is_wet, ie_periods):
    return (
        is_wet.rolling(int(ie_periods), min_periods=1)
        .apply(lambda window: window.any(), raw=False)
        .diff()
    )


def parse_record(
    data,
    intereventHours,
    outputfreqMinutes,
    precipcol=None,
    inflowcol=None,
    outflowcol=None,
    baseflowcol=None,
    stormcol="storm",
    debug=False,
):
    """Parses the hydrologic data into distinct storms.

    In this context, a storm is defined as starting whenever the
    hydrologic records shows non-zero precipitation or [in|out]flow
    from the BMP after a minimum inter-event dry period duration
    specified in the the function call. The storms ends the observation
    *after* the last non-zero precipitation or flow value.

    Parameters
    ----------
    data : pandas.DataFrame
    intereventHours : float
        The Inter-Event dry duration (in hours) that classifies the
        next hydrlogic activity as a new event.
    precipcol : string, optional (default = None)
        Name of column in `hydrodata` containing precipiation data.
    inflowcol : string, optional (default = None)
        Name of column in `hydrodata` containing influent flow data.
    outflowcol : string, optional (default = None)
        Name of column in `hydrodata` containing effluent flow data.
    baseflowcol : string, optional (default = None)
        Name of column in `hydrodata` containing boolean indicating
        which records are considered baseflow.
    stormcol : string (default = 'storm')
        Name of column in `hydrodata` indentifying distinct storms.
    debug : bool (default = False)
        If True, diagnostic columns will not be dropped prior to
        returning the dataframe of parsed_storms.

    Writes
    ------
    None

    Returns
    -------
    parsed_storms : pandas.DataFrame
        Copy of the origin `hydrodata` DataFrame, but resampled to a
        fixed frequency, columns possibly renamed, and a `storm` column
        added to denote the storm to which each record belongs. Records
        where `storm` == 0 are not a part of any storm.

    """

    # pull out the rain and flow data
    if precipcol is None:
        precipcol = "precip"
        data.loc[:, precipcol] = numpy.nan

    if inflowcol is None:
        inflowcol = "inflow"
        data.loc[:, inflowcol] = numpy.nan

    if outflowcol is None:
        outflowcol = "outflow"
        data.loc[:, outflowcol] = numpy.nan

    if baseflowcol is None:
        baseflowcol = "baseflow"
        data.loc[:, baseflowcol] = False

    # bool column where True means there's rain or flow of some kind
    water_columns = [inflowcol, outflowcol, precipcol]
    cols_to_use = water_columns + [baseflowcol]

    agg_dict = {
        precipcol: numpy.sum,
        inflowcol: numpy.mean,
        outflowcol: numpy.mean,
        baseflowcol: numpy.any,
    }

    freq = pandas.offsets.Minute(outputfreqMinutes)
    ie_periods = int(MIN_PER_HOUR / freq.n * intereventHours)

    # periods between storms are where the cumulative number
    # of storms that have ended are equal to the cumulative
    # number of storms that have started.
    # Stack Overflow: http://tinyurl.com/lsjkr9x
    res = (
        data.resample(freq)
        .agg(agg_dict)
        .loc[:, lambda df: df.columns.isin(cols_to_use)]
        .assign(
            __wet=lambda df: numpy.any(df[water_columns] > 0, axis=1) & ~df[baseflowcol]
        )
        .assign(__windiff=lambda df: _wet_window_diff(df["__wet"], ie_periods))
        .pipe(_wet_first_row, "__wet", "__windiff")
        .assign(__event_start=lambda df: df["__windiff"] == 1)
        .assign(__event_end=lambda df: df["__windiff"].shift(-1 * ie_periods) == -1)
        .assign(__storm=lambda df: df["__event_start"].cumsum())
        .assign(
            **{
                stormcol: lambda df: numpy.where(
                    df["__storm"] == df["__event_end"].shift(2).cumsum(),
                    0,  # inter-event periods marked zero
                    df["__storm"],  # actual events keep their number
                )
            }
        )
    )

    if not debug:
        res = res.loc[:, res.columns.map(lambda c: not c.startswith("__"))]

    return res

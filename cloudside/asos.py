# std lib stuff
import datetime
import logging
from ftplib import FTP, error_perm
from pathlib import Path

import numpy
import pandas

from . station import MetarParser
from . import validate


_logger = logging.getLogger(__name__)


__all__ = [
    'parse_file',
    'get_data'
]


HOURLY = pandas.offsets.Hour(1)
MONTHLY = pandas.offsets.MonthBegin(1)
FIVEMIN = pandas.offsets.Minute(5)


def _fetch_file(station_id, timestamp, ftp, raw_folder, force_download=False):
    """ Fetches a single file from the ASOS ftp and returns its pathh on the
    local file system

    Parameters
    ----------
    station_id : str
        The station ID/airport code of the gauge
    timestamp : datetime-like
        A pandas `Timestamp` or other datetime-like object with `.year` and
        `.month` attributes
    ftp : FTP-connection
        Connection to the FAA/ASOS ftp server
    raw_folder : pathlib.Path
        Directory on the local file system where the data should be saved
    force_download : bool (default is False)
        See to the True to force re-downloading of ASOS data that already
        exist

    Returns
    -------
    dst_path : pathlib.Path
        Object representing the location of the downloaded file's location on
        the local file system

    """

    ftpfolder = f"/pub/data/asos-fivemin/6401-{timestamp.year}"
    src_name = f"64010{station_id}{timestamp.year}{timestamp.month:02d}.dat"
    dst_path = Path(raw_folder).joinpath(src_name)
    has_failed = False
    if (not dst_path.exists()) or force_download:
        with dst_path.open(mode='w', encoding='utf-8') as dst_obj:
            try:
                ftp.retrlines(
                    f'RETR {ftpfolder}/{src_name}',
                    lambda x: dst_obj.write(x + '\n')
                )
            except error_perm:
                _logger.log(logging.ERROR, f'No such file {src_name}')
                has_failed = True

        if has_failed:
            dst_path.unlink()
            dst_path = None

    return dst_path


def _fetch_data(station_id, startdate, stopdate, email, raw_folder,
                force_download=False, pbar_fxn=None):
    """ Fetches a single file from the ASOS ftp and returns its pathh on the
    local file system

    Parameters
    ----------
    station_id : str
        The station ID/airport code of the gauge
    startdate, stopdate : datetime-like
        Pandas `Timestamp` or other datetime-like objects with `.year` and
        `.month` attributes representing the date range (inclusive) of data
        to be downloaded
    email : str
        Your email address to be used as the ftp login password
    raw_folder : pathlib.Path
        Directory on the local file system where the data should be saved
    force_download : bool (default is False)
        See to the True to force re-downloading of ASOS data that already
        exist
    pbar_fxn : callable, optional
        A tqdm-like progress bar function such as `tqdm.tqdm` or
        `tqdm.tqdm_notebook`.

    Returns
    -------
    raw_paths : list of pathlib.Path
        list of objects representing the location of the downloaded files'
        locations on the local file system

    """

    dates = pandas.date_range(startdate, stopdate, freq=MONTHLY)
    dates_to_fetch = validate.progress_bar(pbar_fxn, dates, desc='Fetching')
    with FTP('ftp.ncdc.noaa.gov') as ftp:
        ftp.login(passwd=email)
        raw_paths = [
            _fetch_file(station_id, ts, ftp, raw_folder, force_download)
            for ts in dates_to_fetch
        ]
    return filter(lambda x: x is not None, raw_paths)


def _find_reset_time(precip_ts):
    """ Determines the precipitation gauge's accumulation reset time.

    Parameters
    ----------
    precip_ts : pandas.Series
        Time series of the raw precipitation data.

    Returns
    -------
    rt : int
        The minute of the hour which is most likely the reset time for the
        chunk of data.
    """

    def get_idxmin(g):
        if g.shape[0] > 0:
            return g.idxmin()

    rt = 0
    if precip_ts.any():
        rt = (
            precip_ts.resample(HOURLY)
                .apply(get_idxmin)
                .dropna()
                .dt.minute.value_counts()
                .idxmax()
        )
    return rt


def _process_precip(data, rt, raw_precipcol):
    """ Processes precip data that accumulates hourly into raw minute
    intensities.

    Parameters
    ----------
    data : pandas.DataFrame
    rt : int
        Minute of the hour at which the gauge's hourly accumulation is reset
    raw_precipcol : str
        Label of the column in `data` that contains the raw (hourly acummulated)
        precipitation data.

    Returns
    -------
    precip : pandas.Series
        Cleaned up precip record with instaneous 5-min rainfall depths

    """

    df = (
        data[[raw_precipcol]]
            .assign(rp=lambda df: df[raw_precipcol])
            .assign(d1=lambda df: df['rp'].diff())
    )

    is_reset = df.index.minute == rt
    neg_diff = df['d1'] < 0
    first_in_chunk = df['d1'].isnull() & ~df['rp'].isnull()
    precip = numpy.where(
        is_reset | neg_diff | first_in_chunk,
        df[raw_precipcol],
        df['d1']
    )
    return precip


def parse_file(filepath, new_precipcol='precipitation'):
    """ Parses a raw ASOS/METAR file into a pandas.DataFrame

    Parameters
    ----------
    filepath : str or pathlib.Path object of the METAR file
    new_precipcol : str
        The desired column label of the precipitation column after it has been
        disaggregated from hourly accumulations

    Returns
    -------
    df : pandas.DataFrame

    """

    with filepath.open('r') as rawf:
        df = pandas.DataFrame(list(map(lambda x: MetarParser(x, strict=False).asos_dict(), rawf)))

    if not df.empty:
        data = (
            df.groupby('datetime').last()
              .sort_index()
              .resample(FIVEMIN).asfreq()
        )

        rt = _find_reset_time(data['raw_precipitation'])
        precip = _process_precip(data, rt, 'raw_precipitation')
        return data.assign(**{new_precipcol: precip})


def get_data(station_id, startdate, stopdate, email, folder='.',
             raw_folder='01-raw', force_download=False, pbar_fxn=None):
    """ Download and process a range of FAA/ASOS data files for a given station

    Parameters
    ----------
    station_id : str
        The station ID/airport code of the gauge
    startdate, stopdate : str or datetime-like
        Pandas `Timestamp` or other datetime-like objects with `.year` and
        `.month` attributes representing the date range (inclusive) of data
        to be downloaded
    email : str
        Your email address to be used as the ftp login password
    folder : str or pathlib.Path
        Top-level folder to store all of the transferred ftp data
    raw_folder : pathlib.Path
        Directory on the local file system where the data should be saved
    force_download : bool (default is False)
        See to the True to force re-downloading of ASOS data that already
        exist
    pbar_fxn : callable, optional
        A tqdm-like progress bar function such as `tqdm.tqdm` or
        `tqdm.tqdm_notebook`.

    Returns
    -------
    weather : pandas.DataFrame

    Examples
    --------
    >>> from cloudside import asos
    >>> from tqdm import tqdm
    >>> pdx = asos.get_data('KPDX', '2010-10-01', '2013-10-31', my_email,
    ...                     folder='Portland_weather', raw_folder='asos_files',
    ...                     force_download=False, pbar_fxn=tqdm)
    """

    _raw_folder = Path(folder).joinpath(raw_folder)
    _raw_folder.mkdir(parents=True, exist_ok=True)
    _raw_files = _fetch_data(station_id, startdate, stopdate, email,
                             raw_folder=_raw_folder, pbar_fxn=pbar_fxn,
                             force_download=force_download)
    raw_files = validate.progress_bar(pbar_fxn, _raw_files, desc='Parsing')
    df = pandas.concat([parse_file(rf) for rf in raw_files])
    return df.pipe(validate.unique_index)

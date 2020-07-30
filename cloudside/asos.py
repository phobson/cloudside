# std lib stuff
import logging
import warnings
from ftplib import FTP, error_perm
from pathlib import Path
from collections import namedtuple

import numpy
import pandas
from metar import Metar

from . import validate


_fields = [
    "datetime",
    "raw_precipitation",
    "temperature",
    "dew_point",
    "wind_speed",
    "wind_direction",
    "air_pressure",
    "sky_cover",
]
Obs = namedtuple("Obs", _fields)


_logger = logging.getLogger(__name__)


__all__ = ["fetch_files", "parse_file", "get_data", "Obs"]


HOURLY = pandas.offsets.Hour(1)
MONTHLY = pandas.offsets.MonthBegin(1)
FIVEMIN = pandas.offsets.Minute(5)


def value_or_not(obs_attr):
    if obs_attr is None:
        return numpy.nan
    else:
        return obs_attr.value()


class MetarParser(Metar.Metar):
    def __init__(self, *args, **kwargs):
        self._datetime = None
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            super().__init__(*args, **kwargs)
            if len(w) > 1:
                for _w in w:
                    _logger.info(_w.message)

    def _unparsed_group_handler(self, d):
        """
        Handle otherwise unparseable main-body groups.
        """
        self._unparsed_groups.append(d["group"])

    @property
    def datetime(self):
        """get date/time of asos reading"""
        if self._datetime is None and len(self.code) > 45:
            self._datetime = pandas.Timestamp(self.code[28:45])
        return self._datetime

    def asos_dict(self):
        if self.datetime is not None:
            return Obs(
                datetime=self.datetime.round("5min"),
                raw_precipitation=value_or_not(self.precip_1hr),
                temperature=value_or_not(self.temp),
                dew_point=value_or_not(self.dewpt),
                wind_speed=value_or_not(self.wind_speed),
                wind_direction=value_or_not(self.wind_dir),
                air_pressure=value_or_not(self.press),
                sky_cover=_process_sky_cover(self),
            )
        else:
            _blanks = [None] * 8
            return Obs(*_blanks)


def _process_sky_cover(obs):
    coverdict = {
        "CLR": 0.0000,
        "SKC": 0.0000,
        "NSC": 0.0000,
        "NCD": 0.0000,
        "FEW": 0.1785,
        "SCT": 0.4375,
        "BKN": 0.7500,
        "VV": 0.9900,
        "OVC": 1.0000,
    }
    coverlist = []
    for sky in obs.sky:
        coverval = coverdict[sky[0]]
        coverlist.append(coverval)

    if len(coverlist) > 0:
        cover = numpy.max(coverlist)
    else:
        cover = "NA"

    return cover


def _fetch_file(
    station_id,
    timestamp,
    ftp,
    raw_folder,
    force_download=False,
    past_attempts=0,
    max_attempts=10,
):
    """Fetches a single file from the ASOS ftp and returns its pathh on the
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
        with dst_path.open(mode="w", encoding="utf-8") as dst_obj:
            try:
                past_attempts += 1
                ftp.retrlines(
                    f"RETR {ftpfolder}/{src_name}", lambda x: dst_obj.write(x + "\n")
                )
            except TimeoutError:  # pragma: no cover
                _logger.log(
                    logging.WARNING,
                    f"Timedout fetch {src_name} on attempt {past_attempts}",
                )
                if past_attempts >= max_attempts:
                    has_failed = True
                else:
                    return _fetch_file(
                        station_id,
                        timestamp,
                        ftp,
                        raw_folder,
                        force_download=force_download,
                        past_attempts=past_attempts,
                        max_attempts=max_attempts,
                    )
            except error_perm:
                _logger.log(logging.ERROR, f"No such file {src_name}")
                has_failed = True

        if has_failed:
            dst_path.unlink()
            dst_path = None

    return dst_path


def fetch_files(
    station_id,
    startdate,
    stopdate,
    email,
    raw_folder,
    force_download=False,
    pbar_fxn=None,
):
    """Fetches a single file from the ASOS ftp and returns its path on the
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
    dates_to_fetch = validate.progress_bar(pbar_fxn, dates, desc="Fetching")
    with FTP("ftp.ncei.noaa.gov") as ftp:
        ftp.login(passwd=email)
        raw_paths = [
            _fetch_file(station_id, ts, ftp, raw_folder, force_download)
            for ts in dates_to_fetch
        ]
    return filter(lambda x: x is not None, raw_paths)


def _find_reset_time(precip_ts):
    """Determines the precipitation gauge's accumulation reset time.

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
    """Processes precip data that accumulates hourly into raw minute
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
        .assign(d1=lambda df: df["rp"].diff())
    )

    is_reset = df.index.minute == rt
    neg_diff = df["d1"] < 0
    first_in_chunk = df["d1"].isnull() & ~df["rp"].isnull()
    precip = numpy.where(
        is_reset | neg_diff | first_in_chunk, df[raw_precipcol], df["d1"]
    )
    return precip


def parse_file(filepath, new_precipcol="precipitation"):
    """Parses a raw ASOS/METAR file into a pandas.DataFrame

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

    def _do_parse(x):
        try:
            return MetarParser(x, strict=False).asos_dict()
        except Metar.ParserError:
            return {}

    with filepath.open("r") as rawf:
        df = pandas.DataFrame(list(map(_do_parse, rawf)))

    if not df.empty:
        data = df.groupby("datetime").last().sort_index().resample(FIVEMIN).asfreq()

        rt = _find_reset_time(data["raw_precipitation"])
        precip = _process_precip(data, rt, "raw_precipitation")
        return data.assign(**{new_precipcol: precip})


def get_data(
    station_id,
    startdate,
    stopdate,
    email,
    folder=".",
    raw_folder="01-raw",
    force_download=False,
    pbar_fxn=None,
):
    """Download and process a range of FAA/ASOS data files for a given station

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
        See to the True to force re-downloading of data that already exists
        in the folder specified structure.
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
    >>> pdx = asos.get_data('KPDX', '2013-09-01', '2013-10-31', 'iamweather@sensors.net',
    ...                     folder='Portland_weather', raw_folder='asos_files',
    ...                     force_download=False, pbar_fxn=tqdm)
    """

    _raw_folder = Path(folder).joinpath(raw_folder)
    _raw_folder.mkdir(parents=True, exist_ok=True)
    _raw_files = fetch_files(
        station_id,
        startdate,
        stopdate,
        email,
        raw_folder=_raw_folder,
        pbar_fxn=pbar_fxn,
        force_download=force_download,
    )
    raw_files = validate.progress_bar(pbar_fxn, _raw_files, desc="Parsing")
    df = pandas.concat([parse_file(rf) for rf in raw_files])
    return df.pipe(validate.unique_index)

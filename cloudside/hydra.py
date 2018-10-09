from pathlib import Path

import pandas
import requests

from cloudside import validate


def _fetch_file(station_id, raw_folder, force_download=False):
    sta = station.lower()
    url = 'https://or.water.usgs.gov/non-usgs/bes/{}.rain'.format(sta)
    dst_path = Path(raw_folder).joinpath(sta + '.txt')
    dst_path.write_text(requests.get(url).text)
    return dst_path


def parse_file(filepath):
    """ Parses a rain file downloaded from the Portland Hydra Network

    Parameters
    ----------
    filepath : string or pathlib.Path
        Object representing the downloaded file

    Returns
    -------
    rain_df : pandas.DataFrame
        Dataframe with the hourly rainfall depth in inches. The column label
        will be the station's name. The index is set to the hourly timestamps.

    """

    read_opts = {
        'sep': '\s+',
        'header': None,
        'parse_dates': ['Date'],
        'na_values': ['-'],
    }

    with Path(filepath).open('r') as fr:
        for line in fr:
            if line.strip().startswith('Daily'):
                headers = next(fr).strip().split()
                _ = next(fr)
                df = (
                    pandas.read_table(fr, names=headers, **read_opts)
                        .drop(columns=['Total'])
                        .melt(id_vars=['Date'], value_name=filepath.stem, var_name='Hour')
                        .assign(Hour=lambda df: df['Hour'].astype(int).map(lambda x: pandas.Timedelta(x, unit='h')))
                        .assign(datetime=lambda df: df['Date'] + df['Hour'])
                        .set_index('datetime')
                        .sort_index()
                        .loc[:, [filepath.stem]]
                        .div(100)
                )
    return df


def get_data(station_id, folder='.', raw_folder='01-raw', force_download=False):
    """ Download and parse full records from Portland's Hydra Network

    Parameters
    ----------
    station_id : string
        Short name of the rain gauge. To locate this, go to the
        `Hydra Click Map <https://or.water.usgs.gov/non-usgs/bes/raingage_info/clickmap.html>`_,
        select your site, and inspect the final URL for the HTML in file.
        For example, for Hydra Site #3, which has this URL:
        https://or.water.usgs.gov/non-usgs/bes/sauvies_island.html,
        you would pass ``"sauvies_island"`` as the station ID.
    folder : str or pathlib.Path
        This is the top-level directory where data will be saved.
    raw_folder : string or pathlib.Path
        This is a subdirectory where the raw data will be downloaded.
    force_download : bool (default is False)
        See to the True to force re-downloading of data that already exists
        in the folder specified structure.

    Returns
    -------
    rain_df : pandas.DataFrame
        Dataframe with the hourly rainfall depth in inches. The column label
        will be the *station_id*. The index is set to the hourly timestamps.

    See also
    --------
    https://or.water.usgs.gov/non-usgs/bes/
    https://or.water.usgs.gov/non-usgs/bes/raingage_info/clickmap.html
    https://or.water.usgs.gov/non-usgs/bes/rainfall_data_quality.html

    """

    _raw_folder = Path(folder).joinpath(raw_folder)
    _raw_folder.mkdir(parents=True, exist_ok=True)
    _raw_path = _fetch_file(station_id, _raw_folder, force_download=force_download)
    return parse_file(_raw_path).pipe(validate.unique_index)

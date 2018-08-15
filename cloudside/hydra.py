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
    read_opts = {
        'sep': '\s+',
        'header': None,
        'parse_dates': ['Date'],
        'na_values': ['-'],
    }

    with filepath.open('r') as fr:
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
    _raw_folder = Path(folder).joinpath(raw_folder)
    _raw_folder.mkdir(parents=True, exist_ok=True)
    _raw_path = _fetch_file(station_id, _raw_folder, force_download=force_download)
    return parse_file(_raw_path).pipe(validate.unique_index)

from datetime import datetime
import pathlib
from pkg_resources import resource_filename
import tempfile
import ftplib

import numpy
import pandas

from unittest import mock
import pytest
import numpy.testing as nptest
import pandas.util.testing as pdtest

from cloudside import asos, station
from .helpers import get_test_file, raises


@pytest.fixture
def fake_rain_data():
    rain_raw = [
        0.,  1.,  2.,  3.,  4.,  4.,  4.,  4.,  4.,  4.,  4.,  4.,
        0.,  0.,  0.,  0.,  0.,  5.,  5.,  5.,  5.,  5.,  5.,  5.,
        0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,
        1.,  2.,  3.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.
    ]
    daterange = pandas.date_range(start='2001-01-01 11:55',
                                  end='2001-01-01 15:50',
                                  freq=asos.FIVEMIN)
    return pandas.Series(rain_raw, index=daterange)


def retr_error(cmd, action):
    raise ftplib.error_perm


@pytest.mark.parametrize(('exists', 'force', 'call_count'), [
    (True, True, 1),
    (True, False, 0),
    (False, True, 1),
    (False, False, 1),
])
@pytest.mark.parametrize('datestr', ['2016-01-01', '1999-01-01'])
@mock.patch('ftplib.FTP')
def test__fetch_file(ftp, exists, force, call_count, datestr):
    ts = pandas.Timestamp('2016-01-01')
    with tempfile.TemporaryDirectory() as rawdir:
        std_path = pathlib.Path(rawdir).joinpath(f'64010KPDX{ts.year}01.dat')
        if exists:
            std_path.touch()

        if ts.year == 1999 and call_count == 1:
            expected_path = None
        else:
            expected_path = std_path

        if expected_path is None:
            ftp.retrlines.side_effect = retr_error

        dst_path = asos._fetch_file('KPDX', ts, ftp, rawdir, force_download=force)
        assert dst_path == expected_path
        assert ftp.retrlines.call_count == call_count


@mock.patch.object(ftplib.FTP, 'retrlines')
@mock.patch.object(ftplib.FTP, 'login')
def test_fetch_files(ftp_login, ftp_retr):
    with tempfile.TemporaryDirectory() as rawdir:
        raw_paths = asos.fetch_files('KPDX', '1999-10-01', '2000-02-01',
                                     'tester@cloudside.net', rawdir)
        assert isinstance(raw_paths, filter)
        assert all([
            (isinstance(rp, pathlib.Path) or (rp is None))
            for rp in raw_paths
        ])
        assert ftp_login.called_once_with('tester@cloudside.net')
        assert ftp_retr.call_count == 5


@pytest.mark.parametrize(('all_na', 'expected'), [(False, 55), (True, 0)])
def test__find_reset_time(fake_rain_data, all_na, expected):
    if all_na:
        fake_rain_data.loc[:] = numpy.nan

    result = asos._find_reset_time(fake_rain_data)
    assert result == expected


def test_process_precip(fake_rain_data):
    precip = fake_rain_data.to_frame('raw_precip')
    result = asos._process_precip(precip, 55, 'raw_precip')
    expected = numpy.array([
        0., 1., 1., 1., 1., 0., 0., 0., 0., 0., 0., 0., 0.,
        0., 0., 0., 0., 5., 0., 0., 0., 0., 0., 0., 0., 0.,
        0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 1., 1.,
        0., 0., 0., 0., 0., 0., 0., 0., 0.
    ])
    nptest.assert_array_almost_equal(result, expected)


def test_parse_file():
    datpath = pathlib.Path(get_test_file('sample_asos.dat'))
    csvpath = pathlib.Path(get_test_file('sample_asos.csv'))
    result = asos.parse_file(datpath)
    expected = pandas.read_csv(csvpath, parse_dates=True, index_col=['datetime'])
    pdtest.assert_frame_equal(result.fillna(-9999), expected.fillna(-9999),
                              check_less_precise=True)


@mock.patch('ftplib.FTP')
@mock.patch('cloudside.validate.unique_index')
@mock.patch('cloudside.asos._fetch_file')
@mock.patch('cloudside.asos.parse_file', return_value=pandas.Series([1, 2, 3]))
def test_get_data(parser, fetcher, checker, ftp):
    with tempfile.TemporaryDirectory() as topdir:
        asos.get_data('KPDX', '2012-01-01', '2012-06-02', 'test@cloudside.net',
                      folder=topdir)
        assert fetcher.call_count == 6
        assert parser.call_count == 6

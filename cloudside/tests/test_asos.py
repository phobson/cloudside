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
    daterange = pandas.date_range(start='2001-01-01 12:00',
                                  end='2001-01-01 15:55',
                                  freq=asos.FIVEMIN)
    return pandas.Series(rain_raw, index=daterange)


@pytest.mark.parametrize(('exists', 'force', 'call_count'), [
    (True, True, 1),
    (True, False, 0),
    (False, True, 1),
    (False, False, 1),
])
@mock.patch('ftplib.FTP')
def test__fetch_file(ftp, exists, force, call_count):
    ts = pandas.Timestamp('2016-01-01')
    with tempfile.TemporaryDirectory() as rawdir:
        expected_path = pathlib.Path(rawdir).joinpath('64010KPDX201601.dat')
        if exists:
            expected_path.touch()

        dst_path = asos._fetch_file('KPDX', ts, ftp, rawdir, force)
        assert dst_path == expected_path
        assert ftp.retrlines.call_count == call_count


@pytest.mark.parametrize(('exists', 'force', 'call_count'), [
    (True, True, 5),
    (True, False, 0),
    (False, True, 5),
    (False, False, 5),
])
@mock.patch.object(ftplib.FTP, 'retrlines')
@mock.patch.object(ftplib.FTP, 'login')
def test__fetch_data(ftp_login, ftp_retr, exists, force, call_count):
    with tempfile.TemporaryDirectory() as rawdir:
        expected_paths = [
            pathlib.Path(rawdir).joinpath('64010KPDX201610.dat'),
            pathlib.Path(rawdir).joinpath('64010KPDX201611.dat'),
            pathlib.Path(rawdir).joinpath('64010KPDX201612.dat'),
            pathlib.Path(rawdir).joinpath('64010KPDX201701.dat'),
            pathlib.Path(rawdir).joinpath('64010KPDX201702.dat'),
        ]
        if exists:
            _ = [ep.touch() for ep in expected_paths]

        raw_paths = asos._fetch_data('KPDX', '2016-10-01', '2017-02-01',
                                     'tester@cloudside.net', rawdir,
                                     force_download=force)
        assert raw_paths == expected_paths
        assert ftp_login.called_once_with('tester@cloudside.net')
        assert ftp_retr.call_count == call_count


def test__find_reset_time(fake_rain_data):
    result = asos._find_reset_time(fake_rain_data)
    expected = 0
    assert result == expected


def test_process_precip(fake_rain_data):
    precip = fake_rain_data.to_frame('raw_precip')
    result = asos._process_precip(precip, 0, 'raw_precip')
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

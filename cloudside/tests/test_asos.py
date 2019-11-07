from datetime import datetime
import pathlib
import tempfile
import ftplib

import numpy
import pandas

from unittest import mock
import pytest
import numpy.testing as nptest
import pandas.util.testing as pdtest

from cloudside import asos
from .helpers import get_test_file, raises


@pytest.fixture
def fake_rain_data():
    rain_raw = [
        0.0,
        1.0,
        2.0,
        3.0,
        4.0,
        4.0,
        4.0,
        4.0,
        4.0,
        4.0,
        4.0,
        4.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        5.0,
        5.0,
        5.0,
        5.0,
        5.0,
        5.0,
        5.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
        2.0,
        3.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
    ]
    daterange = pandas.date_range(
        start="2001-01-01 11:55", end="2001-01-01 15:50", freq=asos.FIVEMIN
    )
    return pandas.Series(rain_raw, index=daterange)


@pytest.fixture
def asos_metar():
    teststring = (
        "24229KPDX PDX20170108090014901/08/17 09:00:31  5-MIN KPDX 081700Z "
        "10023G35KT 7SM -FZRA OVC065 00/M01 A2968 250 96 -1400 080/23G35 RMK "
        "AO2 PK WND 10035/1654 P0005 I1000 T00001006"
    )
    return asos.MetarParser(teststring, strict=False)


def retr_error(cmd, action):
    raise ftplib.error_perm


def test_MetarParser_datetime(asos_metar):
    assert asos_metar.datetime == datetime(2017, 1, 8, 9)


def test_MetarParser_asos_dict(asos_metar):
    result = asos_metar.asos_dict()
    expected = {
        "datetime": datetime(2017, 1, 8, 9),
        "raw_precipitation": 0.05,
        "temperature": 0.0,
        "dew_point": -0.6,
        "wind_speed": 23.0,
        "wind_direction": 100,
        "air_pressure": 250.0,
        "sky_cover": 1.0,
    }
    assert result == expected


@pytest.mark.parametrize(
    ("exists", "force", "call_count"),
    [(True, True, 1), (True, False, 0), (False, True, 1), (False, False, 1)],
)
@pytest.mark.parametrize("datestr", ["2016-01-01", "1999-01-01"])
@mock.patch("ftplib.FTP")
def test__fetch_file(ftp, exists, force, call_count, datestr):
    ts = pandas.Timestamp("2016-01-01")
    with tempfile.TemporaryDirectory() as rawdir:
        std_path = pathlib.Path(rawdir).joinpath(f"64010KPDX{ts.year}01.dat")
        if exists:
            std_path.touch()

        if ts.year == 1999 and call_count == 1:
            expected_path = None
        else:
            expected_path = std_path

        if expected_path is None:
            ftp.retrlines.side_effect = retr_error

        dst_path = asos._fetch_file("KPDX", ts, ftp, rawdir, force_download=force)
        assert dst_path == expected_path
        assert ftp.retrlines.call_count == call_count


@mock.patch.object(ftplib.FTP, "retrlines")
@mock.patch.object(ftplib.FTP, "login")
def test_fetch_files(ftp_login, ftp_retr):
    with tempfile.TemporaryDirectory() as rawdir:
        raw_paths = asos.fetch_files(
            "KPDX", "1999-10-01", "2000-02-01", "tester@cloudside.net", rawdir
        )
        assert isinstance(raw_paths, filter)
        assert all([(isinstance(rp, pathlib.Path) or (rp is None)) for rp in raw_paths])
        assert ftp_login.called_once_with("tester@cloudside.net")
        assert ftp_retr.call_count == 5


@pytest.mark.parametrize(("all_na", "expected"), [(False, 55), (True, 0)])
def test__find_reset_time(fake_rain_data, all_na, expected):
    if all_na:
        fake_rain_data.loc[:] = numpy.nan

    result = asos._find_reset_time(fake_rain_data)
    assert result == expected


def test_process_precip(fake_rain_data):
    precip = fake_rain_data.to_frame("raw_precip")
    result = asos._process_precip(precip, 55, "raw_precip")
    expected = numpy.array(
        [
            0.0,
            1.0,
            1.0,
            1.0,
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            5.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
            1.0,
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ]
    )
    nptest.assert_array_almost_equal(result, expected)


def test_parse_file():
    datpath = pathlib.Path(get_test_file("sample_asos.dat"))
    csvpath = pathlib.Path(get_test_file("sample_asos.csv"))
    result = asos.parse_file(datpath)
    expected = pandas.read_csv(csvpath, parse_dates=True, index_col=["datetime"])
    pdtest.assert_frame_equal(
        result.fillna(-9999), expected.fillna(-9999), check_less_precise=True
    )


@mock.patch("ftplib.FTP")
@mock.patch("cloudside.validate.unique_index")
@mock.patch("cloudside.asos._fetch_file")
@mock.patch("cloudside.asos.parse_file", return_value=pandas.Series([1, 2, 3]))
def test_get_data(parser, fetcher, checker, ftp):
    with tempfile.TemporaryDirectory() as topdir:
        asos.get_data(
            "KPDX", "2012-01-01", "2012-06-02", "test@cloudside.net", folder=topdir
        )
        assert fetcher.call_count == 6
        assert parser.call_count == 6

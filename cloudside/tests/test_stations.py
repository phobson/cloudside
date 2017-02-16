import shutil
from datetime import datetime
import os

import pytest
from unittest import mock

import numpy
import pandas
from urllib import request
import matplotlib.dates as mdates

import pytest

from cloudside import station


class FakeClass(object):
    def value(self):
        return 'item2'


def makeFakeRainData():
    tdelta = datetime(2001, 1, 1, 1, 5) - datetime(2001, 1, 1, 1, 0)
    start = datetime(2001, 1, 1, 12, 0)
    end = datetime(2001, 1, 1, 16, 0)
    daterange_num = mdates.drange(start, end, tdelta)
    daterange = mdates.num2date(daterange_num)

    rain_raw = [
        0.,  1.,  2.,  3.,  4.,  4.,  4.,  4.,  4.,  4.,  4.,  4.,
        0.,  0.,  0.,  0.,  0.,  5.,  5.,  5.,  5.,  5.,  5.,  5.,
        0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,
        1.,  2.,  3.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.,  0.
    ]

    return daterange, rain_raw


class Test_WeatherStation():
    def setup(self):
        self.max_attempts = 3
        self.sta = station.WeatherStation('KPDX', city='Portland', state='OR',
                                          country='Cascadia', lat=999, lon=999,
                                          max_attempts=self.max_attempts)
        self.sta2 = station.WeatherStation('MWPKO3', max_attempts=self.max_attempts)
        self.start = datetime(2012, 1, 1)
        self.end = datetime(2012, 2, 28)
        self.ts = pandas.DatetimeIndex(start=self.start, freq='D', periods=1)[0]

        self.dates, self.fakeprecip = makeFakeRainData()

    def teardown(self):
        datapath = os.path.join(os.getcwd(), 'data')
        if os.path.exists(datapath):
            shutil.rmtree(datapath)

    def test_attributes(self):
        attributes = ['sta_id', 'city', 'state', 'country', 'position',
                      'name', 'wunderground', 'asos', 'errorfile']
        for attr in attributes:
            assert hasattr(self.sta, attr)

    def test_find_dir(self):
        testdir = self.sta._find_dir('asos', 'raw')

        if os.path.sep == '/':
            knowndir = 'data/%s/asos/raw' % self.sta.sta_id
        else:
            knowndir = 'data\\%s\\asos\\raw' % self.sta.sta_id

        assert testdir == knowndir

    def test_find_file(self):
        testfile1 = self.sta._find_file(self.ts, 'asos', 'raw')
        testfile2 = self.sta._find_file(self.ts, 'wunderground', 'flat')

        knownfile1 = '%s_201201.dat' % self.sta.sta_id
        knownfile2 = '%s_20120101.csv' % self.sta.sta_id

        assert testfile1 == knownfile1
        assert testfile2 == knownfile2

    def test_set_cookies(self):
        assert isinstance(self.sta.asos, request.OpenerDirector)
        assert isinstance(self.sta.wunderground, request.OpenerDirector)

    def test_url_by_date(self):
        testurl1 = self.sta._url_by_date(self.ts, src='wunderground')
        testurl2 = self.sta._url_by_date(self.ts, src='asos')
        knownurl1 = "http://www.wunderground.com/history/airport/%s" \
                    "/2012/01/01/DailyHistory.html?&&theprefset=SHOWMETAR" \
                    "&theprefvalue=1&format=1" % self.sta.sta_id
        knownurl2 = "ftp://ftp.ncdc.noaa.gov/pub/data/asos-fivemin" \
                    "/6401-2012/64010%s201201.dat" % self.sta.sta_id

        assert testurl1 == knownurl1
        assert testurl2 == knownurl2

    def test_make_data_file(self):
        testfile1 = self.sta._make_data_file(self.ts, 'wunderground', 'flat')
        testfile2 = self.sta._make_data_file(self.ts, 'asos', 'raw')

        knownfile1 = os.path.join('data', self.sta.sta_id, 'wunderground',
                                  'flat', '{}_20120101.csv'.format(self.sta.sta_id))
        knownfile2 = os.path.join('data', self.sta.sta_id, 'asos',
                                  'raw', '{}_201201.dat'.format(self.sta.sta_id))

        assert testfile1 == knownfile1
        assert testfile2 == knownfile2

    def test_fetch_data(self):
        status_asos = self.sta._fetch_data(self.ts, 1, src='asos')
        status_wund = self.sta._fetch_data(self.ts, 1, src='wunderground')
        known_statuses = ['ok', 'bad', 'not there']
        assert status_asos in known_statuses
        assert status_wund in known_statuses

    def test_attempt_download(self):
        status_asos, attempt1 = self.sta._attempt_download(self.ts, src='asos')
        status_wund, attempt2 = self.sta._attempt_download(self.ts, src='wunderground')
        known_statuses = ['ok', 'bad', 'not there']
        assert status_asos in known_statuses
        assert status_wund in known_statuses
        self.ts2 = pandas.DatetimeIndex(start='1999-1-1', freq='D', periods=1)[0]
        status_fail, attempt3 = self.sta._attempt_download(self.ts2, src='asos')
        assert status_fail == 'not there'

        assert attempt1 <= self.max_attempts
        assert attempt2 <= self.max_attempts
        assert attempt3 == self.max_attempts

    def test_process_file_asos(self):
        filename, status = self.sta._process_file(self.ts, 'asos')

        if os.path.sep == '/':
            knownfile = 'data/%s/asos/flat/%s_201201.csv' % (self.sta.sta_id, self.sta.sta_id)
        else:
            knownfile = 'data\\%s\\asos\\flat\\%s_201201.csv' % (self.sta.sta_id, self.sta.sta_id)

        assert filename == knownfile
        known_statuses = ['ok', 'bad', 'not there']
        assert status in known_statuses

    def test_process_file_wunderground(self):
        filename, status = self.sta._process_file(self.ts, 'wunderground')

        if os.path.sep == '/':
            knownfile = 'data/%s/wunderground/flat/%s_20120101.csv' % (self.sta.sta_id, self.sta.sta_id)
        else:
            knownfile = 'data\\%s\\wunderground\\flat\\%s_20120101.csv' % (self.sta.sta_id, self.sta.sta_id)

        assert filename == knownfile
        known_statuses = ['ok', 'bad', 'not there']
        assert status in known_statuses

    def test_read_csv_asos(self):
        data, status = self.sta._read_csv(self.ts, 'asos')
        known_columns = ['Sta', 'Date', 'Precip', 'Temp',
                         'DewPnt', 'WindSpd', 'WindDir',
                         'AtmPress', 'SkyCover']
        for col in data.columns:
            assert col in known_columns

    def test_read_csv_wunderground(self):
        data, status = self.sta._read_csv(self.ts, 'wunderground')
        known_columns = ['Sta', 'Date', 'Precip', 'Temp',
                         'DewPnt', 'WindSpd', 'WindDir',
                         'AtmPress', 'SkyCover']
        for col in data.columns:
            assert col in known_columns

    def test_getASOSData(self):
        known_columns = ['Sta', 'Date', 'Precip', 'Temp',
                         'DewPnt', 'WindSpd', 'WindDir',
                         'AtmPress', 'SkyCover']
        df = self.sta.getASOSData(self.start, self.end)
        for col in df.columns:
            assert col in known_columns

        assert df.index.is_unique

    def test_getWundergroundData(self):
        known_columns = ['Sta', 'Date', 'Precip', 'Temp',
                         'DewPnt', 'WindSpd', 'WindDir',
                         'AtmPress', 'SkyCover']
        df = self.sta.getWundergroundData(self.start, self.end)
        for col in df.columns:
            assert col in known_columns

        assert df.index.is_unique

    def test_getDataBadSource(self):
        with pytest.raises(ValueError):
            self.sta._get_data(self.start, self.end, 'fart', None)

    def test_getDataGoodSource(self):
        self.sta._get_data(self.start, self.end, 'asos', None)

    def test_getDataSaveFile(self):
        self.sta._get_data(self.start, self.end, 'asos', 'testfile.csv')

    def test_parse_dates(self):
        datestrings = ['2012-6-4', 'September 23, 1982']
        knowndates = [datetime(2012, 6, 4), datetime(1982, 9, 23)]
        for ds, kd in zip(datestrings, knowndates):
            dd = station._parse_date(ds)
            assert dd.year == kd.year
            assert dd.month == kd.month
            assert dd.day == kd.day

    def test_date_asos(self):
        teststring = '24229KPDX PDX20010101000010001/01/01 00:00:31  5-MIN KPDX'
        knowndate = datetime(2001, 1, 1, 0, 0)
        assert station._date_ASOS(teststring) == knowndate

    def test_append_val(self):
        x = FakeClass()
        knownlist = ['item1', 'item2', 'NA']
        testlist = ['item1']
        testlist = station._append_val(x, testlist)
        testlist = station._append_val(None, testlist)
        assert testlist == knownlist

    def test_determine_reset_time(self):
        test_rt = station._determine_reset_time(self.dates, self.fakeprecip)
        known_rt = 0
        assert known_rt == test_rt

    def test_process_precip(self):
        p2 = station._process_precip(self.dates, self.fakeprecip)
        assert numpy.all(p2 <= self.fakeprecip)

    def test_process_sky_cover(self):
        teststring = 'METAR KPDX 010855Z 00000KT 10SM FEW010 OVC200 04/03 A3031 RMK AO2 SLP262 T00390028 53010 $'
        obs = station._Metar(teststring)
        testval = station._process_sky_cover(obs)
        assert testval == 1.0000

    def test_loadCompData_asos(self):
        self.sta.loadCompiledFile('asos', filename='testfile.csv')
        self.sta.loadCompiledFile('asos', filenum=1)

    def test_loadCompData_wunderground(self):
        self.sta.loadCompiledFile('wunderground', filename='testfile.csv')
        self.sta.loadCompiledFile('wunderground', filenum=1)

    def test_loadCompData_wunderground_nonairport(self):
        self.sta2.loadCompiledFile('wunder_nonairport', filename='testfile.csv')
        self.sta2.loadCompiledFile('wunder_nonairport', filenum=1)


def test_getAllStations():
    stations = station.getAllStations()
    assert isinstance(stations, dict)
    known_vals = ('BIST', 'Stykkisholmur', '', 'Iceland', '65-05N', '022-44W')
    assert stations['BIST'] == known_vals


def test_getStationByID():
    sta = station.getStationByID('KPDX')
    assert isinstance(sta, station.WeatherStation)
    assert sta.sta_id == 'KPDX'
    assert sta.city == 'Portland, Portland International Airport'
    assert sta.state == 'OR'
    assert sta.country == 'United States'
    assert sta.lat == '45-35-27N'
    assert sta.lon == '122-36-01W'


class BaseDataFetch_Mixin(object):
    def test_station_fetch_no_file(self):
        with mock.patch.object(self.station, self.fetcher_name) as gad:
            self.fetcher(self.station, '2012-1-1', '2012-2-1')
            gad.assert_called_once_with('2012-1-1', '2012-2-1', filename=None)

    def test_station_fetch_with_file(self):
        with mock.patch.object(self.station, self.fetcher_name) as gad:
            self.fetcher(self.station, '2012-1-1', '2012-2-1', filename='test.csv')
            gad.assert_called_once_with('2012-1-1', '2012-2-1', filename='test.csv')

    def test_string_fetch_no_file(self):
        with mock.patch.object(station.WeatherStation, self.fetcher_name) as gad:
            self.fetcher(self.sta_id, '2012-1-1', '2012-2-1')
            gad.assert_called_once_with('2012-1-1', '2012-2-1', filename=None)

    def test_string_fetch_with_file(self):
        with mock.patch.object(station.WeatherStation, self.fetcher_name) as gad:
            self.fetcher(self.sta_id, '2012-1-1', '2012-2-1', filename='test.csv')
            gad.assert_called_once_with('2012-1-1', '2012-2-1', filename='test.csv')


class Test_getASOSData(BaseDataFetch_Mixin):
    def setup(self):
        self.sta_id = 'KPDX'
        self.station = station.WeatherStation(self.sta_id)
        self.fetcher_name = 'getASOSData'
        self.fetcher = station.getASOSData


class Test_getWundergroundData(BaseDataFetch_Mixin):
    def setup(self):
        self.sta_id = 'KPDX'
        self.station = station.WeatherStation(self.sta_id)
        self.fetcher_name = 'getWundergroundData'
        self.fetcher = station.getWundergroundData


class Test_getWunderground_NonAirportData(BaseDataFetch_Mixin):
    def setup(self):
        self.sta_id = 'MWPKO3'
        self.station = station.WeatherStation(self.sta_id)
        self.fetcher_name = 'getWunderground_NonAirportData'
        self.fetcher = station.getWunderground_NonAirportData

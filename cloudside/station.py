# std lib stuff
import datetime
import os
import sys
import pdb
import codecs
from pkg_resources import resource_string
from urllib import request, error, parse
from http import cookiejar
import logging

# math stuff
import numpy
import pandas

# metar stuff
from metar import Metar, Datatypes

from . import validate

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(x):
        return x


__all__ = [
    'getAllStations',
    'getStationByID',
    'getASOSData',
    'getWundergroundData',
    'getWunderground_NonAirportData',
    'WeatherStation',
]


def _report_match(handler, match):
    """Report success or failure of the given handler function. (DEBUG)"""
    if not match:
        logging.debug('{} did not match'.format(handler.__name__))


class MetarParser(Metar.Metar):
    def __init__(self, metarcode, month=None, year=None, utcdelta=None,
                 errorfile=None):
        """Parse raw METAR code."""
        self.code = metarcode              # original METAR code
        self.type = 'METAR'                # METAR (routine) or SPECI (special)
        self.mod = "AUTO"                  # AUTO (automatic) or COR (corrected)
        self.station_id = None             # 4-character ICAO station code
        self.time = None                   # observation time [datetime]
        self.cycle = None                  # observation cycle (0-23) [int]
        self.wind_dir = None               # wind direction [direction]
        self.wind_speed = None             # wind speed [speed]
        self.wind_gust = None              # wind gust speed [speed]
        self.wind_dir_from = None          # beginning of range for win dir [direction]
        self.wind_dir_to = None            # end of range for wind dir [direction]
        self.vis = None                    # visibility [distance]
        self.vis_dir = None                # visibility direction [direction]
        self.max_vis = None                # visibility [distance]
        self.max_vis_dir = None            # visibility direction [direction]
        self.temp = None                   # temperature (C) [temperature]
        self.dewpt = None                  # dew point (C) [temperature]
        self.press = None                  # barometric pressure [pressure]
        self.runway = []                   # runway visibility (list of tuples)
        self.weather = []                  # present weather (list of tuples)
        self.recent = []                   # recent weather (list of tuples)
        self.sky = []                      # sky conditions (list of tuples)
        self.windshear = []                # runways w/ wind shear (list of strings)
        self.wind_speed_peak = None        # peak wind speed in last hour
        self.wind_dir_peak = None          # direction of peak wind speed in last hour
        self.peak_wind_time = None         # time of peak wind observation [datetime]
        self.wind_shift_time = None        # time of wind shift [datetime]
        self.max_temp_6hr = None           # max temp in last 6 hours
        self.min_temp_6hr = None           # min temp in last 6 hours
        self.max_temp_24hr = None          # max temp in last 24 hours
        self.min_temp_24hr = None          # min temp in last 24 hours
        self.press_sea_level = None        # sea-level pressure
        self.precip_1hr = None             # precipitation over the last hour
        self.precip_3hr = None             # precipitation over the last 3 hours
        self.precip_6hr = None             # precipitation over the last 6 hours
        self.precip_24hr = None            # precipitation over the last 24 hours
        self._trend = False                # trend groups present (bool)
        self._trend_groups = []            # trend forecast groups
        self._remarks = []                 # remarks (list of strings)
        self._unparsed_groups = []
        self._unparsed_remarks = []

        self._now = datetime.datetime.utcnow()
        if utcdelta:
            self._utcdelta = utcdelta
        else:
            self._utcdelta = datetime.datetime.now() - self._now

        self._month = month
        self._year = year

        code = self.code + " "
        try:
            ngroup = len(self.handlers)
            igroup = 0
            ifailed = -1
            while igroup < ngroup and code:
                pattern, handler, repeatable = self.handlers[igroup]
                logging.debug('{}: {}'.format(handler.__name__, code))
                m = pattern.match(code)
                while m:
                    ifailed = -1
                    _report_match(handler, m.group())
                    handler(self, m.groupdict())
                    code = code[m.end():]
                    if self._trend:
                        code = self._do_trend_handlers(code)
                    if not repeatable:
                        break

                    logging.debug('{}: {}'.format(handler.__name__, code))
                    m = pattern.match(code)

                if not m and ifailed < 0:
                    ifailed = igroup

                igroup += 1
                if igroup == ngroup and not m:
                    pattern, handler = (Metar.UNPARSED_RE, self._unparsed_group_handler)
                    logging.info('{}: {}'.format(handler.__name__, code))
                    m = pattern.match(code)
                    _report_match(handler, m.group())
                    handler(m.groupdict())
                    code = code[m.end():]
                    igroup = ifailed

                    # if it's still -2 when we run out of main-body
                    #  groups, we'll try parsing this group as a remark
                    ifailed = -2

            if pattern == Metar.REMARK_RE or self.press:
                while code:
                    for pattern, handler in self.remark_handlers:
                        logging.debug('{}: {}'.format(handler.__name__, code))
                        m = pattern.match(code)
                        if m:
                            _report_match(handler, m.group())
                            handler(self, m.groupdict())
                            code = pattern.sub("", code, 1)
                            break

        except Exception as err:
            logging.error("failed while processing '" + code + "'\n" + " ".join(err.args))

        if self._unparsed_groups:
            code = ' '.join(self._unparsed_groups)
            logging.info("Unparsed groups in body: " + code)

    def _unparsed_group_handler(self, d):
        """
        Handle otherwise unparseable main-body groups.
        """
        self._unparsed_groups.append(d['group'])


class WeatherStation(object):
    """An object representing a weather station.

    Parameters
    ----------
    sta_id : string
        The handles of the station. For airports, these are prefixed
        with a "K" (e.g., KPDX for the Portland International Airport)
    city, state, country : strings or None (default), optional
        The administrative location of the station.
    lat, lon : floats or None (default), optional
        The geographic coordinates (x, y) of the station.
    max_attempts : int, optional (default = 10)
        The upper limit to the number of times the downloaders will
        try to retrieve a file from the web.

    """

    def __init__(self, sta_id, city=None, state=None, country=None,
                 lat=None, lon=None, max_attempts=10, show_progress=False,
                 datadir=None, errorfile=None):
        self.sta_id = sta_id
        self.city = city
        self.state = state
        self.country = country
        self.position = Datatypes.position(lat, lon)
        self._max_attempts = max_attempts
        self.lat = lat
        self.lon = lon

        if show_progress:
            self.tracker = tqdm
        else:
            self.tracker = lambda x: x

        if self.state:
            self.name = "%s, %s" % (self.city, self.state)
        else:
            self.name = self.city

        self.datadir = datadir or os.path.join('data')
        self._errorfile = errorfile

        self._wunderground = None
        self._wunder_nonairport = None
        self._asos = None

    @property
    def errorfile(self):
        return self._errorfile

    @errorfile.setter
    def errorfile(self, value):
        self._errorfile = value

    @property
    def max_attempts(self):
        return self._max_attempts

    @max_attempts.setter
    def max_attempts(self, value):
        self._max_attempts = value

    @property
    def wunderground(self):
        if self._wunderground is None:
            self._wunderground = self._set_cookies(src='wunderground')
        return self._wunderground

    @property
    def wunder_nonairport(self):
        if self._wunder_nonairport is None:
            self._wunder_nonairport = self._set_cookies(src='wunder_nonairport')
        return self._wunder_nonairport

    @property
    def asos(self):
        if self._asos is None:
            self._asos = self._set_cookies(src='asos')
        return self._asos

    def _find_dir(self, src, step):
        '''
        returns a string representing the relative path to the requsted data

        input:
            *src* : 'asos' or 'wunderground'
            *step* : 'raw' or 'flat' or 'compile'
        '''
        src = validate.source(src)
        step = validate.step(step)
        return os.path.join(self.datadir, self.sta_id, src.lower(), step.lower())

    def _find_file(self, timestamp, src, step):
        '''
        returns a file name for a data file from the *src* based on the *timestamp*

        input:
            *timestamp* : pands timestamp object
            *src* : 'asos' or 'wunderground'
            *step* : 'raw' or 'flat'
        '''
        date = timestamp.to_pydatetime()
        src = validate.source(src)
        step = validate.step(step)

        if step == 'raw':
            ext = 'dat'
        else:
            ext = 'csv'

        if src.lower() in ['wunderground', 'wunder_nonairport'] or step == 'final':
            datefmtstr = '%Y%m%d'
        else:
            datefmtstr = '%Y%m'

        return '%s_%s.%s' % (self.sta_id, date.strftime(datefmtstr), ext)

    def _set_cookies(self, src):
        '''
        function that returns a urllib2 opener for retrieving data from *src*

        input:
            *src* : 'asos' or 'wunderground' or 'wunder_nonairport'
        '''
        jar = cookiejar.CookieJar()
        handler = request.HTTPCookieProcessor(jar)
        opener = request.build_opener(handler)
        URLs = {
            'wunderground': [
                'http://www.wunderground.com/history/airport/{}/2011/12/4/DailyHistory.html?',
                ('http://www.wunderground.com/cgi-bin/findweather/'
                 'getForecast?setpref=SHOWMETAR&value=1'),
                ('http://www.wunderground.com/history/airport/{}/2011/12/4/DailyHistory.html'
                 '?&&theprefset=SHOWMETAR&theprefvalue=1&format=1'),
            ],
            'asos': ['ftp://ftp.ncdc.noaa.gov/pub/data/asos-fivemin/'],
            'wunder_nonairport': [
                ('http://www.wunderground.com/weatherstation/WXDailyHistory.asp'
                 '?ID=MEGKO3&day=1&year=2013&month=1&graphspan=day&format=1')
            ]
        }

        urls_to_open = URLs.get(src.lower())
        try:
            for url in urls_to_open:
                opener.open(url.format(self.sta_id))
        except error.URLError:
            print('Unable to connect to {}. Working locally'.format(src))

        return opener

    def _url_by_date(self, timestamp, src='wunderground'):
        '''
        function that returns a url to retrieve data for a *timestamp*
        from the *src*

        input:
            *src* : 'asos' or 'wunderground'
            *timestamp* : pands timestamp object
        '''
        date = timestamp.to_pydatetime()
        "http://www.wunderground.com/history/airport/KDCA/1950/12/18/DailyHistory.html?format=1"
        src = validate.source(src)
        if src == 'wunderground':
            baseurl = 'http://www.wunderground.com/history/airport/{}'.format(
                self.sta_id
            )
            endurl = 'DailyHistory.html?&&theprefset=SHOWMETAR&theprefvalue=1&format=1'
            datestring = date.strftime('%Y/%m/%d')
            url = '{}/{}/{}'.format(baseurl, datestring, endurl)

        elif src == 'wunder_nonairport':
            baseurl = 'http://www.wunderground.com/weatherstation/WXDailyHistory.asp?'
            url = '{}ID={}&day={}&year={}&month={}&graphspan=day&format=1'.format(
                baseurl,
                self.sta_id,
                date.strftime('%d'),
                date.strftime('%Y'),
                date.strftime('%m')
            )

        elif src == 'asos':
            baseurl = 'ftp://ftp.ncdc.noaa.gov/pub/data/asos-fivemin/6401-'
            url = '%s%s/64010%s%s%02d.dat' % \
                  (baseurl, date.year, self.sta_id, date.year, date.month)
        else:
            raise ValueError("src must be 'wunderground' or 'asos'")

        return url

    def _make_data_file(self, timestamp, src, step):
        '''
        creates a data file for a *timestamp* from a *src* at a *step*

        input:
            *timestamp* : pands timestamp object
            *src* : 'asos' or 'wunderground'
            *step* : 'raw' or 'flat'
        '''
        src = validate.source(src)
        step = validate.step(step)
        destination = self._find_dir(src, step)
        datafile = self._find_file(timestamp, src, step)
        os.makedirs(destination, exist_ok=True)
        return os.path.join(destination, datafile)

    def _fetch_data(self, timestamp, attempt, src='asos', force_download=False):
        ''' method that downloads data from a *src* for a *timestamp*
        returns the status of the download
            ('ok', 'bad', 'not there')
        input:
        *timestamp* : pands timestamp object
        *src* : 'asos' or 'wunderground'
        *force_download* : bool; default False
        '''

        outname = self._make_data_file(timestamp, src, 'raw')
        status = 'not there'

        logging.basicConfig(filename=self.errorfile, filemode='a', level=logging.INFO)
        if not os.path.exists(outname) or force_download:
            url = self._url_by_date(timestamp, src=src)
            if src.lower() == 'wunderground':
                start = 2
                source = self.wunderground
            elif src.lower() == 'wunder_nonairport':
                start = 1
                source = self.wunder_nonairport
            elif src.lower() == 'asos':
                start = 0
                source = self.asos

            successful = False
            with open(outname, 'w') as outfile:
                try:
                    webdata = source.open(url)
                    for n, line in enumerate(codecs.iterdecode(webdata, 'utf-8')):
                        if n >= start:
                            if src != 'wunder_nonairport':
                                outfile.write(line)
                            else:
                                if line != '<br>\n':
                                    outfile.write(line.strip() + '\n')
                    successful = True

                except Exception as e:
                    logging.error('error parsing: %s\n' % (url,))

            if not successful:
                os.remove(outname)

        return validate.file_status(outname)

    def _attempt_download(self, timestamp, src, attempt=0):
        '''
        recursively calls _attempt_download at most *max_attempts* times.
        returns the status of the download
            ('ok', 'bad', 'not there')
        input:
            *timestamp* : a pandas timestamp object
            *src* : 'asos' or 'wunderground'
            *attempt* : the current attempt number
        '''
        attempt += 1
        status = self._fetch_data(timestamp, attempt, src=src)
        if status == 'not there' and attempt < self.max_attempts:
            status, attempt = self._attempt_download(timestamp, src, attempt=attempt)

        return status, attempt

    def _process_file(self, timestamp, src):
        '''
        processes a raw data file (*.dat) to a flat file (*csv).
        returns the filename and status of the download
            ('ok', 'bad', 'not there')

        input:
            *timestamp* : a pandas timestamp object
        '''
        src = validate.source(src)
        rawfilename = self._make_data_file(timestamp, src, 'raw')
        flatfilename = self._make_data_file(timestamp, src, 'flat')
        if not os.path.exists(rawfilename):
            rawstatus, attempt = self._attempt_download(timestamp, src, attempt=0)
        else:
            rawstatus = validate.file_status(rawfilename)

        if not os.path.exists(flatfilename) and rawstatus == 'ok':
            datain = open(rawfilename, 'r')
            dataout = open(flatfilename, 'w')

            if src.lower() in ['asos', 'wunderground']:

                headers = ('Sta,Date,Precip,Temp,DewPnt,'
                           'WindSpd,WindDir,AtmPress,SkyCover\n')
                dataout.write(headers)

                dates = []
                rains = []
                temps = []
                dewpt = []
                windspd = []
                winddir = []
                press = []
                cover = []

                for line in datain:
                    if src.lower() == 'asos':
                        metarstring = line
                        dates.append(_date_ASOS(metarstring))
                    elif src.lower() == 'wunderground':
                        row = line.split(',')
                        if len(row) > 2:
                            metarstring = row[-3]
                            datestring = row[-1].split('<')[0]
                            dates.append(_parse_date(datestring))
                        else:
                            metarstring = None

                    if metarstring is not None:
                        obs = MetarParser(metarstring, errorfile=self.errorfile)
                        rains = _append_val(obs.precip_1hr, rains, fillNone=0.0)
                        temps = _append_val(obs.temp, temps)
                        dewpt = _append_val(obs.dewpt, dewpt)
                        windspd = _append_val(obs.wind_speed, windspd)
                        winddir = _append_val(obs.wind_dir, winddir)
                        press = _append_val(obs.press, press)
                        cover.append(_process_sky_cover(obs))

                rains = numpy.array(rains)
                dates = numpy.array(dates)

                if src == 'asos':
                    reset_time = _determine_reset_time(dates, rains)
                    final_precip = _process_precip(dates, rains, reset_time)
                else:
                    final_precip = rains

                for row in zip([self.sta_id] * rains.shape[0], dates, final_precip,
                               temps, dewpt, windspd, winddir, press, cover):
                    dataout.write('%s,%s,%s,%s,%s,%s,%s,%s,%s\n' % row)

            else:
                headers = (
                    'Time,TemperatureC,DewpointC,PressurehPa,WindDirection,'
                    'WindDirectionDegrees,WindSpeedKMH,WindSpeedGustKMH,'
                    'Humidity,HourlyPrecipMM,Conditions,Clouds,dailyrainMM,'
                    'SolarRadiationWatts/m^2,SoftwareType,DateUTC\n'
                )

                dataout.write(datain.read())

            datain.close()
            dataout.close()

        flatstatus = validate.file_status(flatfilename)
        return flatfilename, flatstatus

    def _read_csv(self, timestamp, src):
        '''
        tries to retrieve data from the web from *src* for a *timestamp*
        returns a pandas dataframe if the download and prcoessing are
        successful. returns None if they fail.

        input:
            *timestamp* : a pandas timestamp object
            *src* : 'asos' or 'wunderground'
        '''
        if src in ['asos', 'wunderground']:
            icol = 1
        elif src == 'wunder_nonairport':
            icol = 0
        headerrows = {
            'asos': 0,
            'wunderground': 0,
            'wunder_nonairport': 1
        }
        flatfilename = self._make_data_file(timestamp, src, 'flat')
        if not os.path.exists(flatfilename):
            flatfilename, flatstatus = self._process_file(timestamp, src)

        flatstatus = validate.file_status(flatfilename)
        if flatstatus == 'ok':
            data = pandas.read_csv(flatfilename, index_col=False, parse_dates=[icol],
                                   header=headerrows[src])
            data.set_index(data.columns[icol], inplace=True)

        else:
            data = None
            flatstatus = 'missing'

        return data, flatstatus

    def _get_data(self, startdate, enddate, source, filename):
        '''
        This function will return data in the form of a pandas dataframe
        for the station between *startdate* and *enddate*.

        Input:
            *startdate* : string representing the earliest date for the data
            *enddate* : string representing the latest data for the data
            *source* : string indicating where the data will come from
                can in "asos" or "wunderground"

        Returns:
            *data* : a pandas data frame of the data for this station
        '''
        source = validate.source(source)

        freq = {
            'asos': 'MS',
            'wunderground': 'D',
            'wunder_nonairport': 'D'
        }

        timestamps = pandas.DatetimeIndex(start=startdate, end=enddate,
                                          freq=freq[source])
        data = None
        for n, ts in self.tracker(enumerate(timestamps)):
            if data is None:
                data, status = self._read_csv(ts, source)
            else:
                newdata, status = self._read_csv(ts, source)
                data = data.append(newdata)

        # corrected data are appended to the bottom of the ASOS files by NCDC
        # QA people. So for any given date/time index, we want the *last* row
        # that appeared in the data file.
        final_data = data.groupby(level=0).last()

        if filename is not None:
            compdir = self._find_dir(source, 'compile')
            os.makedirs(compdir, exist_ok=True)
            final_data.to_csv(os.path.join(compdir, filename))

        return final_data

    def getASOSData(self, startdate, enddate, filename=None):
        """Downloads ASOS data to a file and returns a dataframe.

        Parameters
        ----------
        startdate, endate : date-like object or date string
            The time windows for which data should be downloaded
        filename : string, optional
            Path and filename of where the data should be saved

        Returns
        -------
        data : pandas.DataFrame

        Examples
        --------
        >>> import cloudside
        >>> startdate = '2012-01-01'
        >>> enddate = 'September 30, 2012'
        >>> fname = 'PDX_Q1thruQ3.csv'
        >>> pdx = cloudside.getStationByID('KPDX')
        >>> data = pdx.getASOSdata(startdate, enddate, filename=fname)

        Notes
        -----
        ASOS data can have quality issues. At a bare minimum, we recommend the
        following:

          1. Screen for unreasonably high values in the ASOS data. This can
             happen. They stick out like a sore thumb when sorting or plotting
             the data. Just remove them.
          2. Compare monthly and daily totals between the ASOS data and the
             co-located NCDC hourly station (available for free download at
             NCDC website). The NCDC hourly data have better quality control.
             Where there are significant deviations, this can indicate anomalous
             data that can be removed. Sometimes this can result from a stuck
             gage etc. This might not show up as an extreme value, but could be
             an unusual pattern (e.g., 0.2 in/hr intensity continually for a
             week)

        """

        return self._get_data(startdate, enddate, 'asos', filename)

    def getWundergroundData(self, startdate, enddate, filename=None):
        '''
        This function will return Wunderground data in the form of a pandas dataframe
        for the station between *startdate* and *enddate*.

        Input:
            *startdate* : string representing the earliest date for the data
            *enddate* : string representing the latest data for the data

        Returns:
            *data* : a pandas data frame of the Wunderground data for this station

        Example:
        >>> import metar.Station as Station
        >>> startdate = '2012-1-1'
        >>> enddate = 'September 30, 2012'
        >>> pdx = Station.getStationByID('KPDX')
        >>> data = pdx.getWundergroundData(startdate, enddate)
        '''
        return self._get_data(startdate, enddate, 'wunderground', filename)

    def getWunderground_NonAirportData(self, startdate, enddate, filename=None):
        '''
        This function will return non-airport Wunderground data in the form of a pandas dataframe
        for the station between *startdate* and *enddate*.

        Input:
            *startdate* : string representing the earliest date for the data
            *enddate* : string representing the latest data for the data

        Returns:
            *data* : a pandas data frame of the Wunderground data for this station

        Example:
        >>> import metar.Station as Station
        >>> startdate = '2012-1-1'
        >>> enddate = 'September 30, 2012'
        >>> pdx = Station.getStationByID('KPDX')
        >>> data = pdx.getWunderground_NonAirportData(startdate, enddate)
        '''
        return self._get_data(startdate, enddate, 'wunder_nonairport', filename)

    def _get_compiled_files(self, source):
        compdir = self._find_dir(source, 'compile')
        os.makedirs(compdir, exist_ok=True)
        compfiles = os.listdir(compdir)
        return compdir, compfiles

    def showCompiledFiles(self, source):
        compdir, compfiles = self._get_compiled_files(source)
        if len(compfiles) == 0:
            print('No compiled files')

        for n, cf in enumerate(compfiles):
            cfile = open(os.path.join(compdir, cf), 'r')
            cdata = cfile.readlines()
            start = cdata[1].split(',')[0]
            end = cdata[-1].split(',')[0]
            cfile.close()
            print(('%d) %s - start: %s\tend: %s' % (n + 1, cf, start, end)))

    def loadCompiledFile(self, source, filename=None, filenum=None):
        if filename is None and filenum is None:
            raise ValueError("must specify either a file name or number")

        compdir, compfiles = self._get_compiled_files(source)
        N = len(compfiles)
        if N > 0:
            if filenum is not None:
                if 0 < filenum <= N:
                    filename = compfiles[filenum - 1]
                else:
                    raise ValueError('file number must be between 1 and %d' % N)
            elif filename not in compfiles:
                raise ValueError('filename does not exist')

            cfilepath = os.path.join(compdir, filename)
            data = pandas.read_csv(cfilepath, index_col=0, parse_dates=True)

        else:
            print('No files to load')
            data = None

        return data


def _parse_date(datestring):
    '''
    takes a date string and returns a datetime.datetime object
    '''
    return pandas.Timestamp(datestring).to_pydatetime()


def _date_ASOS(metarstring):
    '''get date/time of asos reading'''
    yr = int(metarstring[13:17])   # year
    mo = int(metarstring[17:19])   # month
    da = int(metarstring[19:21])   # day
    hr = int(metarstring[37:39])   # hour
    mi = int(metarstring[40:42])   # minute

    date = datetime.datetime(yr, mo, da, hr, mi)

    return date


def _append_val(obsval, listobj, fillNone='NA'):
    '''
    appends attribute of an object to a list. if attribute does
    not exist or is none, appends the *fillNone* value instead.
    '''
    if obsval is not None and hasattr(obsval, 'value'):
        listobj.append(obsval.value())
    else:
        listobj.append(fillNone)
    return listobj


def _determine_reset_time(date, precip):
    '''
    determines the precip gauge reset time for a month's
    worth of ASOS data.
    '''
    minutes = numpy.zeros(12)
    if len(date) != len(precip):
        raise ValueError("date and precip must be same length")
    else:
        for n in range(1, len(date)):
            if precip[n] < precip[n - 1]:
                minuteIndex = int(date[n].minute / 5)
                minutes[minuteIndex] += 1

        resetTime, = numpy.where(minutes == minutes.max())
        return resetTime[0] * 5


def _process_precip(dateval, p1, reset_time):
    '''convert 5-min rainfall data from cumuative w/i an hour to 5-min totals
    p = precip data (list)
    dt = list of datetime objects
    RT = point in the hour when the tip counter resets
    '''
    p2 = numpy.zeros(len(p1))
    p2[0] = p1[0]
    for n in range(1, len(p1)):

        tdelta_minutes = (dateval[n] - dateval[n - 1]).seconds / 60
        if p1[n] < p1[n - 1] or dateval[n].minute == reset_time or tdelta_minutes != 5:
            p2[n] = p1[n]

        else:
            p2[n] = (float(p1[n]) - float(p1[n - 1]))

    return p2


def _process_sky_cover(obs):
    coverdict = {
        'CLR': 0.0000,
        'SKC': 0.0000,
        'NSC': 0.0000,
        'NCD': 0.0000,
        'FEW': 0.1785,
        'SCT': 0.4375,
        'BKN': 0.7500,
        'VV': 0.9900,
        'OVC': 1.0000
    }
    coverlist = []
    for sky in obs.sky:
        coverval = coverdict[sky[0]]
        coverlist.append(coverval)

    if len(coverlist) > 0:
        cover = numpy.max(coverlist)
    else:
        cover = 'NA'

    return cover


def getAllStations():
    stations = {}

    lines = resource_string('cloudside.tests.data', 'nsd_cccc.txt').decode('UTF-8').splitlines()

    for line in lines:
        f = line.strip().split(";")
        stations[f[0]] = (f[0], f[3], f[4], f[5], f[7], f[8])

    return stations


def getStationByID(sta_id):
    stations = getAllStations()
    try:
        info = stations[sta_id]
        sta = WeatherStation(sta_id, city=info[1], state=info[2],
                             country=info[3], lat=info[4], lon=info[5])
    except KeyError:
        sta = WeatherStation(sta_id)

    return sta


def _get_data(station, startdate, enddate, source, filename):
    if not isinstance(station, WeatherStation):
        station = getStationByID(station)
        station.errorfile = '{}.log'.format(station.sta_id)

    return station._get_data(startdate, enddate, source, filename=filename)


def getASOSData(station, startdate, enddate, filename=None):
    return _get_data(station, startdate, enddate, 'asos', filename)


def getWundergroundData(station, startdate, enddate, filename=None):
    return _get_data(station, startdate, enddate, 'wunderground', filename)


def getWunderground_NonAirportData(station, startdate, enddate, filename=None):
    return _get_data(station, startdate, enddate, 'wunder_nonairport', filename)

#!/usr/bin/python
#
#  A python package for interpreting METAR and SPECI weather reports.
#
#  US conventions for METAR/SPECI reports are described in chapter 12 of
#  the Federal Meteorological Handbook No.1. (FMH-1 1995), issued by NOAA.
#  See <http://metar.noaa.gov/>
#
#  International conventions for the METAR and SPECI codes are specified in
#  the WMO Manual on Codes, vol I.1, Part A (WMO-306 I.i.A).
#
#  This module handles a reports that follow the US conventions, as well
#  the more general encodings in the WMO spec.  Other regional conventions
#  are not supported at present.
#
#  The current METAR report for a given station is available at the URL
#  http://weather.noaa.gov/pub/data/observations/metar/stations/<station>.TXT
#  where <station> is the four-letter ICAO station code.
#
#  The METAR reports for all reporting stations for any "cycle" (i.e., hour)
#  in the last 24 hours is available in a single file at the URL
#  http://weather.noaa.gov/pub/data/observations/metar/cycles/<cycle>Z.TXT
#  where <cycle> is a 2-digit cycle number (e.g., "00", "05" or "23").
#
#  Copyright 2004-2009  Tom Pollard
#  All rights reserved.
#
__author__ = "Paul Hobson"

__email__ = "pmhobson@gmail.com"

__version__ = "0.1"


from .station import *
from .exporters import *
from . import viz
from . import ncdc

import os
import sys
from pkg_resources import resource_filename

import nose.tools as ntools
import datetime as dt
import pandas
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.testing.decorators import image_comparison, cleanup

from cloudside import station
from cloudside import viz


@ntools.nottest
def get_test_data():
    csvfile = resource_filename("cloudside.tests.data", 'data_for_viz_tests.csv')
    df = pandas.read_csv(csvfile, parse_dates=True, index_col=0)
    return df


@image_comparison(baseline_images=['rain_clock'], extensions=['png'])
def test_rainclock():
    df = get_test_data()
    fig = viz.rainClock(df)


@image_comparison(baseline_images=['rose_mph', 'rose_kt'], extensions=['png'])
def test_windrose():
    df = get_test_data()
    fig1 = viz.windRose(df, mph=True)
    fig2 = viz.windRose(df, mph=False)


@image_comparison(
    baseline_images=[
        'hyetograph_5min',
        'hyetograph_hourly',
        'hyetograph_daily',
        'hyetograph_weekly',
    ],
    extensions=['png']
)
def test_hyetograph():
    df = get_test_data()
    for freq in ['5min', 'hourly', 'daily', 'weekly']:
        fig = viz.hyetograph(df, freq=freq)


@image_comparison(
    baseline_images=[
        'psychromograph_5min',
        'psychromograph_hourly',
        'psychromograph_daily',
        'psychromograph_weekly',
    ],
    extensions=['png']
)
def test_psychromograph():
    df = get_test_data()
    for freq in ['5min', 'hourly', 'daily', 'weekly']:
        fig = viz.psychromograph(df, freq=freq)


@image_comparison(
    baseline_images=[
        'temperaturePlot_5min',
        'temperaturePlot_hourly',
        'temperaturePlot_daily',
        'temperaturePlot_weekly',
    ],
    extensions=['png']
)
def test_temperaturePlot():
    df = get_test_data()
    for freq in ['5min', 'hourly', 'daily', 'weekly']:
        fig = viz.temperaturePlot(df, freq=freq)

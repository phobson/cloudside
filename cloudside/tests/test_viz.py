import os
import sys
from pkg_resources import resource_filename
from io import StringIO
from textwrap import dedent

import datetime as dt
import pandas
import matplotlib
import matplotlib.pyplot as plt

import pytest
import numpy.testing as nptest
import pandas.util.testing as pdtest

from cloudside import station
from cloudside import viz


BASELINE_DIR = 'baseline_images/viz_tests'
TOLERANCE = 21


@pytest.fixture
def test_data():
    csvfile = resource_filename("cloudside.tests.data", 'data_for_viz_tests.csv')
    df = pandas.read_csv(csvfile, parse_dates=True, index_col=0)
    return df


@pytest.fixture
def frequencies():
    return ['5min', 'hourly', 'daily', 'weekly']


@pytest.mark.mpl_image_compare(baseline_dir=BASELINE_DIR, tolerance=TOLERANCE)
def test_rainclock(test_data):
    fig = viz.rainClock(test_data)
    return fig


@pytest.mark.mpl_image_compare(baseline_dir=BASELINE_DIR, tolerance=TOLERANCE)
def test_windrose(test_data):
    fig, (ax1, ax2) = plt.subplots(figsize=(12, 5), ncols=2, subplot_kw=dict(polar=True))
    _ = viz.windRose(test_data.assign(WindSpd=test_data['WindSpd'] * 1.15), spd_units='mph', ax=ax1)
    _ = viz.windRose(test_data, spd_units='kt', ax=ax2)
    return fig


def test__compute_windrose(test_data):
    expected = pandas.read_csv(StringIO(dedent("""\
        Dir_bins,calm,0 - 5 ,5 - 10 ,10 - 20 ,20 - 30 ,">30 "
        0.0,0.0,0.0,0.0,0.0,0.0,0.003282
        15.0,0.003482,0.0006,0.0,0.008765,0.0,0.003282
        30.0,0.002161,0.0,0.0,0.003842,0.0,0.003282
        45.0,0.006844,0.0,0.0,0.005283,0.0,0.003282
        60.0,0.001201,0.002401,0.0,0.002401,0.0,0.003282
        75.0,0.010926,0.02005,0.0,0.033617,0.0,0.003282
        90.0,0.009125,0.012607,0.00012,0.018129,0.0,0.003282
        105.0,0.030136,0.006483,0.0,0.052227,0.0,0.003282
        120.0,0.010085,0.0,0.0,0.005643,0.0,0.003282
        135.0,0.015848,0.0,0.0,0.005163,0.0,0.003282
        150.0,0.004923,0.00012,0.0,0.002401,0.0,0.003282
        165.0,0.013207,0.00024,0.0,0.011166,0.0,0.003282
        180.0,0.004442,0.00072,0.0,0.009365,0.0,0.003282
        195.0,0.009125,0.00048,0.0,0.008044,0.0,0.003282
        210.0,0.004202,0.0,0.0,0.003122,0.0,0.003282
        225.0,0.014287,0.002401,0.0,0.015368,0.0,0.003282
        240.0,0.004202,0.002281,0.0,0.009725,0.0,0.003282
        255.0,0.005043,0.011286,0.00024,0.013087,0.0,0.003282
        270.0,0.007204,0.007564,0.00012,0.006964,0.0,0.003282
        285.0,0.012607,0.01993,0.00084,0.028335,0.0,0.003282
        300.0,0.006123,0.027734,0.002761,0.014167,0.0,0.003282
        315.0,0.014167,0.107696,0.004923,0.048745,0.0,0.003282
        330.0,0.006964,0.030736,0.00084,0.028695,0.0,0.003282
        345.0,0.010565,0.013687,0.0,0.022932,0.0,0.003282
    """)), index_col=['Dir_bins'])

    columns = pandas.CategoricalIndex(
        data=['calm', '0 - 5 ', '5 - 10 ', '10 - 20 ', '20 - 30 ', '>30 '],
        categories=['calm', '0 - 5 ', '5 - 10 ', '10 - 20 ', '20 - 30 ', '>30 '],
        ordered=True, name='Spd_bins', dtype='category'
    )

    index = pandas.CategoricalIndex(
        data=[0.0,  15.0,  30.0,  45.0,  60.0,  75.0,  90.0, 105.0,
         120.0, 135.0, 150.0, 165.0, 180.0, 195.0, 210.0, 225.0,
         240.0, 255.0, 270.0, 285.0, 300.0, 315.0, 330.0, 345.0],
        categories=[0.0,  15.0,  30.0,  45.0,  60.0,  75.0,  90.0, 105.0,
         120.0, 135.0, 150.0, 165.0, 180.0, 195.0, 210.0, 225.0,
         240.0, 255.0, 270.0, 285.0, 300.0, 315.0, 330.0, 345.0],
        ordered=True, name='Dir_bins', dtype='category'
    )
    expected.columns = columns
    expected.index = index

    rose = viz._compute_windrose(test_data)

    nptest.assert_allclose(rose.values, expected.values, rtol=0.001)
    nptest.assert_array_equal(rose.columns.values, expected.columns.values)
    nptest.assert_array_equal(rose.index.values, expected.index.values)


def test__compute_windorose_short_record():
    expected = pandas.read_csv(StringIO(dedent("""\
        Dir_bins,calm,0 - 5 ,5 - 10 ,10 - 20 ,20 - 30 ,">30 "
        0.0,0.0,0.0,0.0,0.0,0.0,0.0
        15.0,0.0,0.0,0.0,0.0,0.0,0.0
        30.0,0.0,0.0,0.0,0.0,0.0,0.0
        45.0,0.0,0.0,0.0,0.0,0.0,0.0
        60.0,0.0,0.0,0.0,0.0,0.0,0.0
        75.0,0.0,0.0,0.0,0.0,0.0,0.0
        90.0,0.0,0.0,0.0,0.0,0.0,0.0
        105.0,0.0,0.0,0.0,0.0,0.0,0.0
        120.0,0.0,0.0,0.0,0.0,0.0,0.0
        135.0,0.0,0.0,0.0,0.0,0.0,0.0
        150.0,0.0,0.0,0.0,0.0,0.0,0.0
        165.0,0.0,0.0,0.0,0.0,0.0,0.0
        180.0,0.125,0.0,0.0,0.0,0.0,0.0
        195.0,0.0,0.0,0.0,0.125,0.0,0.0
        210.0,0.0,0.0,0.0,0.0,0.0,0.0
        225.0,0.25,0.0,0.0,0.0,0.0,0.0
        240.0,0.125,0.0,0.0,0.125,0.0,0.0
        255.0,0.125,0.0,0.0,0.0,0.0,0.0
        270.0,0.0,0.0,0.0,0.0,0.0,0.0
        285.0,0.125,0.0,0.0,0.0,0.0,0.0
        300.0,0.0,0.0,0.0,0.0,0.0,0.0
        315.0,0.0,0.0,0.0,0.0,0.0,0.0
        330.0,0.0,0.0,0.0,0.0,0.0,0.0
        345.0,0.0,0.0,0.0,0.0,0.0,0.0
    """)), index_col=['Dir_bins']).rename_axis('Spd_bins', axis='columns')

    data = pandas.read_csv(StringIO(dedent("""\
        Date,Sta,Precip,Temp,DewPnt,WindSpd,WindDir,AtmPress,SkyCover
        1971-09-07 00:00:00,KGRB,0.0,25.0,15.0,8.0,240.0,1010.5,0.75
        1971-09-07 03:00:00,KGRB,0.0,18.9,13.9,5.0,260.0,1011.6,0.4375
        1971-09-07 06:00:00,KGRB,0.0,16.7,12.8,4.0,280.0,1012.5,0.0
        1971-09-07 09:00:00,KGRB,0.0,12.8,11.7,4.0,220.0,1013.6,0.0
        1971-09-07 12:00:00,KGRB,0.0,13.3,11.1,3.0,230.0,1014.8,0.0
        1971-09-07 15:00:00,KGRB,0.0,22.2,16.1,4.0,180.0,1015.4,0.0
        1971-09-07 18:00:00,KGRB,0.0,26.7,15.6,5.0,240.0,1014.2,0.0
        1971-09-07 21:00:00,KGRB,0.0,28.9,15.0,7.0,200.0,1012.6,0.0
    """)), parse_dates=True, index_col=['Date'])

    rose = viz._compute_windrose(data)

    nptest.assert_allclose(rose.values, expected.values, rtol=0.001)
    nptest.assert_array_equal(rose.columns.values, expected.columns.values)
    nptest.assert_array_equal(rose.index.values, expected.index.values)


@pytest.mark.mpl_image_compare(baseline_dir=BASELINE_DIR, tolerance=TOLERANCE)
def test_hyetograph(test_data, frequencies):
    fig, axes = plt.subplots(ncols=2, nrows=2, figsize=(9, 9))
    for freq, ax in zip(frequencies, axes.flat):
        fig = viz.hyetograph(test_data, freq=freq, ax=ax)
    return fig


@pytest.mark.mpl_image_compare(baseline_dir=BASELINE_DIR, tolerance=TOLERANCE)
def test_psychromograph(test_data, frequencies):
    fig, axes = plt.subplots(ncols=2, nrows=2, figsize=(9, 9))
    for freq, ax in zip(frequencies, axes.flat):
        fig = viz.psychromograph(test_data, freq=freq, ax=ax)
    return fig


@pytest.mark.mpl_image_compare(baseline_dir=BASELINE_DIR, tolerance=TOLERANCE)
def test_temperaturePlot(test_data, frequencies):
    fig, axes = plt.subplots(ncols=2, nrows=2, figsize=(9, 9))
    for freq, ax in zip(frequencies, axes.flat):
        fig = viz.temperaturePlot(test_data, freq=freq, ax=ax)
    return fig

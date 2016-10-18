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
        Dir_bins,calm,0 - 5 ,5 - 10 ,10 - 20 ,20 - 30
        0.0,0.003281706,0.0,0.0,0.0,0.0
        15.0,0.003281706,0.003481811,0.008764558,0.000600312,0.0
        30.0,0.003281706,0.002161124,0.003841998,0.0,0.0
        45.0,0.003281706,0.006843559,0.005282747,0.0,0.0
        60.0,0.003281706,0.001200624,0.002401249,0.002401249,0.0
        75.0,0.003281706,0.010925681,0.033617481,0.020050426,0.0
        90.0,0.003281706,0.009124745,0.018129427,0.012606555,0.000120062
        105.0,0.003281706,0.030135671,0.052227158,0.006483371,0.0
        120.0,0.003281706,0.010085244,0.005642934,0.0,0.0
        135.0,0.003281706,0.015848241,0.005162685,0.0,0.0
        150.0,0.003281706,0.00492256,0.002401249,0.000120062,0.0
        165.0,0.003281706,0.013206868,0.011165806,0.000240125,0.0
        180.0,0.003281706,0.00444231,0.00936487,0.000720375,0.0
        195.0,0.003281706,0.009124745,0.008044183,0.00048025,0.0
        210.0,0.003281706,0.004202185,0.003121623,0.0,0.0
        225.0,0.003281706,0.014287429,0.015367991,0.002401249,0.0
        240.0,0.003281706,0.004202185,0.009725057,0.002281186,0.0
        255.0,0.003281706,0.005042622,0.013086805,0.011285869,0.000240125
        270.0,0.003281706,0.007203746,0.006963621,0.007563933,0.000120062
        285.0,0.003281706,0.012606555,0.028334734,0.019930364,0.000840437
        300.0,0.003281706,0.006123184,0.014167367,0.027734422,0.002761436
        315.0,0.003281706,0.014167367,0.048745348,0.107696002,0.00492256
        330.0,0.003281706,0.006963621,0.028694921,0.030735983,0.000840437
        345.0,0.003281706,0.010565494,0.022931925,0.013687117,0.0
    """)), index_col=['Dir_bins'])

    columns = pandas.CategoricalIndex(
        data=['calm', '0 - 5 ', '5 - 10 ', '10 - 20 ', '20 - 30 '],
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

    pdtest.assert_frame_equal(
        rose, expected,
        check_index_type=False,
        check_column_type=False,
        check_less_precise=True
    )


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

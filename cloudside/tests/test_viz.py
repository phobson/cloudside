from pkg_resources import resource_filename
from io import StringIO
from textwrap import dedent
import warnings

from matplotlib import figure
import pandas

import pytest
import numpy.testing as nptest
import pandas.util.testing as pdtest

from cloudside import station
from cloudside import viz


IMG_OPTS = dict(
    tolerance=21,
    baseline_dir='baseline_images/viz_tests'
)


def quiet_layout(fig):
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        fig.tight_layout()


def _make_polar_fig():
    fig = figure.Figure(figsize=(12, 5))
    ax1 = fig.add_subplot(1, 2, 1, polar=True)
    ax2 = fig.add_subplot(1, 2, 2, polar=True)
    return fig, ax1, ax2


def _make_ts_fig():
    fig = figure.Figure(figsize=(9, 9))
    ax1 = fig.add_subplot(2, 2, 1)
    ax2 = fig.add_subplot(2, 2, 2, sharex=ax1)
    ax3 = fig.add_subplot(2, 2, 3, sharex=ax1)
    ax4 = fig.add_subplot(2, 2, 4, sharex=ax1)
    return fig, [ax1, ax2, ax3, ax4]


@pytest.fixture
def test_data():
    csvfile = resource_filename("cloudside.tests.data", 'data_for_viz_tests.csv')
    df = pandas.read_csv(csvfile, parse_dates=True, index_col=0)
    return df


@pytest.fixture
def short_data():
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
    return data


@pytest.fixture
def frequencies():
    return ['5min', 'hourly', 'daily', 'weekly']


@pytest.fixture
def rose_index():
    index = pandas.CategoricalIndex(
        data=[
            0.0,  15.0,  30.0,  45.0,  60.0,  75.0,  90.0, 105.0,
            120.0, 135.0, 150.0, 165.0, 180.0, 195.0, 210.0, 225.0,
            240.0, 255.0, 270.0, 285.0, 300.0, 315.0, 330.0, 345.0
        ],
        categories=[
            0.0,  15.0,  30.0,  45.0,  60.0,  75.0,  90.0, 105.0,
            120.0, 135.0, 150.0, 165.0, 180.0, 195.0, 210.0, 225.0,
            240.0, 255.0, 270.0, 285.0, 300.0, 315.0, 330.0, 345.0
        ],
        ordered=True, name='Dir_bins', dtype='category'
    )
    return index


@pytest.mark.mpl_image_compare(**IMG_OPTS)
def test_rain_clock(test_data):
    fig = viz.rain_clock(test_data, raincol='Precip')
    quiet_layout(fig)
    return fig


@pytest.mark.mpl_image_compare(**IMG_OPTS)
def test_rose(test_data):
    fig, ax1, ax2 = _make_polar_fig()
    _ = viz.rose(test_data.assign(WindSpd=test_data['WindSpd'] * 1.15),
                 'WindSpd', 'WindDir', spd_units='mph', ax=ax1)
    _ = viz.rose(test_data, 'WindSpd', 'WindDir', spd_units='kt', ax=ax2)
    quiet_layout(fig)
    return fig


@pytest.mark.mpl_image_compare(**IMG_OPTS)
def test_windrose_short(short_data):
    fig, ax1, ax2 = _make_polar_fig()
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        _ = viz.windRose(short_data.assign(WindSpd=short_data['WindSpd'] * 1.15),
                        spd_units='mph', ax=ax1, spdcol='WindSpd', dircol='WindDir')
        _ = viz.windRose(short_data, spdcol='WindSpd', dircol='WindDir',
                        spd_units='kt', ax=ax2)
    quiet_layout(fig)
    return fig


@pytest.mark.mpl_image_compare(**IMG_OPTS)
def test_rose_short(short_data):
    fig, ax1, ax2 = _make_polar_fig()
    _ = viz.rose(short_data.assign(WindSpd=short_data['WindSpd'] * 1.15),
                 'WindSpd', 'WindDir', spd_units='mph', ax=ax1)
    _ = viz.rose(short_data, 'WindSpd', 'WindDir', spd_units='kt', ax=ax2)
    quiet_layout(fig)
    return fig


def test__compute_rose(test_data, rose_index):
    expected = pandas.read_csv(StringIO(dedent("""\
        Dir_bins,calm,0 - 5 ,5 - 10 ,10 - 20 ,20 - 30 ,">30 "
        0.0,0.0032817,0.0,0.0,0.0,0.0,0.0
        15.0,0.0032817,0.0034818,0.0087646,0.0006003,0.0,0.0
        30.0,0.0032817,0.0021611,0.003842,0.0,0.0,0.0
        45.0,0.0032817,0.0068436,0.0052827,0.0,0.0,0.0
        60.0,0.0032817,0.0012006,0.0024012,0.0024012,0.0,0.0
        75.0,0.0032817,0.0109257,0.0336175,0.0200504,0.0,0.0
        90.0,0.0032817,0.0091247,0.0181294,0.0126066,0.0001201,0.0
        105.0,0.0032817,0.0301357,0.0522272,0.0064834,0.0,0.0
        120.0,0.0032817,0.0100852,0.0056429,0.0,0.0,0.0
        135.0,0.0032817,0.0158482,0.0051627,0.0,0.0,0.0
        150.0,0.0032817,0.0049226,0.0024012,0.0001201,0.0,0.0
        165.0,0.0032817,0.0132069,0.0111658,0.0002401,0.0,0.0
        180.0,0.0032817,0.0044423,0.0093649,0.0007204,0.0,0.0
        195.0,0.0032817,0.0091247,0.0080442,0.0004802,0.0,0.0
        210.0,0.0032817,0.0042022,0.0031216,0.0,0.0,0.0
        225.0,0.0032817,0.0142874,0.015368,0.0024012,0.0,0.0
        240.0,0.0032817,0.0042022,0.0097251,0.0022812,0.0,0.0
        255.0,0.0032817,0.0050426,0.0130868,0.0112859,0.0002401,0.0
        270.0,0.0032817,0.0072037,0.0069636,0.0075639,0.0001201,0.0
        285.0,0.0032817,0.0126066,0.0283347,0.0199304,0.0008404,0.0
        300.0,0.0032817,0.0061232,0.0141674,0.0277344,0.0027614,0.0
        315.0,0.0032817,0.0141674,0.0487453,0.107696,0.0049226,0.0
        330.0,0.0032817,0.0069636,0.0286949,0.030736,0.0008404,0.0
        345.0,0.0032817,0.0105655,0.0229319,0.0136871,0.0,0.0
    """)), index_col=['Dir_bins']).rename_axis('Spd_bins', axis='columns')

    rose = viz._compute_rose(test_data, 'WindSpd', 'WindDir')
    rose.columns = rose.columns.astype(str)

    expected.index = rose_index
    rose.index = rose_index
    pdtest.assert_frame_equal(rose, expected, check_less_precise=True)


def test__compute_rose_short_record(short_data, rose_index):
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
        180.0,0.0,0.125,0.0,0.0,0.0,0.0
        195.0,0.0,0.0,0.125,0.0,0.0,0.0
        210.0,0.0,0.0,0.0,0.0,0.0,0.0
        225.0,0.0,0.25,0.0,0.0,0.0,0.0
        240.0,0.0,0.125,0.125,0.0,0.0,0.0
        255.0,0.0,0.125,0.0,0.0,0.0,0.0
        270.0,0.0,0.0,0.0,0.0,0.0,0.0
        285.0,0.0,0.125,0.0,0.0,0.0,0.0
        300.0,0.0,0.0,0.0,0.0,0.0,0.0
        315.0,0.0,0.0,0.0,0.0,0.0,0.0
        330.0,0.0,0.0,0.0,0.0,0.0,0.0
        345.0,0.0,0.0,0.0,0.0,0.0,0.0
    """)), index_col=['Dir_bins']).rename_axis('Spd_bins', axis='columns')

    rose = viz._compute_rose(short_data, 'WindSpd', 'WindDir')
    rose.columns = rose.columns.astype(str)

    expected.index = rose_index
    rose.index = rose_index
    pdtest.assert_frame_equal(rose, expected, check_less_precise=True)


@pytest.mark.mpl_image_compare(**IMG_OPTS)
def test_hyetograph(test_data, frequencies):
    fig, axes = _make_ts_fig()
    for freq, ax in zip(frequencies, axes):
        fig = viz.hyetograph(test_data, col='Precip', freq=freq, ax=ax)
    quiet_layout(fig)
    return fig


@pytest.mark.mpl_image_compare(**IMG_OPTS)
def test_psychromograph(test_data, frequencies):
    fig, axes = _make_ts_fig()
    for freq, ax in zip(frequencies, axes):
        fig = viz.psychromograph(test_data, col='AtmPress', freq=freq, ax=ax)
    quiet_layout(fig)
    return fig


@pytest.mark.mpl_image_compare(**IMG_OPTS)
def test_temperature(test_data, frequencies):
    fig, axes = _make_ts_fig()
    for freq, ax in zip(frequencies, axes):
        fig = viz.temperature(test_data, col='Temp', freq=freq, ax=ax)
    quiet_layout(fig)
    return fig

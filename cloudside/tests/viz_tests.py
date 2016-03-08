import os
import sys
from pkg_resources import resource_filename
from io import StringIO
from textwrap import dedent

import nose.tools as ntools
import datetime as dt
import pandas
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.testing.decorators import image_comparison, cleanup
import pandas.util.testing as pdtest

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
    fig1 = viz.windRose(df.assign(WindSpd=df['WindSpd'] * 1.15), spd_units='mph')
    fig2 = viz.windRose(df, spd_units='kt')


def test__compute_windrose():
    df = get_test_data()
    expected = pandas.read_csv(StringIO(dedent("""\
        Dir_bins,calm,0 - 5 ,5 - 10 ,10 - 20 ,20 - 30
        0.0,0.003281706487373434,0.003241685676551807,0.008524432705006604,0.0009604994597190539,0.0
        15.0,0.003281706487373434,0.0034818105414815706,0.008764557569936366,0.0006003121623244087,0.0
        30.0,0.003281706487373434,0.0021611237843678715,0.0038419978388762157,0.0,0.0
        45.0,0.003281706487373434,0.006843558650498259,0.005282747028454797,0.0,0.0
        60.0,0.003281706487373434,0.0012006243246488173,0.0024012486492976347,0.0024012486492976347,0.0
        75.0,0.003281706487373434,0.010925681354304238,0.033617481090166886,0.02005042622163525,0.0
        90.0,0.003281706487373434,0.009124744867331011,0.018129427302197142,0.012606555408812583,0.00012006243246488174
        105.0,0.003281706487373434,0.030135670548685316,0.05222715812222355,0.006483371353103614,0.0
        120.0,0.003281706487373434,0.010085244327050066,0.005642934325849442,0.0,0.0
        135.0,0.003281706487373434,0.015848241085364388,0.005162684595989914,0.0,0.0
        150.0,0.003281706487373434,0.004922559731060152,0.0024012486492976347,0.00012006243246488174,0.0
        165.0,0.003281706487373434,0.01320686757113699,0.011165806219234001,0.00024012486492976348,0.0
        180.0,0.003281706487373434,0.004442310001200624,0.009364869732260776,0.0007203745947892904,0.0
        195.0,0.003281706487373434,0.009124744867331011,0.008044182975147076,0.00048024972985952696,0.0
        210.0,0.003281706487373434,0.004202185136270861,0.003121623244086925,0.0,0.0
        225.0,0.003281706487373434,0.014287429463320928,0.015367991355504863,0.0024012486492976347,0.0
        240.0,0.003281706487373434,0.004202185136270861,0.009725057029655421,0.002281186216832753,0.0
        255.0,0.003281706487373434,0.005042622163525033,0.01308680513867211,0.011285868651698883,0.00024012486492976348
        270.0,0.003281706487373434,0.007203745947892904,0.006963621082963141,0.00756393324528755,0.00012006243246488174
        285.0,0.003281706487373434,0.012606555408812583,0.02833473406171209,0.019930363789170367,0.0008404370272541722
        300.0,0.003281706487373434,0.006123184055708969,0.014167367030856045,0.02773442189938768,0.00276143594669228
        315.0,0.003281706487373434,0.014167367030856045,0.048745347580741984,0.10769600192099892,0.004922559731060152
        330.0,0.003281706487373434,0.006963621082963141,0.028694921359106736,0.030735982711009725,0.0008404370272541722
        345.0,0.003281706487373434,0.010565494056909593,0.02293192460079241,0.013687117300996518,0.0
    """)), index_col=['Dir_bins'])
    columns = pandas.CategoricalIndex(
        ['calm', '0 - 5 ', '5 - 10 ', '10 - 20 ', '20 - 30 '],
        categories=['calm', '0 - 5 ', '5 - 10 ', '10 - 20 ', '20 - 30 ', '>30 '],
        ordered=True, name='Spd_bins', dtype='category'
    )
    rose = viz._compute_windrose(df)
    expected.columns = columns
    pdtest.assert_frame_equal(rose, expected, check_index_type=False)


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

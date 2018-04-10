from pkg_resources import resource_filename

from matplotlib import figure
from matplotlib import axes

import pytest

from cloudside import validate
from .helpers import raises


def getTestFile(filename):
    return resource_filename("cloudside.tests.data", filename)


def test_axes_object_invalid():
    with pytest.raises(ValueError):
        validate.axes_object('junk')


def test_axes_object_with_ax():
    fig = figure.Figure()
    ax = fig.add_subplot(1, 1, 1)
    fig1, ax1 = validate.axes_object(ax)
    assert isinstance(ax1, axes.Axes)
    assert isinstance(fig1, figure.Figure)
    assert ax1 is ax
    assert fig1 is fig


def test_axes_object_with_None():
    fig1, ax1 = validate.axes_object(None)
    assert isinstance(ax1, axes.Axes)
    assert isinstance(fig1, figure.Figure)


@pytest.mark.parametrize(('src', 'error'), [
    ('asos', None),
    ('wunderground', NotImplementedError),
    ('junk', ValueError)
])
def test_source(src, error):
    with raises(error):
        validate.source(src)


@pytest.mark.parametrize(('step', 'error'), [
    ('flat', None),
    ('raw', None),
    ('junk', ValueError)
])
def test_step(step, error):
    validate.step('flat')
    validate.step('raw')
    with pytest.raises(ValueError):
        validate.step('junk')


@pytest.mark.parametrize(('filename', 'expected'), [
    ('status_ok', 'ok'),
    ('status_bad', 'bad'),
    ('doesnotexist', 'not there'),
])
def test_file_status(filename, expected):
    fn = getTestFile(filename)
    validate.file_status(fn) == expected


@pytest.mark.parametrize(('index', 'error'), [
    (list('ABCD'), None),
    (list('AABC'), ValueError)
])
def unique_index(index, error):
    x = pandas.Series(range(4), index=index)
    with raises(error):
        pdtest.assert_series_equal(x, validate.unique_index(x))

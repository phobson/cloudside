from pkg_resources import resource_filename

from matplotlib import pyplot

import pytest

from cloudside import validate
from .helpers import raises


def getTestFile(filename):
    return resource_filename("cloudside.tests.data", filename)


def test_axes_object_invalid():
    with pytest.raises(ValueError):
        validate.axes_object('junk')


def test_axes_object_with_ax():
    fig, ax = pyplot.subplots()
    fig1, ax1 = validate.axes_object(ax)
    assert isinstance(ax1, pyplot.Axes)
    assert isinstance(fig1, pyplot.Figure)
    assert ax1 is ax
    assert fig1 is fig


def test_axes_object_with_None():
    fig1, ax1 = validate.axes_object(None)
    assert isinstance(ax1, pyplot.Axes)
    assert isinstance(fig1, pyplot.Figure)


@pytest.mark.parametrize(('src', 'error'), [
    ('asos', None),
    ('wunderground', None),
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

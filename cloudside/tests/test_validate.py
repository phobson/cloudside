from pkg_resources import resource_filename

from matplotlib import pyplot

import pytest

from cloudside import validate


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


def test_source():
    validate.source('asos')
    validate.source('wunderground')
    with pytest.raises(ValueError):
        validate.source('junk')


def test_step():
    validate.step('flat')
    validate.step('raw')
    with pytest.raises(ValueError):
        validate.step('junk')


def test_file_status():
    known_results = ['bad', 'ok', 'not there']
    for n, known_result in enumerate(known_results, 1):
        fn = getTestFile('testfile{:d}'.format(n))
        validate.file_status(fn) == known_result

from pkg_resources import resource_filename

import pytest

from cloudside import validate


def getTestFile(filename):
    return resource_filename("cloudside.tests.data", filename)


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

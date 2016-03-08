from pkg_resources import resource_filename

import nose.tools as ntools

from cloudside import validate


@ntools.nottest
def getTestFile(filename):
    return resource_filename("cloudside.tests.data", filename)


def test_source():
    validate.source('asos')
    validate.source('wunderground')
    ntools.assert_raises(ValueError, validate.source, 'fart')


def test_step():
    validate.step('flat')
    validate.step('raw')
    ntools.assert_raises(ValueError, validate.step, 'fart')


def test_file_status():
    known_results = ['bad', 'ok', 'not there']
    for n, known_result in enumerate(known_results, 1):
        fn = getTestFile('testfile{:d}'.format(n))
        ntools.assert_equal(validate.file_status(fn), known_result)

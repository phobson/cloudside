from pkg_resources import resource_filename

import pandas

import pytest
import pandas.util.testing as pdtest

from cloudside import ncdc
from .helpers import get_test_file


@pytest.fixture
def sample_data():
    fname = get_test_file('sample_ncdc_data.csv')
    return pandas.read_csv(fname, parse_dates=['date'])


def test_set_status():
    data = pandas.DataFrame({
        'rain': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 99999, 0, 0],
        'flag': ['{', '}', '[', None, None, None, ']', 'a', None, None, None, 'A', None, None, None, 'A']
    })

    result = (
        data.pipe(ncdc.set_status, 'a', 'A', 1)
            .pipe(ncdc.set_status, '{', '}', 2)
            .pipe(ncdc.set_status, '[', ']', 3)
    )

    expected = data.assign(status=[2, 2, 3, 3, 3, 3, 3, 1, 1, 1, 1, 1, 0, 0, 0, 1])
    pdtest.assert_frame_equal(result, expected)

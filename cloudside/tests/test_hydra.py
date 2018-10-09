from pathlib import Path
from io import StringIO
from textwrap import dedent
import tempfile

import pandas

from unittest import mock
import pytest
import pandas.util.testing as pdtest

from cloudside import hydra
from .helpers import get_test_file


@pytest.fixture
def expected_hydra():
    csv = StringIO(dedent("""\
        datetime,sample_hydra
        2018-10-06 00:00:00,0.01
        2018-10-06 01:00:00,0.0
        2018-10-06 02:00:00,0.01
        2018-10-06 03:00:00,0.01
        2018-10-06 04:00:00,0.01
        2018-10-06 05:00:00,0.0
        2018-10-06 06:00:00,0.0
        2018-10-06 07:00:00,0.0
        2018-10-06 08:00:00,0.0
        2018-10-06 09:00:00,0.0
        2018-10-06 10:00:00,0.0
        2018-10-06 11:00:00,0.0
        2018-10-06 12:00:00,0.0
        2018-10-06 13:00:00,0.0
        2018-10-06 14:00:00,0.0
        2018-10-06 15:00:00,0.0
        2018-10-06 16:00:00,0.0
        2018-10-06 17:00:00,0.0
        2018-10-06 18:00:00,0.0
        2018-10-06 19:00:00,0.0
        2018-10-06 20:00:00,0.0
        2018-10-06 21:00:00,0.0
        2018-10-06 22:00:00,0.0
        2018-10-06 23:00:00,0.0
        2018-10-07 00:00:00,0.0
        2018-10-07 01:00:00,0.0
        2018-10-07 02:00:00,0.0
        2018-10-07 03:00:00,0.0
        2018-10-07 04:00:00,0.0
        2018-10-07 05:00:00,0.0
        2018-10-07 06:00:00,0.0
        2018-10-07 07:00:00,0.0
        2018-10-07 08:00:00,0.0
        2018-10-07 09:00:00,0.01
        2018-10-07 10:00:00,0.01
        2018-10-07 11:00:00,0.02
        2018-10-07 12:00:00,0.02
        2018-10-07 13:00:00,0.02
        2018-10-07 14:00:00,0.0
        2018-10-07 15:00:00,0.0
        2018-10-07 16:00:00,0.0
        2018-10-07 17:00:00,0.0
        2018-10-07 18:00:00,0.0
        2018-10-07 19:00:00,0.0
        2018-10-07 20:00:00,0.02
        2018-10-07 21:00:00,0.01
        2018-10-07 22:00:00,0.01
        2018-10-07 23:00:00,0.01
        2018-10-08 00:00:00,0.01
        2018-10-08 01:00:00,0.03
        2018-10-08 02:00:00,0.04
        2018-10-08 03:00:00,0.03
        2018-10-08 04:00:00,0.02
        2018-10-08 05:00:00,0.02
        2018-10-08 06:00:00,0.02
        2018-10-08 07:00:00,0.01
        2018-10-08 08:00:00,0.01
        2018-10-08 09:00:00,0.01
        2018-10-08 10:00:00,0.01
        2018-10-08 11:00:00,0.0
        2018-10-08 12:00:00,0.01
        2018-10-08 13:00:00,0.0
        2018-10-08 14:00:00,
        2018-10-08 15:00:00,
        2018-10-08 16:00:00,
        2018-10-08 17:00:00,
        2018-10-08 18:00:00,
        2018-10-08 19:00:00,
        2018-10-08 20:00:00,
        2018-10-08 21:00:00,
        2018-10-08 22:00:00,
        2018-10-08 23:00:00,
    """))
    return pandas.read_csv(csv, parse_dates=True, index_col=[0])


def test_parse_file(expected_hydra):
    filepath = Path(get_test_file('sample_hydra.txt'))
    result = hydra.parse_file(filepath)
    pdtest.assert_frame_equal(expected_hydra, result)


@mock.patch('requests.get')
@mock.patch('cloudside.validate.unique_index')
@mock.patch('cloudside.hydra._fetch_file', return_value='this/kpdx.txt')
@mock.patch('cloudside.hydra.parse_file')
def test_get_data(parser, fetcher, checker, getter):
    with tempfile.TemporaryDirectory() as topdir:
        hydra.get_data('KPDX', folder=topdir)
        parser.assert_called_once_with('this/kpdx.txt')
        fetcher.assert_called_once_with('KPDX', Path(topdir) / '01-raw',
                                        force_download=False)

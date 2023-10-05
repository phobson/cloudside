from datetime import timedelta

import numpy
import pandas

import pytest
import pandas.testing as pdtest

from cloudside import storms
from cloudside.tests import get_test_file  # noqa


@pytest.mark.parametrize(
    ("df", "expected"),
    [
        (
            pandas.DataFrame({"wet": [True, True], "diff": [0, 1]}),
            pandas.DataFrame({"wet": [True, True], "diff": [1, 1]}),
        ),
        (
            pandas.DataFrame({"wet": [False, True], "diff": [0, 1]}),
            pandas.DataFrame({"wet": [False, True], "diff": [0, 1]}),
        ),
    ],
)
def test__wet_first_row(df, expected):
    result = storms._wet_first_row(df, "wet", "diff")
    pdtest.assert_frame_equal(result, expected)


def test__wet_window_diff():
    wet = pandas.Series([0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1])
    expected = pandas.Series(
        [
            numpy.nan,
            0.0,
            0.0,
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            -1.0,
            0.0,
            1.0,
            0.0,
            0.0,
            0.0,
        ]
    )
    result = storms._wet_window_diff(wet, 6)
    pdtest.assert_series_equal(result, expected)


def prep_storm_record(fname):
    filename = get_test_file(fname)
    return pandas.read_csv(filename, index_col="date", parse_dates=True)


@pytest.mark.parametrize(
    "fname",
    ["teststorm_simple.csv", "teststorm_firstobs.csv", "teststorm_singular.csv"],
)
def test_parse_record(fname):
    df = prep_storm_record(fname)
    expected = df["storm"]
    result = storms.parse_record(
        df.drop(columns="storm"),
        6,
        5,
        precipcol="rain",
        inflowcol="influent",
        outflowcol="effluent",
    ).dropna(subset=["influent", "effluent"])
    pdtest.assert_series_equal(
        result["storm"].astype(numpy.int32), expected.astype(numpy.int32)
    )


@pytest.mark.parametrize(
    "fname",
    ["teststorm_simple.csv", "teststorm_firstobs.csv", "teststorm_singular.csv"],
)
@pytest.mark.parametrize("keepzeroes", [True, False])
def test_parse_record_fast(fname, keepzeroes):
    df = prep_storm_record(fname).drop(columns=["storm", "influent", "effluent"])
    expected = storms.parse_record(df, 6, 5, precipcol="rain")
    result = storms.parse_record_fast(df, 6, 5, precipcol="rain", keepzeroes=keepzeroes)

    if not keepzeroes:
        expected = expected.loc[lambda df: df["rain"] > 0]

    pdtest.assert_series_equal(
        expected["storm"].astype(numpy.int32),
        result["storm"].astype(numpy.int32)
    )

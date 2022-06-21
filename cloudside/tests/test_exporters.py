import os
import tempfile

import pandas

import pytest
import pandas.testing as pdtest

from cloudside import exporters
from cloudside.tests import get_test_file  # noqa


@pytest.fixture
def fivemin():
    return pandas.read_csv(
        get_test_file("data_for_tests.csv"), parse_dates=True, index_col=0
    )


@pytest.mark.parametrize(("dropzeros", "shape"), [(True, (178, 7)), (False, (336, 7))])
def test_dumpSWMM5Format_form(fivemin, dropzeros, shape):
    with tempfile.TemporaryDirectory() as datadir:
        outfile = os.path.join(datadir, "test_dumpSWMM.dat")
        data = exporters.SWMM5Format(
            fivemin,
            "Test-Station",
            col="precip",
            freq="5min",
            dropzeros=dropzeros,
            filename=outfile,
        )
        expected_cols = ["station", "year", "month", "day", "hour", "minute", "precip"]
        assert isinstance(data, pandas.DataFrame)
        assert data.columns.tolist() == expected_cols
        assert data.shape == shape
        assert data["precip"].sum() == fivemin["precip"].sum()
        if dropzeros:
            assert data[data.precip == 0].shape[0] == 0


@pytest.mark.parametrize(
    ("freq", "expected_file"),
    [("5min", "known_fivemin_swmm5.dat"), ("hourly", "known_hourly_swmm5.dat")],
)
def test_dumpSWMM5Format_results(fivemin, freq, expected_file):
    if freq == "hourly":
        data = fivemin.resample("1H").sum()
    else:
        data = fivemin

    with tempfile.TemporaryDirectory() as datadir:
        outfile = os.path.join(datadir, "test_dumpSWMM.dat")
        data = exporters.SWMM5Format(
            data,
            "Test-Station",
            col="precip",
            freq=freq,
            dropzeros=True,
            filename=outfile,
        )
        pdtest.assert_frame_equal(
            data.reset_index(drop=True),
            pandas.read_table(get_test_file(expected_file), sep="\t"),
        )


def test_dumpNCDCFormat(fivemin):
    knownfile = get_test_file("known_hourly_NCDC.dat")
    with tempfile.TemporaryDirectory() as datadir:
        outfile = os.path.join(datadir, "test_dumpNCDC.dat")
        exporters.NCDCFormat(
            fivemin.resample("1H").sum(),
            "041685",
            "California",
            col="precip",
            filename=outfile,
        )

        with open(knownfile, "r") as f:
            known_data = f.read()

        with open(outfile, "r") as f:
            test_data = f.read()

        assert known_data == test_data


@pytest.mark.parametrize(
    ("N", "side", "expected"),
    [(1, "left", "1"), (3, "lEFt", "123"), (1, "right", "8"), (4, "RighT", "5678")],
)
def test__pop_many(N, side, expected):
    x = list("12345678")
    result = exporters._pop_many(x, N, side=side)
    assert result == expected


@pytest.mark.parametrize(
    ("obs", "expected"),
    [
        ("1300000000M", (12, 00, 0.00, "M")),
        ("1300000000", (12, 00, 0.00, "")),
        ("2200099999M", (21, 00, None, "M")),
        ("0300000012A", (2, 00, 0.12, "A")),
        ("0300000145", (2, 00, 1.45, "")),
        ("2500000005I", (24, 00, 0.05, "I")),
    ],
)
def test__parse_obs(obs, expected):
    result = exporters._parse_obs(list(obs))
    assert result == expected


@pytest.mark.parametrize(
    ("parsed_obs", "expected"),
    [
        ((12, 00, 0.00, "M"), "testheader,2012-05-16 12:00,0.00,M\n"),
        ((12, 00, 0.00, ""), "testheader,2012-05-16 12:00,0.00,\n"),
        ((21, 00, None, "M"), None),
        ((2, 00, 0.12, "A"), "testheader,2012-05-16 02:00,0.12,A\n"),
        ((2, 00, 1.45, ""), "testheader,2012-05-16 02:00,1.45,\n"),
        ((24, 00, 0.05, "I"), None),
    ],
)
def test__write(parsed_obs, expected):
    result = exporters._write_obs("testheader", 2012, 5, 16, parsed_obs)
    assert result == expected


@pytest.mark.parametrize(
    ("row", "expected"),
    [
        (
            "HPD04511406HPCPHI19480700010040100000000 1300000000M 2400000000M 2500000000I ",
            (
                "045114,HPD,06HPCP,HI,1948-07-01 00:00,0.00,\n"
                "045114,HPD,06HPCP,HI,1948-07-01 12:00,0.00,M\n"
                "045114,HPD,06HPCP,HI,1948-07-01 23:00,0.00,M\n"
            ),
        ),
        (
            "HPD04511406HPCPHI19480700010040100000000 0800000185A 0900099999M 1300000000M 2400000000M 2500000000I ",
            (
                "045114,HPD,06HPCP,HI,1948-07-01 00:00,0.00,\n"
                "045114,HPD,06HPCP,HI,1948-07-01 07:00,1.85,A\n"
                "045114,HPD,06HPCP,HI,1948-07-01 12:00,0.00,M\n"
                "045114,HPD,06HPCP,HI,1948-07-01 23:00,0.00,M\n"
            ),
        ),
    ],
)
def test__obs_from_row(row, expected):
    result = exporters._obs_from_row(row)
    assert result == expected


def test_NCDCtoCSV():
    inputfile = get_test_file("sample_NCDC_data.NCD")
    knownfile = get_test_file("known_CSV_from_NCDC.csv")
    with tempfile.TemporaryDirectory() as datadir:
        outfile = os.path.join(datadir, "test_out.dat")
        exporters.NCDCtoCSV(inputfile, outfile)

        with open(knownfile, "r") as f:
            known_data = f.read()

        with open(outfile, "r") as f:
            test_data = f.read()

        assert known_data == test_data

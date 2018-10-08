from cloudside import cli, asos

from unittest import mock
from click.testing import CliRunner


@mock.patch('cloudside.asos.get_data')
def test_get_data(get_data):
    args = ['KPDX', '2018-01-01', '2018-05-01', 'test@devnull.net']
    result = CliRunner().invoke(cli.get_data, args)
    get_data.assert_called_with(*args, folder='.', force_download=False,
                                pbar_fxn=cli.tqdm, raw_folder='01-raw')

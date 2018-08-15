from cloudside import cli, asos

from unittest import mock
from click.testing import CliRunner


@mock.patch('cloudside.asos.get_data')
def test_get_asos(get_data):
    args = ['KPDX', '2018-01-01', '2018-05-01', 'test@devnull.net']
    result = CliRunner().invoke(cli.get_asos, args)
    get_data.assert_called_with(*args, folder='.', force_download=False,
                                pbar_fxn=cli.tqdm)


@mock.patch('cloudside.hydra.get_data')
def test_get_hydra(get_data):
    args = ['KPDX', '--force']
    result = CliRunner().invoke(cli.get_hydra, args)
    get_data.assert_called_with('KPDX', folder='.', force_download=True)

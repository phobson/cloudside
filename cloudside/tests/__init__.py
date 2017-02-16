from pkg_resources import resource_filename

import pytest

import cloudside


def test(*args):
    options = [resource_filename('cloudside', '')]
    options.extend(list(args))
    return pytest.main(options)

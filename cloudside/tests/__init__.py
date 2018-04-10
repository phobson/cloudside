from pkg_resources import resource_filename

import cloudside
from .helpers import requires


try:
    import pytest
except ImportError:
    raise ImportError("pytest is requires to run tests")


@requires(pytest, 'pytest')
def test(*args):
    options = [resource_filename('cloudside', '')]
    options.extend(list(args))
    return pytest.main(options)


@requires(pytest, 'pytest')
def teststrict():
    options = [resource_filename('cloudside', ''), '--pep', '--mpl', '--runslow']
    return pytest.main(options)

from pkg_resources import resource_filename

import cloudside


def test(*args):
    try:
        import pytest
    except ImportError:
        raise ImportError("pytest is requires to run tests")

    options = [resource_filename('cloudside', '')]
    options.extend(list(args))
    return pytest.main(options)

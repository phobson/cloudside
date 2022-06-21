from pkg_resources import resource_filename
from contextlib import contextmanager

import pytest


def get_test_file(filename):
    return resource_filename("cloudside.tests.data", filename)


def raises(error):
    """Wrapper around pytest.raises to support None."""
    if error:
        return pytest.raises(error)
    else:

        @contextmanager
        def not_raises():
            try:
                yield
            except Exception as e:
                raise e

        return not_raises()

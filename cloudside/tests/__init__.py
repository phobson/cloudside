from pkg_resources import resource_filename
from functools import wraps
from contextlib import contextmanager


try:
    import pytest
except ImportError:
    pytest = None


def requires(module, modulename):
    def outer_wrapper(function):
        @wraps(function)
        def inner_wrapper(*args, **kwargs):
            if module is None:
                raise RuntimeError(
                    "{} required for `{}`".format(modulename, function.__name__)
                )
            else:
                return function(*args, **kwargs)

        return inner_wrapper

    return outer_wrapper


@requires(pytest, "pytest")
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


@requires(pytest, "pytest")
def test(*args):
    options = [resource_filename("cloudside", "")]
    options.extend(list(args))
    return pytest.main(options)


def get_test_file(filename):
    return resource_filename("cloudside.tests.data", filename)


@requires(pytest, "pytest")
def teststrict(*args):
    options = [
        resource_filename("cloudside", ""),
        "--mpl",
        "--runslow",
        *list(args),
    ]
    options = list(set(options))
    return pytest.main(options)

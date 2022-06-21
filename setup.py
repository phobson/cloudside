import re
from setuptools import setup, find_packages

PACKAGE_DATA = {
    "cloudside.tests.data": ["*.txt", "*.png", "*.dat", "*.csv"],
    "cloudside.tests.baseline_images.viz_tests": ["*.png"],
}

DESCRIPTION = "cloudside - download, assess, and visualize weather data"


def search(substr: str, content: str):
    found = re.search(substr, content)
    if found:
        return found.group(1)
    return ""


with open("cloudside/__init__.py", encoding="utf8") as f:
    content = f.read()
    version = search(r'__version__ = "(.*?)"', content)
    author = search(r'__author__ = "(.*?)"', content)
    author_email = search(r'__email__ = "(.*?)"', content)


setup(
    name="cloudside",
    version=version,
    author=author,
    author_email=author_email,
    url="https://github.com/Geosyntec/cloudside",
    description=DESCRIPTION,
    long_description=DESCRIPTION,
    package_data=PACKAGE_DATA,
    license="BSD 3-Clause",
    packages=find_packages(exclude=[]),
    platforms="Python 3.8 and later.",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
        "Topic :: Scientific/Engineering :: Atmospheric Science",
        "Topic :: Scientific/Engineering :: Visualization",
    ],
    entry_points={"console_scripts": ["cloudside=cloudside.cli:main"]},
)

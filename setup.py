
import os
import sys
from setuptools import setup, find_packages

PACKAGE_DATA = {
    'cloudside.tests.data': ['*.txt', '*.png', '*.dat', '*.csv', 'testfile', 'testfile1', 'testfile2'],
    'cloudside.tests.baseline_images.viz_tests': ['*.png'],
}

DESCRIPTION = "cloudside - download, assess, and visualize weather data"

if __name__ == '__main__':
    setup(
        name="cloudside",
        version="0.1",
        author="Paul Hobson",
        author_email="pmhobson@gmail.com",
        url="http://python-metar.sourceforge.net/",
        description=DESCRIPTION,
        long_description=DESCRIPTION,
        package_data=PACKAGE_DATA,
        download_url="http://sourceforge.net/project/platformdownload.php?group_id=134052",
        license="BSD 3-Clause",
        packages=find_packages(exclude=[]),
        platforms="Python 3.4 and later.",
        classifiers=[
            "Development Status :: 3 - Alpha",
            "Environment :: Console",
            "Intended Audience :: Science/Research",
            "License :: OSI Approved :: BSD License",
            "Operating System :: OS Independent",
            "Programming Language :: Python :: 3.4",
            "Programming Language :: Python :: 3.5",
            "Programming Language :: Python :: 3.6",
            "Topic :: Scientific/Engineering :: Atmospheric Science",
            "Topic :: Scientific/Engineering :: Visualization",
        ]
    )

import setuptools
from distutils.core import setup

setup(
        name        = "smartosse",
        packages    = ['smartosse'],
        version     = "0.0",
        author      = "Matthew Goldberg",
        author_email= 'matthew.goldberg10@utexas.edu',
        description = 'SMART Cable data assimilation utilities',
        license     = '',
        keywords    = 'MIT License',
        url         = '',
        install_requires=[
            'numpy',
            'scipy',
            'matplotlib',
            'xarray',
            'xmitgcm',
            'ecco_v4_py',
            'xgcm',
            'argparse',
            'cartopy',
            'tabulate',
            'typing',
            ],
        tests_require=['pytest>=2.8']
)

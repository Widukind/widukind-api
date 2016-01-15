# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

from widukind_api.version import version_str

setup(
    name='widukind-api',
    version=version_str(),
    description='Widukind Rest API',
    author='Widukind Team',
    url='https://github.com/Widukind/widukind-api',
    zip_safe=False,
    license='AGPLv3',
    include_package_data=True,
    packages=find_packages(),
    test_suite='nose.collector',
    tests_require=[
      'nose',
    ],
    entry_points={
        'console_scripts': [
            'widukind-api = widukind_api.manager:main',
        ],
    },
)

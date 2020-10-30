# -*- coding: utf-8 -*-
import os
import re
from setuptools import setup, find_packages


with open(os.path.join('click_restful', '__init__.py'), encoding='utf8') as f:
    version = re.search(r"__version__ = '(.*?)'", f.read()).group(1)

with open('README.md', encoding='utf8') as f:
    readme = f.read()


setup(
    name='Click-RESTful',
    version=version,
    packages=find_packages(),
    author='Daniel Reeves',
    python_requires='>=3.8.1',
    maintainer='Daniel Reeves',
    license='MIT',
    include_package_data=True,
    setup_requires=[],
    tests_require=[
        'pytest',
        'schemathesis'
    ],
    install_requires=[
        'flask',
        'click',
        'flasgger',
        'PyYAML'
    ],
    extras_require={},
    url='https://github.com/dwreeves/Click-Restful',
    description="Turn Click CLIs into Flask RESTful APIs.",
    long_description=readme,
    long_description_content_type='text/markdown',
)

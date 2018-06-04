from setuptools import setup, find_packages
from os.path import join, dirname


setup(
    name='tasktracker_core',
    version='1.0',
    description='Core library for tasktracker',
    packages=find_packages(),
    include_package_data=False,
    install_requires=['peewee']
)
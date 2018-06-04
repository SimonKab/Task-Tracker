from setuptools import setup, find_packages
from os.path import join, dirname

root = 'tasktracker_core'
packages = [root] + [(root + '.' + subfolder) for subfolder in find_packages(root)]

setup(
    name='tasktracker_core',
    version='1.0',
    description='Core library for tasktracker',
    packages=packages,
    include_package_data=False,
    install_requires=['peewee']
)
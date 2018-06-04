from setuptools import setup, find_packages
from os.path import join, dirname

setup(
    name='tasktracker_console',
    version='1.0',
    description='something unuseful',
    packages=find_packages(),
    include_package_data=False,
    install_requires=['peewee'],
    entry_points={
        'console_scripts':
            ['tt = .start:run']
    }
)
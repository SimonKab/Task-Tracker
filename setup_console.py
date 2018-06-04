from setuptools import setup, find_packages
from os.path import join, dirname

setup(
    name='tasktracker_console',
    version='1.0',
    description='something unuseful',
    packages=['tasktracker_console'],
    include_package_data=False,
    install_requires=['peewee'],
    entry_points={
        'console_scripts':
            ['tt = tasktracker_console.console_parser:parse']
    }
)
from setuptools import setup, find_packages
from os.path import join, dirname

setup(
    name='tasktracker',
    version='1.0',
    descriprion='something unuseful',
    packages=find_packages(),
    include_package_date=False,
    install_requires=['peewee'],
    entry_points={
        'console_scripts':
            ['tt = .start:run']
    }
)
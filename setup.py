from setuptools import setup

setup(
    author="JadenGuo",
    author_email="gxy199172@gmail.com",
    name='Forex_AlgoTrading',
    version='1.0',
    packages=['BackTest','DataHandler','Enums','Event','Plot','Portfolio','Strategy'],
    include_package_data = True,
    exclude_package_date = {'': ['.gitignore']},
    install_requires=[
        'backports.functools-lru-cache>=1.5',
        'cycler>=0.10.0',
        'enum>=0.4.6',
        'kiwisolver>=1.0.1',
        'matplotlib>=2.2.2',
        'numpy>=1.15.0',
        'pandas>=0.23.4',
        'pyparsing>=2.2.0',
        'python-dateutil>=2.7.3',
        'pytz>=2018.5',
        'six>=1.11.0'
    ]

)
"""
Pip Requ helps managing your Python requirements files.
"""
from setuptools import find_packages, setup


def get_long_description():
    with open('README.rst') as fp:
        return fp.read()


setup(
    name='pip-requ',
    version='0.180.7',
    url='https://github.com/suutari-ai/pip-requ/',
    license='BSD',
    maintainer='Tuomas Suutari',
    maintainer_email='tuomas.suutari@anders.fi',
    description=__doc__.strip(),
    long_description=get_long_description(),
    packages=find_packages(exclude=['tests']),
    install_requires=[
        'click>=6',
        'first',
        'six',
    ],
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'pip-requ = pip_requ.scripts.pip_requ:main',
        ],
    },
    platforms='any',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Topic :: System :: Systems Administration',
    ]
)

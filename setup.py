"""
Pip Requ keeps your pinned dependencies fresh.
"""
from setuptools import find_packages, setup

setup(
    name='pip-requ',
    version='0.180.1',
    url='https://github.com/suutari-ai/pip-requ/',
    license='BSD',
    maintainer='Tuomas Suutari',
    maintainer_email='tuomas.suutari@anders.fi',
    description=__doc__,
    packages=find_packages(exclude=['tests']),
    install_requires=[
        'click>=6',
        'first',
        'six',
    ],
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'pip-compile = pip_requ.scripts.compile:cli',
            'pip-requ = pip_requ.scripts.pip_requ:main',
            'pip-sync = pip_requ.scripts.sync:cli',
        ],
    },
    platforms='any',
    classifiers=[
        # As from https://pypi.python.org/pypi?%3Aaction=list_classifiers
        # 'Development Status :: 1 - Planning',
        # 'Development Status :: 2 - Pre-Alpha',
        # 'Development Status :: 3 - Alpha',
        # 'Development Status :: 4 - Beta',
        'Development Status :: 5 - Production/Stable',
        # 'Development Status :: 6 - Mature',
        # 'Development Status :: 7 - Inactive',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        # 'Programming Language :: Python :: 2.3',
        # 'Programming Language :: Python :: 2.4',
        # 'Programming Language :: Python :: 2.5',
        # 'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        # 'Programming Language :: Python :: 3.0',
        # 'Programming Language :: Python :: 3.1',
        # 'Programming Language :: Python :: 3.2',
        # 'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Topic :: System :: Systems Administration',
    ]
)

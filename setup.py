from setuptools import find_packages, setup


def get_long_description():
    with open('README.rst') as fp:
        return fp.read()


setup(
    name='prequ',
    version='0.180.8',
    url='https://github.com/suutari-ai/prequ/',
    license='BSD',
    maintainer='Tuomas Suutari',
    maintainer_email='tuomas.suutari@anders.fi',
    description="Prequ -- Python requirement handling",
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
            'prequ = prequ.scripts.prequ:main',
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

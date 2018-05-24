Prequ Change Log
================

This version of Prequ contains all the changes from pip-tools 2.0.2 and
is in sync with pip-tools master commit 9cb41d8.


General Changes
~~~~~~~~~~~~~~~

- Add support for Pip 10
- Improve error messages when skipping pre-releases
  (jazzband/pip-tools#655)
- tests: Do not download Django from Git (jazzband/pip-tools#629)

Features
~~~~~~~~

- sync: Add "--user" option to install packages into user-local
  directory (jazzband/pip-tools#642)

Bug Fixes
~~~~~~~~~

- Handle environment markers in the source requirements
  (jazzband/pip-tools#647)

1.4.0 (Release Candidate 1)
---------------------------

Released on 2018-01-03 23:05 +02:00.

This version of Prequ is synced with pip-tools 1.11.0.

Features
~~~~~~~~

- Allow editable packages in source requirements even if generating
  hashes is enabled (jazzband/pip-tools#524)

General Changes
~~~~~~~~~~~~~~~

- Improve compile speed of locally available editable requirement by
  avoiding creation of an sdist archive (jazzband/pip-tools#583)
- Improve the ``NoCandidateFound`` error message on potential causes
  (jazzband/pip-tools#614)
- sync: Add ``-markerlib`` to the list of packages to ignore
  (jazzband/pip-tools#613)

1.3.1
-----

Released on 2018-01-01 21:20 +02:00.

Bug Fixes
~~~~~~~~~

- Fix handling of requirements with a period in name

1.3.0
-----

Released on 2017-11-21 20:50 +02:00.

This version of Prequ is synced with pip-tools 1.10.2rc1.

Features
~~~~~~~~

- Add support for unpinned non-editable VCS URLs
- Make relative paths work as a requirement entry (editable or not)

General Changes
~~~~~~~~~~~~~~~

- Make "via package" comments work for editable requirers too
- Speedup: Do not regenerate hashes if they are already known

Bug Fixes
~~~~~~~~~

- Ignore installed packages when calulating dependencies
- Generate hashes of artifacts correctly
- sync: Respect environment markers (jazzband/pip-tools#600)

1.2.2
-----

Released on 2017-09-28 9:50 +03:00.

This version of Prequ is synced with pip-tools 1.10.1.

Bug Fixes
~~~~~~~~~

- Fix a bug where the resolver would sometime not stabilize on
  requirements specifying extras (jazzband/pip-tools#566)
- Fix an unicode encoding error when distribution package contains
  non-ASCII file names (jazzband/pip-tools#567)
- sync: Fix syncing when there were editables present

1.2.1
-----

Released on 2017-09-14 0:15 +03:00.

Bug Fixes
~~~~~~~~~

- Correctly follow only the dependencies of the current platform

1.2.0
-----

Released on 2017-09-12 7:15 +03:00.

Features
~~~~~~~~

- Detect annotation and other options from the existing output files
- Merge configuration from setup.cfg with requirements*.in files
- Add "prequ check --verbose" for showing what is outdated

Bug Fixes
~~~~~~~~~

- Fix "prequ check --silent" not being silent on outdated txt files

1.1.0
-----

Released on 2017-09-03 11:10 +03:00.

This version of Prequ is synced with pip-tools master at commit 8c09d72.

Features
~~~~~~~~

- (jazzband/pip-tools#509) Add a "-q"/"--quiet" argument to the sync
  command to reduce log output

Bug Fixes
~~~~~~~~~

- (jazzband/pip-tools#542) Fix a bug where some primary dependencies
  were annotated with the "via" info comments
- (jazzband/pip-tools#557) Fix package hashing doing unnecessary
  unpacking

1.0.2
-----

Released on 2017-08-28 19:30 +03:00.

Bug Fixes
~~~~~~~~~

- Prevent conflicting package versions as expeceted.  The resolver used
  to allow selecting a pinned version V for a package P1 even though
  another package P2 required a version of P1 that is not V.

1.0.1
-----

Released on 2017-08-02 15:20 +03:00.

This version of Prequ is synced with pip-tools 1.10.0rc2.

Bug Fixes
~~~~~~~~~

- (jazzband/pip-tools#538) Fixed bug where editable PyPI dependencies
  would have a ``download_dir`` and be exposed to ``git-checkout-index``,
  (thus losing their VCS directory) and ``python setup.py egg_info``
  fails.

1.0.0
-----

Released on 2017-06-08 22:55 +03:00.

This version of Prequ is synced with pip-tools 1.10.0rc1.

General Changes
~~~~~~~~~~~~~~~

- compile-in: Mark as internal command
- Rename pre-requirements to Prequ configuration
- Remove requirements.pre support

Features
~~~~~~~~

- (jazzband/pip-tools#520) Using ``generate_hashes = yes`` now generates
  hashes for all wheels, not only for the currently running platform
- Make command line help available also with ``-h``

Bug Fixes
~~~~~~~~~

- (jazzband/pip-tools#517) Fix a bug where unsafe packages would get
  pinned in generated requirements files
- sync: Fix sync to work on Python 3 (TypeError: unorderable types...)

0.500.0
-------

Released on 2017-04-29 11:30 +03:00.

Features
~~~~~~~~

- (jazzband/pip-tools#472) compile-in: Add "--max-rounds" argument to
  allow solving large requirement sets

- (jazzband/pip-tools#461) Allow running as a Python module

- (jazzband/pip-tools#460) Preserve environment markers in generated
  requirements.txt

Bug Fixes
~~~~~~~~~

- (jazzband/pip-tools#476) Fix editable requirements loosing their
  dependencies after first round

0.400.0
-------

- Allow pre-requirements without base requirements
- (jazzband/pip-tools#441) Fixed implementation of excluding packages
  required only by unsafe packages
- Fix constraint handling: Do not add new dependencies from constraints
- compile-in: Rename "--no-trusted-host" to "--no-emit-trusted-host"
- Remove dependency on the "first" Python package
- Use backports.tempfile and contextlib2 on Python 2 for
  TemporaryDirectory and ExitStack rather than vendoring them
- Demand using equality operator (==) in lines with a wheel instruction
- Add new command "prequ check" for checking generated requirements
- Sort generated requirements by lower case distribution name

0.300.0
-------

- Use ``[prequ]`` section in ``setup.cfg`` as default pre-requirements

0.200.1
-------

- (jazzband/pip-tools#464) sync: Use options from the txt file

0.200.0
-------

- Rename "prequ compile-all" to "prequ compile"
- (jazzband/pip-tools#427) Fix duplicate entries that could happen in
  generated requirements.txt
- (jazzband/pip-tools#457) Gracefully report invalid pip version
- (jazzband/pip-tools#452) Fix capitalization in the generated
  requirements.txt, packages will always be lowercased

0.180.9
-------

- (jazzband/pip-tools#453) Write relative find-links opts to output file
- Add "--silent" option for the compile command
- Rename "prequ compile" to "prequ compile-in"
- Use ``requirements.pre`` as input for ``prequ update``

0.180.8
-------

- Rename Pip Requ to Prequ

0.180.7
-------

- (jazzband/pip-tools#450) Calculated dependencies could be left with wrong
  candidates when toplevel requirements happen to be also pinned in
  sub-dependencies
- Convert README and ChangeLog to restructured text (ReST)
- Include README as package long description in setup.py

0.180.6
-------

- (jazzband/pip-tools#417) Exclude irrelevant pip constraints

0.180.5
-------

- Fix "pip-requ compile-all" to handle "-e" and "-c" lines correctly
- Remove "pip-compile" and "pip-sync" commands

0.180.4
-------

- Fix "pip-requ compile --no-annotate"

0.180.3
-------

- Add support for "pip-requ --version"

0.180.2
-------

- (jazzband/pip-tools#378) Recalculate secondary dependencies between rounds
- (jazzband/pip-tools#448) Add "--no-trusted-host" option to fix #382
- (jazzband/pip-tools#448) Deduplicate the option lines of output
- (jazzband/pip-tools#441) Exclude packages required only by unsafe packages
- (jazzband/pip-tools#389) Ignore pkg-resources
- (jazzband/pip-tools#355) Support non-editable pinned VCS dependencies

0.180.1
-------

- Add "pip-requ" command
- Add "pip-requ build-wheels" command
- Add "pip-requ compile-all" command
- Add "pip-requ update" command

0.180.0
-------

- Fork from pip-tools 1.8.0

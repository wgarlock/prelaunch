Unreleased
----------

Features
~~~~~~~~

- Detect annotation and other options from the existing output files
- Merge configuration from setup.cfg with requirements*.in files

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

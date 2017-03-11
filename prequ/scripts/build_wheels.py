import os
import subprocess
from glob import glob

import click

from ..logging import log
from ..prereqfile import PreRequirements


@click.command()
@click.option('-s', '--silent', is_flag=True, help="Show no output")
def main(silent):
    """
    Build wheels of required packages.
    """
    build_wheels(silent=silent)


def build_wheels(silent=False):
    prereq = PreRequirements.from_directory('.')
    to_build = list(prereq.get_wheels_to_build())
    for (pkg, ver, url) in to_build:
        build_wheel(prereq, pkg, ver, url, silent)


def build_wheel(prereq, pkg, ver, url, silent=False):
    info = log.info if not silent else (lambda x: None)
    already_built = get_wheels(prereq, pkg, ver)
    if already_built:
        info('*** Already built: {}'.format(already_built[0]))
        return
    info('*** Building wheel for {} {} from {}'.format(pkg, ver, url))
    call('pip wheel {verbosity} -w {w} --no-deps {u}',
         verbosity=('-q' if silent else '-v'),
         w=prereq.wheel_dir, u=url)
    built_wheel = get_wheels(prereq, pkg, ver)[0]
    info('*** Built: {}'.format(built_wheel))
    for wheel in get_wheels(prereq, pkg):  # All versions
        if wheel != built_wheel:
            info('*** Removing: {}'.format(wheel))
            os.remove(wheel)


def get_wheels(prereq, pkg, ver='*'):
    return glob(os.path.join(
        prereq.wheel_dir, '{}-{}-*.whl'.format(pkg.replace('-', '_'), ver)))


def call(cmd, stdout=None, **kwargs):
    formatted_cmd = [x.format(**kwargs) for x in cmd.split()]
    return subprocess.check_call(formatted_cmd, stdout=stdout)

import os
import subprocess
from glob import glob

from .. import click
from ..prereqfile import PreRequirements


@click.command()
def main():
    """
    Build wheels of required packages.
    """
    build_wheels()


def build_wheels():
    prereq = PreRequirements.from_file('requirements.pre')
    to_build = list(prereq.get_wheels_to_build())
    for (pkg, ver, url) in to_build:
        build_wheel(prereq, pkg, ver, url)


def build_wheel(prereq, pkg, ver, url):
    already_built = get_wheels(prereq, pkg, ver)
    if already_built:
        print('*** Already built: {}'.format(already_built[0]))
        return
    print('*** Building wheel for {} {} from {}'.format(pkg, ver, url))
    call('pip wheel -v -w {w} --no-deps {u}', w=prereq.wheel_dir, u=url)
    built_wheel = get_wheels(prereq, pkg, ver)[0]
    print('*** Built: {}'.format(built_wheel))
    for wheel in get_wheels(prereq, pkg):  # All versions
        if wheel != built_wheel:
            print('*** Removing: {}'.format(wheel))
            os.remove(wheel)


def get_wheels(prereq, pkg, ver='*'):
    return glob(os.path.join(
        prereq.wheel_dir, '{}-{}-*.whl'.format(pkg.replace('-', '_'), ver)))


def call(cmd, stdout=None, **kwargs):
    formatted_cmd = [x.format(**kwargs) for x in cmd.split()]
    return subprocess.check_call(formatted_cmd, stdout=stdout)

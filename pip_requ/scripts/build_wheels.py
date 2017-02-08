import io
import os
import re
from glob import glob

from .. import click
from ._utils import call

WHEEL_DIR = 'wheels'

WHEEL_LINE_RX = re.compile(
    '^\s*(?P<pkg>(\w|-)+)(?P<verspec>\S*)\s+'
    '#\s*wheel:\s*(?P<wheel_spec>\S.*)$')


@click.command()
def main():
    """
    Build wheels of required packages.
    """
    build_wheels()


def build_wheels():
    to_build = list(get_packages_to_build())
    for (pkg, ver, url) in to_build:
        build_wheel(pkg, ver, url)


def get_packages_to_build():
    for requirement_file in glob('requirements*.in'):
        with io.open(requirement_file, 'rt', encoding='utf-8') as fp:
            for line in fp:
                if line.lstrip().startswith('#'):
                    continue
                m = WHEEL_LINE_RX.match(line)
                if m:
                    yield parse_requirement_wheel_line_data(**m.groupdict())


def parse_requirement_wheel_line_data(pkg, verspec, wheel_spec):
    if not verspec.startswith(('>=', '~=', '==')):
        raise Exception('No version (>=, ~=, ==) for: {}'.format(pkg))
    ver = verspec[2:]
    (provider, src) = wheel_spec.strip().split(':', 1)
    if provider == 'github':
        url = 'git+ssh://git@github.com/{}@v{}'.format(src, ver)
    else:
        raise Exception('Currently only github repos are supported')
    return (pkg, ver, url)


def build_wheel(pkg, ver, url):
    d = locals()
    if get_wheels(pkg, ver):
        print('*** Already built: {}'.format(get_wheels(pkg, ver)[0]))
        return
    print('*** Building wheel for {} {} from {}'.format(pkg, ver, url))
    call('pip wheel -v -w {w} --no-deps {u}', w=WHEEL_DIR, u=url)
    built_wheel = get_wheels(pkg, ver)[0]
    print('*** Built: {}'.format(built_wheel))
    for wheel in get_wheels(pkg):  # All versions
        if wheel != built_wheel:
            print('*** Removing: {}'.format(wheel))
            os.remove(wheel)


def get_wheels(pkg, ver='*'):
    return glob(os.path.join(
        WHEEL_DIR, '{}-{}-*.whl'.format(pkg.replace('-', '_'), ver)))

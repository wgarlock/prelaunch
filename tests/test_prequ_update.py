# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import contextlib
import io
import os

import pytest
from click.testing import CliRunner

from prequ.scripts.update import main


@pytest.yield_fixture
def pip_conf(tmpdir):
    pip_conf_file = 'pip.conf' if os.name != 'nt' else 'pip.ini'
    path = (tmpdir / pip_conf_file).strpath
    with open(path, 'w') as f:
        f.write(
            '[global]\n'
            'index-url = http://localhost\n'
            'trusted-host = localhost\n')
    old_value = os.environ.get('PIP_CONFIG_FILE')
    try:
        os.environ['PIP_CONFIG_FILE'] = path
        yield path
    finally:
        if old_value is not None:
            os.environ['PIP_CONFIG_FILE'] = old_value
        else:
            del os.environ['PIP_CONFIG_FILE']
        os.remove(path)


@contextlib.contextmanager
def run_check(pip_conf, options=None, requirements=None):
    assert os.path.exists(pip_conf)
    runner = CliRunner()
    with runner.isolated_filesystem():
        create_prerequirements(options, requirements)
        out = runner.invoke(main, ['-v'])
        yield out


def create_prerequirements(options=None, requirements=None):
    with io.open('requirements.pre', 'wt', encoding='utf-8') as fp:
        if options:
            fp.write('options:\n')
            for (key, value) in options.items():
                fp.write('  {}: {}\n'.format(key, value))
        fp.write('requirements:\n')
        if not requirements:
            fp.write('  base: ""\n')
        else:
            fp.write('  base: |')
            for req in requirements:
                fp.write(req + '\n')


def test_default_pip_conf_read(pip_conf):
    with run_check(pip_conf) as out:
        assert 'Using indexes:\n  http://localhost' in out.output
        assert '--index-url http://localhost' in out.output


def test_extra_index_option(pip_conf):
    options = {
        'extra_index_urls': (
            '["http://extraindex1.com", "http://extraindex2.com"]')
    }
    with run_check(pip_conf, options) as out:
        assert ('--index-url http://localhost\n'
                '--extra-index-url http://extraindex1.com\n'
                '--extra-index-url http://extraindex2.com' in out.output)


def test_wheel_dir_option(pip_conf):
    with run_check(pip_conf, options={'wheel_dir': 'foo/bar'}) as out:
        assert '--find-links foo/bar\n' in out.output


def test_trusted_host_option(pip_conf):
    options = {'trusted_hosts': '["example.com", "other.example.com"]'}
    with run_check(pip_conf, options) as out:
        assert ('--trusted-host example.com\n'
                '--trusted-host other.example.com\n') in out.output


def test_invalid_option(pip_conf):
    options = {'invalid': 'foobar'}
    with run_check(pip_conf, options) as out:
        assert out.exit_code != 0
        assert type(out.exc_info[1]).__name__ == 'InvalidPreRequirements'
        assert '{}'.format(out.exc_info[1]) == (
            'Errors in pre-requirement data:'
            ' Unknown key name: "options.invalid"')


def test_umlaut_in_pre_requirements_file(pip_conf):
    options = {'wheel_sources': '{"mämmi": "http://localhost/mämmi"}'}
    with run_check(pip_conf, options) as out:
        assert out.exit_code == 0

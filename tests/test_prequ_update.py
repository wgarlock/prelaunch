# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import contextlib
import io
import os

import pytest
import six
from click.testing import CliRunner

from prequ.configuration import InvalidPrequConfiguration
from prequ.scripts.update import main


@pytest.yield_fixture
def pip_conf(tmpdir):
    with get_temporary_pip_conf(tmpdir) as path:
        yield path


@pytest.yield_fixture
def pip_conf_with_index(tmpdir):
    with get_temporary_pip_conf(tmpdir, index='http://localhost') as path:
        yield path


@contextlib.contextmanager
def get_temporary_pip_conf(tmpdir, index=None):
    pip_conf_file = 'pip.conf' if os.name != 'nt' else 'pip.ini'
    path = (tmpdir / pip_conf_file).strpath
    index_line = ('index-url = ' + index) if index else 'no-index = yes'
    with open(path, 'w') as f:
        f.write(
            '[global]\n'
            + index_line + '\n' +
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
        create_configuration(options, requirements)
        out = runner.invoke(main, ['-v'])
        if out.exit_code == -1:
            (exc_type, exc_value, traceback) = out.exc_info
            exc_value.run_result = out
            six.reraise(exc_type, exc_value, traceback)
        yield out


def create_configuration(options=None, requirements=None):
    with io.open('setup.cfg', 'wt', encoding='utf-8') as fp:
        fp.write('[prequ]\n')
        if options:
            for (key, value) in options.items():
                if isinstance(value, dict):
                    value = [
                        '{} = {}'.format(k, v)
                        for (k, v) in value.items()
                    ]
                if isinstance(value, list):
                    value = '\n    ' + '\n    '.join(value)
                fp.write('{} = {}\n'.format(key, value))
        fp.write('requirements =\n')
        if requirements:
            for req in requirements:
                fp.write('    {}\n'.format(req))


def test_default_pip_conf_read(pip_conf):
    with run_check(pip_conf) as out:
        assert 'Using indexes:\n' in out.output
        after_index_title_line = out.output.split(
            'Using indexes:\n', 1)[1].split('\n', 1)[0]
        assert after_index_title_line == 'Limiting constraints:'
        assert '--trusted-host localhost' in out.output


def test_extra_index_option(pip_conf_with_index):
    options = {
        'extra_index_urls': [
            'http://extraindex1.com',
            'http://extraindex2.com',
        ],
    }
    with run_check(pip_conf_with_index, options) as out:
        assert ('--index-url http://localhost\n'
                '--extra-index-url http://extraindex1.com\n'
                '--extra-index-url http://extraindex2.com' in out.output)


def test_wheel_dir_option(pip_conf):
    with run_check(pip_conf, options={'wheel_dir': 'foo/bar'}) as out:
        find_links_line = '--find-links foo/bar\n'.replace('/', os.path.sep)
        assert find_links_line in out.output


def test_trusted_host_option(pip_conf):
    options = {'trusted_hosts': ['example.com', 'other.example.com']}
    with run_check(pip_conf, options) as out:
        assert ('--trusted-host example.com\n'
                '--trusted-host other.example.com\n') in out.output


def test_invalid_option(pip_conf):
    options = {'invalid': 'foobar'}
    with pytest.raises(InvalidPrequConfiguration) as excinfo:
        with run_check(pip_conf, options):
            pass
        assert '{}'.format(excinfo.value) == (
            'Errors in Prequ configuration:'
            ' Unknown key name: "options.invalid"')


def test_umlaut_in_prequ_conf_file(pip_conf):
    options = {'wheel_sources': {'mämmi': 'http://localhost/mämmi'}}
    with run_check(pip_conf, options) as out:
        assert out.exit_code == 0

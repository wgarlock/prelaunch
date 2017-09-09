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

from .dirs import FAKE_PYPI_WHEELS_DIR


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
def run_check(pip_conf, options=None, requirements=None,
              existing_out_files=None):
    assert os.path.exists(pip_conf)
    runner = CliRunner()
    with runner.isolated_filesystem():
        create_configuration(options, requirements, existing_out_files)
        out = runner.invoke(main, ['-v'])
        if out.exit_code == -1:
            (exc_type, exc_value, traceback) = out.exc_info
            exc_value.run_result = out
            six.reraise(exc_type, exc_value, traceback)
        yield out


def create_configuration(options=None, requirements=None,
                         existing_out_files=None):
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
        for (out_file, contents) in (existing_out_files or {}).items():
            with io.open(out_file, 'wt', encoding='utf-8') as fp:
                fp.write(contents)


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


def test_detect_annotate(pip_conf):
    txt_output = run_detection_check(
        pip_conf,
        'tiny-depender==1.0\n'
        'tiny-dependee==1.0  # via tiny-depender\n')
    assert txt_output == (
        '--trusted-host localhost\n'
        '\n'
        'tiny-dependee==1.0        # via tiny-depender\n'
        'tiny-depender==1.1\n')


WHEEL_HASHES = {
    'dependee_hash': (
        '01571cd4b1bc8c2a48cbd7a65313cde1a7a2a8b570d91986f7450dfa67bca30c'),
    'depender_hash': (
        'c0e69216348b53df1a5093c4d262f8b3f6fb9e392a71dfc5467120e1ff448a72'),
}


def test_detect_generate_hashes(pip_conf):
    txt_output = run_detection_check(
        pip_conf,
        'tiny-depender==0.1  \\\n    --hash=sha256:abc')
    assert txt_output == (
        '--trusted-host localhost\n'
        '\n'
        'tiny-dependee==1.0 \\\n'
        '    --hash=sha256:{dependee_hash}\n'
        'tiny-depender==1.1 \\\n'
        '    --hash=sha256:{depender_hash}\n').format(**WHEEL_HASHES)


@pytest.mark.parametrize('header_setting', [None, 'auto', 'yes', 'no'])
@pytest.mark.parametrize('header_present', [True, False, None])
def test_detect_header(pip_conf, header_setting, header_present):
    header = (
        '# This file is autogenerated by Prequ.  To update, run:\n'
        '#\n'
        '#   prequ update\n'
        '#\n')
    input_header = header if header_present else ''
    output_header = (
        header if (header_setting == 'yes' or
                   (header_setting != 'no' and header_present is not False))
        else '')
    input_content = (input_header + 'tiny-depender==1.0\ntiny-dependee==1.0\n'
                     if header_present is not None else None)
    options = {'header': header_setting} if header_setting else {}
    txt_output = run_detection_check(pip_conf, input_content, options)
    assert txt_output == (
        output_header +
        '--trusted-host localhost\n'
        '\n'
        'tiny-dependee==1.0\n'
        'tiny-depender==1.1\n')


def run_detection_check(pip_conf, req_txt_content, extra_options=None):
    options = {'wheel_dir': FAKE_PYPI_WHEELS_DIR}
    options.update(extra_options or {})
    conf = {
        'options': options,
        'requirements': ['tiny-depender>=1.1'],
    }
    if req_txt_content is not None:
        conf['existing_out_files'] = {'requirements.txt': req_txt_content}
    with run_check(pip_conf, **conf) as out:
        assert out.exit_code == 0
        with io.open('requirements.txt', 'rt', encoding='utf-8') as fp:
            result = fp.read()
        return result

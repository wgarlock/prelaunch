from __future__ import unicode_literals

import contextlib
import io
import os

import six
from click.testing import CliRunner


def make_cli_runner(cli_function, cli_args):
    @contextlib.contextmanager
    def run_check(pip_conf, options=None, requirements=None, **extra_conf):
        assert os.path.exists(pip_conf)
        runner = CliRunner()
        with runner.isolated_filesystem():
            create_configuration(options, requirements, **extra_conf)
            out = runner.invoke(cli_function, cli_args)
            if out.exit_code == -1:
                (exc_type, exc_value, traceback) = out.exc_info
                exc_value.run_result = out
                six.reraise(exc_type, exc_value, traceback)
            yield out
    return run_check


def create_configuration(options=None, requirements=None,
                         existing_out_files=None, no_setup_cfg=False):
    with io.open('setup.cfg', 'wt', encoding='utf-8') as fp:
        fp.write('[prequ]\n')
        if options is not None:
            _write_options(fp, options)
        _write_requirements(fp, requirements or [])
    if no_setup_cfg:
        os.remove('setup.cfg')
    if existing_out_files is not None:
        _write_existing_out_files(existing_out_files)


def _write_options(fp, options):
    for (key, value) in options.items():
        if isinstance(value, dict):
            value = [
                '{} = {}'.format(k, v)
                for (k, v) in value.items()
            ]
        if isinstance(value, list):
            value = '\n    ' + '\n    '.join(value)
        fp.write('{} = {}\n'.format(key, value))


def _write_requirements(fp, requirements):
    def write_req_section(label, req_list):
        suffix = '-{}'.format(label) if label != 'base' else ''
        fp.write('requirements{} =\n'.format(suffix))
        for req in req_list:
            fp.write('    {}\n'.format(req))

    if isinstance(requirements, list):
        write_req_section('base', requirements)
    elif isinstance(requirements, dict):
        for (label_or_filename, req_list) in requirements.items():
            if label_or_filename.endswith('.in'):
                _write_file(label_or_filename, '\n'.join(req_list))
            else:
                write_req_section(label_or_filename, req_list)


def _write_existing_out_files(existing_out_files):
    for (out_file, contents) in (existing_out_files or {}).items():
        _write_file(out_file, contents)


def _write_file(out_file, contents):
    with io.open(out_file, 'wt', encoding='utf-8') as fp:
        fp.write(contents)

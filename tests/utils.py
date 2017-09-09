from __future__ import unicode_literals

import contextlib
import io
import os

import six
from click.testing import CliRunner


def make_cli_runner(cli_function, cli_args):
    @contextlib.contextmanager
    def run_check(pip_conf, options=None, requirements=None,
                  existing_out_files=None):
        assert os.path.exists(pip_conf)
        runner = CliRunner()
        with runner.isolated_filesystem():
            create_configuration(options, requirements, existing_out_files)
            out = runner.invoke(cli_function, cli_args)
            if out.exit_code == -1:
                (exc_type, exc_value, traceback) = out.exc_info
                exc_value.run_result = out
                six.reraise(exc_type, exc_value, traceback)
            yield out
    return run_check


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

import difflib
import os
import sys
from tempfile import NamedTemporaryFile
from glob import glob
import click

from . import compile_in
from ..configuration import PrequConfiguration, CheckerPrequConfiguration
from ..exceptions import FileOutdated, PrequError
from ..logging import log
import yaml
import fileinput

click.disable_unicode_literals_warning = True


@click.command()
@click.option('-v', '--verbose', is_flag=True, help="Show more output")
@click.option('-s', '--silent', is_flag=True, help="Show no output")
@click.option('-c', '--check', is_flag=True,
              help="Check if the generated files are up-to-date")
@click.pass_context
def main(ctx, verbose, silent, check):
    """
    Compile requirements from source requirements.
    """
    try:
        compile(ctx, verbose, silent, check)
    except PrequError as error:
        if not check or not silent:
            log.error('{}'.format(error))
        raise SystemExit(1)


def compile(ctx, verbose, silent, check):
    info = log.info if not silent else (lambda x: None)
    conf_cls = PrequConfiguration if not check else CheckerPrequConfiguration
    conf = conf_cls.from_directory('.')

    compile_opts = dict(conf.get_prequ_compile_options())
    compile_opts.update(verbose=verbose, silent=(not verbose))
    if check:
        compile_opts.update(verbose=False, silent=True)

    try:
        if not check:
            version_number = str([x[2]  for x in conf.wheels_to_build if x[1] == conf.app_name][0])
            app_dir = os.path.join(os.getcwd(), conf.app_name)
            for path in os.listdir(app_dir):
                full_path = os.path.join(app_dir, path)
                _file = os.path.join(full_path, '__init__.py')
                if os.path.isdir(full_path) and os.path.exists(_file):
                    info('*** Updating {}'.format(
                        conf.get_output_file_for_nonreq(path))
                    )
                    for line in fileinput.input(_file, inplace = 1):
                        new_version = f'__version__ = "{version_number}"'
                        if "__version__ =" in line and line != new_version:
                            line.strip()
                            print(new_version)

                            
        if isinstance(conf, CheckerPrequConfiguration):
            conf.check(label, info, verbose)
    finally:
        if isinstance(conf, CheckerPrequConfiguration):
            conf.cleanup()

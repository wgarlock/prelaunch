import os
from tempfile import NamedTemporaryFile

import click

from . import compile_in
from ..exceptions import FileOutdated, PrequError
from ..logging import log
from ..prereqfile import PreRequirements

click.disable_unicode_literals_warning = True


@click.command()
@click.option('-v', '--verbose', is_flag=True, help="Show more output")
@click.option('-s', '--silent', is_flag=True, help="Show no output")
@click.option('-c', '--check', is_flag=True,
              help="Check if the generated files are up-to-date")
@click.pass_context
def main(ctx, verbose, silent, check):
    """
    Compile requirements from pre-requirements.
    """
    try:
        compile(ctx, verbose, silent, check)
    except PrequError as error:
        log.error('{}'.format(error))
        raise SystemExit(1)


def compile(ctx, verbose, silent, check):
    info = log.info if not silent else (lambda x: None)
    prereq_cls = PreRequirements if not check else CheckerPreRequirements
    prereq = prereq_cls.from_directory('.')

    compile_opts = dict(prereq.get_prequ_compile_options())
    compile_opts.update(verbose=verbose, silent=(not verbose))

    try:
        for label in prereq.labels:
            if not check:
                info('*** Compiling {}'.format(
                    prereq.get_output_file_for(label)))
            do_one_file(ctx, prereq, label, compile_opts)
            if check:
                prereq.check(label, info)
    finally:
        if check:
            prereq.cleanup()


def do_one_file(ctx, prereq, label, compile_opts):
    out_file = prereq.get_output_file_for(label)
    content = prereq.get_requirements_in_for(label).encode('utf-8')
    with get_tmp_file(prefix=out_file, suffix='.in') as tmp:
        tmp.write(content)
    try:
        ctx.invoke(compile_in.cli, src_files=[tmp.name], output_file=out_file,
                   **compile_opts)
    finally:
        os.remove(tmp.name)


class CheckerPreRequirements(PreRequirements):
    def __init__(self, *args, **kwargs):
        super(CheckerPreRequirements, self).__init__(*args, **kwargs)
        self.tmp_out_files = {}

    def get_output_file_for(self, label):
        try:
            return self.tmp_out_files[label]
        except KeyError:
            with get_tmp_file(prefix='req-' + label, suffix='.txt') as tmp:
                filename = tmp.name
            self.tmp_out_files[label] = filename
            return filename

    def get_requirements_in_for(self, label):
        parent = super(CheckerPreRequirements, self)
        parent_file = parent.get_output_file_for(label)
        if not os.path.exists(parent_file):
            raise FileOutdated('{} is missing'.format(parent_file))
        parent_req_in = parent.get_requirements_in_for(label)
        return '-c {}\n'.format(parent_file) + parent_req_in

    def check(self, label, info):
        cur = super(CheckerPreRequirements, self).get_output_file_for(label)
        new = self.get_output_file_for(label)
        if files_have_same_content(cur, new):
            info('{} is OK'.format(cur))
        else:
            raise FileOutdated('{} is outdated'.format(cur))

    def cleanup(self):
        for filename in self.tmp_out_files.values():
            os.remove(filename)


def get_tmp_file(prefix, suffix):
    return NamedTemporaryFile(
        dir='.', prefix=prefix, suffix=suffix, delete=False)


def files_have_same_content(filepath1, filepath2):
    return _read_file(filepath1) == _read_file(filepath2)


def _read_file(path):
    with open(path, 'rb') as fp:
        return fp.read()

import os
from tempfile import NamedTemporaryFile

import click

from ..prereqfile import PreRequirements
from . import compile_in


@click.command()
@click.option('-v', '--verbose', is_flag=True, help="Show more output")
@click.pass_context
def main(ctx, verbose):
    """
    Compile requirements from pre-requirements.
    """
    prereq = PreRequirements.from_directory('.')
    for label in prereq.labels:
        out_file = prereq.get_output_file_for(label)
        print('*** Compiling {}'.format(out_file))

        with NamedTemporaryFile(dir='.', prefix=out_file, suffix='.in',
                                delete=False) as tmp:
            tmp.write(prereq.get_requirements_in_for(label).encode('utf-8'))

        try:
            compile_options = dict(prereq.get_prequ_compile_options())
            compile_options['verbose'] = verbose
            compile_options['silent'] = (not verbose)
            compile_options['src_files'] = [tmp.name]
            compile_options['output_file'] = out_file
            ctx.invoke(compile_in.cli, **compile_options)
        finally:
            os.remove(tmp.name)

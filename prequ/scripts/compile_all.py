import os
from tempfile import NamedTemporaryFile

from .. import click
from ..prereqfile import PreRequirements
from . import compile_in


@click.command()
@click.option('-v', '--verbose', is_flag=True, help="Show more output")
@click.pass_context
def main(ctx, verbose):
    """
    Compile all requirements files (*.in).
    """
    prereq = PreRequirements.from_file('requirements.pre')
    for (mode, requirements) in prereq.get_requirements():
        if mode == 'base':
            out_file = 'requirements.txt'
        else:
            out_file = 'requirements-{}.txt'.format(mode)

        print('*** Compiling {}'.format(out_file))

        with NamedTemporaryFile(dir='.', prefix=out_file, suffix='.in',
                                delete=False) as tmp:
            if mode != 'base':
                tmp.write(b'-c requirements.txt\n')
            tmp.write(requirements.encode('utf-8'))

        try:
            compile_options = dict(prereq.get_prequ_compile_options())
            compile_options['verbose'] = verbose
            compile_options['silent'] = (not verbose)
            compile_options['src_files'] = [tmp.name]
            compile_options['output_file'] = out_file
            ctx.invoke(compile_in.cli, **compile_options)
        finally:
            os.remove(tmp.name)

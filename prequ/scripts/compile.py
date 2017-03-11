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
    for (label, requirement_set) in prereq.get_requirement_sets():
        if label == 'base':
            out_file = 'requirements.txt'
        else:
            out_file = 'requirements-{}.txt'.format(label)

        print('*** Compiling {}'.format(out_file))

        with NamedTemporaryFile(dir='.', prefix=out_file, suffix='.in',
                                delete=False) as tmp:
            if label != 'base' and 'base' in prereq.requirement_sets:
                tmp.write(b'-c requirements.txt\n')
            tmp.write(requirement_set.encode('utf-8'))

        try:
            compile_options = dict(prereq.get_prequ_compile_options())
            compile_options['verbose'] = verbose
            compile_options['silent'] = (not verbose)
            compile_options['src_files'] = [tmp.name]
            compile_options['output_file'] = out_file
            ctx.invoke(compile_in.cli, **compile_options)
        finally:
            os.remove(tmp.name)

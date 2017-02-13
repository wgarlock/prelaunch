from .. import click
from . import build_wheels
from . import compile_all


@click.command()
@click.option('-v', '--verbose', is_flag=True, help="Show more output")
@click.pass_context
def main(ctx, verbose):
    """
    Build wheels and compile all requirements.
    """
    ctx.invoke(build_wheels.main)
    ctx.invoke(compile_all.main, verbose=verbose)

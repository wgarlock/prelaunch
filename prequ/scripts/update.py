import click

from . import build_wheels
from . import compile

click.disable_unicode_literals_warning = True


@click.command()
@click.option('-v', '--verbose', is_flag=True, help="Show more output")
@click.pass_context
def main(ctx, verbose):
    """
    Build wheels and compile requirements.
    """
    ctx.invoke(build_wheels.main)
    ctx.invoke(compile.main, verbose=verbose)

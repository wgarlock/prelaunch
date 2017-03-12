import click

from . import build_wheels, compile


@click.command()
@click.option('-s', '--silent', is_flag=True, help="Show no output")
@click.pass_context
def main(ctx, silent):
    """
    Check if generated requirements are up-to-date.
    """
    ctx.invoke(build_wheels.main, check=True, silent=silent)
    ctx.invoke(compile.main, check=True, silent=silent)

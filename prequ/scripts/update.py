from .. import click
from .build_wheels import build_wheels
from .compile_all import compile_all_requirements


@click.command()
def main():
    """
    Build wheels and compile all requirements.
    """
    build_wheels()
    compile_all_requirements()

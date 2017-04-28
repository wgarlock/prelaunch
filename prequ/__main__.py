import click
from prequ.scripts import compile_in, sync


@click.group()
def cli():
    pass


cli.add_command(compile_in.cli, 'compile')
cli.add_command(sync.cli, 'sync')


# Enable ``python -m prequ ...``.
if __name__ == '__main__':  # pragma: no cover
    cli()

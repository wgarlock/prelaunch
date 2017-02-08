from .. import click
from . import compile
from . import sync


@click.group()
def main():
    pass


main.add_command(compile.cli, 'compile')
main.add_command(sync.cli, 'sync')


if __name__ == '__main__':
    main()

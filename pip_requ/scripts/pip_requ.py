from .. import click
from . import build_wheels
from . import compile
from . import compile_all
from . import sync
from . import update


@click.group()
def main():
    pass


main.add_command(build_wheels.main, 'build-wheels')
main.add_command(compile.cli, 'compile')
main.add_command(compile_all.main, 'compile-all')
main.add_command(sync.cli, 'sync')
main.add_command(update.main, 'update')


if __name__ == '__main__':
    main()

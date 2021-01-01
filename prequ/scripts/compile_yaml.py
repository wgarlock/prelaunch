import difflib
import os
from tempfile import NamedTemporaryFile
from glob import glob
import click

from . import compile_in
from ..configuration import PrequConfiguration, CheckerPrequConfiguration
from ..exceptions import FileOutdated, PrequError
from ..logging import log
import yaml
import re

click.disable_unicode_literals_warning = True


@click.command()
@click.option('-v', '--verbose', is_flag=True, help="Show more output")
@click.option('-s', '--silent', is_flag=True, help="Show no output")
@click.option('-c', '--check', is_flag=True,
              help="Check if the generated files are up-to-date")
@click.pass_context
def main(ctx, verbose, silent, check):
    """
    Compile requirements from source requirements.
    """
    try:
        compile(ctx, verbose, silent, check)
    except PrequError as error:
        if not check or not silent:
            log.error('{}'.format(error))
        raise SystemExit(1)

class ActionResolver(yaml.resolver.BaseResolver):
    pass


ActionResolver.add_implicit_resolver(
        'tag:yaml.org,2002:bool',
        re.compile(r'''^(?:yes|Yes|YES|no|No|NO
                    |true|True|TRUE|false|False|FALSE
                    |off|Off|OFF)$''', re.X),
        list('yYnNtTfFoO'))

ActionResolver.add_implicit_resolver(
        'tag:yaml.org,2002:float',
        re.compile(r'''^(?:[-+]?(?:[0-9][0-9_]*)\.[0-9_]*(?:[eE][-+][0-9]+)?
                    |\.[0-9_]+(?:[eE][-+][0-9]+)?
                    |[-+]?[0-9][0-9_]*(?::[0-5]?[0-9])+\.[0-9_]*
                    |[-+]?\.(?:inf|Inf|INF)
                    |\.(?:nan|NaN|NAN))$''', re.X),
        list('-+0123456789.'))

ActionResolver.add_implicit_resolver(
        'tag:yaml.org,2002:int',
        re.compile(r'''^(?:[-+]?0b[0-1_]+
                    |[-+]?0[0-7_]+
                    |[-+]?(?:0|[1-9][0-9_]*)
                    |[-+]?0x[0-9a-fA-F_]+
                    |[-+]?[1-9][0-9_]*(?::[0-5]?[0-9])+)$''', re.X),
        list('-+0123456789'))

ActionResolver.add_implicit_resolver(
        'tag:yaml.org,2002:merge',
        re.compile(r'^(?:<<)$'),
        ['<'])

ActionResolver.add_implicit_resolver(
        'tag:yaml.org,2002:null',
        re.compile(r'''^(?: ~
                    |null|Null|NULL
                    | )$''', re.X),
        ['~', 'n', 'N', ''])

ActionResolver.add_implicit_resolver(
        'tag:yaml.org,2002:timestamp',
        re.compile(r'''^(?:[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]
                    |[0-9][0-9][0-9][0-9] -[0-9][0-9]? -[0-9][0-9]?
                     (?:[Tt]|[ \t]+)[0-9][0-9]?
                     :[0-9][0-9] :[0-9][0-9] (?:\.[0-9]*)?
                     (?:[ \t]*(?:Z|[-+][0-9][0-9]?(?::[0-9][0-9])?))?)$''', re.X),
        list('0123456789'))

ActionResolver.add_implicit_resolver(
        'tag:yaml.org,2002:value',
        re.compile(r'^(?:=)$'),
        ['='])

# The following resolver is only for documentation purposes. It cannot work
# because plain scalars cannot start with '!', '&', or '*'.
ActionResolver.add_implicit_resolver(
        'tag:yaml.org,2002:yaml',
        re.compile(r'^(?:!|&|\*)$'),
        list('!&*'))


class GithubLoader(yaml.reader.Reader, yaml.scanner.Scanner, yaml.parser.Parser, yaml.composer.Composer, yaml.constructor.Constructor, ActionResolver):
    def __init__(self, stream):
        yaml.reader.Reader.__init__(self, stream)
        yaml.scanner.Scanner.__init__(self)
        yaml.parser.Parser.__init__(self)
        yaml.composer.Composer.__init__(self)
        yaml.constructor.Constructor.__init__(self)
        ActionResolver.__init__(self)



class GithubDumper(yaml.emitter.Emitter, yaml.serializer.Serializer, yaml.representer.Representer, ActionResolver):
    def __init__(self, stream,
            default_style=None, default_flow_style=False,
            canonical=None, indent=None, width=None,
            allow_unicode=None, line_break=None,
            encoding=None, explicit_start=None, explicit_end=None,
            version=None, tags=None, sort_keys=True):
        yaml.emitter.Emitter.__init__(self, stream, canonical=canonical,
                indent=indent, width=width,
                allow_unicode=allow_unicode, line_break=line_break)
        yaml.serializer.Serializer.__init__(self, encoding=encoding,
                explicit_start=explicit_start, explicit_end=explicit_end,
                version=version, tags=tags)
        yaml.representer.Representer.__init__(self, default_style=default_style,
                default_flow_style=default_flow_style, sort_keys=sort_keys)
        ActionResolver.__init__(self)


def compile(ctx, verbose, silent, check):
    info = log.info if not silent else (lambda x: None)
    conf_cls = PrequConfiguration if not check else CheckerPrequConfiguration
    conf = conf_cls.from_directory('.')

    compile_opts = dict(conf.get_prequ_compile_options())
    compile_opts.update(verbose=verbose, silent=(not verbose))
    if check:
        compile_opts.update(verbose=False, silent=True)

    try:
        if not check:
            version_number = [x[2]  for x in conf.wheels_to_build if x[1] == conf.app_name][0]
            
            for action in conf.github_actions:
                key-append = "prod"
                if 'dev' in action:
                    version_number = f"{version_number}dev"
                    key-append = "dev"

                filename = os.path.join('.', conf.github_actions_directory, action)
                info('*** Compiling {}'.format(
                    conf.get_output_file_for_nonreq(filename)))
                with open(filename) as file:
                    action_obj = yaml.load(file, Loader=GithubLoader)
    å
                docker_loc = [
                    d for d in action_obj["jobs"][f"docker-build-push-{key-append}"]["steps"] if d['name'] == "Build and push"
                ][0]["with"]["tags"].split(conf.app_name)
                docker_tag = f"{conf.app_name}:v{version_number}"
                docker_path = "".join([docker_loc[0], docker_tag])
                action_obj["jobs"]["docker-build-push"]["steps"][3]["with"]["tags"] = docker_path

                

                with open(filename, 'w') as file:
                    yaml.dump(action_obj, file, default_flow_style=False, sort_keys=False, Dumper=GithubDumper)



        if isinstance(conf, CheckerPrequConfiguration):
            conf.check(label, info, verbose)
    finally:
        if isinstance(conf, CheckerPrequConfiguration):
            conf.cleanup()

import io
import os
from tempfile import NamedTemporaryFile

import click
import packaging.version

from . import compile_in
from ..configuration import PrequConfiguration
from ..logging import log

try:
    import changelogs
except ImportError:
    changelogs = None


click.disable_unicode_literals_warning = True


@click.command()
@click.option('-a', '--all', 'upgrade_all', is_flag=True,
              help="Upgrade all packages")
@click.option('-i', '--interactive', is_flag=True,
              help="Show changelog and confirm the upgrade")
@click.option('-g', '--git-commit', is_flag=True,
              help="Create a Git commit describing the upgrade")
@click.argument('packages', nargs=-1)
@click.pass_context
def main(ctx, packages, upgrade_all, interactive, git_commit):
    """
    Upgrade pinned packages.

    This command allows to upgrade one or all of the pinned packages to
    a newer version.
    """
    assert isinstance(ctx, click.Context)
    if not packages and not upgrade_all:
        raise click.UsageError(
            "At least one package name or -a/--all must be specified")
    if packages and upgrade_all:
        raise click.UsageError(
            "Package names and -a/--all cannot be combined.")

    conf = PrequConfiguration.from_directory('.')
    compile_opts = conf.get_prequ_compile_options()
    compile_opts['silent'] = True

    if upgrade_all:
        compile_opts['upgrade'] = True
    compile_opts['upgrade_packages'] = packages

    for label in conf.labels:
        in_content = conf.get_requirements_in_for(label)
        output_file = conf.get_output_file_for(label)
        log.info("Checking {}".format(output_file))
        new_content = run_compile(ctx, in_content, output_file, compile_opts)
        comparer = RequirementComparer(output_file, new_content)
        for entry in comparer.describe_package_upgrades():
            print(entry)
        log.info('')


class RequirementComparer(object):
    def __init__(self, filename, new_content):
        self.filename = filename
        self.cur_content = read_utf8_file(filename)
        self.new_content = new_content
        self.cur_versions = parse_requirements(self.cur_content)
        self.new_versions = parse_requirements(self.new_content)

    def describe_package_upgrades(self):
        if self.new_versions == self.cur_versions:
            yield "All packages are up to date."
        else:
            all_pkgs = sorted(set(self.new_versions) | set(self.cur_versions))
            for pkg in all_pkgs:
                cur_ver = self.cur_versions.get(pkg)
                new_ver = self.new_versions.get(pkg)
                if cur_ver != new_ver:
                    yield format_package_upgrade_entry(pkg, cur_ver, new_ver)


def format_package_upgrade_entry(pkg, cur_ver, new_ver):
    assert cur_ver or new_ver
    if cur_ver and new_ver:
        title = "{pkg} {cur_ver} -> {new_ver}".format(**locals())
    elif new_ver:
        title = "{pkg} {new_ver} *NEW*".format(**locals())
    else:
        title = "{pkg} {cur_ver} *REMOVED*".format(**locals())
    title_line = (len(title) * '=')
    header = '\n'.join([title_line, title, title_line]) + '\n'

    if not cur_ver or not new_ver:
        return header

    changelog = list(get_changelog_between(pkg, cur_ver, new_ver))
    if not changelog:
        changelog_lines = ['No changelog available']
    else:
        changelog_lines = list(format_changelog(pkg, changelog))
    return header + '\n' + '\n'.join(changelog_lines) + '\n'


def format_changelog(pkg, changelog):
    for (ver, changes) in changelog:
        ver_text = '{pkg} {ver}'.format(**locals())
        yield ver_text
        for (n, line) in enumerate(changes.strip().splitlines()):
            if n == 0:
                if len(line) >= 3 and line == (line[0] * len(line)):
                    # Fix the length of the version header underlining
                    line = (line[0] * len(ver_text))
            yield line
        yield ''


def get_changelog_between(pkg, cur_ver, new_ver):
    #changelog = changelogs.get(pkg)
    changelog = get_cached_changelog(pkg)
    changelog_by_version = sorted(
        (parse_version(ver), changes)
        for (ver, changes) in (changelog or {}).items())
    cur_ver = parse_version(cur_ver)
    new_ver = parse_version(new_ver)
    for (ver, changes) in changelog_by_version:
        if ver > cur_ver and ver <= new_ver:
            yield (ver, changes)


def get_cached_changelog(pkg):
    import json
    cache_file = 'changelog_cache.json'
    if os.path.exists(cache_file):
        with io.open(cache_file, 'rt', encoding='utf-8') as fp:
            changelog_cache = json.load(fp)
    else:
        changelog_cache = {}
    changelog = changelog_cache.get(pkg)
    if changelog is None:
        changelog = changelogs.get(pkg)
        if changelog is None:
            changelog = {}
        changelog_cache[pkg] = changelog
        with io.open(cache_file, 'wt', encoding='utf-8') as fp:
            fp.write(json.dumps(changelog_cache).decode('utf-8'))
    return changelog


def parse_version(ver_string):
    return packaging.version.parse(ver_string)


def run_compile(ctx, in_content, output_file, compile_opts):
    tmp_in_filename = create_temporary_in_file(output_file, in_content)
    tmp_out_filename = create_temporary_out_file(output_file)
    try:
        ctx.invoke(
            compile_in.cli, src_files=[tmp_in_filename],
            output_file=tmp_out_filename, **compile_opts)
        return read_utf8_file(tmp_out_filename)
    finally:
        os.remove(tmp_in_filename)
        os.remove(tmp_out_filename)


def create_temporary_in_file(output_file, in_content):
    basename = output_file.replace('.txt', '-')
    with get_tmp_file(basename, '.in') as tmp_in:
        tmp_in.write(in_content.encode('utf-8'))
    return tmp_in.name


def create_temporary_out_file(output_file):
    basename = output_file.replace('.txt', '-')
    with get_tmp_file(basename, '.txt') as tmp:
        with open(output_file, 'rb') as src:
            tmp.write(src.read())
    return tmp.name


def get_tmp_file(prefix, suffix):
    return NamedTemporaryFile(
        dir='.', prefix=prefix, suffix=suffix, delete=False)


def read_utf8_file(filename):
    with io.open(filename, 'rt', encoding='utf-8') as fp:
        return fp.read()


def parse_requirements(content):
    versions = {}
    for line in content.replace('\\\n', '').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('-'):
            continue
        if ' --hash' in line:
            line = line.split(' --hash', 1)[0].strip()
        (pkg, ver) = line.split('==', 1)
        versions[pkg] = ver
    return versions

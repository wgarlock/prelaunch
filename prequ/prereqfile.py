"""
Prequ pre-requirements file definition and parsing.
"""
from __future__ import unicode_literals

import io
import os
import re
import sys
from collections import defaultdict
from contextlib import contextmanager
from glob import glob

from .ini_parser import parse_ini
from .repositories.pypi import PyPIRepository

try:
    import yaml
except ImportError:
    yaml = None


DEFAULT_INDEX_URL = PyPIRepository.DEFAULT_INDEX_URL

text = type('')


class PreRequirements(object):
    """
    Pre-requirements specification.

    Pre-requirements define how requirements files should be generated:
    various options, package names and versions.

    It is possible to have several requirement sets defined.  A single
    requirements file will be generated from each set.  These sets are
    addressed by a label which determines the output file name.  Label
    "base" is the default and its output is "requirements.txt".  Other
    output files are named "requirements-{label}.txt" by their labels.
    """

    fields = [
        ('options.annotate', bool),
        ('options.generate_hashes', bool),
        ('options.header', bool),
        ('options.index_url', text),
        ('options.extra_index_urls', [text]),
        ('options.trusted_hosts', [text]),
        ('options.wheel_dir', text),
        ('options.wheel_sources', {text: text}),
        ('requirements', {text: text}),
    ]

    @classmethod
    def from_directory(cls, directory):
        """
        Get pre-requirements of a directory.

        Reads the first existing pre-requirements configuration file(s)
        and parses it/them to a PreRequirements object.  Supported
        configuration files in preference order are:

          * setup.cfg, [prequ] section
          * requirements.pre
          * requirements.in and requirements-*.in

        :rtype: PreRequirements
        """
        def path(filename):
            return os.path.join(directory, filename)

        setup_cfg = path('setup.cfg')
        if os.path.exists(setup_cfg):
            from_ini = cls.from_ini(setup_cfg)
            if from_ini is not None:
                return from_ini
        pre_file = path('requirements.pre')
        if os.path.exists(pre_file):
            return cls.from_yaml(pre_file)
        in_files = (
            glob(path('requirements.in')) +
            glob(path('requirements-*.in')))
        if in_files:
            return cls.from_in_files(*in_files)
        raise NoPreRequirementsFound(
            'Cannot find pre-requirements. '
            'Add [prequ] section to your setup.cfg.')

    @classmethod
    def from_ini(cls, fileobj, section_name='prequ'):
        field_specs = {
            key.split('options.', 1)[1]: value
            for (key, value) in cls.fields
            if key.startswith('options.')
        }
        with _get_fileobj(fileobj, 'rt', 'utf-8') as fp:
            data = parse_ini(fp, field_specs, section_name=section_name)
        if not data:
            return None
        opts = {}
        reqs = {}
        for (key, value) in data.items():
            if key == 'requirements':
                reqs['base'] = value
            elif key.startswith('requirements-'):
                reqs[key.split('requirements-', 1)[1]] = value
            else:
                opts[key] = value
        return cls.from_dict({'options': opts, 'requirements': reqs})

    @classmethod
    def from_yaml(cls, fileobj):
        if not yaml:
            msg = (
                'Cannot load pre-requirements from "{}": No yaml module.  '
                'Migrate to setup.cfg or install pyyaml.').format(fileobj)
            raise Error(msg)
        with _get_fileobj(fileobj) as fp:
            conf_data = yaml.load(fp, UnicodeYamlSafeLoader)
        return cls.from_dict(conf_data)

    @classmethod
    def from_in_files(cls, *filenames):
        reqs = {}
        for filepath in filenames:
            fn = os.path.basename(filepath)
            if fn == 'requirements.in':
                label = 'base'
            elif fn.startswith('requirements-') and fn.endswith('.in'):
                label = fn.split('requirements-', 1)[1].rsplit('.in', 1)[0]
            else:
                raise InvalidPreRequirements(
                    'Invalid in-file name: {}'.format(fn))
            with io.open(filepath, 'rt', encoding='utf-8') as fp:
                reqs[label] = fp.read()
        return cls.from_dict({'requirements': reqs})

    @classmethod
    def from_dict(cls, conf_data):
        errors = get_data_errors(conf_data, cls.fields)
        if errors:
            raise InvalidPreRequirements(
                'Errors in pre-requirement data: {}'.format(', '.join(errors)))

        input_reqs = conf_data['requirements']
        (requirement_sets, extra_opts) = parse_input_requirements(input_reqs)
        options = conf_data.get('options', {})
        options.update(extra_opts)
        return cls(requirement_sets, **options)

    def __init__(self, requirement_sets, **kwargs):
        assert isinstance(requirement_sets, dict)
        assert all(isinstance(x, text) for x in requirement_sets.values())

        self.requirement_sets = requirement_sets
        self.annotate = kwargs.pop('annotate', False)
        self.generate_hashes = kwargs.pop('generate_hashes', False)
        self.header = kwargs.pop('header', True)
        self.index_url = kwargs.pop('index_url', DEFAULT_INDEX_URL)
        self.extra_index_urls = kwargs.pop('extra_index_urls', [])
        self.trusted_hosts = kwargs.pop('trusted_hosts', [])
        self.wheel_dir = kwargs.pop('wheel_dir', None)

        #: Wheel source map, format: {wheel_src_name: url_template}
        self.wheel_sources = kwargs.pop('wheel_sources', {})

        #: List of wheels to build, format [(wheel_src_name, pkg, ver)]
        self.wheels_to_build = kwargs.pop('wheels_to_build', [])

    @property
    def labels(self):
        def sort_key(label):
            return (0, label) if label == 'base' else (1, label)
        return sorted(self.requirement_sets.keys(), key=sort_key)

    def get_output_file_for(self, label):
        """
        Get output file name for a requirement set.

        :type label: text
        :rtype: text
        """
        return (
            'requirements.txt' if label == 'base' else
            'requirements-{}.txt'.format(label))

    def get_requirements_in_for(self, label):
        """
        Get requirements.in file content for a requirement set.

        :type label: text
        :rtype: text
        """
        constraint_line = (
            '-c {}\n'.format(self.get_output_file_for('base'))
            if label != 'base' and 'base' in self.requirement_sets
            else '')
        return constraint_line + self.requirement_sets[label]

    def get_wheels_to_build(self):
        for (wheel_src_name, pkg, ver) in self.wheels_to_build:
            url_template = self.wheel_sources.get(wheel_src_name)
            if not url_template:
                raise UnknownWheelSource(wheel_src_name)
            url = url_template.format(pkg=pkg, ver=ver)
            yield (pkg, ver, url)

    def get_prequ_compile_options(self):
        options = {
            'annotate': self.annotate,
            'header': self.header,
            'generate_hashes': self.generate_hashes,
        }
        if self.index_url != DEFAULT_INDEX_URL:
            options['index_url'] = self.index_url
        if self.extra_index_urls:
            options['extra_index_url'] = self.extra_index_urls
        if self.trusted_hosts:
            options['trusted_host'] = self.trusted_hosts
        if self.wheel_dir:
            options['find_links'] = [self.wheel_dir]
        return options

    def get_pip_options(self):
        options = []
        if self.index_url != DEFAULT_INDEX_URL:
            options.append('--index-url {}\n'.format(self.index_url))
        for extra_index_url in self.extra_index_urls:
            options.append('--extra-index-url {}\n'.format(extra_index_url))
        for trusted_host in self.trusted_hosts:
            options.append('--trusted-host {}\n'.format(trusted_host))
        if self.wheel_dir:
            options.append('--find-links {}\n'.format(self.wheel_dir))
        return options


@contextmanager
def _get_fileobj(file_or_filename, mode='rb', encoding=None):
    if isinstance(file_or_filename, (bytes, type(u''))):
        with io.open(file_or_filename, mode, encoding=encoding) as fp:
            yield fp
    else:
        yield file_or_filename


def get_data_errors(data, field_types):
    return (
        list(_get_key_errors(data, field_types)) +
        list(_get_type_errors(data, field_types)))


def _get_key_errors(data, field_types):
    top_level_keys = {x.split('.', 1)[0] for (x, _) in field_types}
    second_level_keys_map = defaultdict(set)
    for (fieldspec, _) in field_types:
        if '.' in fieldspec:
            (key, subkey) = fieldspec.split('.', 2)[:2]
            second_level_keys_map[key].add(subkey)
    for (key, value) in data.items():
        if key not in top_level_keys:
            yield 'Unknown key name: "{}"'.format(key)
        if isinstance(value, dict) and key in second_level_keys_map:
            second_level_keys = second_level_keys_map[key]
            for (subkey, subvalue) in value.items():
                if subkey not in second_level_keys:
                    yield 'Unknown key name: "{}.{}"'.format(key, subkey)


def _get_type_errors(data, field_types):
    unspecified = object()

    for (fieldspec, typespec) in field_types:
        value = data
        keypath = []
        for key in fieldspec.split('.'):
            if value is not unspecified:
                if isinstance(value, dict):
                    value = value.get(key, unspecified)
                else:
                    yield 'Field "{}" should be dict'.format('.'.join(keypath))
                    value = unspecified
            keypath.append(key)

        if value is unspecified:
            continue

        error = _get_type_error(value, typespec, fieldspec)
        if error:
            yield error


def _get_type_error(value, typespec, fieldspec):
    if isinstance(typespec, list):
        if not isinstance(value, list):
            return 'Field "{}" should be list'.format(fieldspec)
        itemtype = typespec[0]
        if not all(isinstance(x, itemtype) for x in value):
            typename = itemtype.__name__
            return 'Values of "{}" should be {}'.format(fieldspec, typename)
    elif isinstance(typespec, dict):
        if not isinstance(value, dict):
            return 'Field "{}" should be dict'.format(fieldspec)
        (keytype, valuetype) = list(typespec.items())[0]
        if not all(isinstance(x, keytype) for x in value.keys()):
            keytypename = keytype.__name__
            return 'Keys of "{}" should be {}'.format(fieldspec, keytypename)
        if not all(isinstance(x, valuetype) for x in value.values()):
            valtypename = valuetype.__name__
            return 'Values of "{}" should be {}'.format(fieldspec, valtypename)
    else:
        if not isinstance(typespec, type):
            raise ValueError('Invalid type specifier for "{}": {!r}'
                             .format(fieldspec, typespec))
        if not isinstance(value, typespec):
            typename = typespec.__name__
            return 'Field "{}" should be {}'.format(fieldspec, typename)


def parse_input_requirements(input_requirements):
    extra_opts = {}
    requirement_sets = {}
    for (label, req_data) in input_requirements.items():
        (requirement_set, opts) = _parse_req_data(req_data)
        _merge_update_dict(extra_opts, opts)
        requirement_sets[label] = requirement_set
    return (requirement_sets, extra_opts)


def _parse_req_data(req_data):
    result_lines = []
    wheels_to_build = []  # [(wheel_src_name, pkg, ver)]
    for line in req_data.splitlines():
        match = WHEEL_LINE_RX.match(line)
        if match:
            (wheel_data, req_line) = _parse_wheel_match(
                line, **match.groupdict())
            wheels_to_build.append(wheel_data)
            result_lines.append(req_line)
        else:
            result_lines.append(line)
    return ('\n'.join(result_lines), {'wheels_to_build': wheels_to_build})


WHEEL_LINE_RX = re.compile(
    '^\s*(?P<pkg>(\w|-)+)(?P<verspec>\S*)\s+'
    '\(\s*wheel from \s*(?P<wheel_src_name>\S+)\)$')


def _parse_wheel_match(line, pkg, verspec, wheel_src_name):
    if not verspec.startswith('=='):
        raise InvalidPreRequirements(
            'Wheel lines must use "==" version specifier: {}'.format(line))
    ver = verspec[2:]
    wheel_data = (wheel_src_name, pkg, ver)
    req_line = pkg + verspec
    return (wheel_data, req_line)


def _merge_update_dict(dest_dict, src_dict):
    for (key, value) in src_dict.items():
        if isinstance(value, dict):
            _merge_update_dict(dest_dict.setdefault(key, {}), value)
        elif isinstance(value, list):
            dest_dict[key] = dest_dict.get(key, []) + value
        elif isinstance(value, set):
            dest_dict[key] = dest_dict.get(key, set()) | value
        else:
            dest_dict[key] = value


class Error(Exception):
    pass


class NoPreRequirementsFound(Error):
    pass


class InvalidPreRequirements(Error):
    pass


class UnknownWheelSource(Error):
    def __init__(self, name):
        msg = 'No URL template defined for "{}"'.format(name)
        super(UnknownWheelSource, self).__init__(msg)


if yaml:
    class UnicodeYamlSafeLoader(yaml.SafeLoader):
        pass

    def construct_yaml_str(self, node):
        return self.construct_scalar(node)

    if sys.version_info < (3, 0):
        # Override YAML str constructor in Python 2 so that it will
        # construct unicode rather than bytes
        UnicodeYamlSafeLoader.add_constructor(
            'tag:yaml.org,2002:str', construct_yaml_str)

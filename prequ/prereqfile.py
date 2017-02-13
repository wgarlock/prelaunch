"""
Prequ pre-requirements file definition and parsing.
"""
from __future__ import unicode_literals

import re
import sys
from collections import defaultdict

from prequ.repositories.pypi import PyPIRepository

import yaml

DEFAULT_INDEX_URL = PyPIRepository.DEFAULT_INDEX_URL

text = type('')


class PreRequirements(object):
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
    def from_file(cls, fileobj):
        if hasattr(fileobj, 'read'):
            conf_data = yaml.load(fileobj, UnicodeYamlSafeLoader)
        else:
            with open(fileobj, 'rb') as fp:
                conf_data = yaml.load(fp, UnicodeYamlSafeLoader)
        return cls.from_dict(conf_data)

    @classmethod
    def from_dict(cls, conf_data):
        errors = get_data_errors(conf_data, cls.fields)
        if errors:
            raise InvalidPreRequirements(
                'Errors in pre-requirement data: {}'.format(', '.join(errors)))
        if 'base' not in conf_data.get('requirements', {}):
            raise InvalidPreRequirements('Base requirements are required')

        (requirements, extra_opts) = parse_reqs(conf_data['requirements'])
        options = conf_data.get('options', {})
        options.update(extra_opts)
        return cls(requirements, **options)

    def __init__(self, requirements, **kwargs):
        assert isinstance(requirements, dict)
        assert 'base' in requirements
        assert all(isinstance(x, text) for x in requirements.values())

        self.requirements = requirements
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

    def get_requirements(self):
        base_reqs = [('base', self.requirements['base'])]
        non_base_reqs = [
            (mode, self.requirements[mode])
            for mode in self.requirements
            if mode != 'base']
        return base_reqs + non_base_reqs

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


def parse_reqs(requirements_map):
    extra_opts = {}
    reqs = {}
    for (mode, req_data) in requirements_map.items():
        (req, opts) = _parse_req_data(req_data)
        _merge_update_dict(extra_opts, opts)
        reqs[mode] = req
    return (reqs, extra_opts)


def _parse_req_data(req_data):
    result_lines = []
    wheels_to_build = []  # [(wheel_src_name, pkg, ver)]
    for line in req_data.splitlines():
        match = WHEEL_LINE_RX.match(line)
        if match:
            (wheel_data, req_line) = _parse_wheel_match(**match.groupdict())
            wheels_to_build.append(wheel_data)
            result_lines.append(req_line)
        else:
            result_lines.append(line)
    return ('\n'.join(result_lines), {'wheels_to_build': wheels_to_build})


WHEEL_LINE_RX = re.compile(
    '^\s*(?P<pkg>(\w|-)+)(?P<verspec>\S*)\s+'
    '\(\s*wheel from \s*(?P<wheel_src_name>\S+)\)$')


def _parse_wheel_match(pkg, verspec, wheel_src_name):
    if not verspec.startswith(('>=', '~=', '==')):
        raise InvalidPreRequirements(
            'Wheel needs version specifier (==, ~=, or >=): {}'.format(pkg))
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


class InvalidPreRequirements(Error):
    pass


class UnknownWheelSource(Error):
    def __init__(self, name):
        msg = 'No URL template defined for "{}"'.format(name)
        super(UnknownWheelSource, self).__init__(msg)


class UnicodeYamlSafeLoader(yaml.SafeLoader):
    pass


def construct_yaml_str(self, node):
    return self.construct_scalar(node)


if sys.version_info < (3, 0):
    # Override YAML str constructor in Python 2 so that it will
    # construct unicode rather than bytes
    UnicodeYamlSafeLoader.add_constructor(
        'tag:yaml.org,2002:str', construct_yaml_str)

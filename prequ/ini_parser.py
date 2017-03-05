from __future__ import unicode_literals

from six.moves import configparser

text = type('')


class ParseError(Exception):
    pass


def parse_ini(fileobj, field_specs, section_name):
    parser = configparser.RawConfigParser()
    readfile = getattr(parser, 'read_file', getattr(parser, 'readfp', None))
    readfile(fileobj)
    if not parser.has_section(section_name):
        return None
    result = {}
    for (key, value) in parser.items(section_name):
        spec = field_specs.get(key, text)
        result[key] = _parse_value(parser, section_name, key, value, spec)
    return result


def _parse_value(parser, section_name, key, value, spec):
    if spec == bool:
        try:
            return parser.getboolean(section_name, key)
        except ValueError:
            raise ParseError(
                'Unknown value for bool option "{}": {!r}'.format(key, value))
    elif spec == text:
        return value
    elif isinstance(spec, list):
        assert spec == [text], 'Unhandled type spec: %r' % (spec,)
        return [x for x in value.splitlines() if x]
    elif isinstance(spec, dict):
        assert spec == {text: text}, 'Unhandled type spec: %r' % (spec,)
        return dict(x.split(' = ', 1) for x in value.splitlines() if x)
    else:
        assert False, 'Unhandled type spec: %r' % (spec,)

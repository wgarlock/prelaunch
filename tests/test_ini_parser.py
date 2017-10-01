from __future__ import unicode_literals

import textwrap
from io import StringIO

import pytest

from prequ.ini_parser import ParseError, bool_or_auto, parse_ini, text


def test_basics():
    ini_content = StringIO(textwrap.dedent("""
    [some-section]
    b = yes
    ba = auto
    t = Hello World!
    l =
        value 1
        value 2
    d =
        key 1 = value 1
        key 2 = value 2

    [other-section]
    these = variables
    make = no difference
    """.lstrip('\n')))
    specs = {
        'b': bool,
        'ba': bool_or_auto,
        't': text,
        'l': [text],
        'd': {text: text},
    }
    parsed = parse_ini(ini_content, specs, 'some-section')
    assert parsed['b'] is True
    assert parsed['ba'] == 'auto'
    assert parsed['t'] == 'Hello World!'
    assert parsed['l'] == ['value 1', 'value 2']
    assert parsed['d'] == {'key 1': 'value 1', 'key 2': 'value 2'}
    assert set(parsed.keys()) == {'b', 'ba', 't', 'l', 'd'}


def test_no_section():
    ini_content = StringIO(textwrap.dedent("""
    [other-section]
    something = foo bar
    """.lstrip('\n')))
    parsed = parse_ini(ini_content, {}, 'some-section')
    assert parsed is None


def test_empty_section():
    ini_content = StringIO(textwrap.dedent("""
    [some-section]

    [other-section]
    """.lstrip('\n')))
    parsed = parse_ini(ini_content, {}, 'some-section')
    assert parsed == {}


def test_parse_bool_ok():
    data = [
        ('v1', bool, 'yes', True),
        ('v2', bool, 'no', False),
        ('v3', bool, 'true', True),
        ('v4', bool, 'false', False),
        ('v5', bool, '1', True),
        ('v6', bool, '0', False),
        ('v7', bool, 'YES', True),
        ('v8', bool, 'NO', False),
        ('v9', bool, 'True', True),
        ('v10', bool, 'False', False),
        ('v11', bool, 'yEs', True),
        ('v12', bool, 'on', True),
        ('v13', bool, 'off', False),
    ]
    parsed = parse_variables([x[0:3] for x in data])
    for (name, spec, string_val, expected) in data:
        assert parsed[name] is expected


@pytest.mark.parametrize('val', ['foobar', '', '2', 'y', 'n', 'ei'])
def test_parse_bool_invalids(val):
    with pytest.raises(ParseError) as excinfo:
        parse_variables([('bool_variable', bool, val)])
    assert '{}'.format(excinfo.value) == (
        "Unknown bool value for option \"bool_variable\": {!r}".format(val))


def test_parse_text():
    data = [
        ('v1', text, 'hello'),
        ('v2', text, ''),
        ('v3', text, 'has spaces in value'),
    ]
    parsed = parse_variables(data)
    for (name, spec, string_val) in data:
        assert parsed[name] == string_val


def test_parse_list():
    data = [
        ('empty', [text], ''),
        ('single', [text], 'single value'),
        ('single2', [text], '\n   single value on second line'),
        ('abc', [text], '\n  '.join(['', 'a', 'b', 'c'])),
        ('ab_c', [text], '\n  '.join(['', 'a', 'b', '', 'c'])),
    ]
    parsed = parse_variables(data)
    assert parsed['empty'] == []
    assert parsed['single'] == ['single value']
    assert parsed['single2'] == ['single value on second line']
    assert parsed['abc'] == ['a', 'b', 'c']
    assert parsed['ab_c'] == ['a', 'b', 'c']


def test_parse_unsupported_list():
    with pytest.raises(NotImplementedError) as excinfo:
        parse_variables([('bool_list', [bool], 'True')])
    assert "Type spec not implemented" in '{}'.format(excinfo.value)


def test_parse_dict():
    data = [
        ('empty', {text: text}, ''),
        ('single', {text: text}, 'a = single value'),
        ('single2', {text: text}, '\n   a = single value on second line'),
        ('abc', {text: text}, '\n  '.join(['', 'a = 1', 'b = 2', 'c = 3'])),
        ('ab_c', {text: text}, '\n  '.join([
            '', 'a = 1', 'b = 2', '', 'c = 3'])),
    ]
    parsed = parse_variables(data)
    assert parsed['empty'] == {}
    assert parsed['single'] == {'a': 'single value'}
    assert parsed['single2'] == {'a': 'single value on second line'}
    assert parsed['abc'] == {'a': '1', 'b': '2', 'c': '3'}
    assert parsed['ab_c'] == {'a': '1', 'b': '2', 'c': '3'}


def test_parse_unsupported_dict():
    with pytest.raises(NotImplementedError) as excinfo:
        parse_variables([('bool_dict', {bool: bool}, 'a = True')])
    assert "Type spec not implemented" in '{}'.format(excinfo.value)


def test_invalid_spec():
    with pytest.raises(NotImplementedError) as excinfo:
        parse_variables([('bool_dict', float, '0.5')])
    assert "Type spec not implemented" in '{}'.format(excinfo.value)


def parse_variables(variables):
    ini_lines = ['{} = {}'.format(name, val) for (name, _sp, val) in variables]
    ini_content = StringIO('[some_section]\n' + '\n'.join(ini_lines) + '\n')
    specs = {name: spec for (name, spec, _val) in variables}
    parsed = parse_ini(ini_content, specs, 'some_section')
    assert set(parsed.keys()) == set(x[0] for x in variables)
    return parsed

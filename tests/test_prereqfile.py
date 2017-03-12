# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import io

import pytest

from prequ.prereqfile import get_data_errors, PreRequirements, text


field_types = [
    ('text_item', text),
    ('int_item', int),
    ('list_item_int_value', [int]),
    ('dict_item', {text: text}),
    ('dict_item_int_value', {text: int}),
    ('dict_item_int_key', {int: text}),
    ('sub.int_item', int),
    ('sub.text_item', text),
    ('a.b.c', int),
]

ok_data = {
    'text_item': 'hello',
    'int_item': 42,
    'list_item_int_value': [1, 2, 3],
    'dict_item': {'foo': 'bar', 'something': 'else'},
    'dict_item_int_value': {'a': 1, 'b': 2},
    'dict_item_int_key': {4: 'four', 2: 'two'},
    'sub': {'text_item': 'hello'},
    'a': {'b': {'c': 100}},
}


def test_get_data_errors_edge_cases():
    assert get_data_errors({}, []) == []
    assert get_data_errors({}, field_types) == []


def test_get_data_errors_unknown_keys():
    assert get_data_errors({'a': 'b'}, []) == ['Unknown key name: "a"']
    assert get_data_errors({'x': 1}, field_types) == ['Unknown key name: "x"']


def test_get_data_errors_simple():
    assert get_data_errors({'a': 'foobar'}, [('a', int)]) == [
        'Field "a" should be int']
    assert get_data_errors({'a': 'foobar'}, [('a', {text: text})]) == [
        'Field "a" should be dict']
    assert get_data_errors({'a': {'foobar': 2}}, [('a', {text: text})]) == [
        'Values of "a" should be ' + text.__name__]
    assert get_data_errors({'a': {2: 'foobar'}}, [('a', {text: text})]) == [
        'Keys of "a" should be ' + text.__name__]


def test_get_data_errors_sub_dict():
    assert get_data_errors({'a': 1}, field_types) == [
        'Field "a" should be dict']
    assert get_data_errors({'a': {'b': 1}}, field_types) == [
        'Field "a.b" should be dict']


def test_get_data_errors_with_unknown_subkey():
    assert get_data_errors({'sub': {'unknown': 42}}, field_types) == [
        'Unknown key name: "sub.unknown"']


def test_get_data_errors_with_known_subkey():
    assert get_data_errors({'sub': {'int_item': 42}}, field_types) == []
    assert get_data_errors({'sub': {'text_item': ''}}, field_types) == []


def test_get_data_errors_with_ok_data():
    assert get_data_errors(ok_data, field_types) == []


def test_get_data_errors_with_int_error():
    not_ok = dict(ok_data, int_item='hello')
    assert get_data_errors(not_ok, field_types) == [
        'Field "int_item" should be int']


def test_get_data_errors_with_list_error():
    not_ok = dict(ok_data, list_item_int_value=42)
    assert get_data_errors(not_ok, field_types) == [
        'Field "list_item_int_value" should be list']


def test_get_data_errors_with_list_item_error():
    not_ok = dict(ok_data, list_item_int_value=['not int'])
    assert get_data_errors(not_ok, field_types) == [
        'Values of "list_item_int_value" should be int']


def test_get_data_errors_with_dict_error():
    not_ok = dict(ok_data, dict_item='hello')
    assert get_data_errors(not_ok, field_types) == [
        'Field "dict_item" should be dict']


def test_get_data_errors_with_sub_text_error():
    not_ok = dict(ok_data, sub={'text_item': 42})
    assert get_data_errors(not_ok, field_types) == [
        'Field "sub.text_item" should be ' + text.__name__]


def test_get_data_errors_invalid_type_specifier():
    with pytest.raises(ValueError):
        get_data_errors({'x': 1}, [('x', set('abc'))])


def test_label_sorting():
    data = {'requirements': {'a': '', 'base': '', 'b': '', 'c': ''}}
    prereq = PreRequirements.from_dict(data)
    assert prereq.labels == ['base', 'a', 'b', 'c']


def test_requirements_in_generation():
    data = {
        'requirements': {
            'base': 'framework',
            'dev': 'ipython',
            'test': 'pytest',
        }
    }
    prereq = PreRequirements.from_dict(data)
    assert prereq.get_requirements_in_for('base') == 'framework'
    assert prereq.get_requirements_in_for('dev') == (
        '-c requirements.txt\n'
        'ipython')
    assert prereq.get_requirements_in_for('test') == (
        '-c requirements.txt\n'
        'pytest')


prereq_ini_content = """
[prequ]
annotate = True
extra_index_urls =
    https://one.example.com/
    https://two.example.com/
wheel_dir = wh€€ls
wheel_sources =
    test_gh = git+ssh://git@github.com/test/{pkg}@{ver}

requirements =
    foobar
    somewheel==1.0.0 (wheel from test_gh)
    barfoo

requirements-dev =
    devpkg>=2
"""


def test_prerequirements_parsing_ini():
    stream = io.StringIO(prereq_ini_content)
    prereq = PreRequirements.from_ini(stream)
    assert prereq.annotate is True
    assert prereq.extra_index_urls == [
        'https://one.example.com/', 'https://two.example.com/']
    assert prereq.wheel_dir == 'wh€€ls'
    assert prereq.wheel_sources == {
        'test_gh': 'git+ssh://git@github.com/test/{pkg}@{ver}'}
    assert sorted(prereq.requirement_sets.keys()) == ['base', 'dev']
    assert prereq.requirement_sets['base'] == (
        '\n'
        'foobar\n'
        'somewheel==1.0.0\n'
        'barfoo')
    assert prereq.requirement_sets['dev'] == '\ndevpkg>=2'
    assert prereq.wheels_to_build == [('test_gh', 'somewheel', '1.0.0')]
    assert list(prereq.get_wheels_to_build()) == [
        ('somewheel', '1.0.0',
         'git+ssh://git@github.com/test/somewheel@1.0.0')]
    pass


def test_prerequirements_parsing_ini_no_section():
    other_ini_content = (
        '[other_section]\n'
        'something = else\n')
    stream = io.StringIO(other_ini_content)
    prereq = PreRequirements.from_ini(stream)
    assert prereq is None


def test_prerequirements_parsing_ini_simple():
    other_ini_content = (
        '[prequ]\n'
        'requirements = flask\n')
    stream = io.StringIO(other_ini_content)
    prereq = PreRequirements.from_ini(stream)
    assert isinstance(prereq, PreRequirements)
    assert prereq.requirement_sets['base'] == 'flask'


def test_prerequirements_parsing_ini_without_base():
    other_ini_content = (
        '[prequ]\n'
        'requirements-test = pytest\n')
    stream = io.StringIO(other_ini_content)
    prereq = PreRequirements.from_ini(stream)
    assert prereq.requirement_sets['test'] == 'pytest'
    assert 'base' not in prereq.requirement_sets


prereq_yaml_content = """
options:
  annotate: yes
  extra_index_urls:
    - https://one.example.com/
    - https://two.example.com/
  wheel_dir: wh€€ls
  wheel_sources:
    test_gh: git+ssh://git@github.com/test/{pkg}@{ver}

requirements:
  base: |
    foobar
    somewheel==1.0.0 (wheel from test_gh)
    barfoo

  dev: |
    devpkg>=2
"""


def test_prerequirements_parsing_yaml():
    stream = io.BytesIO(prereq_yaml_content.encode('utf-8'))
    prereq = PreRequirements.from_yaml(stream)
    assert prereq.annotate is True
    assert prereq.extra_index_urls == [
        'https://one.example.com/', 'https://two.example.com/']
    assert prereq.wheel_dir == 'wh€€ls'
    assert prereq.wheel_sources == {
        'test_gh': 'git+ssh://git@github.com/test/{pkg}@{ver}'}
    assert sorted(prereq.requirement_sets.keys()) == ['base', 'dev']
    assert prereq.requirement_sets['base'] == (
        'foobar\n'
        'somewheel==1.0.0\n'
        'barfoo')
    assert prereq.requirement_sets['dev'] == 'devpkg>=2'
    assert prereq.wheels_to_build == [('test_gh', 'somewheel', '1.0.0')]
    assert list(prereq.get_wheels_to_build()) == [
        ('somewheel', '1.0.0',
         'git+ssh://git@github.com/test/somewheel@1.0.0')]

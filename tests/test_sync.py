import os
import sys
import tempfile
from collections import Counter

import mock
import pytest

from prequ._pip_compat import path_to_url, url_to_path
from prequ.exceptions import IncompatibleRequirements
from prequ.sync import dependency_tree, diff, merge, sync
from prequ.utils import get_ireq_version, key_from_dist, normalize_req_name


@pytest.fixture
def mocked_tmp_file():
    with mock.patch.object(tempfile, 'NamedTemporaryFile') as m:
        yield m.return_value


@pytest.fixture
def mocked_tmp_req_file(mocked_tmp_file):
    with mock.patch('os.unlink'):
        mocked_tmp_file.name = 'requirements.txt'
        yield mocked_tmp_file


@pytest.mark.parametrize(
    ('installed', 'root', 'expected'),

    [
        ([],
            'prequ', []),

        ([('prequ==1', [])],
            'prequ', ['prequ']),

        ([('prequ==1', []),
          ('django==1.7', [])],
            'prequ', ['prequ']),

        ([('prequ==1', ['click>=2']),
          ('django==1.7', []),
          ('click==3', [])],
            'prequ', ['prequ', 'click']),

        ([('prequ==1', ['click>=2']),
          ('django==1.7', []),
          ('click==1', [])],
            'prequ', ['prequ']),

        ([('root==1', ['child==2']),
          ('child==2', ['grandchild==3']),
          ('grandchild==3', [])],
            'root', ['root', 'child', 'grandchild']),

        ([('root==1', ['child==2']),
          ('child==2', ['root==1'])],
            'root', ['root', 'child']),
    ]
)
def test_dependency_tree(fake_dist, installed, root, expected):
    installed = {key_from_dist(distribution): distribution
                 for distribution in
                 (fake_dist(name, deps) for name, deps in installed)}

    root_key = normalize_req_name(root)
    actual = dependency_tree(installed, root_key)
    assert actual == set(expected)


def test_merge_detect_conflicts(from_line):
    requirements = [from_line('flask==1'), from_line('flask==2')]

    with pytest.raises(IncompatibleRequirements):
        merge(requirements, ignore_conflicts=False)


def test_merge_ignore_conflicts(from_line):
    requirements = [from_line('flask==1'), from_line('flask==2')]

    assert Counter(requirements[1:2]) == Counter(merge(requirements, ignore_conflicts=True))


def test_merge(from_line):
    requirements = [from_line('flask==1'),
                    from_line('flask==1'),
                    from_line('django==2')]

    assert Counter(requirements[1:3]) == Counter(merge(requirements, ignore_conflicts=True))


def test_diff_should_do_nothing():
    installed = []  # empty env
    reqs = []  # no requirements

    to_install, to_uninstall = diff(reqs, installed)
    assert to_install == set()
    assert to_uninstall == set()


def test_diff_should_install(from_line):
    installed = []  # empty env
    reqs = [from_line('django==1.8')]

    to_install, to_uninstall = diff(reqs, installed)
    assert {str(x.req) for x in to_install} == {'django==1.8'}
    assert to_uninstall == set()


def test_diff_should_uninstall(fake_dist):
    installed = [fake_dist('django==1.8')]
    reqs = []

    to_install, to_uninstall = diff(reqs, installed)
    assert to_install == set()
    assert to_uninstall == {'django'}  # no version spec when uninstalling


def test_diff_should_not_uninstall(fake_dist):
    ignored = ('pip==7.1.0', 'prequ==1.0.0', 'pip-review==1.1.1',
               'pkg-resources==0.0.0', 'setuptools==34.0.0', 'wheel==0.29.0',
               'python==3.0', 'distribute==0.1', 'wsgiref==0.1', 'argparse==0.1')
    installed = [fake_dist(pkg) for pkg in ignored]
    reqs = []

    to_uninstall = diff(reqs, installed)[1]
    assert to_uninstall == set()


def test_diff_should_update(fake_dist, from_line):
    installed = [fake_dist('django==1.7')]
    reqs = [from_line('django==1.8')]

    to_install, to_uninstall = diff(reqs, installed)
    assert {str(x.req) for x in to_install} == {'django==1.8'}
    assert to_uninstall == set()


def test_diff_should_install_with_markers(from_line):
    installed = []
    reqs = [from_line("subprocess32==3.2.7 ; python_version=='2.7'")]

    to_install, to_uninstall = diff(reqs, installed)
    assert {str(x.req) for x in to_install} == ({'subprocess32==3.2.7'} if sys.version.startswith('2.7') else set())
    assert to_uninstall == set()


def test_diff_should_uninstall_with_markers(fake_dist, from_line):
    installed = [fake_dist('subprocess32==3.2.7')]
    reqs = [from_line("subprocess32==3.2.7 ; python_version=='2.7'")]

    to_install, to_uninstall = diff(reqs, installed)
    assert to_install == set()
    assert to_uninstall == (set() if sys.version.startswith('2.7') else {'subprocess32'})


def test_diff_leave_packaging_packages_alone(fake_dist, from_line):
    # Suppose an env contains Django, and pip itself
    installed = [
        fake_dist('django==1.7'),
        fake_dist('first==2.0.1'),
        fake_dist('pip==7.1.0'),
    ]

    # Then this Django-only requirement should keep pip around (i.e. NOT
    # uninstall it), but uninstall first
    reqs = [
        from_line('django==1.7'),
    ]

    to_install, to_uninstall = diff(reqs, installed)
    assert to_install == set()
    assert to_uninstall == {'first'}


def test_diff_leave_prequ_alone(fake_dist, from_line):
    # Suppose an env contains Django, and prequ itself (including all of
    # its dependencies)
    installed = [
        fake_dist('django==1.7'),
        fake_dist('first==2.0.1'),
        fake_dist('prequ==1.1.1', [
            'click>=4',
            'first',
            'six',
        ]),
        fake_dist('six==1.9.0'),
        fake_dist('click==4.1'),
        fake_dist('foobar==0.3.6'),
    ]

    # Then this Django-only requirement should keep pip around (i.e. NOT
    # uninstall it), but uninstall first
    reqs = [
        from_line('django==1.7'),
    ]

    to_install, to_uninstall = diff(reqs, installed)
    assert to_install == set()
    assert to_uninstall == {'foobar'}


def test_diff_with_editable(
        fake_dist, from_editable, from_line, small_fake_package_dir):
    installed = [
        fake_dist('small-fake-with-deps==0.0.1'),
        fake_dist('six==1.10.0'),
    ]
    reqs = [
        from_editable(small_fake_package_dir),
        from_line('six==1.10.0'),
    ]
    to_install, to_uninstall = diff(reqs, installed)

    assert to_uninstall == set(), "No packages should be uninstalled"

    # The editable should be upgraded, since the installed version
    # (0.0.1) was different than the version specified in setup.py of
    # the editable package (0.1)
    assert len(to_install) == 1
    package = list(to_install)[0]
    assert package.editable
    assert str(package.link) == path_to_url(small_fake_package_dir)


def test_diff_with_editable_without_changes(
        fake_dist, from_editable, from_line, small_fake_package_dir):
    installed = [
        fake_dist('small-fake-with-deps==0.1'),
        fake_dist('six==1.10.0'),
    ]
    reqs = [
        from_editable(small_fake_package_dir),
        from_line('six==1.10.0'),
    ]
    assert reqs[0].req is None, "Editable doesn't have Requirement data yet"

    to_install, to_uninstall = diff(reqs, installed)

    assert reqs[0].req is not None, "Requirement data has been filled"
    pinned_ver = get_ireq_version(reqs[0])
    assert installed[0].version == pinned_ver

    assert to_uninstall == set(), "No packages should be uninstalled"
    assert to_install == set(), "No packages should be (re)installed"


def test_sync_install_temporary_requirement_file(from_line, from_editable, mocked_tmp_req_file):
    with mock.patch('prequ.sync.check_call') as check_call:
        to_install = {from_line('django==1.8')}
        sync(to_install, set())
        check_call.assert_called_once_with(['pip', 'install', '-r', mocked_tmp_req_file.name, '-q'])


def test_temporary_requirement_file_deleted(from_line, from_editable, mocked_tmp_file):
    with mock.patch('prequ.sync.check_call'):
        to_install = {from_line('django==1.8')}

        with mock.patch('os.unlink') as unlink:
            sync(to_install, set())

            unlink.assert_called_once_with(mocked_tmp_file.name)


def test_sync_requirement_file(from_line, from_editable, mocked_tmp_req_file):
    with mock.patch('prequ.sync.check_call'):
        to_install = {
            from_line('django==1.8'),
            from_editable('git+git://fake.org/x/y.git#egg=y'),
            from_line('click==4.0'),
            from_editable('git+git://fake.org/i/j.git#egg=j'),
            from_line('pytz==2017.2'),
        }

        sync(to_install, set())

        expected = (
            'click==4.0\n'
            'django==1.8\n'
            '-e git+git://fake.org/i/j.git#egg=j\n'
            'pytz==2017.2\n'
            '-e git+git://fake.org/x/y.git#egg=y'
        )
        mocked_tmp_req_file.write.assert_called_once_with(expected)


def test_sync_requirement_file_with_hashes(from_line, from_editable, mocked_tmp_req_file):
    with mock.patch('prequ.sync.check_call'):
        to_install = {
            from_line('django==1.8', options={
                'hashes': {
                    'sha256': [
                        '6a03ce2feafdd193a0ba8a26dbd9773e757d2e5d5e7933a62eac129813bd381a',
                    ]
                }
            }),
            from_line('click==4.0', options={
                'hashes': {
                    'sha256': [
                        '9ab1d313f99b209f8f71a629f36833030c8d7c72282cf7756834baf567dca662',
                    ]
                }
            }),
            from_line('pytz==2017.2', options={
                'hashes': {
                    'sha256': [
                        'd1d6729c85acea5423671382868627129432fba9a89ecbb248d8d1c7a9f01c67',
                        'f5c056e8f62d45ba8215e5cb8f50dfccb198b4b9fbea8500674f3443e4689589'
                    ]
                }
            })
        }

        sync(to_install, set())

        expected = (
            'click==4.0 \\\n'
            '    --hash=sha256:9ab1d313f99b209f8f71a629f36833030c8d7c72282cf7756834baf567dca662\n'
            'django==1.8 \\\n'
            '    --hash=sha256:6a03ce2feafdd193a0ba8a26dbd9773e757d2e5d5e7933a62eac129813bd381a\n'
            'pytz==2017.2 \\\n'
            '    --hash=sha256:d1d6729c85acea5423671382868627129432fba9a89ecbb248d8d1c7a9f01c67 \\\n'
            '    --hash=sha256:f5c056e8f62d45ba8215e5cb8f50dfccb198b4b9fbea8500674f3443e4689589'
        )
        mocked_tmp_req_file.write.assert_called_once_with(expected)


def test_sync_with_editable_uses_abspath(
        from_editable, small_fake_package_dir, mocked_tmp_req_file):
    ireq = from_editable(small_fake_package_dir)
    rel_path = os.path.relpath(url_to_path(ireq.link.url))
    ireq.link.url = 'file:{}'.format(rel_path.replace(os.path.sep, '/'))
    with mock.patch('prequ.sync.check_call'):
        sync({ireq}, set())

        fake_pkg_url = path_to_url(os.path.abspath(small_fake_package_dir))
        mocked_tmp_req_file.write.assert_called_once_with(
            '-e {}'.format(fake_pkg_url))


def test_sync_sorting_ireqs(from_line, mocked_tmp_req_file):
    with mock.patch('prequ.sync.check_call'):
        to_install = {from_line('django==1.8'), from_line('first==2.0.1')}
        sync(to_install, {})
        mocked_tmp_req_file.write.assert_called_once_with(
            'django==1.8\n'
            'first==2.0.1')


def test_sync_sorting_ireqs_with_editable(
        from_line, from_editable, mocked_tmp_req_file):
    with mock.patch('prequ.sync.check_call'):
        path_to_package = os.path.join(os.path.dirname(__file__),
                                       'test_data', 'small_fake_package')
        editable_ireq = from_editable(path_to_package)
        to_install = {
            from_line('django==1.8'),
            from_line('first==2.0.1'),
            editable_ireq,
        }
        sync(to_install, {})
        mocked_tmp_req_file.write.assert_called_once_with(
            (
                'django==1.8\n'
                'first==2.0.1\n'
                '-e {}'
            ).format(editable_ireq.link))

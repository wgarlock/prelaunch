import os
import stat

import pytest

from prequ._compat import TemporaryDirectory
from prequ.file_replacer import FileReplacer


def test_create():
    with TemporaryDirectory() as tmpdir:
        dst = os.path.join(tmpdir, 'some-file.txt')

        with FileReplacer(dst) as fp:
            fp.write(b'Hello')
            assert not os.path.exists(dst)

        assert os.path.exists(dst)
        assert read_file(dst) == b'Hello'

        assert os.listdir(tmpdir) == ['some-file.txt'], (
            "No extra files should be left behind")


def test_replace():
    with TemporaryDirectory() as tmpdir:
        dst = os.path.join(tmpdir, 'some-file.txt')

        create_file(dst, b'old content')
        assert os.path.exists(dst)

        with FileReplacer(dst) as fp:
            fp.write(b'new content')
            assert read_file(dst) == b'old content'

        assert read_file(dst) == b'new content'

        assert os.listdir(tmpdir) == ['some-file.txt'], (
            "No extra files should be left behind")


def test_replace_failing():
    with TemporaryDirectory() as tmpdir:
        dst = os.path.join(tmpdir, 'destination-path')

        os.mkdir(dst)  # Create directory to prevent replacing

        with pytest.raises(OSError) as excinfo:
            with FileReplacer(dst) as fp:
                fp.write(b'content')

        if os.name != 'nt':
            assert 'Is a directory' in '{}'.format(excinfo.value)

        assert os.path.isdir(dst), "Should still be a directory"

        assert os.listdir(tmpdir) == ['destination-path'], (
            "No extra files should be left behind")


def test_failure_in_context():
    with TemporaryDirectory() as tmpdir:
        dst = os.path.join(tmpdir, 'some-file.txt')

        class SomeException(Exception):
            pass

        with pytest.raises(SomeException):
            with FileReplacer(dst) as fp:
                fp.write(b'content')
                raise SomeException("some failure in the context")

        assert not os.path.exists(dst)

        assert os.listdir(tmpdir) == [], "No files should be left behind"


@pytest.mark.skipif(os.name == 'nt', reason="Requires POSIX file modes")
def test_permissions_on_create():
    with TemporaryDirectory() as tmpdir:
        dst = os.path.join(tmpdir, 'some-file.txt')

        old_umask = os.umask(0o027)  # Set umask

        with FileReplacer(dst) as fp:
            fp.write(b'content')

        # Get current umask and restore old umask
        umask_after_replace = os.umask(old_umask)

        assert stat.S_IMODE(os.stat(dst).st_mode) == 0o640, (
            "New files should be created using the current umask")
        assert umask_after_replace == 0o027, (
            "FileReplacer should not change the umask")


@pytest.mark.skipif(os.name == 'nt', reason="Requires POSIX file modes")
def test_permissions_on_replace():
    with TemporaryDirectory() as tmpdir:
        dst = os.path.join(tmpdir, 'some-file.txt')
        create_file(dst, b'old content')
        os.chmod(dst, 0o640)

        with FileReplacer(dst) as fp:
            fp.write(b'content')

        assert stat.S_IMODE(os.stat(dst).st_mode) == 0o640


def create_file(path, content):
    with open(path, 'wb') as fp:
        fp.write(content)


def read_file(path):
    with open(path, 'rb') as fp:
        return fp.read()

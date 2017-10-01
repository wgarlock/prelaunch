import subprocess
import sys


def test_normal_import_doesnt_run_anything(capfd):
    sys.modules.pop('prequ.__main__', None)
    import prequ.__main__
    assert prequ.__main__.__name__ != '__main__'
    (stdout, stderr) = capfd.readouterr()
    assert stdout == ''
    assert stderr == ''


def test_main():
    out = subprocess.check_output([sys.executable, '-m', 'prequ'])
    assert out.startswith(b"Usage: ")

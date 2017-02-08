import subprocess

DEVNULL = subprocess.DEVNULL


def call(cmd, stdout=None, **kwargs):
    formatted_cmd = [x.format(**kwargs) for x in cmd.split()]
    return subprocess.check_call(formatted_cmd, stdout=stdout)

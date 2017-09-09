from __future__ import unicode_literals

import pytest

from prequ.scripts.check import main as check_main

from .dirs import FAKE_PYPI_WHEELS_DIR
from .utils import make_cli_runner

run_check = make_cli_runner(check_main, [])


UP_TO_DATE_REQ_TXT = """
--trusted-host localhost

tiny-dependee==1.0
tiny-depender==1.1
""".lstrip()

OUTDATED_REQ_TXT = UP_TO_DATE_REQ_TXT.replace('==1.1', '')

TXT_CONTENTS = {
    'up_to_date': UP_TO_DATE_REQ_TXT,
    'outdated': OUTDATED_REQ_TXT,
}


@pytest.mark.parametrize('txt_status', ['up_to_date', 'outdated'])
def test_simple_case(pip_conf, txt_status):
    out = run_check(pip_conf, TXT_CONTENTS[txt_status])
    if txt_status == 'up_to_date':
        assert out.exit_code == 0
        assert out.output == 'requirements.txt is OK\n'
    else:
        assert out.exit_code == 1
        assert out.output == 'requirements.txt is outdated\n'


def run_check(pip_conf, txt_content, check_args=[]):
    runner = make_cli_runner(check_main, check_args)
    conf = {
        'options': {'wheel_dir': FAKE_PYPI_WHEELS_DIR},
        'requirements': ['tiny-depender'],
        'existing_out_files': {'requirements.txt': txt_content},
    }
    with runner(pip_conf, **conf) as out:
        return out

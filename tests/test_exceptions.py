import os

from prequ._pip_compat import (
    PackageFinder, install_req_from_editable, install_req_from_line)
from prequ.exceptions import (
    IncompatibleRequirements, NoCandidateFound, UnsupportedConstraint)

from .dirs import FAKE_PYPI_WHEELS_DIR
from .test_repositories import get_pypi_repository

try:
    from pip.index import InstallationCandidate
except ImportError:
    from pip._internal.index import InstallationCandidate


def get_finder():
    repo = get_pypi_repository()
    finder = PackageFinder(
        find_links=[],
        index_urls=['pypi.localhost'],
        allow_all_prereleases=False,
        session=repo.session)
    return finder


def test_no_candidate_found_with_versions():
    ireq = install_req_from_line('some-package==12.3.4')
    tried = [
        InstallationCandidate('some-package', ver, None)
        for ver in ['1.2.3', '12.3.0', '12.3.5']]
    no_candidate_found = NoCandidateFound(ireq, tried, get_finder())
    assert '{}'.format(no_candidate_found) == (
        "Could not find a version that matches some-package==12.3.4\n"
        "Tried: 1.2.3, 12.3.0, 12.3.5\n"
        "There are incompatible versions in the resolved dependencies.")


def test_no_candidate_found_no_versions():
    ireq = install_req_from_line('some-package==12.3.4')
    tried = []
    no_candidate_found = NoCandidateFound(ireq, tried, get_finder())
    assert '{}'.format(no_candidate_found) == (
        "Could not find a version that matches some-package==12.3.4\n"
        "No versions found\n"
        "Was pypi.localhost reachable?")


def test_unsupported_constraint_simple():
    msg = "Foo bar distribution is not supported"
    ireq = install_req_from_line('foo-bar')
    unsupported_constraint = UnsupportedConstraint(msg, ireq)
    assert '{}'.format(unsupported_constraint) == (
        "Foo bar distribution is not supported (constraint was: foo-bar)")


def test_unsupported_constraint_editable_wheel():
    wheel_path = os.path.join(
        FAKE_PYPI_WHEELS_DIR, 'small_fake_a-0.1-py2.py3-none-any.whl')
    msg = "Editable wheel is too square"
    ireq_wheel = install_req_from_line(wheel_path)
    ireq = install_req_from_editable(str(ireq_wheel.link))
    unsupported_constraint = UnsupportedConstraint(msg, ireq)
    assert '{}'.format(unsupported_constraint) == (
        "Editable wheel is too square (constraint was: {})".format(ireq))


def test_incompatible_requirements():
    ireq_a = install_req_from_line('dummy==1.5')
    ireq_b = install_req_from_line('dummy==2.6')
    incompatible_reqs = IncompatibleRequirements(ireq_a, ireq_b)
    assert '{}'.format(incompatible_reqs) == (
        "Incompatible requirements found: dummy==1.5 and dummy==2.6")

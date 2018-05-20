from pip import __version__ as pip_version
from pkg_resources import parse_version

if parse_version(pip_version) >= parse_version('10.0'):
    from pip._internal.req.req_install import InstallRequirement
    from pip._internal.req.req_file import parse_requirements
    from pip._internal.req.req_set import RequirementSet
    from pip._internal.utils.appdirs import user_cache_dir
    from pip._internal.utils.hashes import FAVORITE_HASH
    from pip._internal.download import is_file_url, path_to_url, url_to_path
    from pip._internal.index import FormatControl, PackageFinder
    from pip._internal.wheel import Wheel
    from pip._internal.basecommand import Command
    from pip._internal import cmdoptions
    from pip._internal.utils.misc import get_installed_distributions
    from pip._internal.models.index import PyPI
else:
    from pip.req.req_install import InstallRequirement
    from pip.req.req_file import parse_requirements
    from pip.req.req_set import RequirementSet
    from pip.utils.appdirs import user_cache_dir
    from pip.utils.hashes import FAVORITE_HASH
    from pip.download import is_file_url, path_to_url, url_to_path
    from pip.index import FormatControl, PackageFinder
    from pip.wheel import Wheel
    from pip.basecommand import Command
    from pip import cmdoptions
    from pip.utils import get_installed_distributions
    from pip.models.index import PyPI

__all__ = [
    'Command',
    'FAVORITE_HASH',
    'FormatControl',
    'InstallRequirement',
    'PackageFinder',
    'PyPI',
    'RequirementSet',
    'Wheel',
    'cmdoptions',
    'get_installed_distributions',
    'is_file_url',
    'parse_requirements',
    'path_to_url',
    'url_to_path',
    'user_cache_dir',
]

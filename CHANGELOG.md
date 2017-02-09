# Unreleased

- (nvie/pip-tools#450) Fix resolver when toplevel requirements are also
  in pinned subdependency

# 0.180.6

- (nvie/pip-tools#417) Exclude irrelevant pip constraints

# 0.180.5

- Fix "pip-requ compile-all" to handle "-e" and "-c" lines correctly
- Remove "pip-compile" and "pip-sync" commands

# 0.180.4

- Fix "pip-requ compile --no-annotate"

# 0.180.3

- Add support for "pip-requ --version"

# 0.180.2

- (nvie/pip-tools#378) Recalculate secondary dependencies between rounds
- (nvie/pip-tools#448) Add "--no-trusted-host" option to fix #382
- (nvie/pip-tools#448) Deduplicate the option lines of output
- (nvie/pip-tools#441) Exclude packages required only by unsafe packages
- (nvie/pip-tools#389) Ignore pkg-resources
- (nvie/pip-tools#355) Support non-editable pinned VCS dependencies

# 0.180.1

- Add "pip-requ" command
- Add "pip-requ build-wheels" command
- Add "pip-requ compile-all" command
- Add "pip-requ update" command

# 0.180.0

- Fork from pip-tools 1.8.0

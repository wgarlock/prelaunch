# Unreleased

- Fix "pip-requ compile --no-annotate"

# 0.180.3

- Add support for "pip-requ --version"

# 0.180.2

- Recalculate secondary dependencies between rounds (#378)
- Add "--emit-trusted-host/--no-trusted-host" option
- Deduplicate the option lines of output
- `pip-compile` now excludes packages required only by unsafe packages when
  `--allow-unsafe` is not in use.
- Ignore pkg-resources
- Support pinned VCS dependencies

# 0.180.1

- Add "pip-requ" command
- Add "pip-requ build-wheels" command
- Add "pip-requ compile-all" command
- Add "pip-requ update" command

# 0.180.0

- Fork from pip-tools 1.8.0

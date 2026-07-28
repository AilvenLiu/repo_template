# Pyenv and Poetry recovery

Use this reference after `.agents/bin/agent-python-env-setup diagnose` or
`verify` reports a Python-selection or incomplete-build problem.

## Establish the caller state

Run the repository wrapper from the normal login shell. It records whether the
caller had an active `VIRTUAL_ENV` before Poetry starts its child process.
Poetry setting `VIRTUAL_ENV` inside `poetry run` is expected and is not, by
itself, an error.

```bash
print -r -- "${VIRTUAL_ENV:-unset}"
.agents/bin/agent-python-env-setup diagnose
```

If the login shell has an unwanted external environment, clear it and make the
chosen shell start cleanly. For zsh:

```bash
unset VIRTUAL_ENV
printf '\nunset VIRTUAL_ENV\n' >> ~/.zshrc
exec zsh -l
```

Do not add `unset VIRTUAL_ENV` merely because a program launched by
`poetry run` displays it. If the wrapper reports the variable despite the
parent shell being unset, inspect the wrapper before changing the user shell.

## Initialise pyenv for zsh

Install pyenv through the reviewed project or platform procedure, then let
pyenv write its supported shell initialisation and start a new login shell:

```bash
~/.pyenv/bin/pyenv init --install
exec zsh -l
pyenv --version
```

Confirm that `python` resolves through `.pyenv/shims` only after choosing the
project interpreter with `pyenv local <version>`.

## Treat missing standard-library extensions as a failed build

`pyenv install` can complete while omitting extension modules. Warnings about
`_bz2`, `_curses`, `_ctypes`, `readline`, `_sqlite3`, or `_lzma` mean that
the interpreter is incomplete; do not use it for CI or deployment.

On Debian or Ubuntu, obtain approval for the package change, then install the
development prerequisites before rebuilding:

```bash
sudo apt update
sudo apt install -y \
  build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev \
  libsqlite3-dev libncurses-dev xz-utils tk-dev libffi-dev liblzma-dev \
  libgdbm-dev libnss3-dev uuid-dev
```

For another operating system, use the pyenv build-prerequisite guidance for
that platform rather than copying Debian package names.

## Rebuild a known-broken interpreter

`pyenv uninstall` removes that interpreter. Stop for operator approval and
only remove the explicitly identified broken version. Then recreate the Poetry
environment from the lock file:

```bash
pyenv uninstall -f <version>
pyenv install <version>
pyenv local <version>
env -u VIRTUAL_ENV poetry env remove --all
env -u VIRTUAL_ENV poetry env use "$(pyenv which python)"
env -u VIRTUAL_ENV poetry install
env -u VIRTUAL_ENV poetry run python -c 'import bz2, curses, ctypes, lzma, readline, sqlite3; print("standard-library extensions: OK")'
```

The final command is deliberately inside `poetry run`: it validates the
project environment, where Poetry may legitimately set `VIRTUAL_ENV`.

## Close the recovery

Verify the shell, pyenv selection, Poetry environment location, package-source
policy, and imports with:

```bash
.agents/bin/agent-python-env-setup verify
poetry env info
```

Do not fall back to system Python, manual virtual environments, or direct pip
installation. If the rebuilt interpreter still lacks an extension, retain the
diagnostic output and investigate the missing operating-system development
library before retrying.

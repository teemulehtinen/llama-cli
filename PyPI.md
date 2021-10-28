# Published in PyPI

Short notes on publishing the package

### 0. Prerequisites

Set up https://pypi.org API token in `~/.pypirc`

    python3 -m pip install build twine

### 1. Make changes and update version

    grep version setup.cfg

### 2. Build distribution package and publish

    rm dist/*
    python3 -m build
    python3 -m twine upload dist/*

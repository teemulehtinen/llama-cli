# Published in PyPI

Short notes on publishing the package

### 0. Prerequisites

Create https://pypi.org API token and place it to `~/.pypirc`

    [pypi]
    username = __token__
    password = <PyPI token just generated>

Install package tools

    python3 -m pip install build twine

### 1. Make changes and update version

    grep version setup.cfg

### 2. Build distribution package and publish

    rm dist/*
    python3 -m build
    python3 -m twine upload dist/*

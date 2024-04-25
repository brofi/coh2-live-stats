# CoH2 Live Stats

Show match stats of a currently played, replayed or last played Company of Heroes 2 match.

## Development

### Setup

* Create and activate virtual environment:
```console
$  python -m venv venv
$ .\venv\Scripts\Activate.ps1
```

* Install project with development dependencies in editable mode:
```console
$ pip install invoke
$ inv install --dev
```

* Install `pre-commit` hooks:
```console
$ pre-commit install
```

### Build

* Build with `setuptools` and `build` and create a `PyInstaller` bundle:
```console
$ inv build
```
* Distribution bundle: `.\dist\CoH2LiveStats-bundle-{version}.zip`
* See `inv -l` and `inv [task] -h` for more information on available `invoke` tasks

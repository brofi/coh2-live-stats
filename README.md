# CoH2LiveStats

## Development Setup

* Create Virtual Environment with IDE or with:
```console
$ python -m venv venv
```

* Restart IDE or activate venv e.g. for PowerShell with:
```console
$ .\venv\Scripts\activate.ps1
```

* Install `invoke`:
```console
$ pip install invoke
```

* Use `inv[oke]` to once install the project in editable mode with build and development dependencies:
```console
$ inv install --dev
```

* Install `pre-commit` hooks:
```console
$ pre-commit install
```

* Start developing

## Make package

* To build package with `setuptools/build` and bundle with `PyInstaller`:
```console
$ inv build
```
* Distribution bundle: `.\dist\CoH2LiveStats.zip`
* See `inv -l` and `inv [task] -h` for more information on available `invoke` tasks

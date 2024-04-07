# CoH2LiveStats

## Setup project

* Create Virtual Environment with IDE or with:

```console
$ python -m venv venv
```

* Restart IDE or activate venv e.g. for PowerShell with:

```console
$ .\venv\Scripts\activate.ps1
```

* Install development dependencies: `ruff`, `pre-commit`
* Install pre-commit hooks: `pre-commit install`

## Make package `inv[oke]`

* Install: `build`, `invoke`,  `pyinstaller`, `tomlkit`
* List available tasks: `inv -l`
* Get help with: `inv [task] -h`
* Distribute archive: `.\dist\CoH2LiveStats.zip`

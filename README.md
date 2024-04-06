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

* Install optional dependencies
* tomlkit needed for scripts/generate_settings.py
* pyinstaller needed for scripts/pyinstaller_run.py

## Make package

### setuptools & build

* Install `build`:

```console
$ pip install build
```

* Run `build`:

```console
$ python -m build
```

* Install package:

```console
$ pip install .\dist\coh2_live_stats-0.0.1-py3-none-any.whl
```

* Run installed module:

```console
$ python -m coh2_live_stats
```

* Run installed script:

```console
$ coh2livestats.exe
```

### PyInstaller

* Install `pyinstaller`:

```console
$ pip install pyinstaller
```

* Run `scripts/pyinstaller_run.py`

* Run generated script:

```console
$ .\dist\CoH2LiveStats\CoH2LiveStats.exe
```

* Distribute archive `.\dist\CoH2LiveStats.zip`

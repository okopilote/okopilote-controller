# okopilote-controller

Okopilote-controller is the controller part of the Okopilote suite. It collects heat
needs from rooms and drives the central heating system accordingly, enforcing heat
generation when needed. The regulation is optimized for getting long-run cycles by
avoiding frequent on/off boiler switches.
The controller acts on top of the inner regulation of the central heating system
through a boiler-dependent module.

## Table of Contents

- [Installation](#installation)
- [Usage](#Usage)
- [License](#license)

## Installation

### FUTUR: install packages from PyPi

```console
# Install the controller
pip install okopilote-controller

# Install the controller and the relevant boiler module. Example with Okofen Pellematic
# Touch v4 boiler:
pip install okopilote-controller[okofen-touch4]

# Or install controller and module separately
pip install okopilote okopilote-boilers-okofen-touch4
```

### PRESENT: build and install packages

Packages have be installed from distribution files:

```console
pip install okopilote_controller-a.b.c-py3-none-any.whl
pip install okopilote_devices_common-d.e.f-py3-none-any.whl
pip install okopilote_boilers_okofen_touch4-g.h.i-py3-none-any.whl
```

## Usage

Copy configuration file from repository :

```console
cp examples/controller-example.conf /some/etc/dir/okopilote/controller.conf
```

Adjust configuration then run okopilote-controller :

```console
okopilote-controller -c /some/etc/dir/okopilote/controller.conf [-v] [--dry-run]
```

## License

`okopilote-controller` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.

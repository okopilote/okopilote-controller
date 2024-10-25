# okopilote-controller

Okopilote-controller is the controller part of the Okopilote suite. It collects heat
needs from rooms and drives the central heating system accordingly, enforcing heat
generation when needed. The regulation is optimized for getting long-run cycles by
avoiding frequent on/off boiler switches.
The controller acts on top of the inner regulation of the central heating system
through a boiler-dependent module.

## Table of Contents

- [Installation](#installation)
- [License](#license)

## Installation

Install packages :

```console
# Install the controller
pip install okopilote-controller

# Also install the boiler-specific module. Example with Okofen Pellematic Touch v4:
pip install okopilote-boilers-okofen-touch4
```

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

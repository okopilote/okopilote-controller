import argparse

from .__about__ import __version__
from .app import App

default_cf_file = "/etc/okopilote/controller.conf"


def run():
    """Entry point of the application"""

    parser = argparse.ArgumentParser(
        description="Controller part of the Okopilote suite."
    )
    parser.add_argument(
        "-c",
        "--conf",
        default=default_cf_file,
        help=f"Configuration file. Default: {default_cf_file}",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        default=False,
        help="perform a trial run with no changes made",
    )
    args = parser.parse_args()
    App.start(config_file=args.conf, dry_run=args.dry_run)

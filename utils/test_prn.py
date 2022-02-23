from __future__ import print_function

import argparse

VERSION = "0.0.1"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v",
        "--version",
        required=False,
        action="store_true",
        dest="version",
        default=False,
        help="print version information",
    )

    args = parser.parse_args()
    if args.version:
        print("Version: %s" % VERSION)
        return
    parser.print_help()
    return


if __name__ == "__main__":
    main()

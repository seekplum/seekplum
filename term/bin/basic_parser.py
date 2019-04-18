#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import argparse


class ArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)

    def error(self, message):
        """error(message: string)
        Prints a usage message incorporating the message to stderr and exits.
        """
        self.print_usage(sys.stderr)
        # FIXME(lzyeval): if changes occur in argparse.ArgParser._check_value
        choose_from = ' (choose from'
        self.exit(2, "error: %s\nTry '%s --help' for more information.\n" %
                  (message.split(choose_from)[0], self.prog))


class HelpFormatter(argparse.HelpFormatter):
    def start_section(self, heading):
        # Title-case the headings
        heading = '%s%s' % (heading[0].upper(), heading[1:])
        super(self.__class__, self).start_section(heading)


class BasicParser(object):
    """
    Configure Tool.
    """

    def __init__(self, prog):
        self.prog = prog
        pass

    def get_base_parser(self):
        parser = ArgumentParser(
            prog=self.prog,
            description=self.__doc__.strip(),
            epilog="See '{} COMMAND --help' for help on a specific command.".format(self.prog),
            add_help=True,
            formatter_class=HelpFormatter,
        )
        return parser

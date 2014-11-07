"""
Created on Oct 2, 2013

@author: Duarte Meneses <duarte.meneses@cern.ch>
"""

import argparse
import signal
from threading import Thread
import sys
import errno
import os

import gfal2
from gfal2 import GError
from gfal2_utils_parameters import apply_option


VERSION = '1.0.0'


def arg(*args, **kwargs):
    """Decorator for CLI args."""
    def _decorator(func):
        __add_arg(func, *args, **kwargs)
        return func

    return _decorator


def __add_arg(f, *args, **kwargs):
    """Bind CLI arguments to a shell.py `do_foo` function."""

    if not hasattr(f, 'arguments'):
        f.arguments = []

    if (args, kwargs) not in f.arguments:
        f.arguments.insert(0, (args, kwargs))


class CommandBase(object):
    def __init__(self):
        self.context = None
        self.progress_bar = None
        self.running = False
        self.return_code = -1

    @staticmethod
    def get_subclasses():
        return CommandBase.__subclasses__()

    @staticmethod
    def __set_verbose_mode(verbosity):
        if verbosity < 0:
            raise ValueError('negative verbose!')  # this should never happen

        if verbosity > 3:
            verbosity = 3

        modes = [
            gfal2.verbose_level.normal, gfal2.verbose_level.verbose,
            gfal2.verbose_level.debug, gfal2.verbose_level.trace
        ]
        gfal2.set_verbose(modes[verbosity])

    #wrap method to catch exceptions in thread's stack
    def executor(self, func):
        try:
            self.return_code = func(self)
        except IOError, e:
            if e.errno != errno.EPIPE:
                raise
        except GError, e:
            #get output back!
            #self._enable_output()
            if self.params.verbose:
                sys.stderr.write("gfal-util error: %d (%s) - %s\n" % (e.code, os.strerror(e.code), e.message))
            else:
                sys.stderr.write("%s: error: %s\n" % (self.progr, os.strerror(e.code)))

            self.return_code = e.code

    def execute(self, func):
        def cancel():
            self.context.cancel()

        # Set X509_ environment if --cert is used
        if self.params.cert:
            if not self.params.key:
                self.params.key = self.params.cert
            os.environ['X509_USER_CERT'] = self.params.cert
            os.environ['X509_USER_KEY'] = self.params.key
            if 'X509_USER_PROXY' in os.environ:
                del os.environ['X509_USER_PROXY']

        #Set verbose
        self.__set_verbose_mode(self.params.verbose)

        self.context = gfal2.creat_context()
        apply_option(self.context, self.params)

        t_main = Thread(target=self.executor, args=[func])
        t_main.daemon = True

        try:
            #run in another thread to be able to catch signals while C functions don't return
            # See rule #3 in http://docs.python.org/2/library/signal.html
            t_main.start()
            if self.params.timeout > 0:
                t_main.join(self.params.timeout)
            else:
                #if join(None) is used, it doesn't catch signals
                while t_main.isAlive():
                    t_main.join(3600)

            #self._enable_output()
            if t_main.isAlive():
                if self.progress_bar is not None:
                    self.progress_bar.stop(False)
                sys.stderr.write('Command timed out after %d seconds!\n' % self.params.timeout)
                return errno.ETIMEDOUT

            return self.return_code

        except KeyboardInterrupt:
            sys.stderr.write("Caught keyboard interrupt. Canceling...")
            #ignore any other interrupt signal
            signal.signal(signal.SIGINT, signal.SIG_IGN)

            #cancel in another thread to avoid blocking us
            t_cancel = Thread(target=cancel)
            t_cancel.daemon = True  # in no case hog the entire program
            t_cancel.start()
            t_cancel.join(4)
            if t_cancel.isAlive():
                sys.stderr.write("failed to cancel after waiting some time\n")

            return errno.EINTR

    def parse(self, func, a):
        #Collect some info about the function
        command = func.__name__[8:]
        desc = func.__doc__ or ''
        doc = desc.strip().split('\n')[0]

        description = 'Gfal util ' + command.upper() + ' command. ' + doc
        if description[-1] != '.':
            description += '.'

        arguments = getattr(func, 'arguments', [])

        #Create parser and parse arguments
        parser = argparse.ArgumentParser(prog=os.path.basename(a[0]), description=description, add_help=True)
        parser.add_argument('-V', '--version', action='version',
                            help="output version information and exit.", version=VERSION)
        parser.add_argument('-v', '--verbose', action='count', default=0,
                            help="enable the verbose mode, -vvv enables debug mode")
        parser.add_argument('-D', '--definition', nargs=1, type=str, help="override a gfal parameter", action='append')
        parser.add_argument('-t', '--timeout', type=int, default=1800,
                            help="maximum time for the operation to terminate - default is 1800 seconds")
        parser.add_argument('-E', '--cert', type=str, default=None, help="user certificate")
        parser.add_argument('--key', type=str, default=None, help="user private key")
        parser.add_argument('-4', action='store_true', help='Forces gfal2-util to use IPv4 addresses only')
        parser.add_argument('-6', action='store_true', help='Forces gfal2-util to use IPv6 addresses only')

        for (args, kwargs) in arguments:
            parser.add_argument(*args, **kwargs)

        self.params = parser.parse_args(a[1:])
        self.progr = os.path.basename(a[0])

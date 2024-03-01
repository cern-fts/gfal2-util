#
# Copyright (c) 2013-2022 CERN
#
# Copyright (c) 2012-2013 Members of the EMI Collaboration
#    See http://www.eu-emi.eu/partners for details on the copyright
#    holders.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#from __future__ import absolute_import # not available in python 2.4
from __future__ import division

import argparse
import logging
import signal
try:
    from urllib.parse import urlparse, urlunparse
except ImportError:
    from urlparse import urlparse, urlunparse
from threading import Thread
import sys
import errno
import os

import gfal2
from gfal2_util.gfal2_utils_parameters import apply_option


VERSION = '1.8.2'


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


class Gfal2VersionAction(argparse.Action):
    """
    Custom Version action, so we can insert new lines and so on
    """
    def __init__(self, *args, **kwargs):
        kwargs['nargs'] = 0
        super(Gfal2VersionAction, self).__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        """
        Pretty print of gfal2-util version
        """
        version_str = "gfal2-util version %s (gfal2 %s)" % (VERSION, gfal2.get_version())
        for plugin in sorted(gfal2.creat_context().get_plugin_names()):
            version_str += '\n\t' + plugin
        print(version_str)
        sys.exit(0)


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
    def __setup_logger(level, log_file):
        # Handle logging level
        level = max(0, level)
        level = min(3, level)

        log_level_value = logging.ERROR - (level * 10)
        if level < 3:
            gfal2.set_verbose(gfal2.verbose_level.verbose)
        else:
            gfal2.set_verbose(gfal2.verbose_level.debug)

        # Handle log file
        log_stream = sys.stdout
        if log_file:
            log_stream = open(log_file, 'w+')

        root_logger = logging.getLogger()
        root_logger.setLevel(log_level_value)
        handler = logging.StreamHandler(log_stream)
        handler.setLevel(log_level_value)

        handler.setFormatter(logging.Formatter('%(levelname)s %(message)s'))
        if log_stream.isatty():
            logging.addLevelName(logging.DEBUG, "\033[1;2m%-8s\033[1;m" % logging.getLevelName(logging.DEBUG))
            logging.addLevelName(logging.INFO, "\033[1;34m%-8s\033[1;m" % logging.getLevelName(logging.INFO))
            logging.addLevelName(logging.ERROR, "\033[1;31m%-8s\033[1;m" % logging.getLevelName(logging.ERROR))
            logging.addLevelName(logging.WARNING, "\033[1;33m%-8s\033[1;m" % logging.getLevelName(logging.WARNING))

        root_logger.addHandler(handler)

    #wrap method to catch exceptions in thread's stack
    def executor(self, func):
        try:
            self.return_code = func(self)
        except IOError:
            e = sys.exc_info()[1]
            if e.errno != errno.EPIPE:
                raise
        except gfal2.GError:
            e = sys.exc_info()[1]
            sys.stderr.write("%s error: %d (%s) - %s\n" % (self.progr, e.code, os.strerror(e.code), e.message))
            self.return_code = e.code if 0 <= e.code <= 255 else 255

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

        # Setup log verbosity and destination
        self.__setup_logger(self.params.verbose, self.params.log_file)

        self.context = gfal2.creat_context()
        apply_option(self.context, self.params)
        self.context.set_user_agent("gfal2-util", VERSION)

        t_main = Thread(target=self.executor, args=[func])
        t_main.daemon = True
        if not hasattr(t_main, 'is_alive'):
            # is_alive was added in python 2.6 and isAlive deprecated in python 3.8
            t_main.is_alive = t_main.isAlive

        try:
            #run in another thread to be able to catch signals while C functions don't return
            # See rule #3 in http://docs.python.org/2/library/signal.html
            t_main.start()
            if self.params.timeout > 0:
                # Increment the timeout a bit so plugins have a chance to timeout themselves
                t_main.join(self.params.timeout + 30)
            else:
                #if join(None) is used, it doesn't catch signals
                while t_main.is_alive():
                    t_main.join(3600)

            #self._enable_output()
            if t_main.is_alive():
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
            if not hasattr(t_cancel, 'is_alive'):
                # is_alive was added in python 2.6 and isAlive deprecated in python 3.8
                t_cancel.is_alive = t_cancel.isAlive
            t_cancel.start()
            t_cancel.join(4)
            if t_cancel.is_alive():
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
        self.parser = argparse.ArgumentParser(prog=os.path.basename(a[0]), description=description, add_help=True)
        self.parser.add_argument('-V', '--version', action=Gfal2VersionAction,
                            help="output version information and exit")
        self.parser.add_argument('-v', '--verbose', action='count', default=0,
                            help="enable the verbose mode, -v for warning, -vv for info, -vvv for debug")
        self.parser.add_argument('-D', '--definition', nargs=1, type=str, help="override a gfal parameter", action='append')
        self.parser.add_argument('-t', '--timeout', type=int, default=1800,
                            help="maximum time for the operation to terminate - default is 1800 seconds")
        self.parser.add_argument('-E', '--cert', type=str, default=None, help="user certificate")
        self.parser.add_argument('--key', type=str, default=None, help="user private key")
        self.parser.add_argument('-4', dest='ipv4', action='store_true', help="forces gfal2-util to use IPv4 addresses only. N.B. this is valid only for gridftp")
        self.parser.add_argument('-6', dest='ipv6', action='store_true', help="forces gfal2-util to use IPv6 addresses only. N.B. this is valid only for gridftp")
        self.parser.add_argument('-C', '--client-info', type=str, help="provide custom client-side information",
                            action='append')
        self.parser.add_argument('--log-file', type=str, default=None, help="write Gfal2 library logs to the given file location")

        for (args, kwargs) in arguments:
            self.parser.add_argument(*args, **kwargs)

        self.params = self.parser.parse_args(a[1:])
        self.progr = os.path.basename(a[0])


def surl(value):
    """
    Special "type" for surls.
    It will convert, for instance, paths of the form "/path" to "file:///path" 
    """
    if value == '-':
        return value
    parsed = urlparse(value)
    if not parsed[0]:
        return urlunparse(('file', None, os.path.abspath(parsed[2]), None, None, None))
    return value

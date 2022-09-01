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

from gfal2_util import base
from gfal2_util import commands # @UnusedImport
from gfal2_util import ls # @UnusedImport
from gfal2_util import legacy # @UnusedImport
from gfal2_util import copy # @UnusedImport
from gfal2_util import rm # @UnusedImport
from gfal2_util import tape


class CommandFactory(object):

    @staticmethod
    def __find_classes():
        return base.CommandBase().get_subclasses()

    @staticmethod
    def __find_command(clasz, cmd):
        for name in (a for a in dir(clasz) if a == ('execute_' + cmd)):
            return getattr(clasz, name)
        return None

    @staticmethod
    def get_command(cmd):
        classes = CommandFactory.__find_classes()

        for c in classes:
            func = CommandFactory.__find_command(c, cmd)
            if func:
                return c, func

        raise ValueError("Invalid command")


class Gfal2Shell(object):

    @staticmethod
    def __get_command_string(progr):
        return progr.rsplit('-', 1)[1].lower()

    def main(self, args):
        """Entry point"""
        #get class/function corresponding to the command issued
        cmd = self.__get_command_string(args[0])
        (command_class, command_func) = CommandFactory.get_command(cmd)

        #instantiate class and let it know what is the func called and the args given
        inst = command_class()
        inst.parse(command_func, args)

        return inst.execute(command_func)

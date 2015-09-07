#
# Copyright (c) CERN 2013-2015
#
# Copyright (c) Members of the EMI Collaboration. 2012-2013
#    See  http://www.eu-emi.eu/partners for details on the copyright
#    holders.
#
# This file is part of gfal2-util
#
# gfal2-util is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from base import CommandBase
import commands # @UnusedImport
import ls # @UnusedImport
import legacy # @UnusedImport
import copy # @UnusedImport
import rm # @UnusedImport


class CommandFactory(object):

    @staticmethod
    def __find_classes():
        return CommandBase().get_subclasses()

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

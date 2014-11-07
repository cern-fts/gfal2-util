"""
Created on Oct 2, 2013

@author: "Duarte Meneses <duarte.meneses@cern.ch>"
"""

from base import CommandBase
import commands # @UnusedImport
import ls # @UnusedImport
import legacy # @UnusedImport


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

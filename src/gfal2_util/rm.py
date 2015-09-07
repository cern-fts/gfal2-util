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

import sys
import stat
import errno

import gfal2
import base
from base import CommandBase


class CommandRm(CommandBase):
    @base.arg("-r", "-R", "--recursive", action='store_true',
              help="remove directories and their contents recursively")
    @base.arg("--dry-run", action='store_true',
              help="do not perform any actual change, just print what would happen")
    @base.arg("--from-file", type=str, default=None,
              help="read surls from a file")
    @base.arg("file", action='store', nargs='*', type=str,
              help="uri(s) of the file(s) to be deleted")
    def execute_rm(self):
        """
        Removes files or directories
        """
        if self.params.from_file and self.params.file:
            print >>sys.stderr, "--from-file and positional arguments can not be used at the same time"
            return 1

        if self.params.file:
            files = self.params.file
        elif self.params.from_file:
            files = [line.strip() for line in open(self.params.from_file, 'r').readlines()]
            files = filter(lambda f: len(f) > 0, files)
        else:
            print >>sys.stderr, "Missing surl"
            return 1

        for f in files:
            self._do_rm(f)

    def _do_rm(self, surl):
        """
        Perform the action, either removing or just informing
        """
        try:
            st = self.context.stat(surl)
        except gfal2.GError, e:
            if e.code == errno.ENOENT:
                print "%s\tMISSING" % surl
                return
            else:
                print "%s\tFAILED" % surl
                raise

        if stat.S_ISDIR(st.st_mode):
            self._do_rmdir(surl)
        elif self.params.dry_run:
            print "%s\tSKIP" % surl
        else:
            try:
                self.context.unlink(surl)
                print "%s\tDELETED" % surl
            except gfal2.GError, e:
                if e.code == errno.ENOENT:
                    print "%s\tMISSING" % surl
                    return
                else:
                    print "%s\tFAILED" % surl
                    raise

    def _do_rmdir(self, surl):
        """
        Remove a directory recursively
        """
        if not self.params.recursive:
            raise gfal2.GError("Can not remove %s, is a directory" % surl, errno.EISDIR)

        # Content
        base_dir = surl
        if base_dir[-1] != '/':
            base_dir += '/'
        contents = self.context.listdir(surl)
        for c in contents:
            if c in ['.', '..']:
                continue
            self._do_rm(base_dir + c)

        # Rmdir self
        if self.params.dry_run:
            print "%s\tSKIP DIR" % surl
        else:
            try:
                self.context.rmdir(surl)
                print "%s\tRMDIR" % surl
            except gfal2.GError, e:
                if e.code == errno.ENOENT:
                    print "%s\tMISSING" % surl
                else:
                    print "%s\tFAILED" % surl
                    raise

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

#from __future__ import absolute_import # not available in python 2.4
from __future__ import division

import gfal2
import sys
import stat
from datetime import datetime

from gfal2_util import base
from gfal2_util.utils import file_type_str, file_mode_str


class GfalCommands(base.CommandBase):
    @base.arg('-m', '--mode', action='store', type=int, default=755, help="display hidden files")
    @base.arg('-p', '--parents', action='store_true', help="no error if existing, make parent directories as needed")
    @base.arg('directory', action='store', nargs='+', type=base.surl, help="Directory's uri")
    def execute_mkdir(self):
        """
        Makes directories. By default, it sets file mode 0755.
        """
        if self.params.mode:
            try:
                mode = int(str(self.params.mode), 8)
            except ValueError:
                mode = int('755', 8) # python < 2.6 doesn't support 0o755
        else:
            mode = int('755', 8) # python < 2.6 doesn't support 0o755
        for d in self.params.directory:
            if self.params.parents:
                self.context.mkdir_rec(d, mode)
            else:
                self.context.mkdir(d, mode)

    @base.arg('file', action='store', type=base.surl, help="uri of the file to be written")
    def execute_save(self):
        """
        Reads from stdin and writes to a file. If the file exists, it will be overwritten
        """
        f = self.context.open(self.params.file, 'w')

        while True:
            b = sys.stdin.read(65000)
            if b:
                f.write(b)
            else:
                break

    @base.arg('file', action='store', nargs='+', type=base.surl, help="uri of the file to be displayed")
    def execute_cat(self):
        """
        Sends to stdout the contents of files
        """

        for fname in self.params.file:
            f = self.context.open(fname, 'r')

            while True:
                b = f.read(65000)
                sys.stdout.write(b)
                if not b:
                    break

    @base.arg('file', action='store', type=base.surl, help="file uri")
    @base.arg('attribute', nargs='?', type=str, help="attribute to retrieve or set. To set, use key=value")
    def execute_xattr(self):
        """
        Gets or set the extended attributes of files and directories
        """
        if self.params.attribute is not None:
            if '=' in self.params.attribute:
                i = self.params.attribute.find("=")
                attr = self.params.attribute[:i]
                v = self.params.attribute[(i+1):]

                if len(attr) > 0 and len(v) > 0:
                    self.context.setxattr(self.params.file, attr, v, 0)
            else:
                v = self.context.getxattr(self.params.file, self.params.attribute)
                sys.stdout.write(v + '\n')
        else:
            l = self.context.listxattr(self.params.file)

            for attr in l:
                try:
                    v = self.context.getxattr(self.params.file, attr)
                    sys.stdout.write(attr + ' = ' + v + '\n')
                except gfal2.GError:
                    e = sys.exc_info()[1]
                    sys.stdout.write(attr + ' FAILED: ' + str(e) + '\n')

    @base.arg('file', action='store', type=base.surl,
              help="file uri to use for checksum calculation")
    @base.arg('checksum_type', action='store', type=str,
              help="checksum algorithm to use. For example: ADLER32, CRC32, MD5")
    def execute_sum(self):
        """
        Calculates the checksum of a file
        """
        checksum = self.context.checksum(self.params.file, self.params.checksum_type)
        sys.stdout.write(self.params.file + ' ' + checksum + '\n')

    @base.arg('file', action='store', type=base.surl, help="uri of the file to be stat")
    def execute_stat(self):
        """
        Stats a file
        """
        st = self.context.stat(self.params.file)
        print("  File: '%s'" % self.params.file)
        print("  Size: %d\t%s" % (st.st_size, file_type_str(stat.S_IFMT(st.st_mode))))
        print("Access: (%04o/%s)\tUid: %d\tGid: %d\t" % (stat.S_IMODE(st.st_mode), file_mode_str(st.st_mode), st.st_uid, st.st_gid))
        if sys.version_info >= (2, 6):
            print("Access: %s" % datetime.fromtimestamp(st.st_atime).strftime("%Y-%m-%d %H:%M:%S.%f"))
            print("Modify: %s" % datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S.%f"))
            print("Change: %s" % datetime.fromtimestamp(st.st_ctime).strftime("%Y-%m-%d %H:%M:%S.%f"))
        else:
            # python 2.4 and 2.5 doesn't support %f in strftime
            print("Access: %s" % datetime.fromtimestamp(st.st_atime).strftime("%Y-%m-%d %H:%M:%S.000000"))
            print("Modify: %s" % datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S.000000"))
            print("Change: %s" % datetime.fromtimestamp(st.st_ctime).strftime("%Y-%m-%d %H:%M:%S.000000"))

    @base.arg('source', action='store', type=base.surl, help="original file name")
    @base.arg('destination', action='store', type=base.surl, help="new file name")
    def execute_rename(self):
        """
        Renames files or directories
        """
        self.context.rename(self.params.source, self.params.destination)

    @base.arg('mode', action='store', type=str, help="new mode, in octal")
    @base.arg('file', action='store', type=base.surl, help="uri of the file to change permissions")
    def execute_chmod(self):
         """
         Change the permissions of a file
         """
         try:
            mode = int(self.params.mode, base=8)
         except ValueError:
             self.parser.error('Mode must be an octal number (i.e. 0755)')
             return
         self.context.chmod(self.params.file, mode)

    @base.arg('--issuer', action='store', type=str, help="token issuer URL")
    @base.arg('--validity', action='store', type=int, default=60, help="token validity in minutes")
    @base.arg('-w', '--write', dest='write_access', action='store_true', help="flag to request write access token")
    @base.arg('path', action='store', type=base.surl, help="URI to request token for")
    @base.arg('activities', action='store', nargs='*', type=str, help="activities for macaroon request")
    def execute_token(self):
        """
        Retrieve a SE-issued token
        """
        if self.params.validity < 0:
            sys.stderr.write("Validity must be a number >= 0\n")
            return 1

        if self.params.verbose:
            if len(self.params.activities) > 0:
                print("Will use user-provided activities")
            else:
                print("Will use default activities for {} access"
                      .format(['read', 'write'][self.params.write_access]))

        issuer = self.params.issuer if self.params.issuer is not None else ''
        if len(self.params.activities) > 0:
            token = self.context.token_retrieve(self.params.path, issuer, self.params.validity,
                                                self.params.activities)
        else:
            token = self.context.token_retrieve(self.params.path, issuer, self.params.validity,
                                                self.params.write_access)
        sys.stdout.write(token + '\n')

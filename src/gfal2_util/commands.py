"""
Created on Oct 2, 2013

@author: "Duarte Meneses <duarte.meneses@cern.ch>"
"""
import sys
import os
import stat
import errno
from datetime import datetime

import gfal2
import base
from base import CommandBase
from progress import Progress
from utils import file_type_str, file_mode_str


class GfalCommands(CommandBase):
    @base.arg('-m', '--mode', action="store", type=int, default=755, help="display hidden files")
    @base.arg('-p', '--parents', action='store_true', help='no error if existing, make parent directories as needed')
    @base.arg('directory', action='store', nargs='+', type=str, help="Directory's uri.")
    def execute_mkdir(self):
        """
        Makes directories. By default, it sets file mode 0755.
        """
        if self.params.mode:
            try:
                mode = int(str(self.params.mode), 8)
            except ValueError:
                mode = 0755
        else:
            mode = 0755
        for d in self.params.directory:
            if self.params.parents:
                self.context.mkdir_rec(d, mode)
            else:
                self.context.mkdir(d, mode)

    @base.arg("file", action='store', type=str, help='uri of the file to be written')
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

    @base.arg("file", action='store', nargs='+', type=str, help='uri of the file to be displayed')
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

    @base.arg('file', action='store', type=str, help="file uri")
    @base.arg('attribute', nargs='?', type=str, help="attribute to retrieve or set. To set, use key=value")
    def execute_xattr(self):
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
                v = self.context.getxattr(self.params.file, attr)
                sys.stdout.write(attr + ' = ' + v + '\n')

    @base.arg('file', action='store', type=str,
              help="file uri to use for checksum calculation")
    @base.arg('checksum_type', action='store', type=str,
              help="checksum algorithm to use. For example: ADLER32, CRC32, MD5.")
    def execute_sum(self):
        """
        Calculates the checksum of a file
        """
        checksum = self.context.checksum(self.params.file, self.params.checksum_type)
        sys.stdout.write(self.params.file + ' ' + checksum + '\n')

    @base.arg("-r", "-R", "--recursive", action='store_true',
              help="remove directories and their contents recursively")
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
        else:
            files = [line.strip() for line in open(self.params.from_file, 'r').readlines()]
            files = filter(lambda f: len(f) > 0, files)

        for f in files:
            try:
                print f,
                self.context.unlink(f)
                print '\tDELETED'
            except gfal2.GError, e:
                if e.code == errno.ENOENT:
                    print '\tMISSING'
                elif (e.code == errno.EISDIR or e.code == errno.ENOTEMPTY) and self.params.recursive:
                    self.__rm_dir(f)
                    self.context.rmdir(f)
                    print '\tRMDIR'
                else:
                    print '\tFAILED'
                    raise

    def __rm_dir(self, directory):
        exclude = ['.', '..']
        contents = self.context.listdir(directory)
        if directory[-1] != '/':
            directory += '/'

        for c in contents:
            if c in exclude:
                continue
            try:
                self.context.unlink(directory + c)
            except gfal2.GError, e:
                if e.code == errno.EISDIR or e.code == errno.ENOTEMPTY:
                    self.__rm_dir(directory + c)
                    self.context.rmdir(directory + c)
                else:
                    raise

    @base.arg("file", action="store", type=str, help="uri of the file to be stat")
    def execute_stat(self):
        st = self.context.stat(self.params.file)
        print "  File: '%s'" % self.params.file
        print "  Size: %d\t%s" % (st.st_size, file_type_str(stat.S_IFMT(st.st_mode)))
        print "Access: (%04o/%s)\tUid: %d\tGid: %d\t" % (stat.S_IMODE(st.st_mode), file_mode_str(st.st_mode), st.st_uid, st.st_gid)
        print "Access: %s" % datetime.fromtimestamp(st.st_atime).strftime("%Y-%m-%d %H:%M:%S.%f")
        print "Modify: %s" % datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S.%f")
        print "Change: %s" % datetime.fromtimestamp(st.st_ctime).strftime("%Y-%m-%d %H:%M:%S.%f")

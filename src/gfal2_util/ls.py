"""
Created on Oct 10, 2013

@author: Duarte Meneses <duarte.meneses@cern.ch>
"""
import math
from datetime import datetime
import os
import sys
import stat

import base
from base import CommandBase
from utils import file_mode_str


class CommandLs(CommandBase):
    @base.arg('-a', '--all', action="store_true", help="display hidden files")
    @base.arg('-l', '--long', action="store_true", help='long listing format')
    @base.arg('-d', '--directory', action="store_true",
              help='list directory entries instead of contents')
    @base.arg('-H', '--human-readable', action="store_true",
              help='with -l, prints size in human readable format (e.g., 1K 234M 2G')
    @base.arg('--xattr', type=str, action='append', default=[],
              help="Query additional attributes. Can be specified multiple times. Only works for --long output")
    @base.arg('file', type=str, help="File's uri")
    def execute_ls(self):
        """List directory's contents"""
        st = self.context.stat(self.params.file)

        if stat.S_ISDIR(st.st_mode) and not self.params.directory:
            directory = self.context.opendir(self.params.file)
            st = None
            while True:
                if self.params.long:
                    (dirent, st) = directory.readpp()
                else:
                    dirent = directory.read()
                if dirent is None or dirent.d_name is None or len(dirent.d_name) == 0:
                    break

                if not self.params.all and dirent.d_name[0] == '.':
                    continue

                extra = list()
                if self.params.long:
                    for xattr in self.params.xattr:
                        surl = os.path.join(self.params.file, dirent.d_name)
                        extra.append(self.context.getxattr(surl, xattr))
                self._print_ls_entry(dirent.d_name, st, extra)
        else:
            extra = list()
            if self.params.long:
                for xattr in self.params.xattr:
                    extra.append(self.context.getxattr(self.params.file, xattr))
            self._print_ls_entry(self.params.file, st, extra)

        return 0

    def _print_ls_entry(self, name, stat, extra=None):
        space = {
            'st_mode': 5, 'st_nlink': 3, 'st_gid': 4, 'st_uid': 4,
            'st_mtime': 10, 'size': 9, 'size_human': 4
        }

        #if long, print some stuff from stat. Try to align as best as possible without buffering
        if self.params.long:
            size = stat.st_size
            size_sp = space['size']

            if self.params.human_readable:
                size = self._size_to_human(size)
                size_sp = space['size_human']

            date = self._date_to_human(stat.st_mtime)

            extra_str = ''
            if extra:
                extra_str = '\t'.join(extra)

            sys.stdout.write(
                "%s %s %s %s %s %s %s\t%s\n" % (
                    file_mode_str(stat.st_mode),
                    str(stat.st_nlink).ljust(space['st_nlink']),
                    str(stat.st_gid).ljust(space['st_gid']),
                    str(stat.st_uid).ljust(space['st_uid']),
                    str(date).ljust(space['st_mtime']),
                    str(size).ljust(size_sp),
                    name,
                    extra_str
                )
            )
            #else simply print name
        else:
            sys.stdout.write("%s\n" % name)

    @staticmethod
    def _date_to_human(date):
        dt = datetime.fromtimestamp(date)
        dt_now = datetime.now()

        diff_months = (dt_now - dt).days / 30  # approximate...
        day = dt.strftime("%d").lstrip("0").rjust(2)

        if diff_months < 6:
            return dt.strftime("%b " + day + " %H:%M")
        else:
            return dt.strftime("%b " + day + "  %Y")

    @staticmethod
    def _size_to_human(size):
        degree_symbols = ['', 'K', 'M', 'G', 'T', 'P']
        degree = 0
        while float(size) >= 1024.0 and degree < len(degree_symbols)-1:
            size = float(size) / 1024.0
            degree += 1

        #round up the result
        if size < 10.0:
            return "%0.1f%s" % (math.ceil(size*10.0)/10.0, degree_symbols[degree])
        else:
            return "%0.0f%s" % (math.ceil(size), degree_symbols[degree])

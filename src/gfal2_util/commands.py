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

    @base.arg('-f', "--force", action='store_true',
              help="if destination file(s) cannot be overwritten, delete it and try again")
    @base.arg('-p', "--parent", action='store_true',
              help="if the destination directory does not exist, create it")
    @base.arg('-n', "--nbstreams", type=int, default=None,
              help="specify the maximum number of parallel streams to use for the copy")
    @base.arg("--tcp-buffersize", type=int, default=None,
              help="specify the TCP buffersize")
    @base.arg('-s', "--src-spacetoken", type=str, default="",
              help="source spacetoken to use for the transfer")
    @base.arg('-S', "--dst-spacetoken", type=str, default="",
              help="destination spacetoken to use for the transfer")
    @base.arg('-T', "--transfer-timeout", type=int, default=None,
              help="global timeout for the transfer operation")
    @base.arg('-K', "--checksum", type=str, default=None,
              help='checksum algorithm to use, or algorithm:value')
    @base.arg('--from-file', type=str, default=None,
              help="read sources from a file")
    @base.arg('--just-copy', action='store_true',
              help='just do the copy and skip any preparation (i.e. checksum, overwrite, etc.)')
    @base.arg('src', type=str, nargs='?', help="source file")
    @base.arg('dst', action='store', nargs='+', type=str,
              help="destination file(s). If more than one is given, they will be chained copy: src -> dst1, dst1->dst2, ...")
    def execute_copy(self):
        """
        Copy a file
        """

        if not self.params.src and self.params.from_file:
            src_file = open(self.params.from_file, 'r')
            dst = self.params.dst[0]
            i = 1
            for src in [line.strip() for line in src_file.readlines()]:
                try:
                    if src:
                        self._copy(src, dst, src)
                except gfal2.GError, e:
                    pass
                i += 1
            src_file.close()
        elif self.params.from_file and self.params.src:
            print >>sys.stderr, "Could not combine --from-file with a source in the positional arguments"
            return 1
        elif self.params.src:
            s = self.params.src
            i = 1
            for d in self.params.dst:
                try:
                    d = self._copy(s, d, i)
                    s = d
                    i += 1
                except:
                    if len(self.params.dst) > 1:
                        print "%s to %s" % (s, d)
                    raise
        else:
            print >>sys.stderr, "Missing source"
            return 1

    def _copy(self, s, d, n):
        try:
            file_size = self.context.stat(s).st_size
        except Exception:
            file_size = None

        if not self.params.verbose and sys.stdout.isatty():
            if n > 1:
                print ''  # just do a new line
            self.progress_bar = Progress('Copying %s' % str(n))
            self.progress_bar.update(total_size=file_size)

        def event_callback(event):
            if self.params.verbose:
                print "event: %s" % str(event)

        def monitor_callback(src, dst, avg, inst, trans, elapsed):
            if self.params.verbose:
                print "monitor: %s %s %s %s %s %s" % (
                    str(src), str(dst),
                    str(avg), str(inst), str(trans), str(elapsed)
                )

            if self.progress_bar:
                self.progress_bar.update(trans, file_size, avg, elapsed)

        #set up transfer parameters. Leave defaults unless specified
        t = self.context.transfer_parameters()
        t.event_callback = event_callback
        t.monitor_callback = monitor_callback
        if self.params.nbstreams:
            t.nbstreams = self.params.nbstreams
        if self.params.transfer_timeout:
            t.transfer_timeout = self.params.timeout
        if self.params.src_spacetoken:
            t.src_spacetoken = self.params.src_spacetoken
        if self.params.dst_spacetoken:
            t.dst_spacetoken = self.params.dst_spacetoken
        if self.params.parent:
            t.create_parent = self.params.parent
        if self.params.tcp_buffersize:
            t.tcp_buffersize = self.params.tcp_buffersize
        if self.params.force:
            t.overwrite = self.params.force
        if self.params.checksum:
            t.checksum_check = True
            chk_args = self.params.checksum.split(':')
            if len(chk_args) == 1:
                chk_args.append('')
            t.set_user_defined_checksum(chk_args[0], chk_args[1])
        if self.params.just_copy:
            t.strict_copy = True

        #deduce destination name
        try:
            if stat.S_ISDIR(self.context.stat(d).st_mode):
                d += '/' + os.path.basename(s)
        except:
            pass

        ret = -1
        if self.progress_bar:
            self.progress_bar.start()
        try:
            try:
                ret = self.context.filecopy(t, s, d)
            except gfal2.GError, e:
                if e.code == errno.EISDIR:
                    if d[-1] != '/':
                        d += '/'
                    d += os.path.basename(s)
                    ret = self.context.filecopy(t, s, d)
                elif e.code == errno.EEXIST and self.params.force:
                    ret = self.context.unlink(d)
                    ret = self.context.filecopy(t, s, d)
                else:
                    raise
        finally:
            if self.progress_bar:
                self.progress_bar.stop(ret == 0)

        return d

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

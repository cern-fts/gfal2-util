import sys
import os
import stat
import errno

import gfal2
import base
from base import CommandBase
from progress import Progress


class CommandCopy(CommandBase):

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

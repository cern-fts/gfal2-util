import sys
import os
import stat
import errno

import gfal2
import base
from base import CommandBase
from progress import Progress


class CommandCopy(CommandBase):

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
              help="just do the copy and skip any preparation (i.e. checksum, overwrite, etc.)")
    @base.arg('-r', '--recursive', action='store_true',
              help="copy directories recursively")
    @base.arg('--abort-on-failure', action='store_true',
              help="abort the whole copy as soon as one failure is encountered")
    @base.arg('--dry-run', action='store_true',
              help="do not perform any action, just print what would be done")
    @base.arg('src', type=str, nargs='?', help="source file")
    @base.arg('dst', action='store', nargs='+', type=str,
              help="destination file(s). If more than one is given, they will be chained copy: src -> dst1, dst1->dst2, ...")
    def execute_copy(self):
        """
        Copy a file or set of files
        """
        if self.params.from_file and self.params.src:
            print >>sys.stderr, "Could not combine --from-file with a source in the positional arguments"
            return 1

        copy_jobs = list()
        if self.params.from_file:
            src_file = open(self.params.from_file)
            dst = self.params.dst[0]
            for src in map(str.strip, src_file.readlines()):
                if src:
                    copy_jobs.append((src, dst))
            src_file.close()
        elif self.params.src:
            for dst in self.params.dst:
                copy_jobs.append((self.params.src, dst))
        else:
            print >>sys.stderr, "Missing source"
            return 1

        # Do the actual work
        for (source, destination) in copy_jobs:
            self._do_copy(source, destination)
        return 0

    def _failure(self, msg, errno):
        if self.params.abort_on_failure or not self.params.recursive:
            raise gfal2.GError(msg, errno)
        print "ERROR (%d): %s" % (errno, msg)
        return False

    def _do_copy(self, source, destination):
        # Check what are we dealing with
        try:
            source_stat = self.context.stat(source)
            source_isdir = stat.S_ISDIR(source_stat.st_mode)
        except gfal2.GError, e:
            return self._failure("Could not stat the source: %s" % e.message, e.code)

        dest_isdir = False
        dest_exists = False
        try:
            dest_stat = self.context.stat(destination)
            dest_isdir = stat.S_ISDIR(dest_stat.st_mode)
            dest_exists = True
        except:
            pass

        # Perform some checks before continuing
        if dest_exists and not dest_isdir and not self.params.force:
            return self._failure("Destination %s exists and overwrite is not set" % destination, errno.EEXIST)
        if dest_exists and not dest_isdir and source_isdir:
                return self._failure("Can not copy a directory over a file", errno.EISDIR)

        if source_isdir and not dest_exists:
            try:
                self._mkdir(destination)
            except gfal2.GError, e:
                return self._failure("Could not create the directory: %s" % e.message, e.code)
            return self._recursive_copy(source, destination)
        elif dest_isdir and source_isdir:
            if self.params.recursive:
                return self._recursive_copy(source, destination)
            else:
                print "Skipping %s" % source
                return True
        elif dest_isdir:
            if destination[-1] != '/':
                destination += '/'
            destination += os.path.basename(source)

        return self._do_file_copy(source, destination, source_stat.st_size)

    def _mkdir(self, surl):
        print "Mkdir %s" % surl
        if not self.params.dry_run:
            self.context.mkdir_rec(surl, 0755)

    def _recursive_copy(self, source, destination):
        all_sources = self.context.listdir(source)
        src_base_dir = source
        dst_base_dir = destination
        if src_base_dir[-1] != '/':
            src_base_dir += '/'
        if dst_base_dir[-1] != '/':
            dst_base_dir += '/'
        for entry in all_sources:
            if entry not in ['.', '..']:
                new_source = src_base_dir + entry
                new_destination = dst_base_dir + entry
                self._do_copy(new_source, new_destination)

    def _setup_transfer_params(self, t, event_callback, monitor_callback):
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

    def _do_file_copy(self, source, destination, source_size):
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
                self.progress_bar.update(trans, source_size, avg, elapsed)

        t = self.context.transfer_parameters()
        self._setup_transfer_params(t, event_callback, monitor_callback)

        progress_bar = None
        if not self.params.dry_run and not self.params.verbose and sys.stdout.isatty():
            progress_bar = Progress("Copying %s" % source)
            progress_bar.update(total_size=source_size)
            progress_bar.start()
        else:
            print "Copying %d bytes %s => %s" % (source_size, source, destination)

        ret = -1
        try:
            if not self.params.dry_run:
                ret = self.context.filecopy(t, source, destination)
        except gfal2.GError, e:
            if e.code == errno.EEXIST and self.params.force:
                self.context.unlink(destination)
                return self._do_file_copy(source, destination, source_size)
            return self._failure(e.message, e.code)
        finally:
            if progress_bar:
                progress_bar.stop(ret == 0)
                print

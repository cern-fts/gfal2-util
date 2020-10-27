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

import logging
import sys
import os
import stat
import errno

import gfal2
from gfal2_util import base
from gfal2_util.progress import Progress


log = logging.getLogger(__name__)


def _is_special_file(fstat):
    """
    Returns true if the file is a special one (i.e. stdout, stderr, null....)
    """
    return stat.S_ISFIFO(fstat.st_mode) or stat.S_ISCHR(fstat.st_mode) or stat.S_ISSOCK(fstat.st_mode)


class CommandCopy(base.CommandBase):

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
    @base.arg("--copy-mode", type=str, default='', choices=['pull', 'push', 'streamed',''],
              help='copy mode. N.B. supported only for HTTP/DAV to HTTP/DAV transfers, if not specified the pull mode will be executed first with fallbacks to other modes in case of errors')
    @base.arg("--checksum-mode", type=str, default='both', choices=['source', 'target', 'both'],
              help='checksum validation mode')
    @base.arg('--from-file', type=str, default=None,
              help="read sources from a file")
    @base.arg('--just-copy', action='store_true',
              help="just do the copy and skip any preparation (i.e. checksum, overwrite, etc.)")
    @base.arg('--no-delegation', action='store_true',
              help="disable TPC with proxy delegation")
    @base.arg('-r', '--recursive', action='store_true',
              help="copy directories recursively")
    @base.arg('--abort-on-failure', action='store_true',
              help="abort the whole copy as soon as one failure is encountered")
    @base.arg('--dry-run', action='store_true',
              help="do not perform any action, just print what would be done")
    @base.arg('src', type=base.surl, nargs='?', help="source file")
    @base.arg('dst', action='store', nargs='+', type=base.surl,
              help="destination file(s). If more than one is given, they will be chained copy: src -> dst1, dst1->dst2, ...")
    def execute_copy(self):
        """
        Copy a file or set of files
        """
        if self.params.from_file and self.params.src:
            sys.stderr.write("Could not combine --from-file with a source in the positional arguments\n")
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
            s = self.params.src
            for dst in self.params.dst:
                copy_jobs.append((s, dst))
                # Next hop
                # If dst happens to be a dir, append the file name
                is_dst_dir = False
                if not self.params.just_copy:
                    try:
                        is_dst_dir = stat.S_ISDIR(self.context.stat(dst).st_mode)
                    except:
                        pass
                if is_dst_dir:
                    s = dst + '/' + os.path.basename(s)
                else:
                    s = dst
        else:
            sys.stderr.write("Missing source\n")
            return 1

        # Do the actual work
        for (source, destination) in copy_jobs:
            if destination == '-':
                destination = 'file:///dev/stdout'

            if self.params.just_copy:
                self._do_file_copy(source, destination, 0)
            else:
                self._do_copy(source, destination)

        return 0

    def _failure(self, msg, errno):
        if self.params.abort_on_failure or not self.params.recursive:
            raise gfal2.GError(msg, errno)
        print("ERROR (%d): %s" % (errno, msg))
        return False

    def _do_copy(self, source, destination):
        # Check what are we dealing with
        try:
            source_stat = self.context.stat(source)
            source_isdir = stat.S_ISDIR(source_stat.st_mode)
        except gfal2.GError:
            e = sys.exc_info()[1]
            return self._failure("Could not stat the source: %s" % e.message, e.code)

        dest_isdir = False
        dest_exists = False
        dest_special = False
        try:
            dest_stat = self.context.stat(destination)
            dest_isdir = stat.S_ISDIR(dest_stat.st_mode)
            dest_exists = True
            if destination.startswith('file:'):
                dest_special = _is_special_file(dest_stat)
        except:
            pass

        # Perform some checks before continuing
        is_lfc = destination.startswith('lfc://') or destination.startswith('lfn://') or destination.startswith('guid://')
        if dest_exists and not dest_isdir and not dest_special and not self.params.force:
            if is_lfc:
                log.warning("Destination exists, but it is an LFC, so try to add a new replica")
            else:
                return self._failure("Destination %s exists and overwrite is not set" % destination, errno.EEXIST)
        if dest_exists and not dest_isdir and source_isdir:
                return self._failure("Can not copy a directory over a file", errno.EISDIR)

        if source_isdir and not dest_exists:
            try:
                self._mkdir(destination)
            except gfal2.GError:
                e = sys.exc_info()[1]
                return self._failure("Could not create the directory: %s" % e.message, e.code)
            return self._recursive_copy(source, destination)
        elif dest_isdir and source_isdir:
            if self.params.recursive:
                return self._recursive_copy(source, destination)
            else:
                print("Skipping %s" % source)
                return True
        elif dest_isdir:
            if destination[-1] != '/':
                destination += '/'
            destination += os.path.basename(source)

        return self._do_file_copy(source, destination, source_stat.st_size)

    def _mkdir(self, surl):
        print("Mkdir %s" % surl)
        if not self.params.dry_run:
            self.context.mkdir_rec(surl, int('755', 8)) # python < 2.6 doesn't support 0o755

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
            t.timeout = self.params.transfer_timeout
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
        if self.params.just_copy:
            t.strict_copy = True
        if self.params.no_delegation:
            if hasattr(t, 'proxy_delegation'): # available since gfal-python 1.9.6
                t.proxy_delegation = False
            else:
                sys.stderr.write("[warn] '--no-delegation' flag requires gfal2-python >= 1.9.6\n")

        if self.params.checksum:
            chk_args = self.params.checksum.split(':')
            if len(chk_args) == 1:
                chk_args.append('')
            if hasattr(t, 'set_checksum'): # available since gfal-python 1.9.0
                mode = dict(
                        source=gfal2.checksum_mode.source,
                        target=gfal2.checksum_mode.target,
                        both=gfal2.checksum_mode.both
                       )[self.params.checksum_mode]
                t.set_checksum(mode, chk_args[0], chk_args[1])
            else:
                t.checksum_check = True
                t.set_user_defined_checksum(chk_args[0], chk_args[1])

        if self.params.copy_mode:
            if self.params.copy_mode == 'pull':
                self.context.set_opt_boolean("HTTP PLUGIN", "ENABLE_REMOTE_COPY", True)
                self.context.set_opt_boolean("HTTP PLUGIN", "ENABLE_FALLBACK_TPC_COPY", False)
                self.context.set_opt_string("HTTP PLUGIN", "DEFAULT_COPY_MODE", "3rd pull")
            elif self.params.copy_mode == 'push':
                self.context.set_opt_boolean("HTTP PLUGIN", "ENABLE_REMOTE_COPY", True)
                self.context.set_opt_boolean("HTTP PLUGIN", "ENABLE_FALLBACK_TPC_COPY", False)
                self.context.set_opt_string("HTTP PLUGIN", "DEFAULT_COPY_MODE", "3rd push")
            elif self.params.copy_mode == 'streamed':
                self.context.set_opt_boolean("HTTP PLUGIN", "ENABLE_REMOTE_COPY", False)
                self.context.set_opt_string("HTTP PLUGIN", "DEFAULT_COPY_MODE", "streamed")
            else:
                self.context.set_opt_boolean("HTTP PLUGIN", "ENABLE_REMOTE_COPY", True)
                self.context.set_opt_boolean("HTTP PLUGIN", "ENABLE_FALLBACK_TPC_COPY", True)
                self.context.set_opt_string("HTTP PLUGIN", "DEFAULT_COPY_MODE", "3rd pull")

        if event_callback:
            t.event_callback = event_callback
        if monitor_callback:
            t.monitor_callback = monitor_callback

    def _do_file_copy(self, source, destination, source_size):
        def event_callback(event):
            if self.params.verbose:
                print("event: %s" % str(event))

        def monitor_callback(src, dst, avg, inst, trans, elapsed):
            if self.params.verbose:
                print("monitor: %s %s %s %s %s %s" % (
                    str(src), str(dst),
                    str(avg), str(inst), str(trans), str(elapsed)
                ))

            if self.progress_bar:
                self.progress_bar.update(trans, source_size, avg, elapsed)

        t = self.context.transfer_parameters()
        self._setup_transfer_params(t, event_callback, monitor_callback)

        self.progress_bar = None
        if not self.params.dry_run and not self.params.verbose and sys.stdout.isatty():
            self.progress_bar = Progress("Copying %s" % source)
            self.progress_bar.update(total_size=source_size)
            self.progress_bar.start()
        else:
            print("Copying %d bytes %s => %s" % (source_size, source, destination))

        try:
            if not self.params.dry_run:
                ret = self.context.filecopy(t, source, destination)
            if self.progress_bar:
                self.progress_bar.stop(True)
                print("")
        except gfal2.GError:
            e = sys.exc_info()[1]
            if self.progress_bar:
                self.progress_bar.stop(False)
                print("")
            if e.code == errno.EEXIST and self.params.force:
                self.context.unlink(destination)
                return self._do_file_copy(source, destination, source_size)
            return self._failure(e.message, e.code)
        except SystemError:
            #e = sys.exc_info()[1]
            #etype, value = sys.exc_info()[:2]
            etype, value, tb = sys.exc_info()
            print("ERROR: %s (%s)" % (str(etype), str(value)))
            import traceback
            traceback.print_exception(etype, value, tb)

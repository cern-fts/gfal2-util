#
# Copyright (c) 2013-2022 CERN
#
# Copyright (c) 2012-2013 Members of the EMI Collaboration
#    See http://www.eu-emi.eu/partners for details on the copyright
#    holders.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#from __future__ import absolute_import # not available in python 2.4
from __future__ import division

import sys
import stat
import errno

import gfal2
from gfal2_util import base


class CommandRm(base.CommandBase):
    def __init__(self):
        self.return_code = 0

    @base.arg("-r", "-R", "--recursive", action='store_true',
              help="remove directories and their contents recursively")
    @base.arg("--dry-run", action='store_true',
              help="do not perform any actual change, just print what would happen")
    @base.arg("--just-delete", action='store_true',
              help="do not perform any check on the file, this is needed for HTTP signed URLs")
    @base.arg("--from-file", type=str, default=None,
              help="read surls from a file")
    @base.arg("--bulk", action='store_true', default=False,
              help="use bulk deletion")
    @base.arg("file", action='store', nargs='*', type=base.surl,
              help="uri(s) of the file(s) to be deleted")
    def execute_rm(self):
        """
        Removes files or directories
        """
        if self.params.from_file and self.params.file:
            sys.stderr.write("--from-file and positional arguments can not be used at the same time\n")
            return errno.EINVAL
        if self.params.bulk and self.params.recursive:
            sys.stderr.write("--bulk and --recursive can not be used at the same time\n")
            return errno.EINVAL

        if self.params.file:
            files = self.params.file
        elif self.params.from_file:
            files = [line.strip() for line in open(self.params.from_file, 'r').readlines()]
            files = [f for f in files if len(f) > 0]
        else:
            sys.stderr.write("Missing surl\n")
            return errno.EINVAL

        if self.params.bulk:
            self._do_bulk(files)
        else:
            for f in files:
                self._do_rm(f)

        return self.return_code

    def _do_rm(self, surl):
        """
        Perform the action, either removing or just informing
        """
        if not self.params.just_delete:
            try:
                st = self.context.stat(surl)
            except gfal2.GError:
                e = sys.exc_info()[1]
                self._propagate_error_code(e.code)
                if e.code == errno.ENOENT:
                    print("%s\tMISSING" % surl)
                    return
                else:
                    print("%s\tFAILED" % surl)
                    raise

            if stat.S_ISDIR(st.st_mode):
                self._do_rmdir(surl)
                return

        if self.params.dry_run:
            print("%s\tSKIP" % surl)
            return

        try:
            self.context.unlink(surl)
            print("%s\tDELETED" % surl)
        except gfal2.GError:
            e = sys.exc_info()[1]
            self._propagate_error_code(e.code)
            if e.code == errno.ENOENT:
                print("%s\tMISSING" % surl)
                return
            else:
                print("%s\tFAILED" % surl)
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
            print("%s\tSKIP DIR" % surl)
        else:
            try:
                self.context.rmdir(surl)
                print("%s\tRMDIR" % surl)
            except gfal2.GError:
                e = sys.exc_info()[1]
                self._propagate_error_code(e.code)
                if e.code == errno.ENOENT:
                    print("%s\tMISSING" % surl)
                else:
                    print("%s\tFAILED" % surl)
                    raise

    def _do_bulk(self, surls):
        """
        Do a bulk deletion
        """
        if self.params.dry_run:
            print("\tBULK DELETION")
            return

        errors = self.context.unlink(surls)
        for error, surl in zip(errors, surls):
            if error is None:
                print("%s\tDELETED" % surl)
            else:
                print("%s\tFAILED: %s" % (surl, error))
                self._propagate_error_code(error.code)

    def _propagate_error_code(self, error_code):
        """
        Propagate the error code if the return code is empty
        """
        if self.return_code == 0:
            self.return_code = error_code

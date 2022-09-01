#
# Copyright (c) CERN 2022
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import time
import sys
import errno

from gfal2_util import base


def _evaluate_errors(errors, surls, polling):
    n_terminal = 0
    for surl, error in zip(surls, errors):
        if error:
            if error.code != errno.EAGAIN:
                print("%s => FAILED: %s" % (surl, error.message))
                n_terminal += 1
            else:
                print("%s QUEUED" % surl)
        elif not polling:
            print("%s QUEUED" % surl)
        else:
            n_terminal += 1
            print("%s READY" % surl)
    return n_terminal


class CommandTape(base.CommandBase):
    """
    Implement tape operations support via Gfal2 library
    """

    @base.arg('--pin-lifetime', action='store', type=int, default=0, help='Desired pin lifetime')
    @base.arg('--desired-request-time', action='store', type=int, default=28800, help='Desired total request time')
    @base.arg('--staging-metadata', action='store', type=str, default="", help='Metadata for the bringonline operation')
    @base.arg('--polling-timeout', action='store', type=int, default=0, help='Timeout for the polling operation')
    @base.arg('--from-file', type=str, default=None, help="read sources from a file")
    @base.arg('surl', action='store', type=base.surl, nargs='?', help='Site URL')
    def execute_bringonline(self):
        """
        Execute bring online
        """
        if self.params.from_file and self.params.surl:
            sys.stderr.write('Could not combine --from-file with a surl in the positional arguments\n'
                             )
            return 1

        surls = list()
        if self.params.from_file:
            src_file = open(self.params.from_file)
            for src in map(str.strip, src_file.readlines()):
                if src:
                    surls.append(src)
            src_file.close()
        elif self.params.surl:
            surls.append(self.params.surl)
        else:
            sys.stderr.write('Missing surl\n')
            return 1

        nbfiles = len(surls)
        metadata_list = [self.params.staging_metadata] * nbfiles

        # Create bringonline request
        (errors, token) = self.context.bring_online(surls, metadata_list,
                                                    self.params.pin_lifetime,
                                                    self.params.desired_request_time, True)

        n_terminal = _evaluate_errors(errors, surls, polling=False)

        # Start the polling
        wait = self.params.polling_timeout
        sleep = 1

        while n_terminal != len(surls) and wait > 0:
            print("Request queued, sleep %d seconds..." % sleep)
            wait -= sleep
            time.sleep(sleep)
            errors = self.context.bring_online_poll(surls, token)
            n_terminal = _evaluate_errors(errors, surls, polling=True)
            sleep *= 2
            sleep = min(sleep, 300)

    @base.arg('--polling-timeout', action='store', type=int, default=0, help='Timeout for the polling operation')
    @base.arg('surl', action='store', type=base.surl, help='Site URL')
    def execute_archivepoll(self):
        """
        Execute bring online
        """
        wait = self.params.polling_timeout
        sleep = 1
        ret = self.context.archive_poll(self.params.surl)

        while ret == 0 and wait > 0:
            print("Archiving ongoing, sleep %d seconds..." % sleep)
            wait -= sleep
            time.sleep(sleep)
            ret = self.context.archive_poll(self.params.surl)
            sleep *= 2
            sleep = min(sleep, 300)

        if ret > 0:
            print("Archiving finished")
        elif ret == 0:
            print("File is not yet archived")
        else:
            print("Archiving polling failed")

    @base.arg('file', action='store', type=base.surl, help="URI to the file to be evicted")
    @base.arg('token', type=str, nargs='?', default="", help="The token from the bring online request")
    def execute_evict(self):
        """
        Evict file from a disk buffer
        """
        st = self.context.release(self.params.file, self.params.token)

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

from gfal2_util import base


class CommandTape(base.CommandBase):
    """
    Implement tape operations support via Gfal2 library
    """
    @base.arg('--pin-lifetime', action='store', type=int, default=0, help='Desired pin lifetime')
    @base.arg('--desired-request-time', action='store', type=int, default=28800, help='Desired total request time')
    @base.arg('--staging-metadata', action='store', type=str, default="", help='Metadata for the bringonline operation')
    @base.arg('--polling-timeout', action='store', type=int, default=-1, help='Timeout for the polling operation')
    @base.arg('surl', action='store', type=base.surl, help='Site URL')
    def execute_bringonline(self):
        """
        Execute bring online
        """
        (ret, token) = self.context.bring_online(
            self.params.surl, self.params.staging_metadata,
            self.params.pin_lifetime, self.params.desired_request_time, True
        )
        # Check if stage request failed
        if ret < 0:
            print("Staging request failed")
            return

        print("Request queued! Got token %s" % token)
        wait = self.params.polling_timeout
        sleep = 1
        while ret == 0 and wait > 0:
            print("Request queued, sleep %d seconds..." % sleep)
            wait -= sleep
            time.sleep(sleep)
            ret = self.context.bring_online_poll(self.params.surl, token)
            sleep *= 2
            sleep = min(sleep, 300)

        if ret > 0:
            print("File brought online with token %s" % token)
        elif wait <= 0:
            print("The file is not yet online")
        else:
            print("Bring online failed with an error")

    @base.arg('file', action='store', type=base.surl, help="URI to the file to be evicted")
    @base.arg('token', type=str, nargs='?', default="", help="The token from the bring online request")
    def execute_evict(self):
        """
        Evict file from a disk buffer
        """
        st = self.context.release(self.params.file, self.params.token)

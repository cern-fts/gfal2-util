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

from __future__ import division

import signal
import stat


class Timeout:
    """Timeout class using ALARM signal."""
    class Timeout(Exception):
        pass

    def __init__(self, sec):
        self.sec = sec

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.raise_timeout)
        signal.alarm(self.sec)

    def __exit__(self, *args):
        signal.alarm(0)    # disable alarm

    def raise_timeout(self, *args):
        raise Timeout.Timeout()


def file_type_str(type):
    ftype_str = {
        stat.S_IFBLK: 'block device',
        stat.S_IFCHR: 'character device',
        stat.S_IFDIR: 'directory',
        stat.S_IFIFO: 'fifo',
        stat.S_IFLNK: 'symbolic link',
        stat.S_IFREG: 'regular file',
        stat.S_IFSOCK: 'socket'
    }
    repr = ftype_str.get(type, 'unknown')
    return repr


def _mode_str_triplet(mode):
    mode_str = ['-'] * 3
    if mode & stat.S_IROTH:
        mode_str[0] = 'r'
    if mode & stat.S_IWOTH:
        mode_str[1] = 'w'
    if mode & stat.S_IXOTH:
        mode_str[2] = 'x'
    return ''.join(mode_str)


def file_mode_str(mode):
    mode_str = ''
    if stat.S_ISDIR(mode):
        mode_str += 'd'
    elif stat.S_ISBLK(mode):
        mode_str +='b'
    elif stat.S_ISCHR(mode):
        mode_str += 'c'
    elif stat.S_ISFIFO(mode):
        mode_str += 'f'
    elif stat.S_ISSOCK(mode):
        mode_str += 's'
    else:
        mode_str += '-'
    mode_str += _mode_str_triplet(mode >> 6) + _mode_str_triplet(mode >> 3) + _mode_str_triplet(mode)
    return mode_str

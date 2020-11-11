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

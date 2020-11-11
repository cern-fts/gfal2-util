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

import subprocess
import sys
import datetime
import math
import time
import threading


class Progress(object):
    def __init__(self, label):
        self.started = False
        self.stopped = False
        self.status = None
        self.label = label
        self.lock = threading.Lock()

    def start(self):
        #don't let it start twice, thread safe
        self.lock.acquire()
        if self.started or self.stopped:
            self.lock.release()
            raise
        self.lock.release()

        self.started = True
        self.start_time = datetime.datetime.now()
        self.dots = 0

        self.t_main = threading.Thread(target=self._run)
        self.t_main.daemon = True
        if not hasattr(self.t_main, 'is_alive'):
            # is_alive was added in python 2.6 and isAlive deprecated in python 3.8
            self.t_main.is_alive = self.t_main.isAlive
        self.t_main.start()

    @staticmethod
    def _total_seconds(td):
        #for compatibility with python < 2.7
        return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6

    def _run(self):
        #use lock to avoid main thread assume we are done while we are printing
        while True:
            self.lock.acquire()
            if self.stopped or not self.started:
                break

            try:
                self._update()
            finally:
                self.lock.release()
            time.sleep(0.5)

        self.lock.release()

    def _update(self):
        """
        Prints label, time elapsed, percentage, progress bar, size transferred,
        transfer rate. Some elements are optional, depending on the available info
        """
        time_elapsed = datetime.datetime.now() - self.start_time
        self._clean()

        #write label
        str_label = self.label + ('.' * self.dots).ljust(3)
        sys.stdout.write(str_label)

        #write total time elapsed
        str_time = "  %ds " % self._total_seconds(time_elapsed)
        sys.stdout.write(str_time)

        #we hold the lock, so no concurrency probs while accessing status
        if self.status:
            total_width = self._get_width()

            #we have everything
            if self.status.get('percentage'):
                str_percentage = str(int(round(self.status['percentage']))) + '% '
                str_rate = self._get_rate_str(self.status['rate'])
                str_curr_size = ' ' + self._get_size_str(self.status['curr_size']) + ' '

                used_width = len(str_label) + len(str_time) + len(str_percentage) + len(str_curr_size) + len(str_rate)
                unused_width = total_width - used_width

                if unused_width >= 7:
                    bar_progr_width = unused_width-2
                else:
                    bar_progr_width = 5
                bars_len = int(round((float(self.status['percentage'])*bar_progr_width)/100.0))
                if bars_len == 0:
                    bars_len = 1
                space_len = unused_width-bars_len-2

                progress_str = '[' + '='*(bars_len-1) + '>' + ' '*space_len + ']'

                sys.stdout.write(str_percentage)
                sys.stdout.write(progress_str)

                #write total data size
                sys.stdout.write(str_curr_size)

                #write average transfer rate
                sys.stdout.write(str_rate)

            elif self.status.get('total_size'):
                str_filesize = " File size: %s" % \
                    self._get_size_str(self.status['total_size'])

                #write file size
                sys.stdout.write(str_filesize)
                used_width = len(str_label) + len(str_time) + len(str_filesize)
                unused_width = total_width - used_width

                #white space
                sys.stdout.write(' ' * unused_width)

            elif self.status.get('curr_size'):
                str_rate = self._get_rate_str(self.status['rate'])
                str_curr_size = self._get_size_str(self.status['curr_size']) + ' '

                used_width = len(str_label) + len(str_time) + len(str_curr_size) + len(str_rate)
                unused_width = total_width - used_width

                #white space
                sys.stdout.write(' ' * unused_width)

                #write transfered data size
                sys.stdout.write(str_curr_size)

                #write average transfer rate
                sys.stdout.write(str_rate)

            else:
                used_width = len(str_label) + len(str_time)
                unused_width = total_width - used_width

                #white space
                sys.stdout.write(' ' * unused_width)

        sys.stdout.flush()

        self.dots += 1
        if self.dots == 4:
            self.dots = 0

    def update(self, curr_size=None, total_size=None, rate=None, time_elapsed=None):
        self.lock.acquire()
        self.status = {}

        if curr_size:
            self.status['curr_size'] = curr_size
        if total_size:
            self.status['total_size'] = total_size
        if curr_size and time_elapsed and total_size:
            self.status['rate'] = float(curr_size)/float(time_elapsed)
            self.status['percentage'] = (float(curr_size) / float(total_size))*100.0
        elif rate:
            self.status['rate'] = rate

        self.lock.release()

    def stop(self, success):
        if not self.started:
            return

        if self.t_main.is_alive():
            self.lock.acquire()
            if self.stopped:
                self.lock.release()
                return

            self.stopped = True
            self.lock.release()
        #thread might have died without releasing the lock
        else:
            if self.stopped:
                    return
            self.stopped = True

        self._clean()
        time_elapsed = datetime.datetime.now() - self.start_time
        if success:
            outcome = 'DONE'
        else:
            outcome = 'FAILED'

        str_msg = self.label + '   [' + outcome + ']  after %ds' % self._total_seconds(time_elapsed)

        spaces = self._get_width() - len(str_msg)

        sys.stdout.write(str_msg)
        sys.stdout.write(' ' * spaces)
        sys.stdout.flush()

    @staticmethod
    def _get_width():
        p = subprocess.Popen(['stty', 'size'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if p.returncode != 0:
            return 80  # Asume default
        return int(out.split()[1])

    @staticmethod
    def _clean():
        sys.stdout.write('\r')

    @staticmethod
    def _get_size_str(size):
        size_str = Progress._get_rate_str(size)[:-2]
        if size_str[-1] != 'B':
            size_str = (size_str + "B")

        return size_str

    @staticmethod
    def _get_rate_str(rate):
        degree_symbols = ['B', 'K', 'M', 'G', 'T', 'P']
        degree = 0
        while float(rate) >= 1024.0 and degree < len(degree_symbols)-1:
            rate = float(rate) / 1024.0
            degree += 1

        digits = len(str(math.floor(rate)))
        str_units = degree_symbols[degree] + "/s"

        if digits < 3 and degree != 0:
            precision = 3 - digits
        else:
            precision = 0

        fmt = "%0." + str(precision) + "f"
        str_rate = fmt % round(rate, precision)

        return str_rate + str_units

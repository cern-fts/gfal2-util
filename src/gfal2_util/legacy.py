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

import time

from gfal2_util import base


class CommandLegacy(base.CommandBase):
    """
    Implement some legacy support around gfal2
    """

    @base.arg('lfc', action='store', type=base.surl, help="LFC entry (lfc:// or guid:)")
    @base.arg('surl', action='store', type=base.surl, help="Site URL to be unregistered")
    def execute_unregister(self):
        """
        Unregister a replica.
        """
        value = '-' + self.params.surl
        self.context.setxattr(self.params.lfc, 'user.replicas', value, len(value))

    @base.arg('lfc', action='store', type=base.surl, help="LFC entry (lfc:// or guid:)")
    @base.arg('surl', action='store', type=base.surl, help="Site URL to be unregistered")
    def execute_register(self):
        """
        Register a replica.
        """
        value = '+' + self.params.surl
        self.context.setxattr(self.params.lfc, 'user.replicas', value, len(value))

    @base.arg('lfc', action='store', type=base.surl, help="LFC entry (lfc:// or guid:)")
    def execute_replicas(self):
        """
        List replicas.
        """
        replicas = self.context.getxattr(self.params.lfc, 'user.replicas').split('\n')
        for replica in replicas:
            print(replica)

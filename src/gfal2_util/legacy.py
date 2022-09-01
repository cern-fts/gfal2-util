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

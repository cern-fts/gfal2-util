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

def get_parameter_from_str_list(str_value_list):
    str_value_tab = str_value_list.split(",")
    return [get_parameter_from_str(i) for i in str_value_tab]


def get_parameter_from_str(str_value):
    def str2bool(v):
        s = v.lower()
        if s in ["true", "yes", "y", "1"]:
            return True
        if s in ["false", "no", "n", "0"]:
            return False
        raise ValueError("is not a boolean")

    for i in [int, str2bool, str]:
        try:
            return i(str_value)
        except ValueError:
            pass

    raise ValueError("not a valid parameter type")


def parse_parameter(str_params):
    value_sep = str_params.find('=')
    if value_sep == -1:
        raise ValueError("parameter '%s' doesn't include value, use 'group:option=value'" % str_params)
    group_sep = str_params[:value_sep].rfind(':')
    if group_sep == -1:
        raise ValueError("parameter '%s' doesn't include group name, use 'group:option=value'" % str_params)
    group = str_params[:group_sep]
    option = str_params[group_sep + 1:value_sep]
    value = str_params[value_sep + 1:]
    return (group, option, get_parameter_from_str_list(value))


def set_gfal_tool_parameter(context, param_struct):
    def set_params_struct(p, f):
        f(p[0], p[1], p[2][0])

    if len(param_struct[2]) > 1:
        context.set_opt_string_list(param_struct[0], param_struct[1], param_struct[2])
    elif int == type(param_struct[2][0]):
        set_params_struct(param_struct, context.set_opt_integer)
    elif bool == type(param_struct[2][0]):
        set_params_struct(param_struct, context.set_opt_boolean)
    elif str == type(param_struct[2][0]):
        set_params_struct(param_struct, context.set_opt_string)
    else:
        raise ValueError("not a valid parameter type")


def apply_option(context, params):
    if params.definition:
        p_list = [parse_parameter(str_param[0]) for str_param in params.definition]
        [set_gfal_tool_parameter(context, tuple_param) for tuple_param in p_list]
    if params.client_info:
        for cinfo in params.client_info:
            try:
                key, val = cinfo.split('=', 2)
                context.add_client_info(key, val)
            except:
                context.add_client_info(cinfo, '')

    if params.ipv6:
        context.set_opt_boolean("GRIDFTP PLUGIN", "IPV6", True)
    elif params.ipv4:
        context.set_opt_boolean("GRIDFTP PLUGIN", "IPV6", False)

    if params.timeout:
        context.set_opt_integer("CORE", "NAMESPACE_TIMEOUT", params.timeout)
        context.set_opt_integer("CORE", "CHECKSUM_TIMEOUT", params.timeout)

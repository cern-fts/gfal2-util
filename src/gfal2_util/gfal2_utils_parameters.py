"""
gfal 2.0 tools core  parameters
@author Adrien Devresse <adevress@cern.ch> CERN
@license GPLv3
"""


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
    group_sep = str_params.index(":")
    res = str_params[:group_sep]
    value_sep = str_params[group_sep + 1:].index("=") + group_sep + 1
    return (res, str_params[group_sep + 1:value_sep],
            get_parameter_from_str_list(str_params[value_sep + 1:]))


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

from types import FunctionType
from typing import Any

CO_VARARGS = 4
CO_VARKEYWORDS = 8

ERR_TOO_MANY_POS_ARGS = "Too many positional arguments"
ERR_TOO_MANY_KW_ARGS = "Too many keyword arguments"
ERR_MULT_VALUES_FOR_ARG = "Multiple values for arguments"
ERR_MISSING_POS_ARGS = "Missing positional arguments"
ERR_MISSING_KWONLY_ARGS = "Missing keyword-only arguments"
ERR_POSONLY_PASSED_AS_KW = "Positional-only argument passed as keyword argument"


# 15 - all 7 - no kwargs 11 - no args  3- nothing
def bind_args(func: FunctionType, *args: Any, **kwargs: Any) -> dict[str, Any]:
    """Bind values from `args` and `kwargs` to corresponding arguments of `func`

    :param func: function to be inspected
    :param args: positional arguments to be bound
    :param kwargs: keyword arguments to be bound
    :return: `dict[argument_name] = argument_value` if binding was successful,
             raise TypeError with one of `ERR_*` error descriptions otherwise
    """
    res = {}
    arguments = func.__code__.co_varnames
    number_of_args = func.__code__.co_argcount
    number_of_pos_arguments = func.__code__.co_posonlyargcount
    number_of_kwonly_args = func.__code__.co_kwonlyargcount
    flag = int(func.__code__.co_flags)
    default_positional = func.__defaults__ or ()
    default_keyword = func.__kwdefaults__ or {}

    arg = None
    kwarg = None
    if flag & CO_VARARGS:
        arg = []
    if flag & CO_VARKEYWORDS:
        kwarg = {}
    for i in range(number_of_pos_arguments):
        if arguments[i] in kwargs:
            if kwarg is None:
                raise TypeError(ERR_POSONLY_PASSED_AS_KW)
    sz = len(args)
    for i in range(min(sz, number_of_args)):
        res[arguments[i]] = args[i]
    if sz > number_of_args:
        if arg is None:
            raise TypeError(ERR_TOO_MANY_POS_ARGS)
        for i in range(number_of_args, sz):
            arg.append(args[i])
    for i in range(number_of_pos_arguments, number_of_args):
        if arguments[i] in kwargs:
            if arguments[i] in res:
                raise TypeError(ERR_MULT_VALUES_FOR_ARG)
            res[arguments[i]] = kwargs[arguments[i]]
    if len(default_positional) > 0:
        default_start = number_of_args - len(default_positional)
        for i in range(default_start, number_of_args):
            if arguments[i] not in res:
                res[arguments[i]] = default_positional[i - default_start]
    for i in range(number_of_args):
        if arguments[i] not in res:
            raise TypeError(ERR_MISSING_POS_ARGS)
    kwonly_start = number_of_args
    for i in range(kwonly_start, kwonly_start + number_of_kwonly_args):
        if arguments[i] in kwargs:
            res[arguments[i]] = kwargs[arguments[i]]
        elif arguments[i] in default_keyword:
            res[arguments[i]] = default_keyword[arguments[i]]
        else:
            raise TypeError(ERR_MISSING_KWONLY_ARGS)
    all_named = set(arguments[number_of_pos_arguments : kwonly_start + number_of_kwonly_args])
    for key in kwargs:
        if key not in all_named:
            if kwarg is None:
                raise TypeError(ERR_TOO_MANY_KW_ARGS)
            kwarg[key] = kwargs[key]
    args_kwargs_start = number_of_args + number_of_kwonly_args
    if arg is not None:
        res[arguments[args_kwargs_start]] = tuple(arg)
        args_kwargs_start += 1
    if kwarg is not None:
        res[arguments[args_kwargs_start]] = kwarg
    return res

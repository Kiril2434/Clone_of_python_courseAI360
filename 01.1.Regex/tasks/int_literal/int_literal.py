import re


RE_INT_LITERAL = r'\s*((0[xX])?[0-9a-fA-F]+)((?=[-+*/\s])|$)'


def f_repr_int_literal(m: re.Match[str]) -> str:
    return m.group(1)


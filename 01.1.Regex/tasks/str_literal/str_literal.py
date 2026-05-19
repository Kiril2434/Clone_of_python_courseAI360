import re

RE_STR_LITERAL = r'\s*("(?:\\[nt\\"]|[^"\n\t\\])*"|\'(?:\\[nt\\\']|[^\'\n\t\\])*\')'

def f_repr_str_literal(m: re.Match[str]) -> str:
    return m.group(1)

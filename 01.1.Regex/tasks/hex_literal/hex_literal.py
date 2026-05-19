import re


RE_HEX_LITERAL = r'\s*(0[xX][0-9a-fA-F]+)((?=[-+*/\s])|$)'

def f_repr_hex_literal(m: re.Match[str]) -> str:
    return m.group(1)

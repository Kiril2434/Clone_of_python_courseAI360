import re
from dataclasses import dataclass


@dataclass
class FPLiteral:
    integral: str
    fractional: str
    exp: str | None

RE_FP_LITERAL = r'\s*(\d*)\.(\d*)((?=[eE])[eE]([+-]?\d+)((?=[-+*/])|$)|(?=[-+*/])|$)'


def f_repr_fp_literal(m: re.Match[str]) -> FPLiteral:
    return FPLiteral(m.group(1), m.group(2), m.group(4))

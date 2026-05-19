import re

UNQUOTED = r'(?:[^\s">/]|/(?!>))+'

ATTR = rf'\s+\w+(?:\s*=\s*(?:"[^"]*"|{UNQUOTED}))?'

HREF_ATTR = rf'\s+[hH][rR][eE][fF]\s*=\s*(?:"([^"]+)"|({UNQUOTED}))'

RE_A_HREF = rf'<[aA](?:{ATTR})*{HREF_ATTR}(?:{ATTR})*\s*/?>'

def f_link(m: re.Match[str]) -> str:
    return m.group(1) or m.group(2)

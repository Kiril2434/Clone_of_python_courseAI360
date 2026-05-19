import re

from hex_literal import RE_HEX_LITERAL, f_repr_hex_literal


def extract_token(s, regexp, f_repr):
    if m := re.match(regexp, s):
        return f_repr(m), s[m.span()[1] :]
    else:
        return None, s


def test_empty():
    tr, tail = extract_token("", RE_HEX_LITERAL, None)
    assert tr is None
    assert tail == ""


def test_blank():
    for i in range(1, 20):
        s = i * " "
        tr, tail = extract_token(s, RE_HEX_LITERAL, None)
        assert tr is None
        assert tail == s


def test_just_digits():
    for i in range(1, 100):
        s = str(i)
        tr, tail = extract_token(s, RE_HEX_LITERAL, None)
        assert tr is None
        assert tail == s


def test_just_prefix():
    for s in "0x", "0X":
        tr, tail = extract_token(s, RE_HEX_LITERAL, None)
        assert tr is None
        assert tail == s


def test_just_number():
    for p in "0x", "0X":
        for i in range(1, 100000):
            s = f"{p}{i:x}"
            tr, tail = extract_token(s, RE_HEX_LITERAL, f_repr_hex_literal)
            assert tr == s
            assert tail == ""


def test_number_after_space():
    for p in "0x", "0X":
        for i in range(1, 100000):
            s = f"{p}{i:x}"
            tr, tail = extract_token(" " + s, RE_HEX_LITERAL, f_repr_hex_literal)
            assert tr == s
            assert tail == ""


def test_space_after_number():
    for p in "0x", "0X":
        for i in range(1, 100000):
            s = f"{p}{i:x}"
            tr, tail = extract_token(" " + s + "   ", RE_HEX_LITERAL, f_repr_hex_literal)
            assert tr == s
            assert tail == "   "


def test_mixed_case():
    for p in "0x", "0X":
        for d1 in "0123456789abcdef":
            for d2 in "0123456789ABCDEF":
                s = f"{p}{d1}{d2}"
                tr, tail = extract_token(" " + s + "   ", RE_HEX_LITERAL, f_repr_hex_literal)
                assert tr == s
                assert tail == "   "


def test_arith_after_number():
    for nxt in "-+*/":
        for p in "0x", "0X":
            for i in range(1, 100000):
                s = f"{p}{i:x}"
                tr, tail = extract_token(" " + s + nxt, RE_HEX_LITERAL, f_repr_hex_literal)
                assert tr == s
                assert tail == nxt


def test_alpha_after_number():
    for nxt in "ghixGJX":
        for p in "0x", "0X":
            for i in range(1, 100000):
                s = f"{p}{i:x}{nxt}"
                tr, tail = extract_token(s, RE_HEX_LITERAL, None)
                assert tr is None
                assert tail == s

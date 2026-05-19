import re

from str_literal import RE_STR_LITERAL, f_repr_str_literal


def extract_token(s, regexp, f_repr):
    if m := re.match(regexp, s):
        return f_repr(m), s[m.span()[1] :]
    else:
        return None, s


def test_empty():
    tr, tail = extract_token("", RE_STR_LITERAL, None)
    assert tr is None
    assert tail == ""


def test_blank():
    for i in range(1, 20):
        s = i * " "
        tr, tail = extract_token(s, RE_STR_LITERAL, None)
        assert tr is None
        assert tail == s


def test_just_quote():
    for i in "'", '"':
        s = str(i)
        tr, tail = extract_token(s, RE_STR_LITERAL, None)
        assert tr is None
        assert tail == s


def test_different_quotes():
    for c1, c2 in ("'", '"'), ('"', "'"):
        for s in "", "abc", "~!@#$%^&":
            s = c1 + s + c2
            tr, tail = extract_token(s, RE_STR_LITERAL, None)
            assert tr is None
            assert tail == s


def test_same_quotes():
    for c in "'", '"':
        for s in "", "abc", "~!@#$%^&":
            s = c + s + c
            tr, tail = extract_token(s, RE_STR_LITERAL, f_repr_str_literal)
            assert tr == s
            assert tail == ""


def test_just_backslash():
    for c in "'", '"':
        s = c + "\\" + c
        tr, tail = extract_token(s, RE_STR_LITERAL, f_repr_str_literal)
        assert tr is None
        assert tail == s


def test_just_other_quote():
    for c1, c2 in ("'", '"'), ('"', "'"):
        s = c1 + c2 + c1
        tr, tail = extract_token(s, RE_STR_LITERAL, f_repr_str_literal)
        assert tr == s
        assert tail == ""


def test_two_other_quotes():
    for c1, c2 in ("'", '"'), ('"', "'"):
        s = c1 + c2 + c2 + c1
        tr, tail = extract_token(s, RE_STR_LITERAL, f_repr_str_literal)
        assert tr == s
        assert tail == ""


def test_tree_same_quotes():
    for c in "'", '"':
        s = 3 * c
        tr, tail = extract_token(s, RE_STR_LITERAL, f_repr_str_literal)
        assert tr == 2 * c
        assert tail == c


def test_q_bs_q_q():
    for c in "'", '"':
        s = c + "\\" + 2 * c
        tr, tail = extract_token(s, RE_STR_LITERAL, f_repr_str_literal)
        assert tr == s
        assert tail == ""


def test_many_bs():
    for i in range(1, 10):
        for c in "'", '"':
            for post_bs in c, "n", "t", "\\":
                s = c + i * ("\\" + post_bs) + c
                tr, tail = extract_token(s, RE_STR_LITERAL, f_repr_str_literal)
                assert tr == s
                assert tail == ""


def test_no_space_between():
    s = "'abc''c'"
    tr, tail = extract_token(s, RE_STR_LITERAL, f_repr_str_literal)
    assert tr == "'abc'"
    assert tail == "'c'"


def test_no_close_quote():
    s = "            'abc\\'"
    tr, tail = extract_token(s, RE_STR_LITERAL, f_repr_str_literal)
    assert tr is None
    assert tail == s


def test_double_inside_single():
    s = '\'""\'""'
    tr, tail = extract_token(s, RE_STR_LITERAL, f_repr_str_literal)
    assert tr == s[:4]
    assert tail == s[4:]


def test_ident_after_empty():
    s = "''abc"
    tr, tail = extract_token(s, RE_STR_LITERAL, f_repr_str_literal)
    assert tr == "''"
    assert tail == "abc"

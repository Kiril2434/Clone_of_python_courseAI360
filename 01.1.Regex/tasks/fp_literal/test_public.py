import re

from fp_literal import RE_FP_LITERAL, f_repr_fp_literal


def extract_token(s, regexp, f_repr):
    if m := re.match(regexp, s):
        return f_repr(m), s[m.span()[1] :]
    else:
        return None, s


def test_empty():
    tr, tail = extract_token("", RE_FP_LITERAL, None)
    assert tr is None
    assert tail == ""


def test_blank():
    for i in range(1, 20):
        s = i * " "
        tr, tail = extract_token(s, RE_FP_LITERAL, None)
        assert tr is None
        assert tail == s


def test_just_digits():
    for i in range(1, 100):
        s = str(i)
        tr, tail = extract_token(s, RE_FP_LITERAL, f_repr_fp_literal)
        assert tr is None
        assert tail == s


def test_just_digits_with_dot():
    for i in range(1, 100):
        s = str(i) + "."
        tr, tail = extract_token(s, RE_FP_LITERAL, f_repr_fp_literal)
        assert tr is not None
        assert tr.integral == str(i)
        assert tr.fractional == ""
        assert tr.exp is None
        assert tail == ""


def test_just_digits_with_double_dots():
    for i in range(1, 100):
        s = str(i) + ".."
        tr, tail = extract_token(s, RE_FP_LITERAL, None)
        assert tr is None
        assert tail == s


def test_just_digits_between_dots():
    for i in range(1, 100):
        s = "." + str(i) + "."
        tr, tail = extract_token(s, RE_FP_LITERAL, None)
        assert tr is None
        assert tail == s


def test_just_dot_with_digits():
    for i in range(1, 100):
        s = "." + str(i)
        tr, tail = extract_token(s, RE_FP_LITERAL, f_repr_fp_literal)
        assert tr is not None
        assert tr.integral == ""
        assert tr.fractional == str(i)
        assert tr.exp is None
        assert tail == ""


def test_just_double_dots_with_digits():
    for i in range(1, 100):
        s = ".." + str(i)
        tr, tail = extract_token(s, RE_FP_LITERAL, None)
        assert tr is None
        assert tail == s


def test_just_digits_dot_digits():
    for i in range(1, 100):
        for j in range(1, 1000):
            s = f"{i}.{j}"
            tr, tail = extract_token(s, RE_FP_LITERAL, f_repr_fp_literal)
            assert tr is not None
            assert tr.integral == str(i)
            assert tr.fractional == str(j)
            assert tr.exp is None
            assert tail == ""


def test_value_after_space():
    for i in range(1, 100):
        for j in range(10):
            s = str(1 / i * 10**j)
            tr, tail = extract_token(" " + s, RE_FP_LITERAL, f_repr_fp_literal)
            assert tr is not None
            exp_int, exp_frac = s.split(".", 2)
            assert tr.integral == exp_int
            assert tr.fractional == exp_frac
            assert tr.exp is None
            assert tail == ""


def test_space_after_value():
    for i in range(1, 100):
        for j in range(10):
            s = str(1 / i * 10**j)
            tr, tail = extract_token(" " + s, RE_FP_LITERAL, f_repr_fp_literal)
            assert tr is not None
            exp_int, exp_frac = s.split(".", 2)
            assert tr.integral == exp_int
            assert tr.fractional == exp_frac
            assert tr.exp is None
            assert tail == ""


def test_just_digits_dot_dot_digits():
    for i in range(1, 1000):
        for j in range(1, 100):
            s = f"{i}..{j}"
            tr, tail = extract_token(s, RE_FP_LITERAL, None)
            assert tr is None
            assert tail == s


def test_scientific():
    for i in range(1, 100):
        for j in range(1, 100):
            for k in range(1, 100):
                s = f"{i}.{j}e{k}"
                tr, tail = extract_token(s, RE_FP_LITERAL, f_repr_fp_literal)
                assert tr is not None
                assert tr.integral == str(i)
                assert tr.fractional == str(j)
                assert tr.exp == str(k)
                assert tail == ""


def test_scientific_minus():
    for i in range(1, 100):
        for j in range(1, 100):
            for k in range(1, 100):
                s = f"{i}.{j}e-{k}"
                tr, tail = extract_token(s, RE_FP_LITERAL, f_repr_fp_literal)
                assert tr is not None
                assert tr.integral == str(i)
                assert tr.fractional == str(j)
                assert tr.exp == str(-k)
                assert tail == ""


def test_scientific_double_minus():
    for i in range(1, 100):
        for j in range(1, 100):
            for k in range(1, 100):
                s = f"{i}.{j}e--{k}"
                tr, tail = extract_token(s, RE_FP_LITERAL, None)
                assert tr is None
                assert tail == s


def test_scientific_double_plus():
    for i in range(1, 100):
        for j in range(1, 100):
            for k in range(1, 100):
                s = f"{i}.{j}e++{k}"
                tr, tail = extract_token(s, RE_FP_LITERAL, None)
                assert tr is None
                assert tail == s


def test_scientific_space_minus():
    for i in range(1, 100):
        for j in range(1, 100):
            for k in range(1, 100):
                s = f"{i}.{j}e -{k}"
                tr, tail = extract_token(s, RE_FP_LITERAL, None)
                assert tr is None
                assert tail == s


def test_scientific_space_plus():
    for i in range(1, 100):
        for j in range(1, 100):
            for k in range(1, 100):
                s = f"{i}.{j}e +{k}"
                tr, tail = extract_token(s, RE_FP_LITERAL, None)
                assert tr is None
                assert tail == s


def test_scientific_minus_space():
    for i in range(1, 100):
        for j in range(1, 100):
            for k in range(1, 100):
                s = f"{i}.{j}e- {k}"
                tr, tail = extract_token(s, RE_FP_LITERAL, None)
                assert tr is None
                assert tail == s


def test_scientific_plus_space():
    for i in range(1, 100):
        for j in range(1, 100):
            for k in range(1, 100):
                s = f"{i}.{j}e+ {k}"
                tr, tail = extract_token(s, RE_FP_LITERAL, None)
                assert tr is None
                assert tail == s


def test_scientific_plus():
    for i in range(1, 100):
        for j in range(1, 100):
            for k in range(1, 100):
                s = f"{i}.{j}e+{k}"
                tr, tail = extract_token(s, RE_FP_LITERAL, f_repr_fp_literal)
                assert tr is not None
                assert tr.integral == str(i)
                assert tr.fractional == str(j)
                assert tr.exp == "+" + str(k)
                assert tail == ""


def test_arith_after_value():
    for nxt in "-+*/":
        for i in range(1, 10000):
            s = f"{i}."
            tr, tail = extract_token(" " + s + nxt, RE_FP_LITERAL, f_repr_fp_literal)
            assert tr is not None
            assert tr.integral == str(i)
            assert tr.fractional == ""
            assert tr.exp is None
            assert tail == nxt


def test_arith_after_value_2():
    for nxt in "-+*/":
        for i in range(1, 10000):
            s = f".{i}"
            tr, tail = extract_token(" " + s + nxt, RE_FP_LITERAL, f_repr_fp_literal)
            assert tr is not None
            assert tr.integral == ""
            assert tr.fractional == str(i)
            assert tr.exp is None
            assert tail == nxt


def test_alpha_after_number():
    for nxt in "ghixGJX":
        for i in range(1, 10000):
            for j in range(10):
                s = f"{i / 10**j}{nxt}"
                tr, tail = extract_token(s, RE_FP_LITERAL, None)
                assert tr is None
                assert tail == s

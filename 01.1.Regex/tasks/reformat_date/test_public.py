import re

from reformat import RE_DATE, RE_DATE_SUB


def sub_all(s):
    return re.sub(RE_DATE, RE_DATE_SUB, s)


def test_empty():
    result = sub_all("")
    assert result == ""


def test_blank():
    for i in range(1, 20):
        s = i * " "
        result = sub_all(s)
        assert result == s


def test_just_single_digit():
    for i in range(1, 10):
        s = str(i)
        result = sub_all(s)
        assert result == s


def test_just_two_digits():
    for i in range(1, 32):
        s = str(i)
        result = sub_all(s)
        assert result == s


def test_two_digits_dot():
    for i in range(1, 32):
        s = str(i) + "."
        result = sub_all(s)
        assert result == s


def test_two_digits_dot_digit():
    for i in range(1, 32):
        for j in range(1, 9):
            s = str(i) + "." + str(j)
            result = sub_all(s)
            assert result == s


def test_two_digits_dot_two_digits():
    for i in range(1, 32):
        for j in range(1, 13):
            s = str(i) + "." + str(j)
            result = sub_all(s)
            assert result == s


def test_two_digits_dot_two_digits_dot():
    for i in range(1, 32):
        for j in range(1, 13):
            s = str(i) + "." + str(j) + "."
            result = sub_all(s)
            assert result == s


def test_two_digits_dot_two_digits_dot_digit():
    for i in range(1, 32):
        for j in range(1, 13):
            for k in range(0, 10):
                s = str(i) + "." + str(j) + "." + str(k)
                result = sub_all(s)
                assert result == s


def test_two_digits_dot_two_digits_dot_two_digits():
    for i in range(1, 32):
        for j in range(1, 13):
            for k in range(0, 100):
                s = f"{i}.{j}.{k:02d}"
                print("s", s)
                result = sub_all(s)
                print("result", result)
                assert result == f"{j}/{i}/{k:02d}"


def test_two_digits_dot_two_digits_dot_3_digits():
    j = 0
    for i in range(1, 32):
        for k in range(0, 1000):
            j %= 12
            j += 1
            s = f"{i}.{j}.{k:03d}"
            result = sub_all(s)
            assert result == s


def test_two_digits_dot_two_digits_dot_4_digits():
    j = 0
    for i in range(1, 32):
        for k in range(1000, 3000):
            j %= 12
            j += 1
            s = f"{i}.{j}.{k:04d}"
            print("s", s)
            result = sub_all(s)
            print("result", result)
            assert result == f"{j}/{i}/{k:04d}"


def test_two_digits_dot_two_digits_dot_5_digits():
    j = 0
    for i in range(1, 32):
        for k in range(1000, 3000):
            j %= 12
            j += 1
            s = f"{i}.{j}.{k:05d}"
            print("s", s)
            result = sub_all(s)
            print("result", result)
            assert result == s


def test_two_digits_dot_two_digits_dot_5_digits_2():
    j = 0
    for i in range(1, 32):
        for k in range(1000, 3000):
            j %= 12
            j += 1
            s = f"{i}.{j}.{k:04d}0"
            print("s", s)
            result = sub_all(s)
            print("result", result)
            assert result == s


def test_two_digits_dot_two_digits_dot_4_digits_not_dots():
    j = 0
    for i in range(1, 32):
        for k in range(1000, 3000):
            j %= 12
            j += 1
            s = f"{i}/{j}/{k:04d}"
            print("s", s)
            result = sub_all(s)
            print("result", result)
            assert result == s


def test_two_digits_dot_two_digits_dot_4_digits_space_after():
    j = 0
    for i in range(1, 32):
        for k in range(1000, 3000):
            j %= 12
            j += 1
            s = f"{i}.{j}.{k:04d} "
            print("s", s)
            result = sub_all(s)
            print("result", result)
            assert result == f"{j}/{i}/{k:04d} "


def test_two_digits_dot_two_digits_dot_4_digits_space_before():
    j = 0
    for i in range(1, 32):
        for k in range(1000, 3000):
            j %= 12
            j += 1
            s = f" {i}.{j}.{k:04d}"
            print("s", s)
            result = sub_all(s)
            print("result", result)
            assert result == f" {j}/{i}/{k:04d}"


def test_two_digits_dot_two_digits_dot_4_digits_comma_before_space_after():
    j = 0
    for i in range(1, 32):
        for k in range(1000, 3000):
            j %= 12
            j += 1
            s = f",{i}.{j}.{k:04d} "
            print("s", s)
            result = sub_all(s)
            print("result", result)
            assert result == f",{j}/{i}/{k:04d} "


def test_two_digits_dot_two_digits_dot_4_digits_comma_before_semicolon_after():
    j = 0
    for i in range(1, 32):
        for k in range(1000, 3000):
            j %= 12
            j += 1
            s = f",{i}.{j}.{k:04d};"
            print("s", s)
            result = sub_all(s)
            print("result", result)
            assert result == f",{j}/{i}/{k:04d};"


def test_two_digits_dot_two_digits_dot_4_digits_in_parens():
    j = 0
    for i in range(1, 32):
        for k in range(1000, 3000):
            j %= 12
            j += 1
            s = f"({i}.{j}.{k:04d})"
            print("s", s)
            result = sub_all(s)
            print("result", result)
            assert result == f"({j}/{i}/{k:04d})"


def test_two_digits_dot_two_digits_dot_4_digits_in_parens_same_direction():
    j = 0
    for i in range(1, 32):
        for k in range(1000, 3000):
            j %= 12
            j += 1
            s = f"({i}.{j}.{k:04d}("
            print("s", s)
            result = sub_all(s)
            print("result", result)
            assert result == s


def test_two_dates_with_space():
    s = "30.11.2012 1.9.1998"
    result = sub_all(s)
    assert result == "11/30/2012 9/1/1998"


def test_two_dates_with_double_space():
    s = "30.11.2012  1.9.1998"
    result = sub_all(s)
    assert result == "11/30/2012  9/1/1998"


def test_two_dates_with_no_space():
    s = "30.11.20121.9.1998"
    result = sub_all(s)
    assert result == s


def test_many_dates_with_single_comma():
    s = 100 * ["30.11.2012"]
    result = sub_all(",".join(s))
    assert result == ",".join(100 * ["11/30/2012"])

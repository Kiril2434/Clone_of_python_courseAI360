import re

from palindrome_num import RE_PALINDROME_NUM


def find_all(s, regexp):
    return [e.group(0) for e in re.finditer(regexp, s)]


def test_empty():
    found = find_all("", RE_PALINDROME_NUM)
    assert found == []


def test_blank():
    for i in range(1, 20):
        s = i * " "
        found = find_all(s, RE_PALINDROME_NUM)
        assert found == []


def test_just_single_digit():
    for i in range(0, 10):
        s = str(i)
        found = find_all(s, RE_PALINDROME_NUM)
        assert found == [s]


def test_spaces_single_digit():
    for i in range(0, 10):
        for j in range(1, 20):
            for k in range(1, 20):
                s = (j * " ") + str(i) + (k * " ")
                found = find_all(s, RE_PALINDROME_NUM)
                assert found == [str(i)]


def test_digit_letter():
    for i in range(0, 10):
        for j in range(1, 20):
            for k in range(1, 20):
                s = (j * " ") + str(i) + "a" + (k * " ")
                found = find_all(s, RE_PALINDROME_NUM)
                assert found == []


def test_sign_digit():
    for i in range(0, 10):
        for j in range(1, 20):
            for k in range(1, 20):
                for sgn in "-+":
                    s = (j * " ") + sgn + str(i) + (k * " ")
                    print(s)
                    found = find_all(s, RE_PALINDROME_NUM)
                    assert found == []


def test_just_two_digits_palindrome():
    for i in range(0, 10):
        s = f"{i}{i}"
        found = find_all(s, RE_PALINDROME_NUM)
        assert found == [s]


def test_just_two_digits_non_palindrome():
    for i in range(0, 10):
        for j in range(0, 10):
            if i == j:
                continue
            s = f"{i}{j}"
            found = find_all(s, RE_PALINDROME_NUM)
            assert found == []


def test_two_digits_palindrome_with_spaces():
    for i in range(0, 10):
        for j in range(1, 20):
            for k in range(1, 20):
                s = (i * " ") + f"{i}{i}" + (j * " ")
                found = find_all(s, RE_PALINDROME_NUM)
                assert found == [f"{i}{i}"]


def test_digit_double_space_digit():
    for i in range(0, 10):
        for j in range(0, 10):
            s = f"{i}  {j}"
            found = find_all(s, RE_PALINDROME_NUM)
            assert found == [str(i), str(j)]


def test_digit_single_space_digit():
    for i in range(0, 10):
        for j in range(0, 10):
            s = f"{i} {j}"
            found = find_all(s, RE_PALINDROME_NUM)
            assert found == [str(i), str(j)]


def test_digit_single_plus_digit():
    for i in range(0, 10):
        for j in range(0, 10):
            s = f"{i}+{j}"
            found = find_all(s, RE_PALINDROME_NUM)
            assert found == []


def test_3_digits():
    for i in range(0, 1000):
        s = f"{i:03d}"
        found = find_all(s, RE_PALINDROME_NUM)
        if s == s[::-1]:
            assert found == [s]
        else:
            assert found == []


def test_3_digits_all():
    nums = [str(i) for i in range(0, 1000)]
    expected = [s for s in nums if s == s[::-1]]
    found = find_all(" ".join(nums), RE_PALINDROME_NUM)
    assert expected == found


def test_4_digits():
    for i in range(0, 10000):
        s = f"{i:04d}"
        found = find_all(s, RE_PALINDROME_NUM)
        if s == s[::-1]:
            assert found == [s]
        else:
            assert found == []


def test_4_digits_all():
    nums = [str(i) for i in range(0, 10000)]
    expected = [s for s in nums if s == s[::-1]]
    found = find_all(" ".join(nums), RE_PALINDROME_NUM)
    assert expected == found


def test_5_digits():
    for i in range(0, 100000):
        s = f"{i:05d}"
        found = find_all(s, RE_PALINDROME_NUM)
        if s == s[::-1]:
            assert found == [s]
        else:
            assert found == []


def test_5_digits_all():
    nums = [str(i) for i in range(0, 100000)]
    expected = [s for s in nums if s == s[::-1]]
    found = find_all(" ".join(nums), RE_PALINDROME_NUM)
    assert expected == found

import dataclasses
import dis
import io
from typing import Any, Callable
import sys

import pytest

import byteme


@dataclasses.dataclass
class Case:
    func: Callable[..., Any]
    expected_dis_out: str

    def __str__(self) -> str:
        return self.func.__name__


TEST_CASES = [
    Case(
        func=byteme.f0,
        expected_dis_out='''\
  0       RESUME                   0
  2       RETURN_CONST             0 (None)
'''
    ),
    Case(
        func=byteme.f1,
        expected_dis_out='''\
  0       RESUME                   0
  2       LOAD_CONST               1 (0)
  4       STORE_FAST               0 (a)
  6       LOAD_FAST                0 (a)
  8       RETURN_VALUE
'''
    ),
    Case(
        func=byteme.f2,
        expected_dis_out='''\
  0       RESUME                   0
  2       LOAD_CONST               1 (0)
  4       STORE_FAST               0 (a)
  6       LOAD_GLOBAL              1 (print + NULL)
 16       LOAD_FAST                0 (a)
 18       CALL                     1
 26       POP_TOP
 28       RETURN_CONST             0 (None)
'''
    ),
    Case(
        func=byteme.f3,
        expected_dis_out='''\
  0       RESUME                   0
  2       LOAD_CONST               1 (0)
  4       STORE_FAST               0 (a)
  6       LOAD_FAST                0 (a)
  8       LOAD_CONST               2 (1)
 10       BINARY_OP               13 (+=)
 14       STORE_FAST               0 (a)
 16       LOAD_GLOBAL              1 (print + NULL)
 26       LOAD_FAST                0 (a)
 28       CALL                     1
 36       POP_TOP
 38       RETURN_CONST             0 (None)
'''
    ),
    Case(
        func=byteme.f4,
        expected_dis_out='''\
  0       RESUME                   0
  2       LOAD_GLOBAL              1 (range + NULL)
 12       LOAD_CONST               1 (10)
 14       CALL                     1
 22       RETURN_VALUE
'''
    ),
    Case(
        func=byteme.f5,
        expected_dis_out='''\
  0       RESUME                   0
  2       LOAD_GLOBAL              1 (range + NULL)
 12       LOAD_CONST               1 (10)
 14       CALL                     1
 22       GET_ITER
 24       FOR_ITER                14 (to L2)
 28       STORE_FAST               0 (i)
 30       LOAD_GLOBAL              3 (print + NULL)
 40       LOAD_FAST                0 (i)
 42       CALL                     1
 50       POP_TOP
 52       JUMP_BACKWARD           16 (to L1)
 56       END_FOR
 58       POP_TOP
 60       RETURN_CONST             0 (None)
'''
    ),
    Case(
        func=byteme.f6,
        expected_dis_out='''\
  0       RESUME                   0
  2       LOAD_CONST               1 (0)
  4       STORE_FAST               0 (a)
  6       LOAD_GLOBAL              1 (range + NULL)
 16       LOAD_CONST               2 (10)
 18       CALL                     1
 26       GET_ITER
 28       FOR_ITER                 8 (to L2)
 32       STORE_FAST               1 (i)
 34       LOAD_FAST                0 (a)
 36       LOAD_CONST               3 (1)
 38       BINARY_OP               13 (+=)
 42       STORE_FAST               0 (a)
 44       JUMP_BACKWARD           10 (to L1)
 48       END_FOR
 50       POP_TOP
 52       LOAD_GLOBAL              3 (print + NULL)
 62       LOAD_FAST                0 (a)
 64       CALL                     1
 72       POP_TOP
 74       RETURN_CONST             0 (None)
'''
    ),
    Case(
        func=byteme.f8,
        expected_dis_out='''\
  0       RESUME                   0
  2       LOAD_CONST               1 ((1, 2))
  4       UNPACK_SEQUENCE          2
  8       STORE_FAST_STORE_FAST    1 (x, y)
 10       RETURN_CONST             0 (None)
'''
    ),
    Case(
        func=byteme.f9,
        expected_dis_out='''\
  0       RESUME                   0
  2       LOAD_CONST               1 (1)
  4       LOAD_CONST               1 (1)
  6       COMPARE_OP              88 (bool(==))
 10       POP_JUMP_IF_FALSE        2 (to L1)
 14       LOAD_CONST               1 (1)
 16       RETURN_VALUE
 18       LOAD_CONST               2 (2)
 20       RETURN_VALUE
'''
    ),
    Case(
        func=byteme.f10,
        expected_dis_out='''\
  0       RESUME                   0
  2       LOAD_GLOBAL              1 (range + NULL)
 12       LOAD_CONST               1 (10)
 14       CALL                     1
 22       GET_ITER
 24       FOR_ITER                11 (to L3)
 28       STORE_FAST               0 (i)
 30       LOAD_FAST                0 (i)
 32       LOAD_CONST               2 (3)
 34       COMPARE_OP              88 (bool(==))
 38       POP_JUMP_IF_TRUE         2 (to L2)
 42       JUMP_BACKWARD           11 (to L1)
 46       POP_TOP
 48       RETURN_CONST             0 (None)
 50       END_FOR
 52       POP_TOP
 54       RETURN_CONST             0 (None)
'''
    ),
    Case(
        func=byteme.f11,
        expected_dis_out='''\
  0       RESUME                   0
  2       BUILD_LIST               0
  4       LOAD_CONST               1 ((1, 2, 3))
  6       LIST_EXTEND              1
  8       STORE_FAST               0 (list_)
 10       LOAD_CONST               2 (1)
 12       LOAD_CONST               3 (2)
 14       LOAD_CONST               4 (('a', 'b'))
 16       BUILD_CONST_KEY_MAP      2
 18       STORE_FAST               1 (dict_)
 20       LOAD_FAST_LOAD_FAST      1 (list_, dict_)
 22       BUILD_TUPLE              2
 24       RETURN_VALUE
'''
    ),
    Case(
        func=byteme.f12,
        expected_dis_out='''\
  0       RESUME                   0
  2       LOAD_CONST               1 (1)
  4       STORE_FAST               0 (a)
  6       LOAD_CONST               2 (2)
  8       STORE_FAST               1 (b)
 10       LOAD_CONST               3 (3)
 12       STORE_FAST               2 (c)
 14       LOAD_CONST               4 (4)
 16       STORE_FAST               3 (d)
 18       LOAD_CONST               5 (5)
 20       STORE_FAST               4 (e)
 22       LOAD_FAST_LOAD_FAST      1 (a, b)
 24       LOAD_FAST                2 (c)
 26       BINARY_OP                5 (*)
 30       LOAD_FAST_LOAD_FAST     52 (d, e)
 32       BINARY_OP                8 (**)
 36       BINARY_OP               11 (/)
 40       BINARY_OP                0 (+)
 44       RETURN_VALUE
'''
    ),
]


def test_version() -> None:
    """
    To do this task you need python=3.13.7
    """
    assert '3.13.7' == sys.version.split(' ', maxsplit=1)[0]


def strip_dis_out(dis_out: str) -> str:
    """Strip first 11 chars from dis_out and remove empty lines"""
    return '\n'.join(line[11:] for line in dis_out.split('\n') if line) + '\n'


@pytest.mark.parametrize('t', TEST_CASES, ids=str)
def test_byteme(t: Case) -> None:
    out = io.StringIO()
    dis.dis(t.func, file=out, show_offsets=True)
    actual_dis_out = out.getvalue()
    print(actual_dis_out)
    assert strip_dis_out(actual_dis_out) == t.expected_dis_out

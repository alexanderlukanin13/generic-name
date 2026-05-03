from typing import Generic, TypeVar, ClassVar

from genericname import generic_args_to_classvar

T = TypeVar('T')

@generic_args_to_classvar
class A(Generic[T]):
    _T: ClassVar[type[T]]
    value: T

    def __init__(self):
        self.value = self._T()

class B(A[int]):
    pass


class C(A[list]):
    pass


def test_simple_v_hierarchy():
    assert B._T is int
    assert B().value == 0

    assert C._T is list
    assert C().value == []

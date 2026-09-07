from typing import Generic, TypeVar, ClassVar

from genericname import generic_args_to_classvar

T = TypeVar('T')
U = TypeVar('U')


def test_simple_v_hierarchy():
    @generic_args_to_classvar(classes='subclasses')
    class A(Generic[T]):
        _T: ClassVar[type[T]]
        value: T

        def __init__(self):
            self.value = self._T()

    class B(A[int]):
        pass

    class C(A[list]):
        pass

    assert not hasattr(A, '_T')

    assert B._T is int
    assert B().value == 0

    assert C._T is list
    assert C().value == []


def test_simple_diamond_hierarchy():
    @generic_args_to_classvar(classes='subclasses')
    class A(Generic[T]):
        _T: ClassVar[type[T]]
        value: T

        def __init__(self):
            self.value = self._T()

    class B(A[int]):
        pass

    class C(A[int]):
        pass

    class D(B, C):
        pass

    assert not hasattr(A, '_T')

    assert B._T is int
    assert B().value == 0

    assert C._T is int
    assert C().value == 0

    assert D._T is int
    assert D().value == 0

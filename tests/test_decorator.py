from re import escape as esc
from typing import Generic, TypeVar, ClassVar

import pytest

from genericname import generic_args_to_classvar, ConflictingTypesError

T = TypeVar('T')
U = TypeVar('U')


def test_simple_v_hierarchy():
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

    assert not hasattr(A, '_T')

    assert B._T is int
    assert B().value == 0

    assert C._T is list
    assert C().value == []


def test_simple_diamond_hierarchy():
    @generic_args_to_classvar
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


def test_simple_diamond_hierarchy_conflict():
    @generic_args_to_classvar
    class A(Generic[T]):
        _T: ClassVar[type[T]]
        value: T

        def __init__(self):
            self.value = self._T()

    class B(A[int]):
        pass

    class C(A[float]):
        pass

    with pytest.raises(ConflictingTypesError, match=r"Conflicting types in class variable .*\.D\._T: "
                                                    r"trying to assign _T=<class 'float'> from generic parameter T, "
                                                    r"but the variable already exists and has a distinct value "
                                                    r"_T=<class 'int'>"):
        class D(B, C):
            pass


def test_simple_multi_inheritance():
    @generic_args_to_classvar
    class A(Generic[T]):
        _T: ClassVar[type[T]]
        value: T

        def __init__(self):
            self.value = self._T()

    @generic_args_to_classvar
    class B(Generic[U]):
        _U: ClassVar[type[U]]
        value2: U

        def __init__(self):
            self.value2 = self._U()

    class C(A[int], B[float]):
        pass

    assert not hasattr(A, '_T')
    assert not hasattr(A, '_U')
    assert not hasattr(B, '_T')
    assert not hasattr(B, '_U')
    assert C._T is int
    print(dir(C))
    assert C._U is float
    c = C()
    assert isinstance(c.value, int)
    assert c.value == 0
    assert isinstance(c.value2, float)
    assert c.value2 == 0.0


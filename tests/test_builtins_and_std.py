import collections.abc as cabc
from typing import TypeVar, Generic, ClassVar

import pytest

from genericname import iter_generic_args, generic_args_to_classvar, get_generic_args

T = TypeVar('T')
U = TypeVar('U')


def test_list():
    # list -> no args
    # list[int] -> exception, not a type
    assert list(iter_generic_args(list)) == []
    with pytest.raises(TypeError, match=r"Expected an instance of type, not 'GenericAlias'"):
        list(iter_generic_args(list[int]))


def test_list_1():
    # Simple class based on builtin generic type
    class A(list[int]):
        pass

    # In class A, typevar T_co becomes int
    assert list(iter_generic_args(A)) == [(A, 'T_co', int)]


def test_list_2():
    class A(list[int]):
        pass

    class B(A):
        pass

    # In class A, typevar T_co becomes int
    assert list(iter_generic_args(B)) == [(A, 'T_co', int)]


def test_list_3():
    class A(list[T], Generic[T]):
        pass

    assert list(iter_generic_args(A)) == []

    class B(A[int]):
        pass

    # In class B, typevar T becomes int
    assert list(iter_generic_args(B)) == [(B, 'T', int)]


def test_list_4():
    class A(list[T], Generic[T]):
        pass

    class B(A[T], Generic[T]):
        pass

    class C(B[int]):
        pass

    assert list(iter_generic_args(C)) == [(C, 'T', int)]

def test_list_5():
    class A(list[T], Generic[T]):
        pass

    class B(A[T], Generic[T]):
        pass

    class C(B[int]):
        pass

    class D(C):
        pass

    assert list(iter_generic_args(D)) == [(C, 'T', int)]

def test_Collection():
    @generic_args_to_classvar
    class A(cabc.Collection[T], Generic[T]):
        _T: ClassVar[type[T]]

        def __contains__(self, value: T):
            return False

        def __iter__(self):
            raise StopIteration

        def __len__(self):
            return 0

    class B(A[int]):
        pass

    assert not hasattr(A, '_T')
    assert B._T is int

    assert get_generic_args(A) == []
    assert get_generic_args(B) == [(B, 'T', int)]


@pytest.mark.parametrize("cls", [
    list,
    set,
    frozenset,
    cabc.Container,
    cabc.Collection,
    cabc.Iterable,
    cabc.Iterator,
    cabc.MutableSequence,
    cabc.MutableSet,
    cabc.Reversible,
    cabc.Sequence,
    cabc.Set,
])
def test_base_class(cls):
    @generic_args_to_classvar
    class A(cls[T], Generic[T]):
        _T: ClassVar[type[T]]

    class B(A[int]):
        pass

    assert B._T is int

# AsyncGenerator, AsyncIterator, AsyncIterable, cabc.Awaitable

@pytest.mark.parametrize("cls", [
    dict,
    cabc.Mapping,
    cabc.MutableMapping,

])
def test_base_class_mapping(cls):
    @generic_args_to_classvar
    class A(cls[T], Generic[T]):
        _T: ClassVar[type[T]]

    class B(A[int]):
        pass

    assert B._T is int

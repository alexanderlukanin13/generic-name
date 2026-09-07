from typing import Generic, TypeVar

import pytest

from genericname import iter_generic_args, get_generic_args_for_base, NoGenericArgsError, \
    get_generic_args_for_subclasses

T = TypeVar('T')
U = TypeVar('U')

def test_get_generic_args_simple():
    class A(Generic[T]):
        pass

    assert list(iter_generic_args(A)) == []
    assert get_generic_args_for_base(A, A) == {}
    assert get_generic_args_for_subclasses(A, A) == {}

    class B(A[T], Generic[T]):
        pass

    assert list(iter_generic_args(B)) == []
    assert get_generic_args_for_base(B, A) == {}
    assert get_generic_args_for_subclasses(B, A) == {}

    class C(B[int]):
        pass

    assert list(iter_generic_args(C)) == [(C, 'T', int)]
    assert get_generic_args_for_base(C, A) == {'T': int}
    assert get_generic_args_for_base(C, B) == {'T': int}
    assert get_generic_args_for_subclasses(C, A) == {'T': int}

    assert get_generic_args_for_subclasses(C, B) == {'T': int}
    with pytest.raises(NoGenericArgsError, match=r'Class test_get_generic_args_simple.<locals>.C has no generic parameters'):
        get_generic_args_for_base(C, C)

    class D(C):
        pass

    assert list(iter_generic_args(D)) == [(C, 'T', int)]
    assert get_generic_args_for_base(D, A) == {'T': int}
    assert get_generic_args_for_subclasses(D, A) == {'T': int}
    assert get_generic_args_for_base(D, B) == {'T': int}
    assert get_generic_args_for_subclasses(D, B) == {'T': int}
    with pytest.raises(NoGenericArgsError):
        get_generic_args_for_base(D, C)
    with pytest.raises(NoGenericArgsError):
        get_generic_args_for_base(D, D)
    with pytest.raises(NoGenericArgsError):
        get_generic_args_for_subclasses(D, C)
    with pytest.raises(NoGenericArgsError):
        get_generic_args_for_subclasses(D, D)

    class E(A[int]):
        pass

    assert list(iter_generic_args(E)) == [(E, 'T', int)]
    assert get_generic_args_for_base(E, A) == {'T': int}
    assert get_generic_args_for_subclasses(E, A) == {'T': int}
    with pytest.raises(NoGenericArgsError):
        get_generic_args_for_base(E, E)
    with pytest.raises(NoGenericArgsError):
        get_generic_args_for_subclasses(E, E)


def test_repeating_name_diff_type():

    class A(Generic[T]):
        pass

    assert list(iter_generic_args(A)) == []

    class B(A[int]):
        pass

    assert list(iter_generic_args(B)) == [(B, 'T', int)]

    class C(B, Generic[T]):
        pass

    assert list(iter_generic_args(C)) == [(B, 'T', int)]

    class D(C[float]):
        pass

    assert list(iter_generic_args(D)) == [(B, 'T', int), (D, 'T', float)]


def test_get_generic_args_for_base_and_subclasses():
    class A(Generic[T]):
        pass

    class B(A[int]):
        pass

    class C(B, Generic[U]):
        pass

    class D(C[float]):
        pass

    assert get_generic_args_for_base(D, A) == {'T': int}
    assert get_generic_args_for_subclasses(D, A) == {'T': int, 'U': float}

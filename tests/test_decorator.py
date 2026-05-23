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
            super().__init__()
            self.value = self._T()

    @generic_args_to_classvar
    class B(Generic[U]):
        _U: ClassVar[type[U]]
        value2: U

        def __init__(self):
            super().__init__()
            self.value2 = self._U()

    class C(A[int], B[float]):
        pass

    assert not hasattr(A, '_T')
    assert not hasattr(A, '_U')
    assert not hasattr(B, '_T')
    assert not hasattr(B, '_U')
    assert C._T is int
    assert C._U is float
    c = C()
    assert isinstance(c.value, int)
    assert c.value == 0
    assert isinstance(c.value2, float)
    assert c.value2 == 0.0


def test_simple_multi_inheritance_A_init_subclass():
    @generic_args_to_classvar
    class A(Generic[T]):
        _T: ClassVar[type[T]]
        value: T
        a_init_fired: ClassVar[bool]

        def __init__(self):
            super().__init__()
            self.value = self._T()

        def __init_subclass__(cls, **kwargs):
            super().__init_subclass__(**kwargs)
            cls.a_init_fired = True

    @generic_args_to_classvar
    class B(Generic[U]):
        _U: ClassVar[type[U]]
        value2: U

        def __init__(self):
            super().__init__()
            self.value2 = self._U()

    class C(A[int], B[float]):
        pass

    assert not hasattr(A, '_T')
    assert not hasattr(A, '_U')
    assert C.a_init_fired is True
    assert not hasattr(B, '_T')
    assert not hasattr(B, '_U')
    assert C._T is int
    assert C._U is float
    c = C()
    assert isinstance(c.value, int)
    assert c.value == 0
    assert isinstance(c.value2, float)
    assert c.value2 == 0.0


def test_simple_multi_inheritance_B_init_subclass():
    @generic_args_to_classvar
    class A(Generic[T]):
        _T: ClassVar[type[T]]
        value: T

        def __init__(self):
            super().__init__()
            self.value = self._T()

    @generic_args_to_classvar
    class B(Generic[U]):
        _U: ClassVar[type[U]]
        value2: U
        b_init_fired: ClassVar[bool]

        def __init__(self):
            super().__init__()
            self.value2 = self._U()

        def __init_subclass__(cls, **kwargs):
            super().__init_subclass__(**kwargs)
            cls.b_init_fired = True

    class C(A[int], B[float]):
        pass

    assert not hasattr(A, '_T')
    assert not hasattr(A, '_U')
    assert not hasattr(B, '_T')
    assert not hasattr(B, '_U')
    assert C.b_init_fired is True
    assert C._T is int
    assert C._U is float
    c = C()
    assert isinstance(c.value, int)
    assert c.value == 0
    assert isinstance(c.value2, float)
    assert c.value2 == 0.0


def test_simple_multi_inheritance_both_init_subclass():
    @generic_args_to_classvar
    class A(Generic[T]):
        _T: ClassVar[type[T]]
        value: T
        a_init_fired: ClassVar[bool]

        def __init__(self):
            super().__init__()
            self.value = self._T()

        def __init_subclass__(cls, **kwargs):
            super().__init_subclass__(**kwargs)
            cls.a_init_fired = True

    @generic_args_to_classvar
    class B(Generic[U]):
        _U: ClassVar[type[U]]
        value2: U
        b_init_fired: ClassVar[bool]

        def __init__(self):
            super().__init__()
            self.value2 = self._U()

        def __init_subclass__(cls, **kwargs):
            super().__init_subclass__(**kwargs)
            cls.b_init_fired = True

    class C(A[int], B[float]):
        pass

    assert not hasattr(A, '_T')
    assert not hasattr(A, '_U')
    assert C.a_init_fired is True
    assert not hasattr(B, '_T')
    assert not hasattr(B, '_U')
    assert C.b_init_fired is True
    assert C._T is int
    assert C._U is float
    c = C()
    assert isinstance(c.value, int)
    assert c.value == 0
    assert isinstance(c.value2, float)
    assert c.value2 == 0.0


def test_simple_multi_inheritance_different_kwargs():
    @generic_args_to_classvar
    class A(Generic[T]):
        _T: ClassVar[type[T]]
        value: T
        a_arg: ClassVar[str]

        def __init__(self):
            super().__init__()
            self.value = self._T()

        def __init_subclass__(cls, a_arg, **kwargs):
            super().__init_subclass__(**kwargs)
            cls.a_arg = a_arg

    @generic_args_to_classvar
    class B(Generic[U]):
        _U: ClassVar[type[U]]
        value2: U
        b_arg: ClassVar[str]

        def __init__(self):
            super().__init__()
            self.value2 = self._U()

        def __init_subclass__(cls, b_arg, **kwargs):
            super().__init_subclass__(**kwargs)
            cls.b_arg = b_arg

    class C(A[int], B[float], a_arg='this is a', b_arg='this is b'):
        pass

    assert not hasattr(A, '_T')
    assert not hasattr(A, '_U')
    assert C.a_arg == 'this is a'
    assert not hasattr(B, '_T')
    assert not hasattr(B, '_U')
    assert C.b_arg == 'this is b'
    assert C._T is int
    assert C._U is float
    c = C()
    assert isinstance(c.value, int)
    assert c.value == 0
    assert isinstance(c.value2, float)
    assert c.value2 == 0.0


def test_simple_multi_inheritance_A_kwargs():
    @generic_args_to_classvar
    class A(Generic[T]):
        _T: ClassVar[type[T]]
        value: T
        a_arg: ClassVar[str]

        def __init__(self):
            super().__init__()
            self.value = self._T()

        def __init_subclass__(cls, a_arg, **kwargs):
            super().__init_subclass__(**kwargs)
            cls.a_arg = a_arg

    @generic_args_to_classvar
    class B(Generic[U]):
        _U: ClassVar[type[U]]
        value2: U

        def __init__(self):
            super().__init__()
            self.value2 = self._U()

    class C(A[int], B[float], a_arg='this is a'):
        pass

    assert not hasattr(A, '_T')
    assert not hasattr(A, '_U')
    assert C.a_arg == 'this is a'
    assert not hasattr(B, '_T')
    assert not hasattr(B, '_U')
    assert C._T is int
    assert C._U is float
    c = C()
    assert isinstance(c.value, int)
    assert c.value == 0
    assert isinstance(c.value2, float)
    assert c.value2 == 0.0


def test_simple_multi_inheritance_B_kwargs():
    @generic_args_to_classvar
    class A(Generic[T]):
        _T: ClassVar[type[T]]
        value: T

        def __init__(self):
            super().__init__()
            self.value = self._T()

    @generic_args_to_classvar
    class B(Generic[U]):
        _U: ClassVar[type[U]]
        value2: U
        b_arg: ClassVar[str]

        def __init__(self):
            super().__init__()
            self.value2 = self._U()

        def __init_subclass__(cls, b_arg=None, **kwargs):
            super().__init_subclass__(**kwargs)
            cls.b_arg = b_arg

    class C(A[int], B[float], b_arg='this is b'):
        pass

    assert not hasattr(A, '_T')
    assert not hasattr(A, '_U')
    assert not hasattr(B, '_T')
    assert not hasattr(B, '_U')
    assert C.b_arg == 'this is b'
    assert C._T is int
    assert C._U is float
    c = C()
    assert isinstance(c.value, int)
    assert c.value == 0
    assert isinstance(c.value2, float)
    assert c.value2 == 0.0


def test_long_multi_inheritance():
    @generic_args_to_classvar
    class A(Generic[T]):
        _T: ClassVar[type[T]]
        value: T

        def __init__(self):
            super().__init__()
            self.value = self._T()

    @generic_args_to_classvar
    class B(Generic[U]):
        _U: ClassVar[type[U]]
        value2: U

        def __init__(self):
            super().__init__()
            self.value2 = self._U()

    class A2(A[int]):
        pass

    class B2(B[float]):
        pass

    class C(A2, B2):
        pass

    assert not hasattr(A, '_T') and not hasattr(A, '_U')
    assert not hasattr(B, '_T') and not hasattr(B, '_U')
    assert A2._T is int
    assert B2._U is float
    assert C._T is int and C._U is float
    c = C()
    assert isinstance(c.value, int)
    assert c.value == 0
    assert isinstance(c.value2, float)
    assert c.value2 == 0.0

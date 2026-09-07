============
generic-name
============
You need a specialization of generic base class with ``@generic_args_to_classvar``,
you can't work with the base class directly like this:

..code-block:: python

    >>> from genericname import generic_args_to_classvar
    >>> @generic_args_to_classvar
    ... class A[T]:
    ...     _T: ClassVar[T]
    ...     _value: T
    ...
    ...     def __init__(self, value: T):
    ...         self._value = value
    ...
    >>> a: A[int] = A(1)
    >>> assert a._value == 1
    >>> assert a._T is int
    Traceback (most recent call last):
      File "<python-input-5>", line 1, in <module>
        assert a._T is int
               ^^^^
    AttributeError: 'A' object has no attribute '_T'

Limitations
-----------

Treat any class with ``@generic_args_to_classvar`` as abstract; or even better, make it an abstract class explicitly.
Remember, ``_T`` is only set in specialized (non-generic) subclasses of it.

It works with plain, normal classes, including multiple inheritance and diamond-shaped class hierarchies.
But it may not mix well with advanced class manipulations, such as metaclasses, changing ``__mro__``, etc.
Test such scenarios carefully.

If you override ``__init_subclass__``, you MUST call ``super().__init_subclass__``.

Generic classes that are not implemented in pure Python may not be recognized as generic and you won't see their
parameters.

Many builtin and standard library generic types are supported, such as ``list[T]``, ``dict[T]``, etc.
The fastest way to check (replace `list[int]` with actual class):

..code-block:: python

    >>> from genericname import get_generic_args
    >>> class A(list[int]):
    ...     pass
    ...
    >>>(get_generic_args(A)
    [(<class '__main__.A'>, 'T_co', <class 'int'>)]

Full list of supported types: list[T_Co,
    set,
    frozenset,
    cabc.Container,
    cabc.Iterable,
    cabc.Iterator,
    cabc.MutableSequence,
    cabc.MutableSet,
    cabc.Reversible,
    cabc.Sequence,
    cabc.Set,


Check full list in ``get_generic_parameters`` implementation. If you think something is missing, please create an issue.


import contextlib
import functools
import sys
import collections as coll
import collections.abc as cabc
from collections.abc import Iterable
from itertools import repeat
import types
import typing

__version__ = '0.1.0'
__version_tuple__ = (0, 1, 0)
__all__ = ['iter_generic_args', 'get_generic_args',
           'get_generic_args_for_base',
           'get_generic_args_for_subclasses', 'generic_args_to_classvar']


class GenericArg(typing.NamedTuple):
    cls: type            # class where typevar_name becomes runtime_class
    parameter: str       # type parameter (TypeVar name)
    argument: type       #


def get_generic_args(cls: type) -> list[tuple[type, str, type]]:
    return list(iter_generic_args(cls))

def iter_generic_args(cls: type) -> Iterable[tuple[type, str, type]]:
    """
    Returns all generic args of this class and all its superclasses
    as a sequence of tuples:
    `(GenericClass: type, TypeVarName: str, RuntimeClass: type)`, where
    `GenericClass` is a class in hierarchy in which `TypeVarName`
    becomes `RuntimeClass`.
    """
    # From get_original_bases documentation (python >= 3.12):
    # For classes that have an __orig_bases__ attribute, this function returns the value of cls.__orig_bases__.
    # For classes without the __orig_bases__ attribute, cls.__bases__ is returned.
    print(f'get_generic_args({cls!r}')
    if sys.version_info >= (3, 12):
        orig_bases = types.get_original_bases(cls)  # could be less fragile?
    else:
        if hasattr(cls, '__orig_bases__'):
            orig_bases = cls.__orig_bases__
        else:
            orig_bases = cls.__bases__
    for orig_base in orig_bases:
        # get_origin returns None for runtime classes, original class for generics
        base = typing.get_origin(orig_base)
        if base is None:  # real class without parameters
            yield from iter_generic_args(orig_base)
        else:  # generic
            assert isinstance(base, type)
            yield from iter_generic_args(base)
            parameters = get_generic_parameters(base)
            if parameters:
                print(f'!!! parameters for from base class {base}')
            args = [x for x in typing.get_args(orig_base) ]
            print(f'{base!r} parameters = {parameters!r}') # TODO REMOVE_THIS
            print(f'{orig_base!r} args = {args!r}')  # TODO REMOVE_THIS
            print()
            yield from (x for x in zip(repeat(cls), parameters, args) if type(x[2]) is type)


def get_generic_parameters(t: type) -> list[str]:
    # For generic type, return __parameters__
    parameters = [x.__name__ for x in getattr(t, '__parameters__', [])]
    if parameters:
        return parameters
    # For particular builtins and standard library types, return parameter names as in docs
    if t.__module__ not in ('builtins', 'collections', 'collections.abc', 'contextlib'):
        return []
    _t_co_types = [
        list, set, frozenset,
        cabc.Collection, cabc.Sequence, cabc.MutableSequence, cabc.Container,
        cabc.Iterable, cabc.Iterator, cabc.Reversible, cabc.Set, cabc.MutableSet,
        coll.deque, coll.Counter
    ]
    if any(t is x for x in _t_co_types):
        return ['T_co']
    if t is cabc.KeysView:
        return ['KT_co']
    if t is cabc.ValuesView:
        return ['VT_co']
    _dict_types = [
        dict,
        cabc.Mapping, cabc.MutableMapping, cabc.MappingView,
        coll.ChainMap, coll.defaultdict, coll.OrderedDict
    ]
    if any(t is x for x in _dict_types):
        return ['KT_co', 'VT_co']
    if t is contextlib.AbstractContextManager:
        return ['T_co', 'ExitT_co']
    if t is contextlib.AbstractAsyncContextManager:
        return ['T_co', 'AExitT_co']
    # NOTE: following types are explicitly *not* supported:
    # Callable, Awaitable, Coroutine, Generator, AsyncGenerator
    return []

class C(coll.Counter[int, str, float]):
    pass


def get_generic_args_for_base(cls: type, base_cls: type) -> dict[str, type]:
    """
    Similar to `get_generic_args`, but returns `{TypeVarName: RuntimeClass}`
    subset for the target base class only.

    All other classes and their template parameters are ignored.
    """
    parameters = get_generic_parameters(base_cls)
    if not parameters:
        raise NoGenericArgsError(f'Class {base_cls.__qualname__} has no generic parameters')
    return {
        typevar_name: runtime_class
        for (x, typevar_name, runtime_class) in iter_generic_args(cls) if typevar_name in parameters
    }

def get_generic_args_for_subclasses(cls: type, base_cls: type) -> dict[str, type]:
    """
    Similar to `get_generic_args_for_base`, but returns `{TypeVarName: RuntimeClass}`
    subset for the target base class and all of its subclasses.

    All other classes and their template parameters are ignored.
    """
    parameters = set(get_generic_parameters(base_cls))
    if not parameters:
        raise NoGenericArgsError(f'Class {base_cls.__qualname__} has no generic parameters')
    for x in cls.__mro__:
        if issubclass(x, base_cls):
            parameters.update(get_generic_parameters(x))
            print(f'  {x.__qualname__} -> {get_generic_parameters(x)}')
    return {
        typevar_name: runtime_class
        for (x, typevar_name, runtime_class) in iter_generic_args(cls)
        if typevar_name in parameters and issubclass(x, base_cls)
    }


class ConflictingTypesError(TypeError):
    pass


class NoGenericArgsError(TypeError):
    pass


def get_all_unique_generic_args(cls: type) -> dict[str, type]:
    """
    Similar to `get_generic_args`, but returns `{TypeVarName: RuntimeClass}`
    for all base classes, no matter where generics are found.

    If the same TypeVar name occurs in class hierarchy more than once, and
    runtime classes are not exactly the same, raises ConflictingTypesError.
    """
    result: dict[str, type] = {}
    bases_classes: dict[str, type] = {}
    for base_class, typevar_name, runtime_class in iter_generic_args(cls):
        if typevar_name in result:
            if result[typevar_name] is runtime_class:
                continue  # normal situation, just complex inheritance
            raise ConflictingTypesError(f'Generic parameter has conflicting runtime types: '
                                        f'{typevar_name}={result[typevar_name]} in {bases_classes[typevar_name]} vs '
                                        f'{typevar_name}={runtime_class} in {base_class}. '
                                        f'Either change your TypeVar names, class hierarchy, or switch to '
                                        f'single-class functions: generic_args_to_classvar, get_generic_args_for_base')
        result[typevar_name] = runtime_class
    return result


class _GenericArgsToClassVar:

    def __init__(self, *,
                 classes: typing.Literal['this', 'subclasses', 'all'],
                 classvar_name_format: str | typing.Callable[[str], str]
                 ):
        # Let's test arguments carefully. Fail early, fail cheap!
        if not isinstance(classes, str):
            raise TypeError(f"generic_args_to_classvar(classes=...) argument: "
                            f"expected str, got {classes.__class__.__qualname__}")
        if classes not in ('this', 'all', 'subclasses'):
            raise ValueError(f"generic_args_to_classvar(classes=...) argument: "
                             f"expected ['this', 'subclasses', 'all'], got {classes!r}")
        self._classes = classes

        if isinstance(classvar_name_format, str):
            self._format = functools.partial(str.format, classvar_name_format)
        else:
            self._format = classvar_name_format
        try:
            assert isinstance(self._format('T'), str)
        except Exception:
            raise ValueError(f"generic_args_to_classvar(classvar_name_format=...) argument: "
                             f"must be a single-placeholder format string "
                             f"or a single-argument callable converting str to str")

    def __call__(self, target_class, /):
        try:
            orig_init_subclass = target_class.__init_subclass__.__func__
        except AttributeError:
            orig_init_subclass = None

        @functools.wraps(target_class.__init_subclass__)
        def __init_subclass__(subclass, /, **kwargs):  # type: ignore
            print(f'[{target_class}] @ __init_subclass__({subclass})')
            if orig_init_subclass is None:
                super(target_class, subclass).__init_subclass__(**kwargs)
            else:
                orig_init_subclass(subclass, **kwargs)
            if self._classes == 'this':
                generic_args = get_generic_args_for_base(subclass, target_class)
                print(f'get_generic_args_for_base({subclass}, {target_class}) = {generic_args!r}')
            elif self._classes == 'subclasses':
                generic_args = get_generic_args_for_subclasses(subclass, target_class)
            elif self._classes == 'all':
                generic_args = get_all_unique_generic_args(subclass)
                print(f'get_all_unique_generic_args({subclass}) = {generic_args!r}')
            else:
                raise ValueError(f"Unexpected 'classes' argument: {self._classes!r}")
            if not generic_args:
                raise TypeError(f'Failed to apply @generic_args_to_classvar to {subclass} '
                                f'via base class {target_class}: no template parameters found. '
                                "If you think it's a bug, please report it: "
                                "<https://github.com/alexanderlukanin13/generic-name/issues>")
            for typevar, type_ in generic_args.items():
                attr = self._format(typevar)
                if hasattr(subclass, attr):
                    existing_value = getattr(subclass, attr)
                    if existing_value is not type_:
                        raise ConflictingTypesError(
                            f'Conflicting types in class variable {subclass.__qualname__}.{attr}: '
                            f'trying to assign {attr}={type_} from generic parameter {typevar}, '
                            f'but the variable already exists and has a distinct value {attr}={existing_value!r}')
                else:
                    setattr(subclass, attr, type_)

        target_class.__init_subclass__ = classmethod(__init_subclass__)
        return target_class


def generic_args_to_classvar(
        _decorated_class: type | None = None, /, *,
        classes: typing.Literal['this', 'subclasses', 'all'] = 'this',
        classvar_name_format: str | typing.Callable[[str], str]= '_{}'):
    """
    Class decorator that automatically assigns runtime generic argument types
    to ClassVar fields in all subclasses.

    If classes='this' (default), only generic type variables for the decorated
    class are used, any other generics in the class hierarchy are ignored.

    If classes='all', all type variables for all classes are used.

    Default ClassVar name for typevar `SomeT` would be `_SomeT`.
    You can change it by using custom format string or str->str conversion
    callable in classvar_name_format.

    This decorator can be used with or without brackets.
    """
    _ = _GenericArgsToClassVar(classes=classes, classvar_name_format=classvar_name_format)
    if _decorated_class is None:  # with brackets - not decorating yet
        return _
    else:  # without brackets - decorating
        return _(_decorated_class)

from __future__ import annotations

import typing

import pytest

from .typing_tools import *

T = typing.TypeVar("T")


def i(fn):
    return lambda *args, **kwargs: infer(fn)(*args, **kwargs)[-1]


def test_simple():
    @i
    def _simple_return() -> int:
        ...

    assert _simple_return() == int


def test_generic():
    @i
    def _generic_return(arg: T) -> T:
        ...

    assert _generic_return(123.0) == float


class _GenericClass(GenericCheck, typing.Generic[T]):
    ...


def test_generic_class_return():
    @i
    def create(t: T) -> _GenericClass[T]:
        ...

    assert create(123) == _GenericClass[int]


class _GenericClassMethod(GenericCheck, typing.Generic[T]):
    @i
    def method(self) -> T:
        ...


def test_generic_class_arg():

    assert _GenericClassMethod[int]().method() == int
    assert (
        _GenericClassMethod[_GenericClassMethod[int]]().method()
        == _GenericClassMethod[int]
    )


@i
def create(tp: typing.Type[T]) -> T:
    ...


def test_type_arg():

    assert create(int) == int
    assert create(float) == float
    assert create(_GenericClassMethod[int]) == _GenericClassMethod[int]
    assert create(_GenericClassMethod[int]) != _GenericClassMethod


class _NonGenericClass:
    @i
    def method(self) -> int:
        ...


def test_non_generic_method():

    assert _NonGenericClass().method() == int


def test_variable_args():
    @i
    def many_args(*x: T) -> T:
        ...

    assert many_args(1) == int
    with pytest.raises(TypeError):
        many_args(1, "hj")


def test_variable_args_empty():
    @i
    def many_args(*x: int) -> int:
        ...

    assert many_args() == int


def test_keyword_args():
    @i
    def many_args(a: int, b: T) -> T:
        ...

    assert many_args(b="df", a=123) == str


def test_keyword_default():
    @i
    def default_kwarg(b: T = 10) -> T:  # type: ignore
        ...

    assert default_kwarg() == int
    assert default_kwarg(b="df") == str

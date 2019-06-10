from __future__ import annotations

import typing
import typing_inspect
import pytest

from .expressions import *

T = typing.TypeVar("T")


@expression
def fn(a: T, b: T) -> T:
    ...


@expression
def value_fn(a: int) -> Expression:
    ...


class Subclass(Expression):
    pass


@expression
def subclass_fn(a: int) -> Subclass:
    ...


def test_expression_subclass() -> None:
    assert isinstance(subclass_fn(1), Subclass)


class Generic(Expression, typing.Generic[T]):
    def get_inner_type(self) -> typing.Type[T]:
        return typing_inspect.get_args(typing_inspect.get_generic_type(self))[0]

    @expression
    def get(self) -> T:
        ...


@expression
def instance_arg_fn(a: int) -> Generic[int]:
    ...


def test_expression_subclass_generic() -> None:
    assert instance_arg_fn(10).get_inner_type() == int


@expression
def mutable_fn(a: typing.List) -> Expression:
    ...


class SubclassWithMethod(Expression):
    @expression
    def __add__(self, other: SubclassWithMethod) -> SubclassWithMethod:
        ...


@expression
def create_generic(t: typing.Type[T]) -> Generic[T]:
    ...


def test_classmethod():
    c = create_generic(Subclass)
    assert isinstance(c.get(), Subclass)


@expression
def create_method_subclass(i: int) -> SubclassWithMethod:
    ...


@expression
def variadic(*args: int) -> Expression:
    ...


def test_variadic():
    assert variadic(1, 2).args == (1, 2)


@expression
def create_variadic_ints() -> typing.Iterable[int]:
    ...


def test_iterated():
    assert variadic(1, 2, *create_variadic_ints(), 3, 4) == Expression(
        variadic,
        (
            1,
            2,
            IteratedPlaceholder[int](
                create_iterated_placeholder,
                (
                    PlaceholderExpression[typing.Iterable[int]](
                        create_variadic_ints, (), {}
                    ),
                ),
                {},
            ),
            3,
            4,
        ),
        {},
    )


TEST_EXPRESSIONS: typing.Iterable[object] = [
    value_fn(123),
    fn(value_fn(10), value_fn(11)),
    fn(subclass_fn(1), subclass_fn(2)),
    instance_arg_fn(10),
    create_method_subclass(10) + create_method_subclass(10),
    mutable_fn([1, 2, 3]),  # mutable value that doesn't have hash
    variadic(1, 2, 3),
]


@pytest.mark.parametrize("instance", TEST_EXPRESSIONS)
def test_fold_identity(instance) -> None:
    """
    You should be able to decompose any instances into it's type and expression and recompose it.
    """
    result = ExpressionFolder(lambda e: e)(instance)
    assert instance == result


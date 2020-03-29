from __future__ import annotations
import typing

from metadsl import *
from .rules import *
from .conversion import *
from .maybe import *


__all__ = ["Boolean"]

T = typing.TypeVar("T")


class Boolean(Expression):
    @expression
    @classmethod
    def create(cls, b: bool) -> Boolean:
        ...

    @expression
    def if_(self, true: T, false: T) -> T:
        ...

    @expression
    def and_(self, other: Boolean) -> Boolean:
        ...

    @expression
    def or_(self, other: Boolean) -> Boolean:
        ...


@register  # type: ignore
@rule
def if_(b: bool, l: T, r: T) -> R[T]:
    return Boolean.create(b).if_(l, r), lambda: l if b else r


@register  # type: ignore
@rule
def and_or(l: bool, r: bool) -> R[Boolean]:
    l_boolean = Boolean.create(l)
    r_boolean = Boolean.create(r)

    yield l_boolean.and_(r_boolean), lambda: Boolean.create(l and r)
    yield l_boolean.or_(r_boolean), lambda: Boolean.create(l or r)


@register_convert
@rule
def convert_bool(b: bool) -> R[Maybe[Boolean]]:
    """
    >>> execute(Converter[Boolean].convert(True), convert_bool) == Maybe.just(Boolean.create(True))
    True
    >>> list(convert_bool(ExpressionReference.from_expression(Converter[Boolean].convert("not bool"))))
    []
    """
    return Converter[Boolean].convert(b), Maybe.just(Boolean.create(b))

import typing

import numpy
from metadsl import *

from . import numpy as numpy_api
from .abstraction import *
from .conversion import *
from .either import *
from .integer import *
from .maybe import *
from .pair import *
from .rules import *
from .vec import *

__all__ = ["unbox_ndarray_compat", "ndarray_getitem"]


@expression
def box_ndarray(n: numpy.ndarray) -> numpy_api.NDArray:
    ...


@expression
def unbox_ndarray(n: numpy_api.NDArray) -> numpy.ndarray:
    ...


@register_unbox
@rule
def box_unbox_ndarray(n: numpy.ndarray) -> R[numpy.ndarray]:
    return unbox_ndarray(box_ndarray(n)), n


@expression
def unbox_ndarray_compat(n: numpy_api.NDArrayCompat) -> numpy.ndarray:
    ...


@register_unbox
@rule
def box_unbox_ndarray_compat(n: numpy_api.NDArray) -> R[numpy.ndarray]:
    return (
        unbox_ndarray_compat(numpy_api.NDArrayCompat.from_ndarray(Maybe.just(n))),
        unbox_ndarray(n),
    )


@expression
def unbox_integer(i: Integer) -> int:
    ...


@register_unbox  # type: ignore
@rule
def unbox_integer_rule(i: int) -> R[int]:
    return unbox_integer(Integer.from_int(i)), i


@expression
def arange(stop: int) -> numpy.ndarray:
    return numpy.arange(stop)


@register_unbox
@rule
def unbox_arange(i: Integer):
    return (unbox_ndarray(numpy_api.arange_(i)), arange(unbox_integer(i)))


register_numpy_engine(default_rule(arange))
# @expression
# def arange_compat(stop: object) -> Maybe[numpy.ndarray]:
#     return Converter[int].convert(stop).map(Abstraction.from_fn(arange))


@expression
def ndarray_getitem(
    self: numpy.ndarray, i: typing.Union[int, typing.Tuple[int, ...]]
) -> numpy.ndarray:
    return self[i]


register_numpy_engine(default_rule(ndarray_getitem))


@expression
def ndarray_add(
    self: typing.Union[numpy.ndarray, numpy.int64],
    other: typing.Union[numpy.ndarray, numpy.int64],
) -> typing.Union[numpy.ndarray, numpy.int64]:
    return self + other


register_numpy_engine(default_rule(ndarray_add))


@register_unbox  # type: ignore
@rule
def unbox_ndarray_add(a: numpy_api.NDArray, b: numpy_api.NDArray) -> R[numpy.ndarray]:
    return unbox_ndarray(a + b), ndarray_add(unbox_ndarray(a), unbox_ndarray(b))


@expression
def unbox_idxs(
    idxs: Either[Integer, Vec[Integer]]
) -> typing.Union[int, typing.Tuple[int, ...]]:
    ...


@expression
def homo_tuple(*values: T) -> typing.Tuple[T, ...]:
    return tuple(values)


register(default_rule(homo_tuple))


@register_unbox  # type: ignore
@rule
def unbox_idxs_rule(
    i: Integer, ints: typing.Sequence[Integer]
) -> R[typing.Union[int, typing.Tuple[int, ...]]]:
    yield (unbox_idxs(Either[Integer, Vec[Integer]].left(i)), unbox_integer(i))
    yield (
        unbox_idxs(Either[Integer, Vec[Integer]].right(Vec.create(*ints))),
        lambda: homo_tuple(*(unbox_integer(i_) for i_ in ints)),  # type: ignore
    )


@register_unbox  # type: ignore
@rule
def unbox_ndarray_getitem(
    a: numpy_api.NDArray, idx: Either[Integer, Vec[Integer]]
) -> R[numpy.ndarray]:
    return unbox_ndarray(a[idx]), ndarray_getitem(unbox_ndarray(a), unbox_idxs(idx))


# @expression
# def ndarray_getitem_compat(self: object, i: object) -> Maybe[numpy.ndarray]:
#     return (
#         Converter[numpy.ndarray].convert(self)
#         & Converter[typing.Union[int, typing.Tuple[int, ...]]].convert(i)
#     ).map(
#         Abstraction[
#             Pair[numpy.ndarray, typing.Union[int, typing.Tuple[int, ...]]],
#             numpy.ndarray,
#         ].from_fn(lambda p: ndarray_getitem(p.left, p.right()))
#     )

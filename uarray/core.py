import functools
import typing

from .core_types import *
from .machinery import *


@operation
def CallUnary(fn: CCallableUnary[RET, ARG1], a1: ARG1) -> RET:
    ...


@operation(to_str=lambda fn, a1, a2: f"{fn}({a1}, {a2})")
def CallBinary(fn: CCallableBinary[RET, ARG1, ARG2], a1: ARG1, a2: ARG2) -> RET:
    ...


@operation
def Sequence(length: CContent, getitem: CGetItem) -> CNestedSequence:
    ...


@operation
def GetItem(array: CNestedSequence) -> CGetItem:
    ...


register(GetItem(Sequence(w("length"), w("getitem"))), lambda length, getitem: getitem)


@operation
def Length(seq: CNestedSequence) -> CContent:
    ...


register(Length(Sequence(w("length"), w("_"))), lambda _, length: length)


@operation
def Scalar(cont: CContent) -> CNestedSequence:
    ...


@operation
def Content(sca: CNestedSequence) -> CContent:
    ...


register(Content(Scalar(w("content"))), lambda content: content)


@operation(to_str=lambda variable_name: variable_name or "_")
def Unbound(*, variable_name: str) -> CUnbound:
    ...


# other callables


@operation(to_str=lambda a: f"_ -> {a}")
def Always(a: T) -> CCallableUnary[T, typing.Any]:
    ...


register(CallUnary(Always(w("a")), w("_")), lambda _, a: a)


@operation
def Compose(l: CCallableUnary[T, V], r: CCallableUnary[V, U]) -> CCallableUnary[T, U]:
    ...


def _compose(l: CCallableUnary[T, V], r: CCallableUnary[V, U], v: U) -> T:
    return CallUnary(l, CallUnary(r, v))


register(CallUnary(Compose(w("l"), w("r")), w("v")), _compose)


class CUnaryPythonFunction(CCallableUnary[RET, ARG1]):
    # add any cause not sure how to tell it this isn't method
    name: typing.Callable[[typing.Any, ARG1], RET]


@symbol
def UnaryPythonFunction(
    # name should be typing.Callable[[ARG1], RET]
    name: typing.Callable[[typing.Any], typing.Any]
) -> CUnaryPythonFunction[RET, ARG1]:
    ...


def _call_unary_py_function(fn: CUnaryPythonFunction[RET, ARG1], arg: ARG1) -> RET:
    return fn.name(arg)


register(CallUnary(sw("fn", UnaryPythonFunction), w("arg")), _call_unary_py_function)

# def unbound_content(variable_name: str) -> CContent:
#     return Unbound(name="", variable_name=variable_name)


@operation(to_str=lambda body, a1: f"({a1} -> {body})")
def UnaryFunction(body: T, a1: CUnbound) -> CCallableUnary[T, ARG1]:
    ...


@operation(to_str=lambda body, a1, a2: f"({a1}, {a2} -> {body})")
def BinaryFunction(
    body: T, a1: CUnbound, a2: CUnbound
) -> CCallableBinary[T, ARG1, ARG2]:
    ...


for call_type, fn_type in [(CallBinary, BinaryFunction), (CallUnary, UnaryFunction)]:
    register(
        call_type(fn_type(w("body"), ws("args")), ws("arg_vals")),  # type: ignore
        lambda body, args, arg_vals: matchpy.substitute(
            body, {arg.variable_name: arg_val for (arg, arg_val) in zip(args, arg_vals)}
        ),
    )


_counter = 0


def gensym() -> str:
    global _counter
    variable_name = f"i{_counter}"
    _counter += 1
    return variable_name


def unbound(variable_name: str = None) -> CUnbound:
    return Unbound(variable_name=variable_name or gensym())


def unbound_content(variable_name: str = None) -> CUnboundContent:
    return typing.cast(CUnboundContent, unbound(variable_name))


def unary_function(fn: typing.Callable[[ARG1], RET]) -> CCallableUnary[RET, ARG1]:
    a1 = unbound()
    return UnaryFunction(fn(typing.cast(ARG1, a1)), a1)


def binary_function(
    fn: typing.Callable[[ARG1, ARG2], RET]
) -> CCallableBinary[RET, ARG1, ARG2]:
    a1 = unbound()
    a2 = unbound()
    return BinaryFunction(fn(typing.cast(ARG1, a1), typing.cast(ARG2, a2)), a1, a2)


@symbol
def Int(name: int) -> CInt:
    pass


@functools.singledispatch
def to_array(v) -> CNestedSequence:
    """
    Convert some value into a matchpy expression
    """
    raise NotImplementedError()


@to_array.register(int)
def to_array__int(v):
    return Scalar(Int(v))


@to_array.register(matchpy.Expression)
def to_array__expr(v):
    return v


@to_array.register(tuple)
def to_array__tuple(t):
    return vector_of(*(to_array(t_) for t_ in t))


@operation(to_str=lambda items: f"<{' '.join(str(i) for i in items)}>")
def Vector(*items: T) -> CVector[T]:
    ...


register(
    CallUnary(Vector(ws("items")), sw("index", Int)),
    lambda index, items: items[index.name],
)


@operation
def PushVector(new_item: T, vector_callable: CVector[T]) -> CVector[T]:
    ...


register(
    PushVector(w("new_item"), Vector(ws("items"))),
    lambda new_item, items: Vector(new_item, *items),
)


@operation
def ConcatVector(l: CVector[T], r: CVector[T]) -> CVector[T]:
    ...


register(ConcatVector(Vector(ws("l")), Vector(ws("r"))), lambda l, r: Vector(*l, *r))


@operation
def FirstVector(vec: CVector[T]) -> T:
    ...


register(FirstVector(Vector(w("x"), w("xs"))), lambda x, xs: x)


@operation
def RestVector(vec: CVector[T]) -> CVector[T]:
    ...


register(RestVector(Vector(w("x"), w("xs"))), lambda x, xs: xs)


def vector_of(*values: CNestedSequence) -> CNestedSequence:
    return Sequence(Int(len(values)), Vector(*values))


def vector(*values: int) -> CNestedSequence:
    # vc: CCallableUnary[CContent, CContent] = Vector(*map(Int, values))
    # getitem = Compose(scalar_fn, vc)

    return vector_of(*(Scalar(Int(v)) for v in values))


@operation
def NDArray(shape: CVector[CContent], index_fn: CIndexFn) -> CNDArray:
    ...


@operation
def Shape_(array: CNDArray) -> CVector[CContent]:
    ...


register(Shape_(NDArray(w("shape"), w("index_fn"))), lambda shape, index_fn: shape)


@operation
def IndexFn(array: CNDArray) -> CIndexFn:
    ...


register(IndexFn(NDArray(w("shape"), w("index_fn"))), lambda shape, index_fn: index_fn)


@operation
def NDArrayToNestedSequence(array: CNDArray) -> CNestedSequence:
    ...


register(
    NDArrayToNestedSequence(NDArray(Vector(), w("index_fn"))),
    lambda index_fn: Scalar(CallUnary(index_fn, Vector())),
)


def _ndarray_to_nested_sequence(
    first_dim: CContent, rest_dims: typing.Sequence[CContent], index_fn: CIndexFn
) -> CNestedSequence:
    def getitem(idx: CContent) -> CNestedSequence:
        def new_index_fn(indices: CVector[CContent]) -> CContent:
            return CallUnary(index_fn, PushVector(idx, indices))

        inner_ndarray = NDArray(Vector(*rest_dims), unary_function(new_index_fn))
        return NDArrayToNestedSequence(inner_ndarray)

    return Sequence(first_dim, unary_function(getitem))


register(
    NDArrayToNestedSequence(
        NDArray(Vector(w("first_dim"), w("rest_dims")), w("index_fn"))
    ),
    _ndarray_to_nested_sequence,
)


@operation
def NestedSequenceToNDArray(array: CNestedSequence) -> CNDArray:
    ...


register(
    NestedSequenceToNDArray(Scalar(w("content"))),
    lambda content: NDArray(Vector(), Always(content)),
)


def _nested_sequence_to_ndarray(length: CContent, getitem: CGetItem) -> CNDArray:
    inner_shape = Shape_(NestedSequenceToNDArray(CallUnary(getitem, unbound_content())))
    shape = PushVector(length, inner_shape)

    def index_fn(indices: CVector[CContent]) -> CContent:
        outer_index = FirstVector(indices)
        rest_indices = RestVector(indices)

        inner_index_fn = IndexFn(
            NestedSequenceToNDArray(CallUnary(getitem, outer_index))
        )

        return CallUnary(inner_index_fn, rest_indices)

    return NDArray(shape, unary_function(index_fn))


register(
    NestedSequenceToNDArray(Sequence(w("length"), w("getitem"))),
    _nested_sequence_to_ndarray,
)


@operation
def WrapShape(shape: CVector[CContent]) -> CNestedSequence:
    ...


register(WrapShape(Vector(ws("items"))), lambda items: vector_of(*map(Scalar, items)))


@operation
def Unify(*args: T) -> T:
    ...


# TODO: Support unification on unequal but equivelent form
# similar to question of equivalencies of lambda calculus, i.e. lambda a: a + 1 == lambda b: b + 1
# even though variables are different name
# Also need to be able to say some thing *could* be equal at runtime, whereas some others cannot be.
# i.e. If two `Value`s are unequal, they cannot be unified. However, if two arbitrary expressions are not equal
# at compile time, they still could end up being equal at runtime.
register(Unify(w("x")), lambda x: x)
register(
    Unify(w("x"), w("y"), ws("rest")),
    lambda x, y, rest: Unify(x, *rest),
    matchpy.EqualVariablesConstraint("x", "y"),
)


def with_shape(
    x: CNestedSequence, shape: typing.Sequence[CContent], i=0
) -> CNestedSequence:
    if i == len(shape):
        return Scalar(Content(x))
    return Sequence(
        shape[i],
        unary_function(
            lambda idx: with_shape(CallUnary(GetItem(x), idx), shape, i + 1)
        ),
    )


def with_dims(x: CNestedSequence, n_dim: int, i=0) -> CNestedSequence:
    if i == n_dim:
        return Scalar(Content(x))
    return Sequence(
        Length(x),
        unary_function(lambda idx: with_dims(CallUnary(GetItem(x), idx), n_dim, i + 1)),
    )


def unbound_array(variable_name: str, n_dim: int) -> CNestedSequence:
    return with_dims(typing.cast(CNestedSequence, unbound(variable_name)), n_dim)


def unbound_with_shape(variable_name: str, n_dim: int) -> CNestedSequence:
    return with_shape(
        typing.cast(CNestedSequence, unbound(variable_name)),
        tuple(unbound_content(f"{variable_name}_shape_{i}") for i in range(n_dim)),
    )

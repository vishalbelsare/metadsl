"""
Convert expressions wrap existing expression types and provide all the same methods,
but do type conversion for the arguments.
"""

# import typing

# from .expressions import Expression
# from .conversion import convert, register_converter
# import dataclasses

# T_expression = typing.TypeVar("T_expression", bound=Expression)



# @dataclasses.dataclass
# class ConvertExpression(typing.Generic[T_expression]):
#     _expression: T_expression
    
#     def _get_expression_type(self) -> T_expression:
#         """
#         Returns the type of the expression it is wrapping.
#         """
#         ...

# T_callable = typing.TypeVar("T_callable", bound=typing.Callable)

# def convert_expression(fn: T_callable) -> T_callable:
#     ...
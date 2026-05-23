"""AST compiler for structured debt covenant rules.

Rules enter this module as dictionaries and are translated into Python AST.
No raw string eval is used. The generated callable is compiled from a typed
syntax tree and executed in a minimal namespace.
"""

from __future__ import annotations

import ast
from collections.abc import Callable
from dataclasses import dataclass
import logging
import math
from typing import Any, Final

from contracts import CovenantRuleConfig


logger = logging.getLogger(__name__)

ComplianceFunction = Callable[[float, float, float], tuple[bool, float]]


SUPPORTED_GOVERNORS: Final[set[str]] = {
    "Consolidated Net Leverage Ratio",
    "Consolidated Interest Coverage Ratio",
    "Fixed Charge Coverage Ratio",
    "Minimum Liquidity",
}
SUPPORTED_OPERATORS: Final[set[str]] = {
    "less_than_or_equal",
    "less_than",
    "greater_than_or_equal",
    "greater_than",
}


class CovenantCompilerError(ValueError):
    """Raised when a covenant dictionary cannot be safely compiled."""


@dataclass(frozen=True, slots=True)
class CompiledCovenant:
    """Compiled covenant metadata and executable compliance function."""

    threshold: float
    governor: str
    operator: str
    evaluate: ComplianceFunction
    covenant_type: str


class CovenantCompiler:
    """Object-oriented facade for compiling structured covenant dictionaries."""

    def compile(self, rule: dict[str, Any]) -> CompiledCovenant:
        """Compile a covenant rule into a safe executable compliance function."""

        return compile_covenant(rule)


def _coerce_threshold(value: Any) -> float:
    try:
        threshold = float(value)
    except (TypeError, ValueError) as exc:
        raise CovenantCompilerError(f"Invalid covenant threshold: {value!r}") from exc

    if not math.isfinite(threshold) or threshold < 0:
        raise CovenantCompilerError("Covenant threshold must be a finite non-negative number")
    return threshold


def _validate_rule(rule: dict[str, Any]) -> tuple[str, str, float]:
    governor = str(rule.get("governors", "")).strip()
    operator = str(rule.get("operator", "")).strip()
    threshold = _coerce_threshold(rule.get("objects"))

    if governor not in SUPPORTED_GOVERNORS:
        raise CovenantCompilerError(f"Unsupported covenant governor: {governor!r}")
    if operator not in SUPPORTED_OPERATORS:
        raise CovenantCompilerError(f"Unsupported covenant operator: {operator!r}")
    return governor, operator, threshold


def _ratio_expression(governor: str) -> ast.expr:
    if governor == "Consolidated Net Leverage Ratio":
        return ast.BinOp(
            left=ast.BinOp(
                left=ast.Name(id="total_debt", ctx=ast.Load()),
                op=ast.Sub(),
                right=ast.Name(id="cash", ctx=ast.Load()),
            ),
            op=ast.Div(),
            right=ast.Name(id="ebitda", ctx=ast.Load()),
        )
    if governor == "Consolidated Interest Coverage Ratio":
        return ast.BinOp(
            left=ast.Name(id="ebitda", ctx=ast.Load()),
            op=ast.Div(),
            right=ast.Name(id="cash", ctx=ast.Load()),
        )
    if governor == "Fixed Charge Coverage Ratio":
        return ast.BinOp(
            left=ast.Name(id="ebitda", ctx=ast.Load()),
            op=ast.Div(),
            right=ast.Name(id="total_debt", ctx=ast.Load()),
        )
    if governor == "Minimum Liquidity":
        return ast.Name(id="cash", ctx=ast.Load())
    raise CovenantCompilerError(f"Unsupported covenant governor: {governor!r}")


def _denominator_guard(governor: str) -> ast.expr | None:
    if governor == "Consolidated Net Leverage Ratio":
        return ast.Name(id="ebitda", ctx=ast.Load())
    if governor == "Consolidated Interest Coverage Ratio":
        return ast.Name(id="cash", ctx=ast.Load())
    if governor == "Fixed Charge Coverage Ratio":
        return ast.Name(id="total_debt", ctx=ast.Load())
    return None


def _comparison_node(operator: str) -> ast.cmpop:
    if operator == "less_than_or_equal":
        return ast.LtE()
    if operator == "less_than":
        return ast.Lt()
    if operator == "greater_than_or_equal":
        return ast.GtE()
    if operator == "greater_than":
        return ast.Gt()
    raise CovenantCompilerError(f"Unsupported covenant operator: {operator!r}")


def _buffer_expression(operator: str) -> ast.expr:
    ratio = ast.Name(id="ratio", ctx=ast.Load())
    threshold = ast.Name(id="threshold", ctx=ast.Load())
    if operator in {"less_than_or_equal", "less_than"}:
        return ast.BinOp(left=threshold, op=ast.Sub(), right=ratio)
    return ast.BinOp(left=ratio, op=ast.Sub(), right=threshold)


def _build_function_ast(governor: str, operator: str, threshold: float) -> ast.Module:
    args = ast.arguments(
        posonlyargs=[],
        args=[
            ast.arg(arg="total_debt", annotation=ast.Name(id="float", ctx=ast.Load())),
            ast.arg(arg="cash", annotation=ast.Name(id="float", ctx=ast.Load())),
            ast.arg(arg="ebitda", annotation=ast.Name(id="float", ctx=ast.Load())),
        ],
        kwonlyargs=[],
        kw_defaults=[],
        defaults=[],
    )

    body: list[ast.stmt] = [
        ast.Assign(
            targets=[ast.Name(id="threshold", ctx=ast.Store())],
            value=ast.Constant(value=threshold),
        )
    ]
    denominator = _denominator_guard(governor)
    if denominator is not None:
        body.append(
            ast.If(
                test=ast.Compare(
                    left=denominator,
                    ops=[ast.LtE()],
                    comparators=[ast.Constant(value=0.0)],
                ),
                body=[
                    ast.Return(
                        value=ast.Tuple(
                            elts=[
                                ast.Constant(value=False),
                                ast.UnaryOp(op=ast.USub(), operand=ast.Name(id="inf", ctx=ast.Load())),
                            ],
                            ctx=ast.Load(),
                        )
                    )
                ],
                orelse=[],
            )
        )

    body.extend(
        [
            ast.Assign(
                targets=[ast.Name(id="ratio", ctx=ast.Store())],
                value=_ratio_expression(governor),
            ),
            ast.Assign(
                targets=[ast.Name(id="buffer_distance", ctx=ast.Store())],
                value=_buffer_expression(operator),
            ),
            ast.Assign(
                targets=[ast.Name(id="compliant", ctx=ast.Store())],
                value=ast.Compare(
                    left=ast.Name(id="ratio", ctx=ast.Load()),
                    ops=[_comparison_node(operator)],
                    comparators=[ast.Name(id="threshold", ctx=ast.Load())],
                ),
            ),
            ast.Return(
                value=ast.Tuple(
                    elts=[
                        ast.Name(id="compliant", ctx=ast.Load()),
                        ast.Name(id="buffer_distance", ctx=ast.Load()),
                    ],
                    ctx=ast.Load(),
                )
            ),
        ]
    )

    function = ast.FunctionDef(
        name="evaluate_covenant",
        args=args,
        body=body,
        decorator_list=[],
        returns=ast.Subscript(
            value=ast.Name(id="tuple", ctx=ast.Load()),
            slice=ast.Tuple(
                elts=[ast.Name(id="bool", ctx=ast.Load()), ast.Name(id="float", ctx=ast.Load())],
                ctx=ast.Load(),
            ),
            ctx=ast.Load(),
        ),
    )
    module = ast.Module(body=[function], type_ignores=[])
    return ast.fix_missing_locations(module)


def compile_covenant(rule: CovenantRuleConfig | dict[str, Any]) -> CompiledCovenant:
    """Compile a structured covenant dictionary into an executable function."""

    governor, operator, threshold = _validate_rule(rule)
    module = _build_function_ast(governor=governor, operator=operator, threshold=threshold)
    namespace: dict[str, Any] = {
        "__builtins__": {},
        "inf": math.inf,
        "float": float,
        "bool": bool,
        "tuple": tuple,
    }

    logger.info("Compiling covenant AST for governor=%s operator=%s", governor, operator)
    exec(compile(module, filename="<ddcse-covenant-ast>", mode="exec"), namespace)
    evaluate = namespace["evaluate_covenant"]
    return CompiledCovenant(
        threshold=threshold,
        governor=governor,
        operator=operator,
        evaluate=evaluate,
        covenant_type=governor,
    )

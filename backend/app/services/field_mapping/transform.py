from __future__ import annotations
import ast
import operator
from typing import Any

from app.services.field_mapping.canonical_schema import get_canonical_type, FieldType


class TransformEngine:
    """Applies mapping configuration to transform raw data rows into canonical schema."""

    def __init__(self, mapping_config: dict[str, Any]):
        self.entries = mapping_config.get("mappings", [])

    def transform_row(self, row: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
        result: dict[str, Any] = {}
        warnings: list[str] = []

        for entry in self.entries:
            source = entry.get("source_field")
            target = entry["target_field"]
            transform = entry.get("transform")

            if source and source not in row:
                warnings.append(f"Source field '{source}' not found in data")
                continue

            raw_value = row.get(source) if source else None

            if transform is None:
                result[target] = raw_value
            else:
                t_type = transform.get("type")
                t_config = transform.get("config", {})

                if t_type == "value_mapping":
                    str_val = str(raw_value) if raw_value is not None else ""
                    result[target] = t_config.get(str_val, raw_value)

                elif t_type == "unit_conversion":
                    try:
                        factor = float(t_config.get("factor", 1))
                        result[target] = float(raw_value) * factor
                    except (TypeError, ValueError):
                        warnings.append(f"Cannot convert '{raw_value}' for field '{target}'")
                        result[target] = None

                elif t_type == "formula":
                    try:
                        expr = t_config["expression"]
                        inputs = t_config.get("inputs", [])
                        namespace = {}
                        for k in inputs:
                            val = result.get(k, row.get(k, 0))
                            namespace[k] = float(val) if val is not None else 0
                        result[target] = _safe_eval(expr, namespace)
                    except Exception as e:
                        warnings.append(f"Formula error for '{target}': {e}")
                        result[target] = None
                else:
                    result[target] = raw_value

            # Type compatibility check
            expected_type = get_canonical_type(target)
            if expected_type and result.get(target) is not None:
                if not _type_compatible(result[target], expected_type):
                    warnings.append(
                        f"Type mismatch: '{target}' expects {expected_type.value}, "
                        f"got {type(result[target]).__name__}"
                    )

        return result, warnings

    def transform_batch(
        self, rows: list[dict[str, Any]]
    ) -> list[tuple[dict[str, Any], list[str]]]:
        return [self.transform_row(row) for row in rows]


# --- Safe expression evaluator ---

_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}

_UNARY_OPS = {
    ast.USub: operator.neg,
}


def _safe_eval(expression: str, namespace: dict[str, float]) -> float:
    """Evaluate a simple arithmetic expression safely using AST parsing.
    Only allows: numbers, variable references, and +, -, *, / operators.
    """
    tree = ast.parse(expression, mode="eval")
    return _eval_node(tree.body, namespace)


def _eval_node(node: ast.expr, namespace: dict[str, float]) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    elif isinstance(node, ast.Name):
        if node.id not in namespace:
            raise ValueError(f"Unknown variable: {node.id}")
        return namespace[node.id]
    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _OPERATORS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        left = _eval_node(node.left, namespace)
        right = _eval_node(node.right, namespace)
        if op_type == ast.Div and right == 0:
            raise ValueError("Division by zero")
        return _OPERATORS[op_type](left, right)
    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _UNARY_OPS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        return _UNARY_OPS[op_type](_eval_node(node.operand, namespace))
    else:
        raise ValueError(f"Unsupported expression: {ast.dump(node)}")


def _type_compatible(value: Any, expected_type: FieldType) -> bool:
    if expected_type == FieldType.STRING:
        return True
    elif expected_type in (FieldType.INTEGER, FieldType.FLOAT):
        return isinstance(value, (int, float))
    elif expected_type in (FieldType.DATE, FieldType.DATETIME):
        return isinstance(value, str)
    elif expected_type == FieldType.BOOLEAN:
        return isinstance(value, bool)
    return True

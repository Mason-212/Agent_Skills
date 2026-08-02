"""
Template for checking docstrings in Python files.
"""

import sys
sys.path.insert(0, '/Users/thomaschang/Documents/dev/git/thomaschangsf/skills/plugins/goal-sandbox-plugin/resources/verifiers')

from template_base import VerificationTemplate
from typing import Any, Dict, List


class CheckDocstringsTemplate(VerificationTemplate):
    def required_params(self) -> List[str]:
        return ["target_file"]

    def optional_params(self) -> Dict[str, Any]:
        return {}

    def validate_params(self, params: Dict[str, Any]) -> bool:
        if not params.get("target_file", "").endswith(".py"):
            raise ValueError("target_file must be a .py file")
        return True

    def render(self, params: Dict[str, Any]) -> str:
        return f"""
def verify_docstrings():
    import ast
    import os

    target = "{params['target_file']}"

    if not os.path.exists(target):
        return False, f"File not found: {{target}}", ["Create the file first"]

    with open(target) as f:
        try:
            tree = ast.parse(f.read())
        except SyntaxError as e:
            return False, f"Syntax error in {{target}}: {{e}}", ["Fix syntax errors first"]

    missing_docs = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            if not ast.get_docstring(node):
                missing_docs.append((node.name, node.lineno))

    if missing_docs:
        suggestions = [f"Add docstring to {{name}} at {{target}}:{{line}}"
                      for name, line in missing_docs[:3]]
        if len(missing_docs) > 3:
            suggestions.append(f"...and {{len(missing_docs) - 3}} more")

        return False, f"{{len(missing_docs)}} functions/classes missing docstrings", suggestions

    return True, "All functions and classes have docstrings", []
"""

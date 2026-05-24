"""
Template for running existing tests.
"""

import sys
sys.path.insert(0, '/Users/thomaschang/Documents/dev/git/thomaschangsf/skills/plugins/goal-sandbox-plugin/resources/verifiers')

from template_base import VerificationTemplate
from typing import Any, Dict, List


class ExistingTestsTemplate(VerificationTemplate):
    def required_params(self) -> List[str]:
        return ["test_command"]

    def optional_params(self) -> Dict[str, Any]:
        return {"timeout": 60}

    def validate_params(self, params: Dict[str, Any]) -> bool:
        if not params.get("test_command"):
            raise ValueError("test_command cannot be empty")
        return True

    def render(self, params: Dict[str, Any]) -> str:
        # Split test command into parts for subprocess
        import shlex
        cmd_parts = shlex.split(params['test_command'])
        cmd_list = str(cmd_parts)

        return f"""
def verify_existing_tests():
    import subprocess

    cmd = {cmd_list}

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout={params['timeout']}
        )

        if result.returncode == 0:
            return True, "All tests passed", []
        else:
            stderr_preview = result.stderr[:300] if result.stderr else "No error output"
            return False, f"Tests failed: {{stderr_preview}}", [
                "Check test output for failing tests",
                "Revert recent changes that may have broken tests",
                f"Run manually: {{' '.join(cmd)}}"
            ]

    except subprocess.TimeoutExpired:
        return False, f"Tests timed out after {params['timeout']} seconds", [
            "Increase timeout if tests are slow",
            "Check for infinite loops in code"
        ]
    except FileNotFoundError:
        return False, f"Command not found: {{cmd[0]}}", [
            f"Install {{cmd[0]}} first",
            "Check that test command is correct"
        ]
    except Exception as e:
        return False, f"Error running tests: {{e}}", [
            f"Run manually to diagnose: {{' '.join(cmd)}}"
        ]
"""

#!/usr/bin/env python3
"""
Generate executable verification suite from configuration.

Usage:
    python generate_verifier.py --config verify_config.json --output .goal-sandbox/verify.py
"""

import argparse
import json
import sys
import os
from datetime import datetime
from pathlib import Path


def load_template(template_name: str, plugin_root: Path) -> type:
    """Load template class dynamically."""
    template_path = plugin_root / "resources" / "verifiers"

    # Find template file
    for category in ["structural", "behavioral", "property"]:
        template_file = template_path / category / template_name
        if template_file.exists():
            # Import template module
            sys.path.insert(0, str(template_path))
            sys.path.insert(0, str(template_file.parent))

            module_name = template_file.stem
            module = __import__(module_name)

            # Find template class
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and
                    attr.__name__.endswith("Template") and
                    attr.__name__ != "VerificationTemplate"):
                    return attr

    raise ValueError(f"Template not found: {template_name}")


def render_verification_method(verification: dict, plugin_root: Path) -> str:
    """Render a single verification method using its template."""
    manifest_path = plugin_root / verification["manifest"]

    # Load manifest to get template name
    import yaml
    with open(manifest_path) as f:
        manifest = yaml.safe_load(f)

    template_name = manifest["template"]
    template_class = load_template(template_name, plugin_root)
    template = template_class()

    # Render verification code
    params = verification.get("params", {})
    code = template.render_with_validation(params)

    # Wrap in a method
    method_name = f"verify_{verification['name']}"
    return f"""
    def {method_name}(self) -> VerificationResult:
        \"\"\"{ verification['type'].title()}: {verification.get('label', verification['name'])}\"\"\"
        import time
        start = time.time()

        # Generated verification code
        passed, message, suggestions = ({code.strip()})()

        return VerificationResult(
            check_name="{verification.get('label', verification['name'])}",
            check_type="{verification['type']}",
            passed=passed,
            message=message,
            suggestions=suggestions,
            execution_time=time.time() - start
        )
"""


def generate_suite(config: dict, plugin_root: Path) -> str:
    """Generate complete verification suite."""

    # Group verifications by type
    by_type = {"structural": [], "behavioral": [], "property": []}
    for v in config["verifications"]:
        by_type[v["type"]].append(v)

    # Generate methods
    methods = []
    run_calls = []

    for vtype in ["structural", "behavioral", "property"]:
        if by_type[vtype]:
            run_calls.append(f"\n        # Phase: {vtype.title()} checks")
            for verification in by_type[vtype]:
                methods.append(render_verification_method(verification, plugin_root))
                method_name = f"verify_{verification['name']}"
                run_calls.append(f"        self.results.append(self.{method_name}())")

    methods_code = "\n".join(methods)
    run_code = "\n".join(run_calls)

    # Generate suite
    suite = f"""#!/usr/bin/env python3
\"\"\"
Verification suite for: {config['goal']}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
\"\"\"

from typing import NamedTuple
import sys
import time


class VerificationResult(NamedTuple):
    check_name: str
    check_type: str
    passed: bool
    message: str
    suggestions: list
    execution_time: float


class VerificationSuite:
    def __init__(self):
        self.results = []

    def run_all(self) -> bool:
        \"\"\"Execute all verifications in order.\"\"\"
        print("━━━ Verification Suite ━━━\\n")

{run_code}

        # Report results
        self.print_report()

        return all(r.passed for r in self.results)

{methods_code}

    def print_report(self):
        \"\"\"Print human-readable summary.\"\"\"
        print("\\n━━━ Verification Report ━━━")

        by_type = {{}}
        for result in self.results:
            by_type.setdefault(result.check_type, []).append(result)

        for check_type, results in by_type.items():
            passed = sum(r.passed for r in results)
            total = len(results)
            symbol = "✓" if passed == total else "✗"
            print(f"\\n{{symbol}} {{check_type.title()}}: {{passed}}/{{total}} passed")

            for r in results:
                status = "✓" if r.passed else "✗"
                time_str = f"({{r.execution_time:.2f}}s)"
                print(f"  {{status}} {{r.check_name}} {{time_str}}")

                if not r.passed:
                    print(f"      {{r.message}}")
                    if r.suggestions:
                        print(f"      Suggestions:")
                        for suggestion in r.suggestions:
                            print(f"        • {{suggestion}}")


if __name__ == "__main__":
    suite = VerificationSuite()
    success = suite.run_all()
    sys.exit(0 if success else 1)
"""

    return suite


def main():
    parser = argparse.ArgumentParser(description="Generate verification suite")
    parser.add_argument("--config", required=True, help="Input config JSON")
    parser.add_argument("--output", required=True, help="Output Python file")
    parser.add_argument("--plugin-root", help="Plugin root directory (auto-detected if not provided)")

    args = parser.parse_args()

    # Find plugin root
    if args.plugin_root:
        plugin_root = Path(args.plugin_root)
    else:
        # Assume we're in scripts/ directory
        plugin_root = Path(__file__).parent.parent

    # Load config
    with open(args.config) as f:
        config = json.load(f)

    # Generate suite
    suite_code = generate_suite(config, plugin_root)

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(suite_code)
    output_path.chmod(0o755)

    print(f"Generated: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

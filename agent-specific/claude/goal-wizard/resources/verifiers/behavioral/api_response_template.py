"""
Template for testing API responses.
"""

import sys
sys.path.insert(0, '/Users/thomaschang/Documents/dev/git/thomaschangsf/skills/plugins/goal-sandbox-plugin/resources/verifiers')

from template_base import VerificationTemplate
from typing import Any, Dict, List


class APIResponseTemplate(VerificationTemplate):
    def required_params(self) -> List[str]:
        return ["endpoint", "expected_status"]

    def optional_params(self) -> Dict[str, Any]:
        return {
            "method": "GET",
            "timeout": 5,
            "base_url": "http://localhost:8000"
        }

    def validate_params(self, params: Dict[str, Any]) -> bool:
        if not params.get("endpoint", "").startswith("/"):
            raise ValueError("endpoint must start with /")
        status = params.get("expected_status")
        if status is None or not (100 <= status < 600):
            raise ValueError("expected_status must be a valid HTTP status code (100-599)")
        return True

    def render(self, params: Dict[str, Any]) -> str:
        return f"""
def verify_api_response():
    try:
        import requests
    except ImportError:
        return False, "requests library not installed", ["pip install requests"]

    url = "{params['base_url']}{params['endpoint']}"
    method = "{params['method']}".upper()

    try:
        if method == "GET":
            response = requests.get(url, timeout={params['timeout']})
        elif method == "POST":
            response = requests.post(url, timeout={params['timeout']})
        elif method == "PUT":
            response = requests.put(url, timeout={params['timeout']})
        elif method == "DELETE":
            response = requests.delete(url, timeout={params['timeout']})
        else:
            return False, f"Unsupported HTTP method: {{method}}", ["Use GET, POST, PUT, or DELETE"]

        if response.status_code == {params['expected_status']}:
            return True, f"API returned expected status {params['expected_status']}", []
        else:
            return False, f"Expected {params['expected_status']}, got {{response.status_code}}", [
                f"Check API implementation at {{url}}",
                f"Response body: {{response.text[:200]}}"
            ]

    except requests.exceptions.ConnectionError:
        return False, f"Cannot connect to {{url}}", [
            "Is the server running?",
            f"Start server on {params['base_url']}"
        ]
    except requests.exceptions.Timeout:
        return False, f"Request timed out after {params['timeout']}s", [
            "Increase timeout if API is slow",
            "Check for performance issues"
        ]
    except Exception as e:
        return False, f"Error making request: {{e}}", [
            f"Test manually: curl -X {{method}} {{url}}"
        ]
"""

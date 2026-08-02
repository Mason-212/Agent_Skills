"""
Base class for all verification templates.

Templates convert user intent → executable Python code.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class VerificationTemplate(ABC):
    """Base class for all verification templates."""

    @abstractmethod
    def required_params(self) -> List[str]:
        """
        Parameters that MUST be provided by user/LLM.

        Returns:
            List of required parameter names
        """
        pass

    @abstractmethod
    def optional_params(self) -> Dict[str, Any]:
        """
        Optional parameters with their default values.

        Returns:
            Dictionary mapping parameter names to default values
        """
        pass

    @abstractmethod
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """
        Validate parameters before rendering.

        Args:
            params: Parameter dictionary to validate

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails with specific error message
        """
        pass

    @abstractmethod
    def render(self, params: Dict[str, Any]) -> str:
        """
        Generate executable verification code.

        Args:
            params: Parameters for code generation

        Returns:
            Python code as a string that can be executed
        """
        pass

    def render_with_validation(self, params: Dict[str, Any]) -> str:
        """
        Validate parameters and render code.

        Args:
            params: Parameters for code generation

        Returns:
            Python code as a string

        Raises:
            ValueError: If required params missing or validation fails
        """
        # Check required params
        missing = [p for p in self.required_params() if p not in params]
        if missing:
            raise ValueError(f"Missing required parameters: {missing}")

        # Merge with defaults
        full_params = {**self.optional_params(), **params}

        # Validate
        self.validate_params(full_params)

        # Render
        return self.render(full_params)

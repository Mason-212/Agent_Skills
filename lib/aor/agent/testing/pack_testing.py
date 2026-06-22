"""Testing utilities for domain pack validation.

Provides standard test edc_harness for validating pack implementations
against the BoundDomainPack contract.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from agent.packs.base import BoundDomainPack, ExecutionContext, PackDescriptor


@dataclass
class MockExecutionContext:
    """Test fixture for ExecutionContext.

    Provides a minimal execution context for testing pack methods.

    Attributes:
        request_id: Test request identifier
        tenant_id: Test tenant identifier
        timestamp: Execution timestamp
        metadata: Additional context metadata
    """
    request_id: str = "test-request-123"
    tenant_id: str = "test-tenant"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_execution_context(self) -> ExecutionContext:
        """Convert to real ExecutionContext."""
        return ExecutionContext(
            request_id=self.request_id,
            tenant_id=self.tenant_id,
            timestamp=self.timestamp,
            metadata=self.metadata
        )


class PackTestHarness:
    """Standard test edc_harness for domain pack validation.

    Provides static methods for validating pack implementations
    against the BoundDomainPack contract.

    Example:
        import pytest

        @pytest.mark.asyncio
        async def test_my_pack():
            pack = MyPack(workspace_dir=Path("/tmp/test"))
            await PackTestHarness.test_pack_lifecycle(pack)
            await PackTestHarness.test_result_building(pack, {"data": [1, 2, 3]})
            PackTestHarness.test_tools(pack)
    """

    @staticmethod
    async def test_pack_lifecycle(pack: BoundDomainPack) -> None:
        """Validate pack lifecycle (open/close) works correctly.

        Tests:
        - Pack can be opened without errors
        - Pack can be closed without errors
        - Close is idempotent (safe to call when already closed)

        Args:
            pack: Pack instance to test

        Raises:
            AssertionError: If lifecycle contract violated
        """
        # Test 1: Normal open/close
        await pack.open()
        assert pack.is_open, \
            "Pack.is_open must be True after open()"
        await pack.close()
        assert not pack.is_open, \
            "Pack.is_open must be False after close()"

        # Test 2: Close is idempotent
        await pack.close()

        # Test 3: Can reopen after close
        await pack.open()
        assert pack.is_open, "Pack.is_open must be True after second open()"
        await pack.close()
        assert not pack.is_open, "Pack.is_open must be False after second close()"

    @staticmethod
    def test_descriptor(pack: BoundDomainPack) -> None:
        """Validate pack descriptor is properly defined.

        Tests:
        - Descriptor returns PackDescriptor instance
        - Required fields are non-empty strings
        - ID follows naming convention (lowercase, underscores)

        Args:
            pack: Pack instance to test

        Raises:
            AssertionError: If descriptor contract violated
        """
        descriptor = pack.descriptor

        assert isinstance(descriptor, PackDescriptor), \
            f"descriptor must return PackDescriptor, got {type(descriptor)}"

        assert descriptor.id, "Pack id must be non-empty"
        assert descriptor.name, "Pack name must be non-empty"
        assert descriptor.version, "Pack version must be non-empty"

        # ID should follow naming convention
        assert descriptor.id.islower(), \
            f"Pack id should be lowercase: {descriptor.id}"
        assert " " not in descriptor.id, \
            f"Pack id should not contain spaces: {descriptor.id}"

    @staticmethod
    async def test_result_building(
        pack: BoundDomainPack,
        mock_output: Any
    ) -> None:
        """Validate result building produces correct format.

        Tests:
        - build_result returns PackResult instance
        - PackResult contains required fields
        - Pack ID matches descriptor

        Args:
            pack: Pack instance to test
            mock_output: Mock orchestrator output to test with

        Raises:
            AssertionError: If result building contract violated
        """
        from agent.packs.base import PackResult

        context = MockExecutionContext().to_execution_context()
        result = pack.build_result(mock_output, context)

        assert isinstance(result, PackResult), \
            f"build_result must return PackResult, got {type(result)}"

        assert result.pack_id == pack.descriptor.id, \
            "PackResult.pack_id must match descriptor.id"

        assert result.request_id == context.request_id, \
            "PackResult.request_id must match context.request_id"

        assert result.output is not None, \
            "PackResult.output must be present"

    @staticmethod
    def test_tools(pack: BoundDomainPack) -> None:
        """Validate pack tools are properly structured.

        Calls ``get_tools(session_id=None)`` — the base class returns ``[]``
        for ``None`` without calling ``_build_tools``, which is the correct
        behaviour for non-conversational callers. To test session-scoped tools,
        call ``get_tools(session_id="test-session")`` directly and pass a
        synthetic but valid session ID.

        Pack authors: override ``_build_tools(session_id)`` (not ``get_tools``)
        to provide tools. ``get_tools`` is a caching wrapper that calls
        ``_build_tools`` exactly once per ``session_id``.

        Tests:
        - get_tools(session_id=None) returns a list
        - Each tool has required attributes (name, description, parameters, execute)
        - Tool names are valid identifiers

        Args:
            pack: Pack instance to test

        Raises:
            AssertionError: If tools contract violated
        """
        tools = pack.get_tools(session_id=None)

        assert isinstance(tools, list), \
            f"get_tools(session_id=None) must return list, got {type(tools)}"

        for i, tool in enumerate(tools):
            # Check required attributes exist
            assert hasattr(tool, 'name'), \
                f"Tool {i} missing 'name' attribute"
            assert hasattr(tool, 'description'), \
                f"Tool {i} missing 'description' attribute"
            assert hasattr(tool, 'parameters'), \
                f"Tool {i} missing 'parameters' attribute"
            assert hasattr(tool, 'execute'), \
                f"Tool {i} missing 'execute' attribute"

            # Validate name is valid identifier
            assert tool.name.isidentifier(), \
                f"Tool name must be valid Python identifier: {tool.name}"

            # Validate execute is callable
            assert callable(tool.execute), \
                f"Tool {tool.name} execute must be callable"

    @staticmethod
    async def test_health_check(pack: BoundDomainPack) -> None:
        """Validate pack health check returns correct format.

        Tests:
        - check_health() returns HealthStatus instance
        - HealthStatus has valid structure

        Args:
            pack: Pack instance to test (must be opened)

        Raises:
            AssertionError: If health check contract violated
        """
        from agent.packs.base import HealthStatus

        status = await pack.check_health()

        assert isinstance(status, HealthStatus), \
            f"check_health must return HealthStatus, got {type(status)}"

        assert isinstance(status.healthy, bool), \
            "HealthStatus.healthy must be boolean"

        assert isinstance(status.message, str), \
            "HealthStatus.message must be string"

        assert isinstance(status.details, dict), \
            "HealthStatus.details must be dict"

    @staticmethod
    async def run_all_tests(pack: BoundDomainPack, mock_output: Any = None) -> None:
        """Run all standard pack tests.

        Convenience method that runs all edc_harness tests in sequence.

        Args:
            pack: Pack instance to test
            mock_output: Mock output for result building test (default: {})

        Raises:
            AssertionError: If any test fails
        """
        if mock_output is None:
            mock_output = {}

        PackTestHarness.test_descriptor(pack)
        await PackTestHarness.test_pack_lifecycle(pack)
        await pack.open()
        try:
            await PackTestHarness.test_result_building(pack, mock_output)
            PackTestHarness.test_tools(pack)
            await PackTestHarness.test_health_check(pack)
        finally:
            await pack.close()

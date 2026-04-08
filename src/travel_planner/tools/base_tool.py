"""Base class for all tools in the tool layer."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional
import time


@dataclass
class ToolResult:
    """Standardized result from tool execution."""

    success: bool
    data: Any | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(cls, data: Any, **metadata) -> "ToolResult":
        """Create a successful result."""
        return cls(success=True, data=data, metadata=metadata)

    @classmethod
    def fail(cls, error: str, **metadata) -> "ToolResult":
        """Create a failed result."""
        return cls(success=False, error=error, metadata=metadata)


@dataclass
class ToolConfig:
    """Configuration for tool execution."""

    timeout_seconds: float = 30.0
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300


class BaseTool(ABC):
    """Abstract base class for all tools.

    Provides:
    - Standardized execution interface
    - Retry logic
    - Caching
    - Logging
    """

    def __init__(self, config: ToolConfig | None = None):
        self.config = config or ToolConfig()
        self._cache: dict[str, tuple[float, Any]] = {}

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name for this tool."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what this tool does."""
        pass

    @abstractmethod
    async def _execute(self, **kwargs) -> ToolResult:
        """Execute the tool's core logic.

        Subclasses must implement this method.
        """
        pass

    async def execute(self, **kwargs) -> ToolResult:
        """Execute with retry and caching support."""
        cache_key = self._build_cache_key(**kwargs)

        # Check cache first
        if self.config.cache_enabled:
            if cached := self._get_from_cache(cache_key):
                return cached

        # Execute with retries
        last_error: Exception | None = None
        for attempt in range(self.config.max_retries):
            try:
                result = await self._execute(**kwargs)
                if result.success and self.config.cache_enabled:
                    self._save_to_cache(cache_key, result)
                return result
            except Exception as e:
                last_error = e
                if attempt < self.config.max_retries - 1:
                    await self._wait_before_retry()

        # All retries exhausted
        return ToolResult.fail(
            error=str(last_error) if last_error else "Unknown error",
            attempts=self.config.max_retries,
        )

    def _build_cache_key(self, **kwargs) -> str:
        """Build a cache key from input arguments."""
        parts = [self.name]
        for k, v in sorted(kwargs.items()):
            parts.append(f"{k}={v}")
        return ":".join(parts)

    def _get_from_cache(self, cache_key: str) -> ToolResult | None:
        """Get cached result if still valid."""
        if cache_key in self._cache:
            timestamp, result = self._cache[cache_key]
            if time.time() - timestamp < self.config.cache_ttl_seconds:
                return result
            del self._cache[cache_key]
        return None

    def _save_to_cache(self, cache_key: str, result: ToolResult) -> None:
        """Save result to cache."""
        self._cache[cache_key] = (time.time(), result)

    async def _wait_before_retry(self) -> None:
        """Wait before retrying."""
        import asyncio
        await asyncio.sleep(self.config.retry_delay_seconds)

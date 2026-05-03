"""Skill Registry - Dynamic discovery and loading of skills.

Pattern 3: Skill Library Mode - Dynamic Discovery + Lazy Loading
- Scans skills/ directory for SKILL.md metadata files
- Lazy loading: metadata first (100 tokens), implementation on-demand
- Provides list_skills/get_skill interfaces for agent discovery
"""

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

# Handle direct execution (add parent directory to path)
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from travel_planner.helpers.logs import get_logger


@dataclass
class SkillMetadata:
    """Metadata for a single skill (loaded from SKILL.md frontmatter).

    Attributes:
        id: Unique skill identifier
        name: Human-readable name
        description: What this skill does
        version: Skill version
        tags: Search tags
        input_schema: Input schema class reference
        output_schema: Output schema class reference
        timeout: Execution timeout in seconds
        is_public: Whether this skill is exposed as a tool
    """
    id: str
    name: str
    description: str
    version: str = "1.0.0"
    author: str = ""
    tags: list[str] = field(default_factory=list)
    input_schema: str = ""
    output_schema: str = ""
    timeout: int = 30
    retry: int = 1
    is_public: bool = True
    skill_dir: Path = field(default=None)

    @classmethod
    def from_frontmatter(cls, frontmatter: dict, skill_dir: Path) -> "SkillMetadata":
        """Create SkillMetadata from SKILL.md frontmatter."""
        return cls(
            id=frontmatter.get("id", ""),
            name=frontmatter.get("name", ""),
            description=frontmatter.get("description", ""),
            version=frontmatter.get("version", "1.0.0"),
            author=frontmatter.get("author", ""),
            tags=frontmatter.get("tags", []),
            input_schema=frontmatter.get("input_schema", ""),
            output_schema=frontmatter.get("output_schema", ""),
            timeout=frontmatter.get("timeout", 30),
            retry=frontmatter.get("retry", 1),
            is_public=frontmatter.get("is_public", True),
            skill_dir=skill_dir,
        )


@dataclass
class LoadedSkill:
    """A fully loaded skill ready for execution.

    Attributes:
        metadata: Skill metadata
        run_func: The skill's run function
        input_schema: Input schema class
        output_schema: Output schema class
    """
    metadata: SkillMetadata
    run_func: Callable[[dict], dict]
    input_schema: Any = None
    output_schema: Any = None


class SkillRegistry:
    """Dynamic skill registry with lazy loading.

    Usage:
        registry = SkillRegistry()
        registry.scan()  # Discover all skills

        # List available skills
        skills = registry.list_skills()

        # Get skill metadata
        meta = registry.get_skill_meta("weather")

        # Load skill implementation on-demand
        skill = registry.get_skill("weather")
        result = skill.run_func({"city": "成都"})
    """

    def __init__(self, skills_dir: str | None = None):
        self.logger = get_logger()
        self.skills_dir = Path(skills_dir) if skills_dir else self._default_skills_dir()
        self._metadata: dict[str, SkillMetadata] = {}  # id -> metadata
        self._loaded_skills: dict[str, LoadedSkill] = {}  # id -> loaded skill

    def _default_skills_dir(self) -> Path:
        """Get default skills directory."""
        return Path(__file__).parent

    def scan(self) -> list[str]:
        """Scan skills/ directory for SKILL.md files and load metadata.

        Returns:
            List of discovered skill IDs
        """
        self._metadata.clear()
        self._loaded_skills.clear()

        skill_dirs = [d for d in self.skills_dir.iterdir()
                      if d.is_dir() and not d.name.startswith("_") and d.name != "__pycache__"]

        for skill_dir in skill_dirs:
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                try:
                    metadata = self._load_metadata(skill_md, skill_dir)
                    self._metadata[metadata.id] = metadata
                    self.logger.info(f"SkillRegistry: Discovered skill '{metadata.id}' ({metadata.name})")
                except Exception as e:
                    self.logger.error(f"SkillRegistry: Failed to load metadata from {skill_md}: {e}")

        self.logger.info(f"SkillRegistry: Found {len(self._metadata)} skills")
        return list(self._metadata.keys())

    def _load_metadata(self, skill_md_path: Path, skill_dir: Path) -> SkillMetadata:
        """Parse SKILL.md frontmatter into SkillMetadata.

        SKILL.md format:
        ---
        id: skill_weather
        name: 天气查询
        description: 查询实时天气
        version: 1.0.0
        tags: [tool, api, weather]
        ---
        """
        content = skill_md_path.read_text(encoding="utf-8")

        # Extract frontmatter (between --- markers)
        if not content.startswith("---"):
            raise ValueError(f"SKILL.md must start with '---': {skill_md_path}")

        parts = content.split("---", 2)
        if len(parts) < 3:
            raise ValueError(f"Invalid SKILL.md format: {skill_md_path}")

        frontmatter_text = parts[1].strip()
        frontmatter = self._parse_frontmatter(frontmatter_text)

        return SkillMetadata.from_frontmatter(frontmatter, skill_dir)

    def _parse_frontmatter(self, text: str) -> dict:
        """Parse YAML-like frontmatter."""
        # Use tomli for TOML parsing (YAML-compatible subset)
        try:
            return tomli.loads(text)
        except Exception:
            # Fallback: simple key-value parsing
            result = {}
            for line in text.split("\n"):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()
                    # Parse arrays like [tool, api]
                    if value.startswith("[") and value.endswith("]"):
                        value = [v.strip() for v in value[1:-1].split(",")]
                    elif value.lower() == "true":
                        value = True
                    elif value.lower() == "false":
                        value = False
                    elif value.isdigit():
                        value = int(value)
                    result[key] = value
            return result

    def list_skills(self) -> list[dict]:
        """List all discovered skills with metadata.

        Returns:
            List of skill metadata dicts (lightweight, no implementation loaded)
        """
        return [
            {
                "id": meta.id,
                "name": meta.name,
                "description": meta.description,
                "version": meta.version,
                "tags": meta.tags,
                "is_public": meta.is_public,
            }
            for meta in self._metadata.values()
        ]

    def get_skill_meta(self, skill_id: str) -> SkillMetadata | None:
        """Get skill metadata by ID (without loading implementation).

        Args:
            skill_id: Skill identifier

        Returns:
            SkillMetadata or None if not found
        """
        return self._metadata.get(skill_id)

    def get_skill(self, skill_id: str) -> LoadedSkill | None:
        """Get a fully loaded skill by ID (lazy loading).

        Args:
            skill_id: Skill identifier

        Returns:
            LoadedSkill or None if not found
        """
        # Check cache first
        if skill_id in self._loaded_skills:
            return self._loaded_skills[skill_id]

        # Load on-demand
        metadata = self._metadata.get(skill_id)
        if not metadata:
            self.logger.error(f"SkillRegistry: Skill '{skill_id}' not found")
            return None

        try:
            loaded = self._load_skill_impl(metadata)
            self._loaded_skills[skill_id] = loaded
            self.logger.info(f"SkillRegistry: Loaded skill implementation '{skill_id}'")
            return loaded
        except Exception as e:
            self.logger.error(f"SkillRegistry: Failed to load skill '{skill_id}': {e}")
            return None

    def _load_skill_impl(self, metadata: SkillMetadata) -> LoadedSkill:
        """Load skill implementation from module.

        Imports:
        - run function from {skill_dir}.impl
        - WeatherInput from {skill_dir}.schema
        - WeatherOutput from {skill_dir}.schema
        """
        skill_dir = metadata.skill_dir
        module_name = f"travel_planner.skills.{skill_dir.name}"

        # Import schema module
        schema_module = __import__(f"{module_name}.schema", fromlist=[""])
        input_schema = getattr(schema_module, "WeatherInput", None)
        output_schema = getattr(schema_module, "WeatherOutput", None)

        # Import impl module
        impl_module = __import__(f"{module_name}.impl", fromlist=[""])
        run_func = getattr(impl_module, "run", None)

        if not run_func:
            raise ValueError(f"Skill '{metadata.id}' missing 'run' function")

        return LoadedSkill(
            metadata=metadata,
            run_func=run_func,
            input_schema=input_schema,
            output_schema=output_schema,
        )

    def get_public_tools(self) -> list[LoadedSkill]:
        """Get all public skills (exposed as tools).

        Returns:
            List of loaded skills with is_public=True
        """
        return [
            self.get_skill(meta.id)
            for meta in self._metadata.values()
            if meta.is_public
        ]


# Global registry instance
_global_registry: SkillRegistry | None = None


def get_skill_registry() -> SkillRegistry:
    """Get or create global skill registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = SkillRegistry()
        _global_registry.scan()
    return _global_registry


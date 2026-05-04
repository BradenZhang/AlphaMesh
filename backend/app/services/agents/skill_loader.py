from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class AgentSkill:
    name: str
    description: str
    body: str
    path: str


class AgentSkillLoader:
    """Load domain skills on demand instead of expanding every prompt."""

    def __init__(self, skills_dir: Path | None = None) -> None:
        self.skills_dir = skills_dir or Path(__file__).parent / "skills"
        self._skills = self._load_skills()

    def list_skills(self) -> list[dict[str, str]]:
        return [
            {
                "name": skill.name,
                "description": skill.description,
                "path": skill.path,
            }
            for skill in self._skills.values()
        ]

    def descriptions(self) -> str:
        if not self._skills:
            return "No domain skills are available."
        return "\n".join(
            f"- {skill.name}: {skill.description}"
            for skill in self._skills.values()
        )

    def get_content(self, name: str) -> str:
        normalized = name.strip().lower()
        skill = self._skills.get(normalized)
        if not skill:
            available = ", ".join(self._skills) or "none"
            return f"Error: unknown skill '{name}'. Available skills: {available}."
        return skill.body.strip()

    def _load_skills(self) -> dict[str, AgentSkill]:
        if not self.skills_dir.exists():
            return {}

        skills: dict[str, AgentSkill] = {}
        for path in sorted(self.skills_dir.rglob("SKILL.md")):
            text = path.read_text(encoding="utf-8")
            metadata, body = self._parse_frontmatter(text)
            name = str(metadata.get("name") or path.parent.name).strip().lower()
            if not name:
                continue
            skills[name] = AgentSkill(
                name=name,
                description=str(metadata.get("description") or "").strip(),
                body=body.strip(),
                path=str(path.relative_to(self.skills_dir)),
            )
        return skills

    def _parse_frontmatter(self, text: str) -> tuple[dict[str, str], str]:
        stripped = text.lstrip()
        if not stripped.startswith("---"):
            return {}, text

        lines = stripped.splitlines()
        metadata: dict[str, str] = {}
        end_index = None
        for index, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                end_index = index
                break
            if ":" in line:
                key, value = line.split(":", 1)
                metadata[key.strip()] = value.strip().strip('"').strip("'")

        if end_index is None:
            return {}, text
        return metadata, "\n".join(lines[end_index + 1 :])


@lru_cache(maxsize=1)
def get_agent_skill_loader() -> AgentSkillLoader:
    return AgentSkillLoader()
